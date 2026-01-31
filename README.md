# Real-Time Indian Concall Transcription & Insight Streaming

A streaming audio processing system that transcribes Indian earnings calls and extracts financial insights in real-time.

## What I Built

This project implements a **streaming pipeline** for processing conference call audio:

1. **Audio Chunking** - Splits audio into configurable segments (default 5s)
2. **Real-time Transcription** - Uses Whisper for speech-to-text
3. **Insight Detection** - Pattern-based extraction of financial signals
4. **Live Console Output** - Formatted streaming display

## High-Level Architecture

```
┌─────────────┐    ┌──────────────┐    ┌─────────────────┐    ┌────────────┐
│ Audio File  │───▶│ Transcriber  │───▶│ Insight Detector │───▶│  Streamer  │
│ (WAV/MP3)   │    │  (Whisper)   │    │  (Rules + LLM)   │    │  (Console) │
└─────────────┘    └──────────────┘    └─────────────────┘    └────────────┘
     │                   │                     │                    │
     │     5s chunks     │    TranscriptChunk  │    InsightResult   │
     └───────────────────┴─────────────────────┴────────────────────┘
```

### Components

| Component | File | Purpose |
|-----------|------|---------|
| Audio Utils | `src/utils/audio_utils.py` | Load, chunk, and convert audio files |
| Transcriber | `src/transcription/transcriber.py` | Speech-to-text using faster-whisper or openai-whisper |
| Detector | `src/insights/detector.py` | Extract financial insights via regex patterns |
| Streamer | `src/streaming/streamer.py` | Console output with rich formatting |

## How Streaming Works

The system processes audio **incrementally**:

1. Audio is loaded and split into chunks (configurable duration)
2. Each chunk is transcribed asynchronously
3. Transcripts are analyzed for insights immediately
4. Results stream to console as they're generated

This simulates real-time processing. For true live audio, the architecture supports `AsyncIterator[bytes]` input (implementation placeholder included).

### Key Design Decisions

- **Async/await throughout** - Non-blocking I/O for concurrent processing
- **Generator pattern** - Memory-efficient chunk-by-chunk processing
- **Rule-based first** - Works without API keys, LLM enhances when available
- **Indian context** - Patterns include Rs., crores, lakhs, YoY, QoQ terminology

## Insights Detected

The system identifies:

- **Revenue** - Rs. X crore, net sales, top line
- **Growth** - YoY, QoQ, CAGR percentages
- **Margins** - EBITDA, operating, gross margins
- **Guidance** - Forward-looking statements
- **Risks** - Headwinds, challenges, declines
- **Outlook** - Positive momentum, confidence signals

## Running the Project

### Prerequisites

```bash
pip install -e ".[faster-whisper]"  # or [whisper] for openai-whisper
```

For audio conversion support:
```bash
# Windows - install ffmpeg and add to PATH
# Or: choco install ffmpeg
```

### Usage

```bash
# Process an audio file
python main.py process data/samples/sample.wav --chunk-duration 5

# Start API server
python main.py serve --port 8000
```

## Assumptions & Tradeoffs

### Assumptions

- Audio is in supported format (WAV preferred, MP3 needs ffmpeg)
- English language (can switch to Hindi with minor changes)
- Internet not required (local Whisper model)

### Tradeoffs

| Choice | Benefit | Cost |
|--------|---------|------|
| Rule-based primary | Works offline, fast | Less nuanced than LLM |
| 5s default chunks | Good for real-time feel | May split sentences |
| Base Whisper model | Faster, less RAM | Lower accuracy than large |

## What I Would Improve

Given more time:

1. **Speaker Diarization** - Distinguish management vs analysts using pyannote
2. **Better Chunking** - Voice activity detection for natural boundaries
3. **Hinglish Support** - Add Hindi-English code-switching detection
4. **WebSocket Output** - Real-time browser streaming
5. **Caching** - Store transcripts to avoid re-processing
6. **Sentiment Timeline** - Track sentiment changes through the call

## Project Structure

```
├── main.py                 # CLI entry point
├── src/
│   ├── transcription/
│   │   └── transcriber.py  # Whisper integration
│   ├── insights/
│   │   └── detector.py     # Pattern matching + LLM
│   ├── streaming/
│   │   └── streamer.py     # Console/SSE output
│   └── utils/
│       └── audio_utils.py  # Audio processing helpers
├── data/samples/           # Test audio files
└── scripts/
    └── generate_sample.py  # Create test audio
```

## Testing

```bash
pytest tests/
```

## License

MIT
