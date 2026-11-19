"""GeoFace Attend - Teacher Dashboard (Flask)

What it does:
  1. Upload the Excel sheets sent by the bot (one or many), choose the subject and date
  2. A student is saved only ONCE per day per subject (duplicates are removed automatically)
  3. View daily / monthly records and download them as Excel
  4. List of registered students

Needs an `attendance_records` table in Supabase (SQL is in the setup notes).
Env vars: SUPABASE_URL, SUPABASE_KEY (read by db.py), DASHBOARD_PASSWORD (optional but recommended).
"""
import calendar
import hmac
import io
import json
import os
from collections import defaultdict
from datetime import datetime, timedelta

from flask import Flask, Response, jsonify, request, send_file
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Alignment, Font, PatternFill

from db import supabase

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 4 * 1024 * 1024  # Vercel's request body limit is ~4.5 MB

BOT_USERNAME = "GeoFaceAttendBot"
SUBJECTS = ["TOC", "Deep Learning", "Virtualization", "Maths for ML"]  # edit this list if needed
SHEET_TIME_IS_UTC = True  # the bot runs on Render (UTC); set to False if the bot's time is ever changed to IST
IST_OFFSET = timedelta(hours=5, minutes=30)
TABLE = "attendance_records"


# ---------------------------------------------------------------- login (optional)
@app.before_request
def require_login():
    password = os.getenv("DASHBOARD_PASSWORD")
    if not password:
        return None
    auth = request.authorization
    if auth and auth.password and hmac.compare_digest(auth.password, password):
        return None
    return Response("Login required", 401, {"WWW-Authenticate": 'Basic realm="GeoFace Dashboard"'})


@app.errorhandler(413)
def too_big(_):
    return jsonify(error="Files are too large (keep the total under 4 MB)"), 413


# ---------------------------------------------------------------- helpers
def norm_roll(value):
    return str(value).strip().upper()


def sheet_time_to_ist(raw):
    """Sheet time (HH:MM:SS) -> '10:05 AM' (IST)."""
    if not raw:
        return ""
    try:
        t = datetime.strptime(str(raw)[:8], "%H:%M:%S")
        if SHEET_TIME_IS_UTC:
            t += IST_OFFSET
        return t.strftime("%I:%M %p")
    except ValueError:
        return str(raw)


def parse_sheet(file_bytes):
    """Read a bot Excel sheet. The header row is found by the 'Roll No' column, so title rows do not matter."""
    wb = load_workbook(io.BytesIO(file_bytes), data_only=True, read_only=True)
    ws = wb.active
    header_idx, cols = None, {}
    all_rows = list(ws.iter_rows(values_only=True))
    for i, row in enumerate(all_rows[:15]):
        names = [str(c).strip().lower() if c is not None else "" for c in row]
        if "roll no" in names:
            header_idx = i
            cols = {n: j for j, n in enumerate(names) if n}
            break
    if header_idx is None:
        raise ValueError("'Roll No' column not found - this does not look like a bot attendance sheet")

    def cell(row, key):
        j = cols.get(key)
        if j is None or j >= len(row) or row[j] is None:
            return ""
        return str(row[j]).strip()

    out = []
    for row in all_rows[header_idx + 1:]:
        roll = cell(row, "roll no")
        if not roll or roll.upper() == "N/A":
            continue
        year = cell(row, "year")
        out.append({
            "roll_no": norm_roll(roll),
            "name": cell(row, "name"),
            "course": cell(row, "course"),
            "branch": cell(row, "branch"),
            "year": int(year) if year.isdigit() else None,
            "raw_time": cell(row, "time"),
        })
    return out


def fetch_records(start, end, subject=None):
    """Supabase returns at most 1000 rows per request, so read page by page."""
    rows, step, offset = [], 1000, 0
    while True:
        q = supabase.table(TABLE).select("*").gte("class_date", start).lte("class_date", end)
        if subject:
            q = q.eq("subject", subject)
        data = q.order("id").range(offset, offset + step - 1).execute().data
        rows += data
        if len(data) < step:
            return rows
        offset += step


def fetch_students():
    return (supabase.table("students")
            .select("roll_no, name, course, branch, year, created_at")
            .order("created_at", desc=True).execute().data)


def valid_date(text):
    try:
        datetime.strptime(text, "%Y-%m-%d")
        return True
    except (TypeError, ValueError):
        return False


def valid_month(text):
    try:
        datetime.strptime(text, "%Y-%m")
        return True
    except (TypeError, ValueError):
        return False


def monthly_summary(month, subject=None):
    year, mon = map(int, month.split("-"))
    last_day = calendar.monthrange(year, mon)[1]
    recs = fetch_records(f"{month}-01", f"{month}-{last_day:02d}", subject)

    if subject:
        subjects = [subject]
    else:
        subjects = SUBJECTS + sorted({r["subject"] for r in recs} - set(SUBJECTS))

    held = {s: len({r["class_date"] for r in recs if r["subject"] == s}) for s in subjects}
    total_held = sum(held.values())

    people = {}
    for s in fetch_students():  # include every registered student so absentees show 0
        people[norm_roll(s["roll_no"])] = {"roll_no": norm_roll(s["roll_no"]), "name": s["name"] or "", "per": defaultdict(int)}
    for r in recs:
        p = people.setdefault(r["roll_no"], {"roll_no": r["roll_no"], "name": r.get("name") or "", "per": defaultdict(int)})
        p["per"][r["subject"]] += 1

    students = []
    for p in people.values():
        attended = sum(p["per"].get(s, 0) for s in subjects)
        students.append({
            "roll_no": p["roll_no"], "name": p["name"],
            "per": {s: p["per"].get(s, 0) for s in subjects},
            "attended": attended,
            "pct": round(100 * attended / total_held, 1) if total_held else 0,
        })
    students.sort(key=lambda x: x["roll_no"])
    return {"subjects": subjects, "held": held, "total_held": total_held, "students": students}


def build_xlsx(title, headers, rows, widths=None):
    wb = Workbook()
    ws = wb.active
    ws.title = "Records"
    ws.append([title])
    ws["A1"].font = Font(bold=True, size=13)
    ws.append([])
    ws.append(headers)
    for c in ws[3]:
        c.font = Font(bold=True, color="FFFFFF")
        c.fill = PatternFill("solid", start_color="4F46E5", end_color="4F46E5")
        c.alignment = Alignment(horizontal="center")
    for r in rows:
        ws.append(r)
    for i, w in enumerate(widths or [], 1):
        ws.column_dimensions[ws.cell(row=3, column=i).column_letter].width = w
    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf


def xlsx_response(buf, filename):
    return send_file(
        buf, as_attachment=True, download_name=filename,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


# ---------------------------------------------------------------- API
@app.route("/api/upload", methods=["POST"])
def api_upload():
    subject = request.form.get("subject", "").strip()
    class_date = request.form.get("date", "").strip()
    files = request.files.getlist("files")

    if subject not in SUBJECTS:
        return jsonify(error="Please select a subject"), 400
    if not valid_date(class_date):
        return jsonify(error="Please select a valid date"), 400
    if not files:
        return jsonify(error="Please select at least one Excel file"), 400

    merged, per_file, rows_read = {}, [], 0
    for f in files:
        try:
            rows = parse_sheet(f.read())
        except Exception as e:  # one bad file does not stop the others
            text = str(e) if isinstance(e, ValueError) else "This is not a valid .xlsx file"
            per_file.append({"file": f.filename, "ok": False, "msg": text})
            continue
        rows_read += len(rows)
        per_file.append({"file": f.filename, "ok": True, "rows": len(rows)})
        for r in rows:
            old = merged.get(r["roll_no"])
            if old is None or (r["raw_time"] or "~") < (old["raw_time"] or "~"):
                merged[r["roll_no"]] = r  # keep the earliest time

    if not merged:
        return jsonify(error="No students found in any of the files", files=per_file), 400

    try:
        existing = (supabase.table(TABLE).select("roll_no")
                    .eq("class_date", class_date).eq("subject", subject).execute().data)
        already = {e["roll_no"] for e in existing}
        new_rows = [r for roll, r in merged.items() if roll not in already]
        if new_rows:
            payload = [{
                "class_date": class_date, "subject": subject, "roll_no": r["roll_no"],
                "name": r["name"], "course": r["course"], "branch": r["branch"], "year": r["year"],
                "marked_time": sheet_time_to_ist(r["raw_time"]),
            } for r in new_rows]
            supabase.table(TABLE).upsert(
                payload, on_conflict="class_date,subject,roll_no", ignore_duplicates=True
            ).execute()
    except Exception as e:
        return jsonify(error=f"Database error: {e}"), 500

    return jsonify(
        files=per_file,
        rows_read=rows_read,
        unique_students=len(merged),
        duplicates_in_upload=rows_read - len(merged),
        newly_added=len(new_rows),
        already_saved=len(merged) - len(new_rows),
    )


@app.route("/api/records")
def api_records():
    date = request.args.get("date", "")
    subject = request.args.get("subject", "") or None
    if not valid_date(date):
        return jsonify(error="Please select a valid date"), 400
    try:
        rows = fetch_records(date, date, subject)
    except Exception as e:
        return jsonify(error=str(e)), 500
    rows.sort(key=lambda r: (r["subject"], r["roll_no"]))
    return jsonify(rows)


@app.route("/api/monthly")
def api_monthly():
    month = request.args.get("month", "")
    subject = request.args.get("subject", "") or None
    if not valid_month(month):
        return jsonify(error="Please select a valid month"), 400
    try:
        return jsonify(monthly_summary(month, subject))
    except Exception as e:
        return jsonify(error=str(e)), 500


@app.route("/api/delete", methods=["POST"])
def api_delete():
    body = request.get_json(silent=True) or {}
    date, subject = body.get("date", ""), body.get("subject", "")
    if not valid_date(date) or subject not in SUBJECTS:
        return jsonify(error="Both date and subject are required"), 400
    try:
        supabase.table(TABLE).delete().eq("class_date", date).eq("subject", subject).execute()
    except Exception as e:
        return jsonify(error=str(e)), 500
    return jsonify(ok=True)


@app.route("/api/students")
def api_students():
    try:
        return jsonify(fetch_students())
    except Exception as e:
        app.logger.error(f"students error: {e}")
        return jsonify([])


# ---------------------------------------------------------------- Excel downloads
@app.route("/export/daily")
def export_daily():
    date = request.args.get("date", "")
    subject = request.args.get("subject", "") or None
    if not valid_date(date):
        return "Please select a valid date", 400
    rows = fetch_records(date, date, subject)
    rows.sort(key=lambda r: (r["subject"], r["roll_no"]))
    data = [[i, r["class_date"], r["subject"], r["roll_no"], r["name"], r["course"], r["branch"], r["year"], r["marked_time"]]
            for i, r in enumerate(rows, 1)]
    buf = build_xlsx(
        f"Attendance - {date}" + (f" - {subject}" if subject else ""),
        ["S.No", "Date", "Subject", "Roll No", "Name", "Course", "Branch", "Year", "Time"],
        data, [7, 13, 18, 13, 26, 10, 10, 7, 11],
    )
    return xlsx_response(buf, f"attendance_{date}{'_' + subject.replace(' ', '') if subject else ''}.xlsx")


@app.route("/export/monthly")
def export_monthly():
    month = request.args.get("month", "")
    subject = request.args.get("subject", "") or None
    if not valid_month(month):
        return "Please select a valid month", 400
    s = monthly_summary(month, subject)
    headers = ["Roll No", "Name"] + [f"{sub} (held {s['held'][sub]})" for sub in s["subjects"]] + ["Total attended", "Total held", "%"]
    data = [[st["roll_no"], st["name"]] + [st["per"][sub] for sub in s["subjects"]] + [st["attended"], s["total_held"], st["pct"]]
            for st in s["students"]]
    buf = build_xlsx(f"Monthly attendance - {month}" + (f" - {subject}" if subject else ""), headers, data,
                     [13, 26] + [18] * len(s["subjects"]) + [15, 12, 8])
    return xlsx_response(buf, f"monthly_{month}{'_' + subject.replace(' ', '') if subject else ''}.xlsx")


# ---------------------------------------------------------------- page
PAGE = r"""<!DOCTYPE html>
<html lang="en"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>GeoFace Attend - Dashboard</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'Inter',sans-serif;background:linear-gradient(135deg,#667eea,#764ba2);min-height:100vh;padding:24px 14px;color:#1f2937}
.wrap{max-width:1100px;margin:0 auto}
.card{background:rgba(255,255,255,.96);border-radius:18px;padding:24px;box-shadow:0 20px 50px rgba(0,0,0,.15);margin-bottom:18px}
h1{font-size:26px;font-weight:800;background:linear-gradient(135deg,#667eea,#764ba2);-webkit-background-clip:text;-webkit-text-fill-color:transparent}
.sub{color:#6b7280;font-size:13px;margin-top:4px}
.top{display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:12px}
.tabs{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:18px}
.tabbtn{border:none;background:rgba(255,255,255,.35);color:#fff;font:600 14px 'Inter';padding:11px 20px;border-radius:12px;cursor:pointer}
.tabbtn.active{background:#fff;color:#4f46e5}
.row{display:flex;gap:12px;flex-wrap:wrap;align-items:flex-end;margin-bottom:16px}
.field{display:flex;flex-direction:column;gap:5px}
label{font-size:12px;font-weight:600;color:#6b7280;text-transform:uppercase;letter-spacing:.4px}
input,select{padding:11px 14px;border:2px solid #e5e7eb;border-radius:10px;font:500 14px 'Inter';min-width:170px}
input:focus,select:focus{outline:none;border-color:#667eea}
.btn{border:none;border-radius:10px;padding:12px 22px;font:600 14px 'Inter';cursor:pointer;color:#fff;background:linear-gradient(135deg,#667eea,#764ba2);text-decoration:none;display:inline-block}
.btn.green{background:linear-gradient(135deg,#10b981,#059669)}
.btn.red{background:linear-gradient(135deg,#ef4444,#dc2626)}
.btn:disabled{opacity:.5;cursor:wait}
.msg{margin:10px 0;font-size:14px;font-weight:500}.msg.err{color:#dc2626}
.stats{display:flex;gap:12px;flex-wrap:wrap;margin:6px 0 14px}
.stat{background:#f3f4f6;border-radius:12px;padding:12px 18px;font-size:13px;color:#6b7280}
.stat b{display:block;font-size:22px;color:#1f2937}
.scroll{overflow-x:auto}
table{width:100%;border-collapse:collapse}
th{background:#f9fafb;padding:12px;text-align:left;font-size:12px;color:#6b7280;text-transform:uppercase;letter-spacing:.4px;white-space:nowrap}
td{padding:12px;border-bottom:1px solid #f3f4f6;font-size:14px}
.empty{text-align:center;color:#9ca3af;padding:40px 10px}
.ok{color:#059669;font-weight:600}.bad{color:#dc2626;font-weight:600}
.low{color:#dc2626;font-weight:700}
.hint{font-size:13px;color:#6b7280;margin-top:10px;line-height:1.6}
</style></head><body><div class="wrap">

<div class="card top">
  <div><h1>GeoFace Attend</h1><div class="sub">Teacher Dashboard - attendance records</div></div>
  <a class="btn" href="https://t.me/__BOT__" target="_blank">Open Telegram Bot</a>
</div>

<div class="tabs">
  <button class="tabbtn active" data-tab="upload" onclick="showTab('upload')">Upload</button>
  <button class="tabbtn" data-tab="daily" onclick="showTab('daily')">Daily</button>
  <button class="tabbtn" data-tab="monthly" onclick="showTab('monthly')">Monthly</button>
  <button class="tabbtn" data-tab="students" onclick="showTab('students')">Students</button>
</div>

<div class="card tab" id="tab-upload">
  <h2 style="margin-bottom:14px">Upload attendance sheets</h2>
  <div class="row">
    <div class="field"><label>Subject</label><select id="upSubject"></select></div>
    <div class="field"><label>Class date</label><input type="date" id="upDate"></div>
    <div class="field"><label>Excel file(s)</label><input type="file" id="files" accept=".xlsx" multiple></div>
    <button class="btn green" id="upBtn" onclick="doUpload()">Upload</button>
  </div>
  <div class="msg" id="upMsg"></div>
  <div id="upResult"></div>
  <div class="hint">
    Select all the sheets generated for one class together (the first photo plus any sheets for missed students).<br>
    No matter how many sheets a student appears in, they are counted only once for that subject on that day.
  </div>
</div>

<div class="card tab" id="tab-daily" style="display:none">
  <div class="row">
    <div class="field"><label>Date</label><input type="date" id="dDate"></div>
    <div class="field"><label>Subject</label><select id="dSubject"></select></div>
    <button class="btn" onclick="loadDaily()">Show</button>
    <a class="btn green" id="dExport" href="#">Download Excel</a>
    <button class="btn red" onclick="delDay()">Delete this day's record</button>
  </div>
  <div class="msg" id="dMsg"></div>
  <div class="stats" id="dStats"></div>
  <div class="scroll" id="dTable"></div>
</div>

<div class="card tab" id="tab-monthly" style="display:none">
  <div class="row">
    <div class="field"><label>Month</label><input type="month" id="mMonth"></div>
    <div class="field"><label>Subject</label><select id="mSubject"></select></div>
    <button class="btn" onclick="loadMonthly()">Show</button>
    <a class="btn green" id="mExport" href="#">Download Excel</a>
  </div>
  <div class="msg" id="mMsg"></div>
  <div class="stats" id="mStats"></div>
  <div class="scroll" id="mTable"></div>
  <div class="hint">"Held" = number of days in that month on which a record was uploaded for that subject. The percentage is calculated from this.</div>
</div>

<div class="card tab" id="tab-students" style="display:none">
  <div class="row">
    <div class="field"><label>Search</label><input type="text" id="sSearch" placeholder="roll no. or name" oninput="renderStudents()"></div>
  </div>
  <div class="stats" id="sStats"></div>
  <div class="scroll" id="sTable"></div>
</div>

</div>
<script>
const SUBJECTS = __SUBJECTS__;
const $ = id => document.getElementById(id);
const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const today = new Date(Date.now() - new Date().getTimezoneOffset() * 60000).toISOString().slice(0, 10);
let students = [];

function fillSubjects(id, withAll) {
  $(id).innerHTML = (withAll ? '<option value="">All subjects</option>' : '') +
    SUBJECTS.map(s => '<option>' + esc(s) + '</option>').join('');
}
function msg(id, text, err) { $(id).textContent = text || ''; $(id).className = 'msg' + (err ? ' err' : ''); }
function table(headers, rows) {
  if (!rows.length) return '<div class="empty">No records found</div>';
  return '<table><tr>' + headers.map(h => '<th>' + esc(h) + '</th>').join('') + '</tr>' +
    rows.map(r => '<tr>' + r.map(c => '<td>' + c + '</td>').join('') + '</tr>').join('') + '</table>';
}
function stat(label, value) { return '<div class="stat"><b>' + esc(value) + '</b>' + esc(label) + '</div>'; }

function showTab(name) {
  document.querySelectorAll('.tab').forEach(t => t.style.display = t.id === 'tab-' + name ? 'block' : 'none');
  document.querySelectorAll('.tabbtn').forEach(b => b.classList.toggle('active', b.dataset.tab === name));
  if (name === 'daily') loadDaily();
  if (name === 'monthly') loadMonthly();
  if (name === 'students') loadStudents();
}

async function doUpload() {
  const files = $('files').files;
  if (!files.length) return msg('upMsg', 'Please select Excel file(s) first', true);
  const fd = new FormData();
  fd.append('subject', $('upSubject').value);
  fd.append('date', $('upDate').value);
  for (const f of files) fd.append('files', f);
  $('upBtn').disabled = true; $('upResult').innerHTML = ''; msg('upMsg', 'Uploading...');
  try {
    const res = await fetch('/api/upload', { method: 'POST', body: fd });
    const d = await res.json();
    if (!res.ok) throw new Error(d.error || 'Upload failed');
    msg('upMsg', 'Done! ' + d.newly_added + ' new students saved.');
    $('upResult').innerHTML = '<div class="stats">' +
      stat('rows read', d.rows_read) + stat('unique students', d.unique_students) +
      stat('duplicates removed', d.duplicates_in_upload) + stat('newly saved', d.newly_added) +
      stat('already saved', d.already_saved) + '</div>' +
      d.files.map(f => '<div class="' + (f.ok ? 'ok' : 'bad') + '">' + esc(f.file) + ': ' +
        (f.ok ? f.rows + ' rows read' : esc(f.msg)) + '</div>').join('');
    $('files').value = '';
  } catch (e) { msg('upMsg', e.message, true); }
  $('upBtn').disabled = false;
}

async function loadDaily() {
  const date = $('dDate').value, sub = $('dSubject').value;
  $('dExport').href = '/export/daily?date=' + encodeURIComponent(date) + '&subject=' + encodeURIComponent(sub);
  msg('dMsg', 'Loading...');
  try {
    const res = await fetch('/api/records?date=' + encodeURIComponent(date) + '&subject=' + encodeURIComponent(sub));
    const rows = await res.json();
    if (!res.ok) throw new Error(rows.error || 'Error');
    msg('dMsg', '');
    const bySubject = {};
    rows.forEach(r => bySubject[r.subject] = (bySubject[r.subject] || 0) + 1);
    $('dStats').innerHTML = stat('total present', rows.length) +
      Object.keys(bySubject).map(s => stat(s, bySubject[s])).join('');
    $('dTable').innerHTML = table(['Roll No', 'Name', 'Subject', 'Time'],
      rows.map(r => [esc(r.roll_no), esc(r.name), esc(r.subject), esc(r.marked_time)]));
  } catch (e) { msg('dMsg', e.message, true); }
}

async function delDay() {
  const date = $('dDate').value, subject = $('dSubject').value;
  if (!subject) return alert('Select a subject first to delete its record');
  if (!confirm('This will delete all ' + subject + ' records for ' + date + '. Are you sure?')) return;
  const res = await fetch('/api/delete', { method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ date, subject }) });
  const d = await res.json();
  if (!res.ok) return msg('dMsg', d.error || 'Delete failed', true);
  loadDaily();
}

async function loadMonthly() {
  const month = $('mMonth').value, sub = $('mSubject').value;
  $('mExport').href = '/export/monthly?month=' + encodeURIComponent(month) + '&subject=' + encodeURIComponent(sub);
  msg('mMsg', 'Loading...');
  try {
    const res = await fetch('/api/monthly?month=' + encodeURIComponent(month) + '&subject=' + encodeURIComponent(sub));
    const d = await res.json();
    if (!res.ok) throw new Error(d.error || 'Error');
    msg('mMsg', '');
    $('mStats').innerHTML = stat('students', d.students.length) +
      d.subjects.map(s => stat(s + ' (classes held)', d.held[s])).join('');
    $('mTable').innerHTML = table(
      ['Roll No', 'Name'].concat(d.subjects, ['Total', '%']),
      d.students.map(s => [esc(s.roll_no), esc(s.name)]
        .concat(d.subjects.map(sub => s.per[sub] + ' / ' + d.held[sub]))
        .concat([s.attended + ' / ' + d.total_held,
                 '<span class="' + (d.total_held && s.pct < 75 ? 'low' : '') + '">' + s.pct + '%</span>'])));
  } catch (e) { msg('mMsg', e.message, true); }
}

async function loadStudents() {
  try { students = await (await fetch('/api/students')).json(); } catch (e) { students = []; }
  renderStudents();
}
function renderStudents() {
  const q = $('sSearch').value.toLowerCase();
  const list = students.filter(s => (s.roll_no + ' ' + s.name).toLowerCase().includes(q));
  $('sStats').innerHTML = stat('registered students', students.length);
  $('sTable').innerHTML = table(['Roll No', 'Name', 'Course', 'Branch', 'Year'],
    list.map(s => [esc(s.roll_no), esc(s.name), esc(s.course), esc(s.branch), esc(s.year)]));
}

fillSubjects('upSubject', false); fillSubjects('dSubject', true); fillSubjects('mSubject', true);
$('upDate').value = today; $('dDate').value = today; $('mMonth').value = today.slice(0, 7);
</script></body></html>
"""


@app.route("/")
def index():
    return PAGE.replace("__SUBJECTS__", json.dumps(SUBJECTS)).replace("__BOT__", BOT_USERNAME)


if __name__ == "__main__":
    print("Dashboard: http://localhost:5001")
    app.run(debug=True, port=5001)
