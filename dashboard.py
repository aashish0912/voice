import streamlit as st, json, time
from pathlib import Path
from datetime import datetime

st.set_page_config(page_title="Voice AI", layout="wide")
outputs = Path("outputs")
sessions = sorted(outputs.glob("session_*"), reverse=True) if outputs.exists() else []

def load(p):
    try: text = p.read_text(); return json.loads(text) if text.strip() else None
    except: return None
def get_data(s):
    sum_d, tr_d, ins_d, fin_d = load(s/"summary.json"), load(s/"transcript.json"), load(s/"insights.json"), load(s/"final_summary.json")
    return {
        "chunks": len(tr_d) if tr_d else 0,
        "summary": fin_d.get("summary") if fin_d else (sum_d.get("summary") if sum_d else ""),
        "insights": fin_d.get("insights") if fin_d else (ins_d or []),
        "transcript": tr_d or []
    }

def render_summary_insights(sum_txt, ins_list):
    c1, c2 = st.columns(2)
    c1.markdown("### 📋 Summary"); c1.info(sum_txt or "No summary")
    c2.markdown("### 💡 Insights"); 
    for i in ins_list: c2.markdown(f"• **{i.get('type','type')}**: {i.get('text','')}")

st.sidebar.title("🎙️ Voice AI")
if st.sidebar.radio("Nav", ["Live", "History"]) == "Live":
    st.title("🎙️ Live Transcription")
    if not sessions: st.stop()
    s = sessions[0]; st.caption(f"Session: {s.name}")
    
    if st.button("▶ Start"):
        c1, c2 = st.columns([2, 1])
        tr_box, sum_box, ins_box = c1.empty(), c2.empty(), c2.empty()
        fin_box, count = st.empty(), 0
        
        for _ in range(300):
            d = get_data(s)
            if d['transcript']:
                lines = [f"**{t.get('speaker','')}** [{t['start']:.0f}s] {t['text']}" for t in d['transcript'][-12:]]
                tr_box.markdown("\n\n".join(lines))
            if d['summary']: sum_box.info(f"**{d['chunks']} chunks**\n\n{d['summary'][:300]}...")
            if d['insights']: ins_box.markdown("\n".join(f"• {i['type']}: {i['text']}" for i in d['insights'][-8:]))
            
            with fin_box.container(): render_summary_insights(d['summary'], d['insights'])
            time.sleep(1)
    else: render_summary_insights(get_data(s)['summary'], get_data(s)['insights'])

else:
    st.title("📚 History")
    for s in sessions:
        d = get_data(s)
        dt = datetime.strptime(s.name[8:], "%Y%m%d_%H%M%S").strftime("%b %d %I:%M%p")
        with st.expander(f"🗓️ {dt} — {d['chunks']} chunks"):
            render_summary_insights(d['summary'], d['insights'])
            st.markdown("### 📝 Transcript")
            for t in d['transcript']: st.markdown(f"**{t.get('speaker','')}** [{t['start']:.0f}s]: {t['text']}")
