import os
from supabase import create_client
from dotenv import load_dotenv
import json

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("Supabase URL or Key missing in .env file")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def save_student(roll_no, name, telegram_id, embedding_list):
    """Naya student register karo (face embedding save karo)"""
    data = {
        "roll_no": roll_no,
        "name": name,
        "telegram_id": telegram_id,
        "face_embedding": embedding_list  # JSONB automatically handle karega
    }
    response = supabase.table("students").insert(data).execute()
    return response.data

def get_student_by_telegram(telegram_id):
    """Telegram ID se student ka data dhoondho"""
    response = supabase.table("students").select("*").eq("telegram_id", telegram_id).execute()
    if response.data:
        return response.data[0]
    return None

def get_all_embeddings():
    """Saare students ki embeddings aur roll_no lao (attendance match ke liye)"""
    response = supabase.table("students").select("roll_no, face_embedding").execute()
    return response.data  # List of dicts

def get_session_status():
    """Class session active hai ya nahi? (Settings table se)"""
    response = supabase.table("settings").select("session_active, class_lat, class_lon, radius_meters").eq("id", 1).execute()
    if response.data:
        return response.data[0]
    return {"session_active": False, "class_lat": 28.6139, "class_lon": 77.2090, "radius_meters": 500}

def update_session(status):
    """Session ko active/inactive karo"""
    response = supabase.table("settings").update({"session_active": status}).eq("id", 1).execute()
    return response.data

def mark_attendance(roll_no, status, score):
    """Attendance record daalo"""
    data = {
        "roll_no": roll_no,
        "status": status,
        "score": score
    }
    response = supabase.table("attendance").insert(data).execute()
    return response.data


def get_all_students():
    """Saare registered students lao"""
    try:
        response = supabase.table("students").select(
            "roll_no, name, course, branch, year, face_embedding"
        ).execute()
        return response.data
    except Exception as e:
        print(f"get_all_students error: {e}")
        return []

def get_student_count():
    """Total registered students count"""
    try:
        response = supabase.table("students").select("roll_no", count="exact").execute()
        return response.count if response.count else 0
    except Exception as e:
        print(f"get_student_count error: {e}")
        return 0


def save_student(roll_no, name, telegram_id, embedding, course="", branch="", year=0):
    """Student ko Supabase mein save karo"""
    data = {
        "roll_no": str(roll_no),
        "name": name,
        "telegram_id": telegram_id,
        "face_embedding": embedding,
        "course": course,
        "branch": branch,
        "year": year
    }
    response = supabase.table("students").insert(data).execute()
    return response.data