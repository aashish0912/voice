# Voice Transcription & Insights

Real-time audio transcription with insight detection using Whisper and LLM.

## Features
- Audio transcription using faster-whisper
- Keyword-based insight detection
- LLM-powered rolling summaries (Groq/OpenRouter/OpenAI)
- Speaker diarization
- Streamlit dashboard

## Architecture

```
Audio File → Transcriber → Insight Detector → Streamer
   (MP3)      (Whisper)      (Regex + LLM)     (Console/File)
```

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Set API key in .env
GROQ_API_KEY=your_key_here

# Run transcription
python main.py data/samples/transcribing_1.mp3 -c 4

# View dashboard
streamlit run dashboard.py
```

## Project Structure

```
main.py                    # CLI entry point
dashboard.py               # Streamlit UI
src/
├── transcription/
│   ├── transcriber.py     # Whisper transcription
│   └── diarizer.py        # Speaker detection
├── insights/
│   └── detector.py        # Insight extraction + LLM summary
├── streaming/
│   └── streamer.py        # Console and file output
└── utils/
    └── audio_utils.py     # Audio loading
```

## Insights Detected

- Revenue, sales, profit mentions
- Growth percentages
- Risk indicators
- Forward guidance
- General topics

## Requirements

- Python 3.10+
- FFmpeg (for MP3 support)
- faster-whisper

## License

MIT
