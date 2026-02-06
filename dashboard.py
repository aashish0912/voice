"""
Streamlit Dashboard for viewing transcription results.
Run with: streamlit run dashboard.py
"""
import streamlit as st
import json
from pathlib import Path

st.set_page_config(page_title="Transcription Dashboard", layout="wide")
st.title("🎙️ Transcription Dashboard")

# Find latest session
outputs = Path("outputs")
if not outputs.exists():
    st.warning("No outputs found. Run main.py first.")
    st.stop()

sessions = sorted(outputs.glob("session_*"), reverse=True)
if not sessions:
    st.warning("No sessions found.")
    st.stop()

session = st.selectbox("Select Session", sessions, format_func=lambda x: x.name)

col1, col2 = st.columns(2)

# Transcript
with col1:
    st.subheader("📝 Transcript")
    transcript_file = session / "transcript.json"
    if transcript_file.exists():
        data = json.loads(transcript_file.read_text())
        for item in data:
            spk = f"**{item.get('speaker', 'Unknown')}**" if item.get('speaker') else ""
            st.markdown(f"{spk} [{item['start']:.0f}s] {item['text']}")
    else:
        st.info("No transcript.")

# Insights
with col2:
    st.subheader("💡 Insights")
    insights_file = session / "insights.json"
    if insights_file.exists():
        data = json.loads(insights_file.read_text())
        if data:
            for item in data:
                st.markdown(f"- **{item['type']}**: {item['text']}")
        else:
            st.info("No insights detected.")
    else:
        st.info("No insights file.")

# Summary
st.subheader("📋 Summary")
summary_file = session / "summary.json"
if summary_file.exists():
    data = json.loads(summary_file.read_text())
    st.write(data.get("summary", "No summary."))
else:
    st.info("No summary.")
