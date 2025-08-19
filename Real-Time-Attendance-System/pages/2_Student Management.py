# Student Management Page - Using face_recognition
# Author: Ahmad Kraiem

# ========== Imports ==========
import streamlit as st
import cv2
import os
import numpy as np
import pandas as pd
import face_recognition
from datetime import date
import sqlite3

# ========== Paths ==========
DB_PATH = os.path.join("database", "attendance.db")
DATASET_DIR = "dataset"
ENCODING_DIR = "encodings"
os.makedirs("database", exist_ok=True)
os.makedirs(DATASET_DIR, exist_ok=True)
os.makedirs(ENCODING_DIR, exist_ok=True)

# ========== Initialize Database ==========
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            reg_no TEXT NOT NULL UNIQUE,
            folder_name TEXT NOT NULL,
            image_count INTEGER DEFAULT 0,
            registration_date TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

init_db() # Initialize DB on startup

# ========== Page Config ==========
st.set_page_config(page_title="Student Management", page_icon="🧑‍🎓", layout="wide", initial_sidebar_state="expanded")
st.title("🧑‍🎓 Student Management") # Page title
st.markdown("Register students and save their face encodings for recognition.") # Page description

# ========== Helper ==========
def normalize_folder_name(name: str, reg_no: str) -> str:
    # Normalize name and reg_no for folder naming
    name = name.strip().lower().replace(" ", "_")
    reg_no = reg_no.strip().lower()
    return f"{name}_{reg_no}"

# ========== Input Form ==========
form_cols = st.columns([1, 1, 2], gap="large") # Create input form columns

with form_cols[0]:
    st.subheader("Student Info")
    student_name = st.text_input("Full Name (exactly 3 parts)") # Input full name
    name_valid = len(student_name.strip().split()) == 3 if student_name else False # Validate full name has 3 parts
    if student_name and not name_valid:
        st.warning("⚠️ Full name must contain exactly 3 parts (e.g., Ahmad Mahmoud Kraiem).")

with form_cols[1]:
    st.subheader("ID Info")
    registration_number = st.text_input("Registration Number").strip() # Input registration number
    reg_exists = False
    matched_existing_name = False
    existing_name = None

    if registration_number and name_valid:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT full_name FROM students WHERE reg_no = ?", (registration_number,)) # Check if reg_no exists
        row = c.fetchone()
        conn.close()
        if row:
            reg_exists = True
            existing_name = row[0].strip().lower()
            matched_existing_name = existing_name == student_name.strip().lower()

with form_cols[2]:
    st.subheader("Capture Face Data")
    num_images_to_capture = st.slider("Number of images to capture", 1, 50, 5) # Select number of images

    # ✅ Select Camera (0 = built-in, 1 = external)
    camera_index = st.selectbox(
        "Select Camera",
        options=[0, 1],
        format_func=lambda x: "📷 Built-in (0)" if x == 0 else "🔌 External (1)"
    )
    # Validate capture conditions
    allow_capture = (
        student_name and registration_number and name_valid and
        (not reg_exists or (reg_exists and matched_existing_name and st.session_state.get("allow_capture", False)))
    )

    if allow_capture:
        folder_name = normalize_folder_name(student_name, registration_number) # Create student folder name
        folder_path = os.path.join(DATASET_DIR, folder_name) # Path for image storage
        encoding_path = os.path.join(ENCODING_DIR, f"{folder_name}.npy") # Path for encoding file

        if st.button("📸 Capture Images and Register", type="primary"): # Start capture on button click
            os.makedirs(folder_path, exist_ok=True)
            cam = cv2.VideoCapture(camera_index)  # ✅ Use selected camera
            detector = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml') # Face detector
            # Initialize counters
            total_attempts = 0
            accepted = 0
            rejected_blur = 0
            rejected_encoding = 0
            rejected_no_face = 0
            encodings = []

            alert_container = st.empty() # For live messages
            success_container = st.empty()

            if not cam.isOpened():
                alert_container.error("❌ Failed to access camera.") # Camera not opened
            else:
                while accepted < num_images_to_capture: # Loop until required images are accepted
                    ret, frame = cam.read() # Read frame
                    if not ret:
                        alert_container.error("❌ Failed to read frame from camera.")
                        break

                    total_attempts += 1
                    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY) # Convert to grayscale
                    faces = detector.detectMultiScale(gray, 1.3, 5) # Detect face

                    if len(faces) == 0:
                        rejected_no_face += 1 # No face detected
                        alert_container.info("🔍 No face detected. Please face the camera.")
                    else:
                        (x, y, w, h) = faces[0] # Take first face only
                        face = frame[y:y+h, x:x+w] # Crop the face
                        laplacian_var = cv2.Laplacian(cv2.cvtColor(face, cv2.COLOR_BGR2GRAY), cv2.CV_64F).var()  # Blur detection

                        if laplacian_var < 100:
                            rejected_blur += 1 # Image is blurry
                            alert_container.warning("⚠️ Image too blurry. Please hold still.")
                        else:
                            encoding = face_recognition.face_encodings(frame, [(y, x + w, y + h, x)]) # Extract face encoding
                            if encoding:
                                encodings.append(encoding[0]) # Save encoding
                                img_path = os.path.join(folder_path, f"{accepted+1}.jpg") # Build image path
                                cv2.imwrite(img_path, face) # Save image
                                accepted += 1
                                alert_container.empty()
                                success_container.success(f"✅ Captured image {accepted}")
                            else:
                                rejected_encoding += 1 # Encoding failed 
                                alert_container.info("⚠️ Face not clear. Please face the camera and stay still.")

                    cv2.imshow("Face Capture", frame) # Show live preview
                    if cv2.waitKey(1) & 0xFF == 27: # Break on ESC key
                        break

                cam.release() # Release camera
                cv2.destroyAllWindows() # Close window

            if encodings:
                if os.path.exists(encoding_path):
                    old_encodings = list(np.load(encoding_path, allow_pickle=True)) # Load existing encodings
                    encodings = old_encodings + encodings
                np.save(encoding_path, encodings) # Save updated encodings

                conn = sqlite3.connect(DB_PATH)
                c = conn.cursor()
                c.execute("SELECT image_count FROM students WHERE reg_no = ?", (registration_number,))
                row = c.fetchone()
                previous_count = row[0] if row else 0
                total_count = previous_count + accepted
                # Insert or update student record
                c.execute("""
                    INSERT OR REPLACE INTO students 
                    (full_name, reg_no, folder_name, image_count, registration_date)
                    VALUES (?, ?, ?, ?, ?)
                """, (student_name.strip().lower(), registration_number, folder_name, total_count, date.today().isoformat()))
                conn.commit()
                conn.close()

                st.success(f"✅ Encodings saved for {student_name}") # Confirmation
                # Save capture stats to session state
                st.session_state.capture_stats = {
                    "total_attempts": total_attempts,
                    "accepted": accepted,
                    "rejected_blur": rejected_blur,
                    "rejected_encoding": rejected_encoding,
                    "rejected_no_face": rejected_no_face
                }
            else:
                st.error("❌ No face encodings captured.")  # No encodings found

    elif name_valid and registration_number:
        if reg_exists and not matched_existing_name:
            st.error("🚫 This registration number is already used by another student.") # Conflict in name
        elif reg_exists and matched_existing_name and not st.session_state.get("allow_capture", False):
            st.warning("⚠️ This student is already registered. You can add more images if needed.")
            if st.button("Continue Anyway to Add More Images"):
                st.session_state.allow_capture = True # Allow new capture for same student

# ========== Show Capture Statistics ==========
if "capture_stats" in st.session_state:
    if st.button("📊 Show Capture Statistics", type="secondary"): # Display capture summary
        stats = st.session_state.capture_stats
        st.info(f"📊 Total Attempts: {stats['total_attempts']}")
        st.success(f"✅ Accepted Images: {stats['accepted']}")
        st.warning(f"❌ Rejected (Blur): {stats['rejected_blur']}")
        st.warning(f"❌ Rejected (No Encoding): {stats['rejected_encoding']}")
        st.warning(f"❌ Rejected (No Face Detected): {stats['rejected_no_face']}")

# ========== Show Registered Students ==========
st.divider()
st.subheader("📋 Registered Students")

def get_registered_students():
    # Fetch all students from DB
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("""
        SELECT LOWER(full_name) AS 'Name',
               reg_no AS 'Registration #',
               image_count AS 'Images',
               registration_date AS 'Registered On'
        FROM students
    """, conn)
    conn.close()
    return df

df = get_registered_students()
if df.empty:
    st.info("No students registered yet.") # No data yet
else:
    st.dataframe(df, use_container_width=True) # Show students table
    st.caption("Images and encodings are saved locally for each student.") # Info caption
