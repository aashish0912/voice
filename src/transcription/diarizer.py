"""
Speaker detection using energy-based segmentation.
"""
from dataclasses import dataclass
from pathlib import Path
from typing import List
import numpy as np


@dataclass
class SpeakerSegment:
    speaker: str
    start_time: float
    end_time: float


class SpeakerDiarizer:
    def diarize(self, audio_path) -> List[SpeakerSegment]:
        from src.utils.audio_utils import load_audio
        
        audio, sr = load_audio(audio_path)
        
        frame_len = int(0.5 * sr)
        hop = int(0.25 * sr)
        
        segments = []
        current_spk = "SPEAKER_1"
        seg_start = 0.0
        in_silence = False
        silence_start = 0.0
        
        for i in range(0, len(audio) - frame_len, hop):
            frame = audio[i:i + frame_len]
            energy = np.sqrt(np.mean(frame ** 2))
            t = i / sr
            
            is_quiet = energy < 0.01
            
            if is_quiet and not in_silence:
                silence_start = t
            
            if in_silence and not is_quiet:
                gap = t - silence_start
                if gap > 2.0 and t - seg_start > 1.0:
                    segments.append(SpeakerSegment(current_spk, seg_start, silence_start))
                    current_spk = "SPEAKER_2" if current_spk == "SPEAKER_1" else "SPEAKER_1"
                    seg_start = t
            
            in_silence = is_quiet
        
        segments.append(SpeakerSegment(current_spk, seg_start, len(audio) / sr))
        return segments
