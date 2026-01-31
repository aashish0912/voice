"""
Streaming Transcription Module

Implements audio-to-text transcription using Whisper.
Supports chunked processing to simulate streaming behavior.
"""

import asyncio
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import AsyncIterator, Optional

import numpy as np


@dataclass
class TranscriptChunk:
    """Represents a chunk of transcribed audio."""
    
    text: str
    start_time: float  # seconds
    end_time: float    # seconds
    confidence: float = 1.0
    
    # Optional: speaker info for diarization
    speaker: Optional[str] = None


class StreamingTranscriber:
    """
    Streaming audio transcription using Whisper.
    
    Processes audio in chunks to simulate real-time transcription.
    Uses faster-whisper when available, falls back to openai-whisper.
    """
    
    def __init__(self, model_name: str = "base"):
        """
        Initialize the transcriber.
        
        Args:
            model_name: Whisper model size (tiny, base, small, medium, large)
        """
        self.model_name = model_name
        self.model = None
        self.use_faster_whisper = False
        
        self._load_model()
    
    def _load_model(self):
        """Load the ASR model, trying faster-whisper first."""
        # Try faster-whisper first (more efficient)
        try:
            from faster_whisper import WhisperModel
            
            # Use CPU by default, GPU if available
            device = "cuda" if self._check_cuda() else "cpu"
            compute_type = "float16" if device == "cuda" else "int8"
            
            self.model = WhisperModel(
                self.model_name,
                device=device,
                compute_type=compute_type
            )
            self.use_faster_whisper = True
            return
        except ImportError:
            pass
        
        # Fallback to openai-whisper
        try:
            import whisper
            self.model = whisper.load_model(self.model_name)
            self.use_faster_whisper = False
            return
        except ImportError:
            pass
        
        # No model available - will use simulation mode
        self.model = None
    
    def _check_cuda(self) -> bool:
        """Check if CUDA is available."""
        try:
            import torch
            return torch.cuda.is_available()
        except ImportError:
            return False
    
    async def process_audio(
        self, 
        audio_path: Path | str, 
        chunk_duration: float = 5.0,
        enable_diarization: bool = True
    ) -> AsyncIterator[TranscriptChunk]:
        """
        Process an audio file in chunks and yield transcribed text.
        
        Args:
            audio_path: Path to the audio file
            chunk_duration: Duration of each chunk in seconds
            enable_diarization: Whether to identify speakers
            
        Yields:
            TranscriptChunk objects with transcribed text and metadata
        """
        from src.utils.audio_utils import load_audio, split_into_chunks
        
        audio_path = Path(audio_path)
        
        # Run diarization first if enabled
        speaker_segments = []
        if enable_diarization:
            try:
                from src.transcription.diarizer import SpeakerDiarizer
                diarizer = SpeakerDiarizer()
                speaker_segments = diarizer.diarize(audio_path)
            except Exception:
                pass  # Continue without diarization
        
        # Load and prepare audio
        audio_data, sample_rate = load_audio(audio_path)
        
        # Process each chunk
        for chunk_audio, start_time, end_time in split_into_chunks(
            audio_data, sample_rate, chunk_duration
        ):
            # Transcribe this chunk
            text = await self._transcribe_chunk(chunk_audio, sample_rate)
            
            # Find speaker for this time range
            speaker = None
            if speaker_segments:
                mid_time = (start_time + end_time) / 2
                for seg in speaker_segments:
                    if seg.start_time <= mid_time <= seg.end_time:
                        speaker = seg.speaker
                        break
            
            if text.strip():  # Only yield non-empty results
                yield TranscriptChunk(
                    text=text.strip(),
                    start_time=start_time,
                    end_time=end_time,
                    confidence=0.85,
                    speaker=speaker
                )
            
            # Small delay to simulate real-time processing
            await asyncio.sleep(0.1)
    
    async def _transcribe_chunk(
        self, 
        audio_chunk: np.ndarray, 
        sample_rate: int
    ) -> str:
        """Transcribe a single audio chunk."""
        if self.model is None:
            # Simulation mode - return placeholder
            return "[Transcription unavailable - install whisper or faster-whisper]"
        
        if self.use_faster_whisper:
            return await self._transcribe_faster_whisper(audio_chunk)
        else:
            return await self._transcribe_openai_whisper(audio_chunk)
    
    async def _transcribe_faster_whisper(self, audio_chunk: np.ndarray) -> str:
        """Transcribe using faster-whisper."""
        # Run in executor to avoid blocking
        loop = asyncio.get_event_loop()
        
        def _transcribe():
            segments, _ = self.model.transcribe(
                audio_chunk,
                language="en",  # Can be changed to "hi" for Hindi
                beam_size=5,
                vad_filter=True
            )
            return " ".join(seg.text for seg in segments)
        
        return await loop.run_in_executor(None, _transcribe)
    
    async def _transcribe_openai_whisper(self, audio_chunk: np.ndarray) -> str:
        """Transcribe using openai-whisper."""
        import whisper
        
        loop = asyncio.get_event_loop()
        
        def _transcribe():
            # Whisper expects audio at 16kHz
            result = self.model.transcribe(
                audio_chunk,
                language="en",
                fp16=False
            )
            return result["text"]
        
        return await loop.run_in_executor(None, _transcribe)
    
    async def process_audio_stream(
        self, 
        audio_stream: AsyncIterator[bytes]
    ) -> AsyncIterator[TranscriptChunk]:
        """
        Process a live audio stream (for real-time applications).
        
        This is a placeholder for future live streaming support.
        """
        raise NotImplementedError(
            "Live audio streaming requires additional infrastructure. "
            "Use process_audio() for file-based processing."
        )

