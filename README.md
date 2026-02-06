# Voice Intelligence Engine (Minimalist Edition)

A highly optimized, **260-line** real-time audio analysis pipeline.
It combines **Faster Whisper** (transcription) + **Groq LLM** (live insights) into a singular, event-driven system.

![Mockup](https://via.placeholder.com/800x400?text=Voice+AI+Dashboard)

## ⚡ Features

- **Extreme Minimalism**: Entire core logic condensed to <300 lines.
- **Real-Time Transcription**: 5s latency using `faster-whisper` (int8 quantized).
- **Live AI Insights**: Extracts **Revenue, Growth, Risks** headers on-the-fly via Groq.
- **Smart Summaries**: 
  - **Rolling**: Updates every few seconds.
  - **Final**: Generates a comprehensive 3-5 paragraph report + key insights at the end.
- **Interactive Dashboard**: Streamlit UI with history and live view.

## 🛠️ Architecture

| Module | Lines | Function |
|--------|-------|----------|
| `main.py` | 35 | Async event loop & CLI entry point. |
| `transcriber.py` | 35 | Audio chunking + Whisper + Speaker Diarization. |
| `detector.py` | 50 | LLM Insight extraction (Groq/OpenAI) + Fallback logic. |
| `streamer.py` | 40 | JSON output writer (`outputs/`). |
| `dashboard.py` | 50 | Real-time UI reader. |

**Total:** ~250 lines of Python.

## 🚀 Quick Start

1. **Install**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure Credentials**
   ```bash
   # .env file
   GROQ_API_KEY=gsk_...
   ```

3. **Run Pipeline**
   ```bash
   # Transcribe audio file
   python main.py data/samples/your_audio.mp3 -c 4
   ```

4. **View Dashboard**
   ```bash
   streamlit run dashboard.py
   ```

## 📋 Output Format

The system generates structured JSON in `outputs/session_TIMESTAMP/`:

```json
// insights.json
[
  { "type": "REVENUE", "text": "Q3 revenue up 20% YoY" },
  { "type": "RISK", "text": "Supply chain headwinds expected in Q4" }
]
```

## 📝 License

MIT
