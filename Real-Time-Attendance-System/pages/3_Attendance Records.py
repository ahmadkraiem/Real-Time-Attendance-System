# Attendance Records Page
# Author: Ahmad Kraiem
# Description: Displays real attendance logs with filters, stats, charts, and export

# ========== Imports ==========
import streamlit as st
import pandas as pd
import sqlite3
import os
from datetime import datetime, timedelta
import matplotlib.pyplot as plt

# ========== Page Config ==========
st.set_page_config(
    page_title="Attendance Records",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ========== Session State Init ==========
if "show_charts" not in st.session_state:
    st.session_state.show_charts = True
if "original_data" not in st.session_state:
    st.session_state.original_data = None
if "data_changed" not in st.session_state:
    st.session_state.data_changed = False

# ========== Header ==========
st.title("📊 Attendance Records")
st.markdown("""
    View and analyze all attendance logs recorded by the system.  
    Use filters to refine the view, track stats, view charts, and export reports.
""")

# 🔄 Refresh Data Button
if st.button("🔄 Refresh Data", type="primary"):
    st.toast("✅ Data refreshed successfully!", icon="🔁")
    st.cache_data.clear()
    st.rerun()

# ========== Load Data ==========
DB_PATH = "database/attendance.db"

@st.cache_data
def load_data():
    if not os.path.exists(DB_PATH):
        return pd.DataFrame(columns=["id", "Date", "Full Name", "Reg. No", "Time", "Status"])
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("""
        SELECT id, date AS Date, full_name AS 'Full Name', reg_no AS 'Reg. No', time AS Time, status AS Status 
        FROM attendance
    """, conn)
    conn.close()
    df["Date"] = pd.to_datetime(df["Date"])
    return df

df = load_data()

if "force_reload" in st.session_state and st.session_state.force_reload:
    st.session_state.original_data = df.copy()
    st.session_state.force_reload = False

if st.session_state.original_data is None:
    st.session_state.original_data = df.copy()

# ========== Filters ==========
st.subheader("🔍 Filter Options")
col1, col2, col3 = st.columns(3)

with col1:
    time_filter = st.selectbox(
        "Select Time Range",
        options=["All Time", "Last 7 Days", "Last 14 Days", "Last 21 Days", "Last 30 Days"]
    )

with col2:
    selected_date = st.selectbox("Specific Date", options=["All"] + sorted(df["Date"].dt.date.unique(), reverse=True))

with col3:
    selected_name = st.selectbox("Select Student", options=["All"] + sorted(df["Full Name"].unique()))

# ========== Apply Filters ==========
filtered_df = df.copy()
today = datetime.today()

if time_filter == "Last 7 Days":
    filtered_df = filtered_df[filtered_df["Date"] >= today - timedelta(days=7)]
elif time_filter == "Last 14 Days":
    filtered_df = filtered_df[filtered_df["Date"] >= today - timedelta(days=14)]
elif time_filter == "Last 21 Days":
    filtered_df = filtered_df[filtered_df["Date"] >= today - timedelta(days=21)]
elif time_filter == "Last 30 Days":
    filtered_df = filtered_df[filtered_df["Date"] >= today - timedelta(days=30)]

if selected_date != "All":
    filtered_df = filtered_df[filtered_df["Date"].dt.date == selected_date]

if selected_name != "All":
    filtered_df = filtered_df[filtered_df["Full Name"] == selected_name]

filtered_df["Date"] = filtered_df["Date"].dt.date

# ========== Stats ==========
st.subheader("📈 Attendance Summary")
total_records = len(filtered_df)
unique_students = filtered_df["Full Name"].nunique()
valid_times = filtered_df[filtered_df["Time"] != "-"]["Time"]

if not valid_times.empty:
    earliest = valid_times.min()
    latest = valid_times.max()
    try:
        times_dt = pd.to_datetime(valid_times, format="%H:%M:%S")
        avg_time = (times_dt - pd.Timestamp("1900-01-01")).mean() + pd.Timestamp("1900-01-01")
        avg_time_str = avg_time.strftime("%H:%M:%S")
    except:
        avg_time_str = "N/A"
else:
    earliest = latest = avg_time_str = "N/A"

col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("📄 Total Records", total_records)
col2.metric("👥 Unique Students", unique_students)
col3.metric("🕐 Earliest", earliest)
col4.metric("🕓 Latest", latest)
col5.metric("⏱ Average Time", avg_time_str)

# ========== Charts Toggle ==========
st.session_state.show_charts = st.toggle("📊 Show Visual Charts", value=st.session_state.show_charts)

# ========== Charts ==========
if st.session_state.show_charts and not filtered_df.empty:
    st.subheader("📊 Visual Insights")
    row1_col1, row1_col2, row1_col3 = st.columns(3)

    with row1_col1:
        st.caption("📅 Attendance Breakdown by Day")
        status_counts = filtered_df.groupby(["Date", "Status"]).size().unstack(fill_value=0)
        for status in ["Present", "Absent"]:
            if status not in status_counts.columns:
                status_counts[status] = 0
        fig1, ax1 = plt.subplots()
        status_counts[["Present", "Absent"]].plot(kind="bar", ax=ax1, color=["#4e79a7", "#e15759"])
        ax1.set_xlabel("Date")
        ax1.set_ylabel("Count")
        ax1.set_title("Attendance by Day")
        plt.xticks(rotation=45)
        st.pyplot(fig1)

    with row1_col2:
        st.caption("🏆 Top Attendees (Present Only)")
        top_present = filtered_df[filtered_df["Status"] == "Present"]["Full Name"].value_counts().head(10)
        fig2, ax2 = plt.subplots()
        ax2.barh(top_present.index[::-1], top_present.values[::-1], color="#59a14f")
        ax2.set_xlabel("Present Count")
        ax2.set_ylabel("Student")
        ax2.set_title("Top Present Students")
        st.pyplot(fig2)

    with row1_col3:
        st.caption("⏳ Time of Day Distribution (Present Only)")
        try:
            valid_times = filtered_df[(filtered_df["Status"] == "Present") & (filtered_df["Time"] != "-")]["Time"]
            time_series = pd.to_datetime(valid_times, format="%H:%M:%S")
            time_hours = time_series.dt.hour + time_series.dt.minute / 60.0
            fig3, ax3 = plt.subplots()
            ax3.hist(time_hours, bins=12, color="#f28e2b", edgecolor="black")
            ax3.set_xlabel("Hour")
            ax3.set_ylabel("Count")
            ax3.set_title("Time Distribution")
            st.pyplot(fig3)
        except:
            st.warning("⚠️ Time format error")

    row2_col1, row2_col2, _ = st.columns([1, 1, 1])

    with row2_col1:
        st.caption("📆 Top Attendance Days (Present Only)")
        top_days_present = (
            filtered_df[filtered_df["Status"] == "Present"]
            .groupby("Date").size()
            .sort_values(ascending=False).head(7)
        )
        fig4, ax4 = plt.subplots()
        ax4.bar(top_days_present.index.astype(str), top_days_present.values, color="#af7aa1")
        ax4.set_xlabel("Date")
        ax4.set_ylabel("Present Count")
        ax4.set_title("Top Days")
        plt.xticks(rotation=45)
        st.pyplot(fig4)

    with row2_col2:
        st.caption("📊 Daily Attendance Comparison")
        try:
            full_range = pd.date_range(start=filtered_df["Date"].min(), end=filtered_df["Date"].max())
            daily_status = (
                filtered_df.groupby(["Date", "Status"])
                .size().unstack(fill_value=0)
                .reindex(full_range, fill_value=0)
            )
            for status in ["Present", "Absent"]:
                if status not in daily_status.columns:
                    daily_status[status] = 0
            fig5, ax5 = plt.subplots()
            daily_status["Present"].plot(ax=ax5, marker='o', label="Present", color="#4e79a7")
            daily_status["Absent"].plot(ax=ax5, marker='x', linestyle='--', label="Absent", color="#e15759")
            ax5.set_xlabel("Date")
            ax5.set_ylabel("Count")
            ax5.set_title("Daily Comparison")
            ax5.legend()
            plt.xticks(rotation=45)
            st.pyplot(fig5)
        except:
            st.warning("⚠️ Could not render daily comparison chart.")

# ========== Editable Table ==========
st.subheader("📅 Editable Attendance Table")
if filtered_df.empty:
    st.info("No records found for the selected filters.")
else:
    editable_df = st.data_editor(
        filtered_df,
        num_rows="dynamic",
        use_container_width=True,
        key="editable_table"
    )
    if not editable_df.equals(filtered_df):
        st.toast("⚠️ You have made changes to the data.", icon="✏️")
        st.session_state.data_changed = True

# ========== Export & Save ==========
st.divider()
col_save, col_export = st.columns([1, 1], gap="small")

if "confirm_save" not in st.session_state:
    st.session_state.confirm_save = False

with col_save:
    if st.button("💾 Save Changes", use_container_width=True):
        if st.session_state.data_changed:
            if st.session_state.confirm_save:
                current = editable_df.reset_index(drop=True)
                original_all = st.session_state.original_data.reset_index(drop=True)
                original_visible = original_all[original_all["id"].isin(filtered_df["id"])].reset_index(drop=True)

                original_visible["Date"] = pd.to_datetime(original_visible["Date"])
                current["Date"] = pd.to_datetime(current["Date"])

                conn = sqlite3.connect(DB_PATH)
                c = conn.cursor()

                # ✅ Delete rows manually removed from the filtered view
                ids_before = set(original_visible["id"])
                ids_after = set(current["id"].dropna())
                deleted_ids = ids_before - ids_after
                for deleted_id in deleted_ids:
                    c.execute("DELETE FROM attendance WHERE id = ?", (deleted_id,))

                # 📝 Insert or update rows
                for _, row in current.iterrows():
                    row_date = row["Date"].date() if isinstance(row["Date"], pd.Timestamp) else pd.to_datetime(row["Date"]).date()
                    if pd.isna(row["id"]):
                        c.execute("""
                            INSERT INTO attendance (full_name, reg_no, date, time, status)
                            VALUES (?, ?, ?, ?, ?)
                        """, (
                            row["Full Name"], row["Reg. No"], str(row_date),
                            row["Time"], row["Status"]
                        ))
                    else:
                        c.execute("""
                            UPDATE attendance
                            SET full_name = ?, reg_no = ?, date = ?, time = ?, status = ?
                            WHERE id = ?
                        """, (
                            row["Full Name"], row["Reg. No"], str(row_date),
                            row["Time"], row["Status"], int(row["id"])
                        ))

                conn.commit()
                conn.close()
                st.success("✅ Changes saved successfully.")
                st.session_state.data_changed = False
                st.session_state.confirm_save = False
                st.rerun()
            else:
                st.warning("☑ Please confirm save before proceeding.")
        else:
            st.info("No changes to save.")

    st.session_state.confirm_save = st.checkbox("✔ Confirm save changes", value=st.session_state.confirm_save)

with col_export:
    csv = filtered_df.to_csv(index=False)
    st.download_button(
        label="📥 Download CSV",
        data=csv,
        file_name="attendance_records_filtered.csv",
        mime="text/csv",
        use_container_width=True,
        on_click=lambda: st.toast("📄 CSV download started!", icon="📥")
    )

# ========== Footer ==========
st.caption("Attendance logs are recorded automatically via face recognition. Visualizations update based on current filters.")
