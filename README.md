🛰️ GeoFace Attend — Smart Attendance System

**No more proxy. No more disappearing acts.**

Telegram Check-in → Face Match → GPS Lock → Live Teacher Dashboard

`Status: Planning` | `Python 3.x` | `FastAPI` | `face_recognition` | `Supabase` | `Streamlit` | `Telegram Bot`

---

## 🧠 What is this?

Traditional college attendance — roll calls, sign sheets — is broken in two specific ways: friends mark attendance for absent students (**proxy marking**), and once attendance is marked, no one tracks whether a student actually stays for the full class. Existing digital attendance tools don't fix either problem — they don't verify *who* is really present, and they don't verify *where* that person is for the rest of the session.

**ProxyGuard** closes both gaps. It's a Telegram-based attendance system that:
- Locks each student's identity using **face recognition (128-point embeddings)**, so only the actual registered student can mark their own attendance, every day
- Continuously checks the student's **live GPS location** against a geofenced class boundary for the entire session
- Instantly alerts the faculty the moment a student leaves the boundary after check-in
- Converts "presence" into a **dynamic Attendance Score** based on actual time spent inside the classroom boundary, not just a single tap at the start of class

*Being built as a college project to bring identity verification and real-time accountability to classroom attendance — currently in the design/planning phase, so the exact stack and structure below may evolve.*

---

## ✨ Features

| Capability | Description |
|---|---|
| 🤖 **Telegram-Native Check-in** | Students mark attendance directly through a Telegram bot — no separate app install needed |
| 🧬 **Face Identity Lock** | 128-point facial embeddings ensure the same registered student is verified every single day, blocking proxy marking |
| 📍 **GPS Geofencing** | Real-time location is checked against a predefined class boundary using the Haversine formula |
| 🚨 **Instant Exit Alerts** | If a student leaves the geofence mid-session, faculty gets a real-time warning alert |
| 📊 **Dynamic Attendance Score** | Attendance isn't binary — it's calculated from actual time spent inside the boundary during the session |
| ☁️ **Cloud-Synced Records** | All check-ins, embeddings, and location logs are stored securely in a cloud database |
| 🖥️ **Live Teacher Dashboard** | Real-time view of who's in class, who's flagged, and downloadable session reports |

---

## 🏗️ Architecture & Pipeline

```
                ┌─────────────────────┐
                │   Telegram Bot        │
                │  (Student check-in)   │
                └──────────┬──────────┘
                           │ selfie + location ping
                ┌──────────▼──────────┐
                │  FastAPI Webhook      │
                │  Handler (Backend)    │
                └──────────┬──────────┘
              ┌────────────┴────────────┐
              │                         │
   ┌──────────▼──────────┐   ┌──────────▼──────────┐
   │  Face Recognition     │   │  GPS Geofencing       │
   │  Engine (dlib +       │   │  Engine (Geopy /       │
   │  face_recognition)    │   │  Haversine formula)   │
   └──────────┬──────────┘   └──────────┬──────────┘
              │  identity match?         │  inside boundary?
              └────────────┬────────────┘
                           │
                ┌──────────▼──────────┐
                │  Attendance Score      │
                │  Engine (time-in-      │
                │  boundary calculator) │
                └──────────┬──────────┘
                           │
                ┌──────────▼──────────┐
                │  Supabase (Cloud       │
                │  PostgreSQL + Realtime)│
                └──────────┬──────────┘
                           │
                ┌──────────▼──────────┐
                │  Streamlit Teacher     │
                │  Dashboard             │
                │  (live view + alerts) │
                └─────────────────────┘
```

The loop: student checks in on Telegram → face is verified against their stored embedding → session starts → GPS location is pinged periodically and checked against the classroom geofence → any boundary exit triggers an instant faculty alert → attendance score is computed from total in-boundary time → everything syncs live to the teacher's dashboard.

---

## 🛠️ Tech Stack

| Category | Technology |
|---|---|
| 🌐 **Backend API** | Python, FastAPI, Uvicorn — REST API & Telegram Webhook handler |
| 🧬 **Face Detection** | dlib-bin |
| 🧬 **Face Embedding & Verification** | face_recognition (128-point embeddings), face_recognition_models |
| 🖼️ **Image Preprocessing** | OpenCV |
| 📸 **Image Metadata Validation** | Pillow (EXIF timestamp checks) |
| 📍 **GPS Geofencing** | Geopy (Haversine formula for boundary alerts) |
| 🗂️ **Database** | Supabase — Cloud PostgreSQL, auto REST APIs, Realtime, JSONB for storing embeddings |
| 🖥️ **Frontend (Teacher Dashboard)** | Streamlit |
| 🚀 **Deployment** | Render (Backend) + Streamlit Cloud (Dashboard) — free tier |

> 💡 This stack is a current plan, not final — subject to change as the project develops (e.g. deployment target or DB choice may shift later).

---

## 📁 Project Structure *(Planned)*

```
proxyguard/
├── backend/
│   ├── app/
│   │   ├── main.py            # FastAPI app entrypoint, Telegram webhook route
│   │   ├── config.py          # env vars / settings
│   │   ├── models.py          # Pydantic schemas (student, session, attendance record)
│   │   ├── telegram_bot.py    # Telegram bot handlers (check-in flow)
│   │   ├── face_engine.py     # face detection + embedding + verification
│   │   ├── geofence.py        # Haversine distance + boundary check logic
│   │   ├── attendance_score.py # time-in-boundary → score calculation
│   │   └── db.py              # Supabase client + queries
│   └── requirements.txt
├── dashboard/
│   └── app.py                 # Streamlit teacher dashboard
├── data/
│   └── student_embeddings/    # registered face embeddings (or stored in Supabase JSONB)
└── README.md
```

---

## 🔌 API Reference *(Planned)*

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/telegram/webhook` | Receives incoming Telegram updates (selfie + location) from students |
| `POST` | `/students/register` | Registers a new student's face embedding for identity locking |
| `POST` | `/attendance/checkin` | Verifies face match, starts a session, begins geofence tracking |
| `POST` | `/attendance/location-ping` | Receives periodic GPS pings during an active session |
| `GET` | `/attendance/session/{session_id}` | Returns live status + attendance score for a session |
| `GET` | `/dashboard/alerts` | Returns real-time list of geofence-exit alerts for faculty |

---

## 🚀 Getting Started

### Prerequisites
- Python 3.10+
- A Telegram Bot token (via [BotFather](https://t.me/BotFather))
- A Supabase project (URL + API key)

### 1. Clone & set up the backend
```bash
git clone https://github.com/<your-username>/proxyguard.git
cd proxyguard/backend
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure environment variables
Create a `.env` file in `backend/`:
```
TELEGRAM_BOT_TOKEN=your_bot_token_here
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
CLASS_GEOFENCE_LAT=xx.xxxxx
CLASS_GEOFENCE_LNG=xx.xxxxx
CLASS_GEOFENCE_RADIUS_METERS=50
```

### 3. Run the backend
```bash
uvicorn app.main:app --reload
```

### 4. Run the teacher dashboard
```bash
cd ../dashboard
streamlit run app.py
```

> 💡 `dlib-bin` avoids compiling dlib from source, which is a common setup blocker on Windows/low-resource machines.

---

## 🗺️ Roadmap Ideas

- [ ] Sentence-level face embedding registration flow via Telegram
- [ ] Real-time geofence exit alerts to faculty (Telegram + dashboard)
- [ ] Dynamic attendance score engine (time-in-boundary based)
- [ ] Streamlit live dashboard with session monitoring
- [ ] Anti-spoofing / liveness detection for face check-in (block photo-of-a-photo attacks)
- [ ] Offline/low-connectivity fallback for GPS pings
- [ ] Automated end-of-session attendance report export (PDF/CSV)
- [ ] Multi-class / multi-timetable support for a full department
- [ ] Push notifications for students nearing geofence boundary

---

## 🤝 Contributing

This is currently a solo college project — issues, suggestions, and ideas are still welcome if you're exploring similar attendance/geofencing systems.

---

*Built as a B.Tech college project to bring real identity verification and location accountability to classroom attendance.*
