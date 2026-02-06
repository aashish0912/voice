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
        
        # 1. DIARIZATION: Get accurate speaker segments first
        speakers = SpeakerDiarizer().diarize(path) if self.model else []
        
        # 2. LOAD AUDIO
        audio, sr = load_audio(Path(path))
        
        # 3. SMART PROCESSING: Use speaker segments if available (Pro Mode)
        if speakers:
            for spk in speakers:
                # Extract specific segment audio
                start_sample = int(spk.start_time * sr)
                end_sample = int(spk.end_time * sr)
                segment_audio = audio[start_sample:end_sample]
                
                # Transcribe
                text = await self._transcribe(segment_audio)
                if text.strip():
                    yield TranscriptChunk(text.strip(), spk.start_time, spk.end_time, speaker=spk.speaker)
                    
        # 4. FALLBACK: Fixed chunking if Diarization failed (Safety Mode)
        else:
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
 
