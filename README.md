<h1 align="center">🎓 GeoFace Attend</h1>

<p align="center"><b>Take attendance with one photo — AI recognises the class, Excel does the paperwork.</b></p>

<p align="center"><code>Group Photo → Face Detection → Face Matching → Excel Sheet → Dashboard Records</code></p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/Telegram_Bot-26A5E4?style=for-the-badge&logo=telegram&logoColor=white" alt="Telegram Bot">
  <img src="https://img.shields.io/badge/Flask-000000?style=for-the-badge&logo=flask&logoColor=white" alt="Flask">
  <img src="https://img.shields.io/badge/Supabase-3ECF8E?style=for-the-badge&logo=supabase&logoColor=white" alt="Supabase">
  <img src="https://img.shields.io/badge/PostgreSQL-4169E1?style=for-the-badge&logo=postgresql&logoColor=white" alt="PostgreSQL">
  <img src="https://img.shields.io/badge/OpenCV-5C3EE8?style=for-the-badge&logo=opencv&logoColor=white" alt="OpenCV">
  <img src="https://img.shields.io/badge/Render-46E3B7?style=for-the-badge&logo=render&logoColor=black" alt="Render">
  <img src="https://img.shields.io/badge/Vercel-000000?style=for-the-badge&logo=vercel&logoColor=white" alt="Vercel">
  <img src="https://img.shields.io/badge/Status-Deployed-brightgreen?style=for-the-badge" alt="Status: Deployed">
</p>

---

## 🧠 What is this?

Taking attendance by roll call wastes class time and is easy to cheat — friends can mark absent students present. **GeoFace Attend** replaces roll call with a single photo of the class: the teacher sends one group photo to a Telegram bot, the bot recognises every registered student by face, and replies with a ready-made Excel attendance sheet. A web dashboard then stores those sheets as clean daily and monthly records.

- 📸 One photo of the whole class instead of calling names
- 📊 An Excel sheet in the chat within seconds
- 🗂️ Duplicate-free daily records and monthly attendance percentages
- 🔒 Only a 128-number face signature is stored — never the photo

*Built as a B.Tech 3rd-year individual project at Career Point University, Kota (CSE – AI/ML).*

---

## ✨ Features

| Capability | Description |
|---|---|
| **📝 One-time Registration** | Students register once on Telegram with roll number, name, course, branch, year and a selfie. |
| **🧬 Face Embeddings** | Each face becomes a 128-number signature; the photo itself is never saved. |
| **📸 Group-Photo Attendance** | The teacher sends one class photo; every detected face is matched against all registered students. |
| **🔄 Orientation Fix** | EXIF correction and a 0°/90°/180°/270° retry so sideways phone photos still work. |
| **📑 Instant Excel Sheet** | A styled `.xlsx` with roll no, name, course, branch, year and time is sent back in the same chat. |
| **➕ Missed Students** | Anyone not recognised can be covered by sending another photo — each photo gives another sheet. |
| **⬆️ Dashboard Upload** | Upload one or many sheets, choose subject and date; each student is saved only once per day per subject. |
| **📅 Daily Records** | See who was present on any date, download as Excel, or delete a wrongly uploaded day. |
| **📈 Monthly Report** | Per-student attended / held per subject, total and percentage; below 75% is highlighted. |
| **🔐 Password Protection** | Optional login for the dashboard through an environment variable. |
| **💸 Zero Cost** | Runs on free tiers only — Render, Vercel, Supabase and UptimeRobot. |

---

## 🏗️ Architecture & Pipeline

```
 Student ──/register──┐                      Teacher ──group photo──┐
                      ▼                                             ▼
        ┌─────────────────────────────────────────────────────────────┐
        │              Telegram Bot  (bot.py · Render)                │
        └──────────────────────────────┬──────────────────────────────┘
                                       ▼
        ┌─────────────────────────────────────────────────────────────┐
        │   Face Engine  (face_utils.py · dlib / face_recognition)    │
        │   fix rotation → detect faces → 128-d embedding → match     │
        │   → distance ≤ 0.6, one student per face                    │
        └──────────┬────────────────────────────────────┬─────────────┘
                   ▼                                    ▼
     ┌───────────────────────────┐        ┌─────────────────────────────┐
     │ Supabase  `students`      │        │ Excel sheet (excel_utils.py)│
     │ roll_no · name · embedding│        │ sent back to teacher        │
     └───────────────────────────┘        └──────────────┬──────────────┘
                                                         │  upload 1…n sheets
                                                         ▼
        ┌─────────────────────────────────────────────────────────────┐
        │     Dashboard  (dashboard_app/app.py · Flask · Vercel)      │
        │     merge sheets → remove duplicates → pick subject + date  │
        └──────────────────────────────┬──────────────────────────────┘
                                       ▼
        ┌─────────────────────────────────────────────────────────────┐
        │  Supabase  `attendance_records`  (unique: date+subject+roll)│
        └──────────────────────────────┬──────────────────────────────┘
                                       ▼
                     Daily view · Monthly report · Excel export
```

> 🔔 **UptimeRobot** pings the bot every 5 minutes so the free Render server never goes to sleep.

---

## 🛠️ Tech Stack

| Category | Technology |
|---|---|
| **Language** | <img src="https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python"> |
| **Bot Interface** | <img src="https://img.shields.io/badge/Telegram_Bot_API-26A5E4?style=flat-square&logo=telegram&logoColor=white" alt="Telegram"> <img src="https://img.shields.io/badge/python--telegram--bot-22.8-26A5E4?style=flat-square" alt="python-telegram-bot"> |
| **Face Recognition** | <img src="https://img.shields.io/badge/face__recognition-1.3.0-blueviolet?style=flat-square" alt="face_recognition"> <img src="https://img.shields.io/badge/dlib--bin-20.0.1-orange?style=flat-square" alt="dlib-bin"> |
| **Image & Data** | <img src="https://img.shields.io/badge/OpenCV-5C3EE8?style=flat-square&logo=opencv&logoColor=white" alt="OpenCV"> <img src="https://img.shields.io/badge/Pillow-FFD43B?style=flat-square" alt="Pillow"> <img src="https://img.shields.io/badge/NumPy-013243?style=flat-square&logo=numpy&logoColor=white" alt="NumPy"> |
| **Excel** | <img src="https://img.shields.io/badge/openpyxl-217346?style=flat-square&logo=microsoftexcel&logoColor=white" alt="openpyxl"> |
| **Dashboard Backend** | <img src="https://img.shields.io/badge/Flask-000000?style=flat-square&logo=flask&logoColor=white" alt="Flask"> |
| **Dashboard Frontend** | <img src="https://img.shields.io/badge/HTML5-E34F26?style=flat-square&logo=html5&logoColor=white" alt="HTML5"> <img src="https://img.shields.io/badge/CSS3-1572B6?style=flat-square&logo=css3&logoColor=white" alt="CSS3"> <img src="https://img.shields.io/badge/JavaScript-F7DF1E?style=flat-square&logo=javascript&logoColor=black" alt="JavaScript"> |
| **Database** | <img src="https://img.shields.io/badge/Supabase-3ECF8E?style=flat-square&logo=supabase&logoColor=white" alt="Supabase"> <img src="https://img.shields.io/badge/PostgreSQL-4169E1?style=flat-square&logo=postgresql&logoColor=white" alt="PostgreSQL"> |
| **Deployment** | <img src="https://img.shields.io/badge/Render-46E3B7?style=flat-square&logo=render&logoColor=black" alt="Render"> <img src="https://img.shields.io/badge/Vercel-000000?style=flat-square&logo=vercel&logoColor=white" alt="Vercel"> |
| **Monitoring** | <img src="https://img.shields.io/badge/UptimeRobot-3BD671?style=flat-square&logo=uptimerobot&logoColor=white" alt="UptimeRobot"> |
| **Version Control** | <img src="https://img.shields.io/badge/Git-F05032?style=flat-square&logo=git&logoColor=white" alt="Git"> <img src="https://img.shields.io/badge/GitHub-181717?style=flat-square&logo=github&logoColor=white" alt="GitHub"> |

---

## 📁 Project Structure

```
GeoFace-Attend/
├── bot.py                 # Telegram bot: /register flow, group-photo attendance, health-check server
├── face_utils.py          # Face detection, 128-d embeddings and matching (dlib / face_recognition)
├── db.py                  # Supabase client and student queries
├── excel_utils.py         # Builds the styled attendance .xlsx (openpyxl)
├── gps_utils.py           # Legacy helper from the earlier GPS design (not used by the current flow)
├── dashboard.py           # Earlier single-file dashboard (kept for reference)
├── dashboard_app/
│   ├── app.py             # Flask dashboard: upload, de-duplication, daily/monthly reports, Excel export
│   ├── db.py              # Supabase client for the dashboard
│   └── requirements.txt   # flask, supabase, python-dotenv, openpyxl
├── build.sh               # Render build script (dlib-bin + face_recognition installed with --no-deps)
├── requirements.txt       # Bot dependencies (dlib / face_recognition come from build.sh)
├── runtime.txt            # Python version hint for Render
├── .gitignore             # Keeps .env, venv and caches out of Git
└── README.md
```

---

## 🔌 API Reference

### Telegram bot commands

| Command | Description |
|---|---|
| `/start` | Shows how to use the bot and the number of registered students. |
| `/register` | Asks roll no, name, course, branch, year and a selfie, then saves the face embedding. |
| `/status` | Shows the total registered students. |
| `/cancel` | Cancels the current registration. |
| *Send any photo* | Treated as a class group photo: faces are matched and an Excel sheet is returned. |

### Dashboard endpoints (`dashboard_app/app.py`)

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Serves the dashboard page (HTML, CSS and JavaScript in one file). |
| `POST` | `/api/upload` | Form fields `subject`, `date`, `files` (one or more `.xlsx`); merges sheets, removes duplicates, saves new records and returns a summary. |
| `GET` | `/api/records?date=YYYY-MM-DD&subject=` | Records for one day; `subject` is optional. |
| `GET` | `/api/monthly?month=YYYY-MM&subject=` | Per-student attended / held per subject with total and percentage. |
| `POST` | `/api/delete` | JSON `{date, subject}` — deletes that day's records for the subject. |
| `GET` | `/api/students` | Registered students (without face data). |
| `GET` | `/export/daily` | Daily records as an Excel download. |
| `GET` | `/export/monthly` | Monthly report as an Excel download. |

---

## 🚀 Getting Started

### Prerequisites

- Python 3.x
- A Telegram bot token from [@BotFather](https://t.me/BotFather)
- A free [Supabase](https://supabase.com) project (URL and anon key)

### 1. Clone & install

```powershell
git clone https://github.com/prabhattripathi9351/GeoFace-Attend.git
cd GeoFace-Attend
python -m venv venv
.\venv\Scripts\Activate.ps1

pip install "setuptools<81" wheel
pip install dlib-bin==20.0.1
pip install face_recognition_models==0.3.0
pip install --no-deps face_recognition==1.3.0
pip install -r requirements.txt
```

> 💡 `dlib-bin` is a precompiled build, so no C++ compiler is needed. `face_recognition` is installed with `--no-deps` so pip does not try to compile plain `dlib` from source.

### 2. Configure environment variables

Create a `.env` file in the project root (never commit it):

```env
BOT_TOKEN=your_telegram_bot_token
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_supabase_anon_key
```

### 3. Create the database tables

Run in the Supabase **SQL Editor**:

```sql
create table if not exists students (
  roll_no text primary key,
  name text not null,
  telegram_id bigint,
  face_embedding jsonb not null,
  course text, branch text, year int,
  created_at timestamptz default now()
);

create table if not exists attendance_records (
  id bigint generated always as identity primary key,
  class_date date not null,
  subject text not null,
  roll_no text not null,
  name text, course text, branch text, year int,
  marked_time text,
  created_at timestamptz default now(),
  unique (class_date, subject, roll_no)
);

grant all on public.students to anon;
grant all on public.attendance_records to anon;
grant usage, select on all sequences in schema public to anon;
alter table students disable row level security;
alter table attendance_records disable row level security;
```

> 💡 `roll_no` is `text` on purpose, so IDs like `K26267` work.

### 4. Run the bot

```powershell
python bot.py
```

Open your bot in Telegram, send `/register`, then send a class photo.

### 5. Run the dashboard

```powershell
cd dashboard_app
pip install -r requirements.txt
python app.py
```

Open `http://localhost:5001`. Set `DASHBOARD_PASSWORD` in `.env` to protect it with a login.

### 6. Deploy (free tier)

| Part | Service | Settings |
|---|---|---|
| Bot | **Render** Web Service | Build: `bash build.sh` · Start: `python bot.py` · Env: `BOT_TOKEN`, `SUPABASE_URL`, `SUPABASE_KEY` |
| Keep-alive | **UptimeRobot** | HTTP monitor on the Render URL, every 5 minutes |
| Dashboard | **Vercel** | Root directory: `dashboard_app` · Env: `SUPABASE_URL`, `SUPABASE_KEY`, `DASHBOARD_PASSWORD` |

> 💡 Run each bot token in only one place. Two running copies cause a Telegram `409 Conflict` error, so use a separate test bot while developing locally.

---

## 🗺️ Roadmap Ideas

- [ ] Liveness detection to block photo-of-a-photo spoofing
- [ ] Verify that the sender is a teacher before taking attendance
- [ ] Choose the subject inside the bot and save attendance straight to the database (no manual upload)
- [ ] Accept photos sent as files for higher quality, and try a stronger recognition model
- [ ] Re-introduce GPS geofencing and live-location checks from the original design
- [ ] Attendance shortage alerts to students and PDF reports
- [ ] Multi-class and multi-teacher support, WhatsApp bot, mobile app

---

## 🤝 Contributing

Ideas, issues and pull requests are welcome — especially around recognition accuracy and the dashboard.

---

*Built with 📸 and a healthy respect for free-tier limits.*
