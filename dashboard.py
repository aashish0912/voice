
import json
import time
from pathlib import Path
import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(
    page_title="Voice AI Insights",
    page_icon="🎙️",
    layout="wide",
)

st.title("🎙️ Real-Time Concall Intelligence")

# Sidebar for session selection
output_dir = Path("outputs")
if not output_dir.exists():
    st.error("No outputs found. Run the extraction pipeline first!")
    st.stop()

sessions = sorted([d for d in output_dir.iterdir() if d.is_dir()], reverse=True)
session_names = [s.name for s in sessions]

if not session_names:
    st.warning("No sessions found.")
    st.stop()

selected_session = st.sidebar.selectbox("Select Session", session_names)
session_path = output_dir / selected_session

# Load data
def load_json(filename):
    try:
        with open(session_path / filename, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

# Layout
col1, col2 = st.columns([2, 1])

# Auto-refresh
if st.sidebar.checkbox("Auto-refresh (Live Mode)", value=True):
    time.sleep(2)
    st.rerun()

# --- MAIN DASHBOARD ---

transcripts = load_json("transcript.json")
insights = load_json("insights.json")
summary_data = load_json("summary.json")

# Metrics
with st.container():
    m1, m2, m3 = st.columns(3)
    m1.metric("Transcribed Chunks", len(transcripts))
    m2.metric("Insights Detected", len(insights))
    
    # Calculate sentiment score
    sentiment_score = 0
    if insights:
        for i in insights:
            s = i.get("sentiment", "neutral")
            if s == "positive": sentiment_score += 1
            elif s == "negative": sentiment_score -= 1
    m3.metric("Net Sentiment Score", sentiment_score)

# Insights Analysis
with col2:
    st.subheader("📊 Detected Insights")
    if insights:
        df_insights = pd.DataFrame(insights)
        
        # Type distribution
        fig = px.pie(df_insights, names='type', title='Insight Types', hole=0.4)
        fig.update_layout(margin=dict(t=30, b=0, l=0, r=0), height=300)
        st.plotly_chart(fig, use_container_width=True)
        
        # List
        for i in insights:
            icon = "📈" if i['type'] == 'growth' else "⚠️" if i['type'] == 'risk' else "💰"
            with st.expander(f"{icon} {i['type'].upper()} ({i['sentiment']})"):
                st.write(i['text'])
                st.caption(f"Confidence: {i.get('confidence', 0.8):.2f}")
    else:
        st.info("No insights detected yet.")

# Transcript Feed
with col1:
    st.subheader("📝 Live Transcript")
    
    if transcripts:
        # Create a container for the transcript
        transcript_container = st.container()
        
        with transcript_container:
            for t in transcripts:
                speaker = t.get("speaker") or "Unknown" # Handle None
                speaker_color = "blue" if "SPEAKER_1" in speaker or "Management" in speaker else "green"
                
                start_fmt = time.strftime('%M:%S', time.gmtime(t['start_time']))
                
                st.markdown(
                    f"""
                    <div style='padding: 10px; border-radius: 5px; background-color: rgba(255, 255, 255, 0.05); margin-bottom: 10px;'>
                        <small style='color: gray;'>{start_fmt}</small> 
                        <strong style='color: {speaker_color};'>{speaker}</strong>: 
                        {t['text']}
                    </div>
                    """,
                    unsafe_allow_html=True
                )
    else:
        st.info("Waiting for transcription...")

# Summary Section
st.divider()
st.subheader("📋 Executive Summary")
if isinstance(summary_data, dict) and "summary" in summary_data:
    st.markdown(summary_data["summary"])
elif summary_data: # Handle legacy format just in case
    st.write(summary_data)
else:
    st.caption("Summary will appear here when processing is complete.")
