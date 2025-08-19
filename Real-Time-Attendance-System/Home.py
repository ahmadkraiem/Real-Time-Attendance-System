# Real-Time Attendance - Home Page
# Author: Ahmad Kraiem 
# Description: Home page layout for the Real-Time Attendance system using Streamlit.

# ========== Imports ==========
import streamlit as st



# ========== Page Config ==========
st.set_page_config(
    page_title="Real-Time Attendance",
    page_icon="🕒",
    layout="wide",
    initial_sidebar_state="expanded"
)



# ========== Sidebar ==========
st.sidebar.title("Navigation")
st.sidebar.info("Use the sidebar to navigate between pages.")


# ========== Header Section ==========
st.title("Real-Time Attendance System")
st.markdown(
    """
    Welcome to the Real-Time Attendance System. This application uses facial recognition to mark and track attendance in real-time.
    It helps automate the process of capturing and storing attendance data, making management simple and efficient.
    """
)


# ========== Main Content ==========
content_cols = st.columns([2, 1])

# --- Left Column: Description and Navigation ---
with content_cols[0]:
    st.subheader("Get Started")
    st.markdown("- 👉 Go to **Capture Attendance** to start recognizing faces.")
    st.markdown("- 🧑‍🎓 Visit **Student Management** to add or update student profiles.")
    st.markdown("- 📊 Open **Attendance Records** to view logs and summaries.")

# --- Right Column: Logo or Image ---
with content_cols[1]:
    st.image("assets/faceRec.png", width=200, caption="Face Recognition")
    

# Divider
st.divider()

# ========== Footer ==========
st.caption("Developed for educational purposes. © 2025 Real-Time Attendance App")