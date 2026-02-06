"""
Audio transcription using Whisper model.
Splits audio into chunks and transcribes each.
"""
import asyncio
from dataclasses import dataclass
from pathlib import Path
from typing import AsyncIterator, Optional
import numpy as np


@dataclass
class TranscriptChunk:
    text: str
    start_time: float
    end_time: float
    confidence: float = 1.0
    speaker: Optional[str] = None


class StreamingTranscriber:
    def __init__(self, model_name="base"):
        self.model = None
        try:
            from faster_whisper import WhisperModel
            self.model = WhisperModel(model_name, device="cpu", compute_type="int8")
        except ImportError:
            pass
    
    async def process_audio(self, audio_path, chunk_duration=5.0, enable_diarization=True):
        from src.utils.audio_utils import load_audio, split_into_chunks
        
        speakers = []
        if enable_diarization:
            try:
                from src.transcription.diarizer import SpeakerDiarizer
                speakers = SpeakerDiarizer().diarize(audio_path)
            except:
                pass
        
        audio, sr = load_audio(Path(audio_path))
        
        for chunk_audio, start, end in split_into_chunks(audio, sr, chunk_duration):
            text = await self._transcribe(chunk_audio)
            
            spk = None
            mid = (start + end) / 2
            for s in speakers:
                if s.start_time <= mid <= s.end_time:
                    spk = s.speaker
                    break
            
            if text.strip():
                yield TranscriptChunk(
                    text=text.strip(),
                    start_time=start,
                    end_time=end,
                    speaker=spk
                )
    
    async def _transcribe(self, audio):
        if not self.model:
            return "[Whisper not installed]"
        
        loop = asyncio.get_event_loop()
        
        def run_whisper():
            segments, _ = self.model.transcribe(audio, language="en", beam_size=5, vad_filter=True)
            return " ".join(seg.text for seg in segments)
        
        return await loop.run_in_executor(None, run_whisper)
