# 1_Capture Attendance - Using face_recognition + Email Notification with Student Name
# Author: Ahmad Kraiem

import streamlit as st
import cv2
import os
import face_recognition
import numpy as np
import sqlite3
import smtplib
from email.message import EmailMessage
from datetime import datetime, date, timedelta
import pandas as pd

from dotenv import load_dotenv
load_dotenv()

# Email configuration from .env
EMAIL_SENDER = os.getenv("EMAIL_SENDER")
EMAIL_APP_PASSWORD = os.getenv("EMAIL_APP_PASSWORD")
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))

# Paths
DB_PATH = os.getenv("DB_PATH", os.path.join("database", "attendance.db"))
ENCODING_DIR = "encodings"

# ========== Initialize DB ==========
def init_db():
    os.makedirs("database", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            reg_no TEXT NOT NULL,
            date TEXT NOT NULL,
            time TEXT NOT NULL,
            status TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

init_db()

# ========== Email Notification ==========
def send_attendance_email(full_name, reg_no):
    """Send a confirmation email to the student's university address.
    Uses EMAIL_SENDER / EMAIL_APP_PASSWORD / SMTP_HOST / SMTP_PORT from .env.
    """
    if not EMAIL_SENDER or not EMAIL_APP_PASSWORD:
        st.warning("Email not configured. Set EMAIL_SENDER and EMAIL_APP_PASSWORD in .env to enable notifications.")
        return

    msg = EmailMessage()
    msg["Subject"] = "Attendance Confirmation"
    msg["From"] = EMAIL_SENDER
    msg["To"] = f"{reg_no}@ses.yu.edu.jo"

    msg.set_content(
        f"""Dear {full_name.title()},

You have been marked Present today.

Regards,
Attendance System"""
    )

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as smtp:
            smtp.ehlo()
            smtp.starttls()
            smtp.login(EMAIL_SENDER, EMAIL_APP_PASSWORD)
            smtp.send_message(msg)
        st.success(f"✉️ Email sent to {msg['To']}")
    except Exception as e:
        st.error(f"Failed to send email: {e}")


# ========== Attendance Logic ==========
def mark_attendance(full_name, reg_no):
    today = date.today().isoformat()
    now = datetime.now().strftime("%H:%M:%S")
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM attendance WHERE full_name = ? AND date = ?", (full_name, today))
    if not c.fetchone():
        c.execute("INSERT INTO attendance (full_name, reg_no, date, time, status) VALUES (?, ?, ?, ?, ?)",
                  (full_name, reg_no, today, now, "Present"))
        conn.commit()
        st.toast(f"✅ Attendance marked for {full_name}")
        send_attendance_email(full_name, reg_no)
    conn.close()

# ========== Load Encodings ==========
def load_known_faces():
    known_encodings = []
    known_names = []
    reg_map = {}
    for file in os.listdir(ENCODING_DIR):
        if file.endswith(".npy"):
            name_with_reg = file.replace(".npy", "")
            encs = np.load(os.path.join(ENCODING_DIR, file), allow_pickle=True)
            for enc in encs:
                known_encodings.append(enc)
                known_names.append(name_with_reg)
                name_part, reg_no = name_with_reg.rsplit("_", 1)
                full_name = name_part.replace("_", " ").strip().lower()
                reg_map[full_name] = reg_no
    return known_encodings, known_names, reg_map

# ========== UI Layout ==========
st.set_page_config(page_title="Capture Attendance", page_icon="🎥", layout="wide", initial_sidebar_state="expanded")
st.title("🎥 Capture Attendance")
st.markdown("Use this page to recognize students and log attendance automatically.")

main_cols = st.columns([2, 1], gap="large")

if "recognized_names" not in st.session_state:
    st.session_state.recognized_names = []
if "camera_running" not in st.session_state:
    st.session_state.camera_running = False
if "camera_stopped" not in st.session_state:
    st.session_state.camera_stopped = False

with main_cols[0]:
    st.subheader("Camera Feed")
    st.caption("ℹ️ Press ESC to stop the camera when the window opens.")

    use_timer = st.checkbox("⏱️ Use Timer", value=False)
    duration_minutes = st.slider("Select camera duration (minutes):", 1, 180, 10) if use_timer else 1

    camera_index = st.selectbox(
        "Select Camera",
        options=[0, 1],
        format_func=lambda x: "📷 Built-in (0)" if x == 0 else "🔌 External (1)"
    )

    start_btn = st.button("Start Camera", type="primary")

    if start_btn:
        known_encodings, known_names, reg_map = load_known_faces()
        if not known_encodings:
            st.error("No known encodings found. Register students first.")
        else:
            st.session_state.recognized_names = []
            st.session_state.camera_running = True
            st.session_state.camera_stopped = False

            cam = cv2.VideoCapture(camera_index)
            start_time = datetime.now()
            end_time = start_time + timedelta(minutes=duration_minutes) if use_timer else None

            while True:
                ret, frame = cam.read()
                if not ret:
                    st.error("❌ Failed to access camera.")
                    break

                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                face_locations = face_recognition.face_locations(rgb_frame)
                face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

                for face_encoding, (top, right, bottom, left) in zip(face_encodings, face_locations):
                    distances = face_recognition.face_distance(known_encodings, face_encoding)
                    best_match_index = np.argmin(distances)
                    if distances[best_match_index] < 0.4:
                        name_with_reg = known_names[best_match_index]
                        name = name_with_reg.replace("_", " ").rsplit(" ", 1)[0].title()
                        if name not in st.session_state.recognized_names:
                            st.session_state.recognized_names.append(name)
                            full_name = name.lower()
                            reg_no = reg_map.get(full_name, "UNKNOWN")
                            mark_attendance(full_name, reg_no)
                        label = f"{name} ({round((1 - distances[best_match_index]) * 100)}%)"
                    else:
                        label = "Unknown"

                    cv2.putText(frame, label, (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
                    cv2.rectangle(frame, (left, top), (right, bottom), (255, 0, 0), 2)

                cv2.imshow("Face Recognition Attendance", frame)

                if cv2.waitKey(1) & 0xFF == 27:
                    st.info("🛑 Camera stopped manually (ESC).")
                    break
                if use_timer and datetime.now() >= end_time:
                    st.info("⏱️ Timer ended. Camera stopped automatically.")
                    break

            cam.release()
            cv2.destroyAllWindows()
            st.session_state.camera_running = False
            st.session_state.camera_stopped = True

    if st.session_state.camera_running:
        st.warning(f"🔍 Camera is running for {duration_minutes} minute(s)...")
    elif st.session_state.camera_stopped:
        st.success("✅ Camera has been stopped.")
    else:
        st.info("Camera is off.")

with main_cols[1]:
    st.subheader("Recognition Status")
    if st.session_state.recognized_names:
        st.success("Recognized and marked present:")
        for name in st.session_state.recognized_names:
            st.write(f"✅ {name}")
    else:
        st.warning("No face detected.")

    st.divider()
    st.subheader("Actions")

    if st.button("📊 View Today’s Attendance Report"):
        today = date.today().isoformat()

        def get_registered_students():
            conn = sqlite3.connect(DB_PATH)
            df = pd.read_sql_query("SELECT full_name FROM students", conn)
            conn.close()
            return sorted(df["full_name"].tolist())

        def get_today_present():
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute("SELECT DISTINCT full_name FROM attendance WHERE date = ? AND status = 'Present'", (today,))
            rows = c.fetchall()
            conn.close()
            return sorted([row[0] for row in rows])

        all_students = get_registered_students()
        present_today = get_today_present()
        absent_students = sorted(list(set(all_students) - set(present_today)))

        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        for name in absent_students:
            c.execute("SELECT * FROM attendance WHERE full_name = ? AND date = ?", (name, today))
            if not c.fetchone():
                c.execute("SELECT reg_no FROM students WHERE full_name = ?", (name,))
                reg_result = c.fetchone()
                reg_no = reg_result[0] if reg_result else "UNKNOWN"
                c.execute("INSERT INTO attendance (full_name, reg_no, date, time, status) VALUES (?, ?, ?, ?, ?)",
                          (name, reg_no, today, "-", "Absent"))
        conn.commit()
        conn.close()

        total = len(all_students)
        present = len(present_today)
        absent = len(absent_students)
        rate = round((present / total) * 100, 2) if total > 0 else 0

        st.info(f"🧑‍🎓 Total Students: {total}")
        st.success(f"🟢 Present Today: {present}")
        st.error(f"🔴 Absent Today: {absent}")
        st.metric(label="📊 Attendance Rate", value=f"{rate} %")

        with st.expander("🟢 Present Students"):
            for name in present_today:
                st.write(f"✅ {name}")
        with st.expander("🔴 Absent Students"):
            for name in absent_students:
                st.write(f"❌ {name}")

# ========== Edit Attendance Status ==========
st.divider()
st.subheader("🗜️ Modify Today's Attendance Status")

def get_today_attendance():
    today = date.today().isoformat()
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query(
        "SELECT id, full_name, reg_no, time, status FROM attendance WHERE date = ?", conn,
        params=(today,)
    )
    conn.close()
    return df

def toggle_status(record_id, current_status):
    new_status = "Absent" if current_status == "Present" else "Present"
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE attendance SET status = ? WHERE id = ?", (new_status, record_id))
    conn.commit()
    conn.close()
    st.session_state.force_reload = True
    st.rerun()

attendance_df = get_today_attendance()
if attendance_df.empty:
    st.info("No attendance records found for today.")
else:
    for idx, row in attendance_df.iterrows():
        col1, col2, col3, col4 = st.columns([3, 2, 2, 2])
        with col1:
            st.write(f"👤 {row['full_name']} ({row['reg_no']})")
        with col2:
            st.write(f"🕒 {row['time']}")
        with col3:
            st.write(f"📌 Status: {row['status']}")
        with col4:
            if st.button(
                f"Toggle to {'Absent' if row['status']=='Present' else 'Present'}",
                key=f"toggle_{row['id']}"
            ):
                toggle_status(row['id'], row['status'])

# ========== Footer ==========
st.caption("Attendance is now marked automatically upon face recognition.")