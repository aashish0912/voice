# Voice Transcription & Insight Analysis System

A modular, real-time AI pipeline that processes audio streams, transcribes speech, and extracts actionable business insights using Large Language Models (LLMs).

## 🚀 Features

- **Real-Time Transcription**: High-performance speech-to-text using `faster-whisper`.
- **Speaker Diarization**: Automatically distinguishes between different speakers.
- **Live Insight Detection**: Extracts key metrics (Revenue, Growth, Risks) and action items on-the-fly using Groq.
- **Dynamic Summaries**: Generates rolling updates during the call and a comprehensive executive summary at the end.
- **Interactive Dashboard**: Real-time visualization of transcripts and insights via Streamlit.

## 🛠️ Architecture

The system follows an event-driven pipeline architecture:

1.  **Ingestion**: Audio is processed in chunks.
2.  **Transcription**: Speech is converted to text and tagged with speaker IDs.
3.  **Analysis**: Text is batched and sent to the LLM for insight extraction.
4.  **Distribution**: Results are streamed to JSON outputs and visualized in the dashboard.

## 📦 Installation

```bash
# 1. Clone the repository
git clone https://github.com/aashish0912/voice.git
cd voice

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure API Keys
# Create a .env file and add your Groq API key:
# GROQ_API_KEY=your_key_here
```

## ⚡ Usage

**1. Run the Backend Pipeline**
```bash
python main.py data/samples/your_file.mp3 -c 4
```

**2. Launch the Dashboard**
```bash
streamlit run dashboard.py
```

## 📝 License

MIT
