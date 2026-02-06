from dataclasses import dataclass
import numpy as np

@dataclass
class SpeakerSegment:
    speaker: str; start_time: float; end_time: float

class SpeakerDiarizer:
    def diarize(self, path):
        import os
        from pyannote.audio import Pipeline
        
        token = os.getenv("HF_TOKEN")
        if not token:
            print("Warning: HF_TOKEN not found. Diarization disabled.")
            return []
            
        try:
            pipeline = Pipeline.from_pretrained("pyannote/speaker-diarization-3.1", use_auth_token=token)
            if not pipeline: return []
            
            # Run pipeline
            diarization = pipeline(str(path))
            
            segments = []
            for turn, _, speaker in diarization.itertracks(yield_label=True):
                segments.append(SpeakerSegment(speaker, turn.start, turn.end))
            return segments
        except Exception as e:
            print(f"Diarization Error: {e}")
            return []
 
