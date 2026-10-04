from flask import Flask, render_template_string, jsonify
from db import supabase
from datetime import datetime
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

# Telegram Bot Username
BOT_USERNAME = "GeoFaceAttendBot"  # Apna bot username daalo

HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GeoFace Attend — Admin Dashboard</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Inter', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 30px 20px;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        .header {
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            border-radius: 20px;
            padding: 30px 40px;
            margin-bottom: 25px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.15);
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 20px;
        }
        .header h1 {
            font-size: 28px;
            font-weight: 800;
            background: linear-gradient(135deg, #667eea, #764ba2);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        .header p {
            color: #6b7280;
            font-size: 14px;
            margin-top: 5px;
        }
        .live-clock {
            font-size: 14px;
            color: #6b7280;
            font-weight: 500;
            padding: 8px 16px;
            background: #f3f4f6;
            border-radius: 10px;
        }
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 20px;
            margin-bottom: 25px;
        }
        .stat-card {
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            border-radius: 20px;
            padding: 30px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.15);
            position: relative;
            overflow: hidden;
            transition: transform 0.3s;
        }
        .stat-card:hover {
            transform: translateY(-5px);
        }
        .stat-card::before {
            content: '';
            position: absolute;
            top: 0; left: 0;
            width: 4px; height: 100%;
        }
        .stat-card.total::before { background: linear-gradient(180deg, #667eea, #764ba2); }
        .stat-card.male::before { background: linear-gradient(180deg, #f093fb, #f5576c); }
        .stat-card.year::before { background: linear-gradient(180deg, #4facfe, #00f2fe); }
        .stat-icon {
            width: 50px; height: 50px;
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 24px;
            margin-bottom: 15px;
            background: linear-gradient(135deg, #667eea, #764ba2);
        }
        .stat-value {
            font-size: 36px;
            font-weight: 800;
            color: #1f2937;
            line-height: 1;
        }
        .stat-label {
            color: #6b7280;
            font-size: 13px;
            font-weight: 500;
            margin-top: 8px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .info-card {
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            border-radius: 20px;
            padding: 30px 40px;
            margin-bottom: 25px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.15);
            display: flex;
            align-items: center;
            justify-content: space-between;
            flex-wrap: wrap;
            gap: 20px;
        }
        .bot-link {
            display: flex;
            align-items: center;
            gap: 15px;
        }
        .bot-logo {
            width: 60px; height: 60px;
            border-radius: 50%;
            background: linear-gradient(135deg, #0088cc, #00a8e8);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 28px;
            color: white;
        }
        .bot-info h3 {
            color: #1f2937;
            font-size: 18px;
            font-weight: 700;
        }
        .bot-info p {
            color: #6b7280;
            font-size: 13px;
            margin-top: 4px;
        }
        .btn-telegram {
            background: linear-gradient(135deg, #0088cc, #00a8e8);
            color: white;
            padding: 14px 28px;
            border-radius: 12px;
            text-decoration: none;
            font-weight: 600;
            font-size: 14px;
            display: inline-flex;
            align-items: center;
            gap: 8px;
            transition: all 0.3s;
            box-shadow: 0 10px 30px rgba(0, 136, 204, 0.3);
        }
        .btn-telegram:hover {
            transform: translateY(-2px);
            box-shadow: 0 15px 40px rgba(0, 136, 204, 0.4);
        }
        .table-section {
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            border-radius: 20px;
            padding: 30px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.15);
        }
        .table-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
            flex-wrap: wrap;
            gap: 15px;
        }
        .table-header h2 {
            font-size: 20px;
            font-weight: 700;
            color: #1f2937;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .search-box {
            padding: 12px 18px;
            border: 2px solid #e5e7eb;
            border-radius: 12px;
            font-family: 'Inter', sans-serif;
            font-size: 14px;
            width: 280px;
            transition: all 0.3s;
            outline: none;
        }
        .search-box:focus {
            border-color: #667eea;
            box-shadow: 0 0 0 4px rgba(102, 126, 234, 0.1);
        }
        table {
            width: 100%;
            border-collapse: collapse;
        }
        thead {
            background: #f9fafb;
            border-radius: 12px;
        }
        th {
            padding: 15px;
            text-align: left;
            font-size: 12px;
            font-weight: 600;
            color: #6b7280;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        th:first-child { border-radius: 12px 0 0 12px; }
        th:last-child { border-radius: 0 12px 12px 0; }
        td {
            padding: 16px 15px;
            border-bottom: 1px solid #f3f4f6;
            color: #374151;
            font-size: 14px;
        }
        tr:hover td {
            background: #fafbfc;
        }
        .roll-badge {
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
            display: inline-block;
        }
        .year-badge {
            background: #dbeafe;
            color: #1e40af;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
            display: inline-block;
        }
        .avatar {
            width: 36px;
            height: 36px;
            border-radius: 50%;
            background: linear-gradient(135deg, #667eea, #764ba2);
            display: inline-flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: 700;
            font-size: 14px;
            margin-right: 10px;
            vertical-align: middle;
        }
        .empty-state {
            text-align: center;
            padding: 60px 20px;
            color: #9ca3af;
        }
        .empty-state .icon {
            font-size: 64px;
            margin-bottom: 15px;
            opacity: 0.5;
        }
        .empty-state p {
            font-size: 15px;
            font-weight: 500;
        }
        .footer {
            text-align: center;
            margin-top: 25px;
            color: rgba(255, 255, 255, 0.8);
            font-size: 13px;
            font-weight: 500;
        }
        @media (max-width: 768px) {
            .header { padding: 20px; }
            .header h1 { font-size: 22px; }
            .stat-card { padding: 20px; }
            .stat-value { font-size: 28px; }
            .info-card { padding: 20px; }
            .table-section { padding: 20px; }
            .search-box { width: 100%; }
            table { font-size: 12px; }
            th, td { padding: 10px 8px; }
        }
    </style>
</head>
<body>
    <div class="container">
        <!-- Header -->
        <div class="header">
            <div>
                <h1>🎓 GeoFace Attend</h1>
                <p>AI-Powered Attendance System — Admin Dashboard</p>
            </div>
            <div class="live-clock" id="liveClock">Loading...</div>
        </div>

        <!-- Stats -->
        <div class="stats-grid">
            <div class="stat-card total">
                <div class="stat-icon">👥</div>
                <div class="stat-value" id="totalCount">0</div>
                <div class="stat-label">Total Registered Students</div>
            </div>
            <div class="stat-card male">
                <div class="stat-icon">📅</div>
                <div class="stat-value" id="todayCount">0</div>
                <div class="stat-label">Registered Today</div>
            </div>
            <div class="stat-card year">
                <div class="stat-icon">🎯</div>
                <div class="stat-value" id="yearCount">0</div>
                <div class="stat-label">Years Covered</div>
            </div>
        </div>

        <!-- Bot Link -->
        <div class="info-card">
            <div class="bot-link">
                <div class="bot-logo">✈️</div>
                <div class="bot-info">
                    <h3>Telegram Bot</h3>
                    <p>Students register here • Teachers send group photos</p>
                </div>
            </div>
            <a href="https://t.me/{{ bot_username }}" target="_blank" class="btn-telegram">
                Open Bot →
            </a>
        </div>

        <!-- Students Table -->
        <div class="table-section">
            <div class="table-header">
                <h2>📋 Registered Students</h2>
                <input type="text" class="search-box" placeholder="🔍 Search by roll or name..." onkeyup="searchTable(this.value)">
            </div>
            <div id="studentsTable">Loading...</div>
        </div>

        <div class="footer">
            🚀 GeoFace Attend System — Powered by AI Face Recognition
        </div>
    </div>

    <script>
        let studentsData = [];

        // Live Clock
        function updateClock() {
            const now = new Date();
            const options = { 
                weekday: 'short', year: 'numeric', month: 'short', 
                day: 'numeric', hour: '2-digit', minute: '2-digit', second: '2-digit'
            };
            document.getElementById('liveClock').textContent = now.toLocaleDateString('en-IN', options);
        }
        updateClock();
        setInterval(updateClock, 1000);

        // Animate Counter
        function animateValue(el, target) {
            const current = parseInt(el.textContent) || 0;
            if (current === target) return;
            const step = target > current ? 1 : -1;
            let val = current;
            const timer = setInterval(() => {
                val += step;
                el.textContent = val;
                if (val === target) clearInterval(timer);
            }, 30);
        }

        // Fetch Students
        async function loadStudents() {
            try {
                const res = await fetch('/api/students');
                studentsData = await res.json();
                renderStudents(studentsData);
                updateStats(studentsData);
            } catch (e) {
                console.error(e);
                document.getElementById('studentsTable').innerHTML = `
                    <div class="empty-state">
                        <div class="icon">⚠️</div>
                        <p>Error loading students</p>
                    </div>`;
            }
        }

        function updateStats(data) {
            animateValue(document.getElementById('totalCount'), data.length);

            // Today's registrations
            const today = new Date().toISOString().split('T')[0];
            const todayCount = data.filter(s => {
                if (!s.created_at) return false;
                return s.created_at.split('T')[0] === today;
            }).length;
            animateValue(document.getElementById('todayCount'), todayCount);

            // Unique years
            const years = new Set(data.map(s => s.year).filter(y => y > 0));
            animateValue(document.getElementById('yearCount'), years.size);
        }

        function renderStudents(data) {
            if (data.length === 0) {
                document.getElementById('studentsTable').innerHTML = `
                    <div class="empty-state">
                        <div class="icon">📭</div>
                        <p>Abhi tak koi student register nahi hua.</p>
                    </div>`;
                return;
            }

            let html = `<table><thead><tr>
                <th>Roll No</th>
                <th>Name</th>
                <th>Course</th>
                <th>Branch</th>
                <th>Year</th>
                <th>Registered On</th>
            </tr></thead><tbody>`;

            data.forEach(s => {
                const initial = (s.name || '?').charAt(0).toUpperCase();
                const date = s.created_at ? new Date(s.created_at).toLocaleDateString('en-IN', {
                    day: '2-digit', month: 'short', year: 'numeric'
                }) : '—';

                html += `<tr>
                    <td><span class="roll-badge">${s.roll_no || '—'}</span></td>
                    <td><span class="avatar">${initial}</span>${s.name || '—'}</td>
                    <td>${s.course || '—'}</td>
                    <td>${s.branch || '—'}</td>
                    <td><span class="year-badge">Year ${s.year || '—'}</span></td>
                    <td>${date}</td>
                </tr>`;
            });

            html += '</tbody></table>';
            document.getElementById('studentsTable').innerHTML = html;
        }

        function searchTable(query) {
            const q = query.toLowerCase();
            const filtered = studentsData.filter(s =>
                String(s.roll_no || '').toLowerCase().includes(q) ||
                String(s.name || '').toLowerCase().includes(q) ||
                String(s.branch || '').toLowerCase().includes(q)
            );
            renderStudents(filtered);
        }

        // Initial Load + Auto Refresh
        loadStudents();
        setInterval(loadStudents, 15000);
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML, bot_username=BOT_USERNAME)

@app.route('/api/students')
def get_students():
    """Saare registered students lao"""
    try:
        response = supabase.table("students").select(
            "roll_no, name, course, branch, year, created_at"
        ).order("created_at", desc=True).execute()
        return jsonify(response.data)
    except Exception as e:
        app.logger.error(f"Students fetch error: {e}")
        return jsonify([])

if __name__ == '__main__':
    print("=" * 50)
    print("🌐 Dashboard: http://localhost:5001")
    print("=" * 50)
    app.run(debug=True, port=5001)