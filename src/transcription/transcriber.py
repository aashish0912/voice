import asyncio
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

@dataclass
class TranscriptChunk:
    text: str; start_time: float; end_time: float; speaker: Optional[str] = None

class StreamingTranscriber:
    def __init__(self, model="base"):
        try:
            from faster_whisper import WhisperModel
            self.model = WhisperModel(model, device="cpu", compute_type="int8")
        except: self.model = None
    
    async def process_audio(self, path, chunk_dur=5.0):
        from src.utils.audio_utils import load_audio, split_into_chunks
        from src.transcription.diarizer import SpeakerDiarizer
        
        speakers = SpeakerDiarizer().diarize(path) if self.model else []
        audio, sr = load_audio(Path(path))
        
        for chunk, start, end in split_into_chunks(audio, sr, chunk_dur):
            text = await self._transcribe(chunk)
            if not text.strip(): continue
                
            mid = (start + end) / 2
            spk = next((s.speaker for s in speakers if s.start_time <= mid <= s.end_time), None)
            yield TranscriptChunk(text.strip(), start, end, speaker=spk)
    
    async def _transcribe(self, audio):
        if not self.model: return ""
        return await asyncio.get_event_loop().run_in_executor(None, lambda: 
            " ".join(s.text for s in self.model.transcribe(audio, language="en")[0]))
 
