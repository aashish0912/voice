from dataclasses import dataclass
import numpy as np

@dataclass
class SpeakerSegment:
    speaker: str; start_time: float; end_time: float

class SpeakerDiarizer:
    def diarize(self, path):
        from src.utils.audio_utils import load_audio
        audio, sr = load_audio(path)
        frame, hop = int(0.5 * sr), int(0.25 * sr)
        
        segments, spk, start, in_silence, sil_start = [], "SPEAKER_1", 0.0, False, 0.0
        
        for i in range(0, len(audio) - frame, hop):
            is_quiet = np.sqrt(np.mean(audio[i:i+frame]**2)) < 0.01
            t = i / sr
            
            if is_quiet and not in_silence: sil_start = t
            if in_silence and not is_quiet:
                if t - sil_start > 2.0 and t - start > 1.0:
                    segments.append(SpeakerSegment(spk, start, sil_start))
                    spk = "SPEAKER_2" if spk == "SPEAKER_1" else "SPEAKER_1"
                    start = t
            in_silence = is_quiet
            
        segments.append(SpeakerSegment(spk, start, len(audio)/sr))
        return segments
 
