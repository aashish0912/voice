"""
Speaker Diarization Module

Identifies different speakers in audio using pyannote.audio.
Falls back to simple energy-based segmentation if pyannote unavailable.
"""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple

import numpy as np


@dataclass
class SpeakerSegment:
    """Represents a segment of speech with speaker identification."""
    
    speaker: str
    start_time: float
    end_time: float
    confidence: float = 1.0


class SpeakerDiarizer:
    """
    Speaker diarization for identifying who spoke when.
    
    Uses pyannote.audio when available, otherwise uses simple heuristics.
    """
    
    def __init__(self):
        """Initialize the diarizer."""
        self.pipeline = None
        self.use_pyannote = False
        
        self._init_pipeline()
    
    def _init_pipeline(self):
        """Initialize diarization pipeline."""
        # Try pyannote.audio
        try:
            from pyannote.audio import Pipeline
            
            # Check for HuggingFace token
            hf_token = os.getenv("HF_TOKEN") or os.getenv("HUGGINGFACE_TOKEN")
            
            if hf_token:
                self.pipeline = Pipeline.from_pretrained(
                    "pyannote/speaker-diarization-3.1",
                    use_auth_token=hf_token
                )
                self.use_pyannote = True
                return
        except ImportError:
            pass
        except Exception:
            pass
        
        # Fallback mode
        self.pipeline = None
        self.use_pyannote = False
    
    def diarize(self, audio_path: Path | str) -> List[SpeakerSegment]:
        """
        Perform speaker diarization on an audio file.
        
        Args:
            audio_path: Path to the audio file
            
        Returns:
            List of SpeakerSegment objects
        """
        if self.use_pyannote and self.pipeline:
            return self._diarize_pyannote(audio_path)
        else:
            return self._diarize_simple(audio_path)
    
    def _diarize_pyannote(self, audio_path: Path | str) -> List[SpeakerSegment]:
        """Diarize using pyannote.audio."""
        diarization = self.pipeline(str(audio_path))
        
        segments = []
        for turn, _, speaker in diarization.itertracks(yield_label=True):
            segments.append(SpeakerSegment(
                speaker=speaker,
                start_time=turn.start,
                end_time=turn.end,
                confidence=0.9
            ))
        
        return segments
    
    def _diarize_simple(self, audio_path: Path | str) -> List[SpeakerSegment]:
        """
        Simple fallback diarization based on audio characteristics.
        
        This is a basic heuristic approach:
        - Alternates speakers on silence gaps
        - Labels as SPEAKER_1, SPEAKER_2, etc.
        """
        from src.utils.audio_utils import load_audio
        
        audio, sr = load_audio(audio_path)
        
        # Find silence points (energy-based)
        frame_length = int(0.5 * sr)  # 500ms frames
        hop_length = int(0.25 * sr)   # 250ms hop
        
        segments = []
        current_speaker = "SPEAKER_1"
        segment_start = 0.0
        last_was_silence = False
        silence_start = 0.0
        
        for i in range(0, len(audio) - frame_length, hop_length):
            frame = audio[i:i + frame_length]
            energy = np.sqrt(np.mean(frame ** 2))
            
            time_sec = i / sr
            is_silence = energy < 0.01  # Threshold
            
            # Start of silence
            if is_silence and not last_was_silence:
                silence_start = time_sec
            
            # Speaker change on silence -> speech transition
            if last_was_silence and not is_silence:
                silence_duration = time_sec - silence_start
                
                # Only switch speakers if there was a significant pause (e.g. > 0.8s)
                # This helps avoid splitting the same speaker on short breaths
                should_switch = silence_duration > 0.8
                
                if time_sec - segment_start > 1.0:  # Min segment length
                    segments.append(SpeakerSegment(
                        speaker=current_speaker,
                        start_time=segment_start,
                        end_time=time_sec - silence_duration,
                        confidence=0.6 if should_switch else 0.8
                    ))
                    
                    if should_switch:
                        # Toggle speaker
                        current_speaker = "SPEAKER_2" if current_speaker == "SPEAKER_1" else "SPEAKER_1"
                    
                    segment_start = time_sec
            
            last_was_silence = is_silence
        
        # Add final segment
        final_time = len(audio) / sr
        if final_time - segment_start > 0.5:
            segments.append(SpeakerSegment(
                speaker=current_speaker,
                start_time=segment_start,
                end_time=final_time,
                confidence=0.5
            ))
        
        return segments
    
    def get_speaker_at_time(
        self, 
        segments: List[SpeakerSegment], 
        time_sec: float
    ) -> Optional[str]:
        """Get the speaker at a specific time."""
        for seg in segments:
            if seg.start_time <= time_sec <= seg.end_time:
                return seg.speaker
        return None
    
    def label_for_earnings_call(self, speaker_id: str) -> str:
        """
        Map speaker IDs to meaningful labels for earnings calls.
        
        In a real implementation, this would use voice profiles
        to identify Management vs Analysts.
        """
        # Simple heuristic: first speaker is usually Management
        speaker_map = {
            "SPEAKER_1": "Management",
            "SPEAKER_2": "Analyst",
            "SPEAKER_0": "Management",
        }
        return speaker_map.get(speaker_id, speaker_id)
