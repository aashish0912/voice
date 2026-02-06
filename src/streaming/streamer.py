"""
Output handlers for transcription results.
Console output and JSON file export.
"""
import json
from datetime import datetime
from pathlib import Path
from src.insights.detector import InsightResult
from src.transcription.transcriber import TranscriptChunk


class ConsoleStreamer:
    async def stream(self, chunk: TranscriptChunk, result: InsightResult = None):
        spk = f" ({chunk.speaker})" if chunk.speaker else ""
        print(f"\n[{chunk.start_time:.0f}s-{chunk.end_time:.0f}s]{spk}")
        print(f'  "{chunk.text}"')
        
        if result and result.insights:
            for ins in result.insights:
                print(f"  >> {ins.type.value}: {ins.text}")
        
        if result and result.rolling_summary:
            print(f"  Summary: {result.rolling_summary[:100]}...")
    
    async def stream_summary(self, text):
        print(f"\n{'='*40}\nFINAL SUMMARY\n{'='*40}\n{text}\n")
    
    async def close(self):
        pass


class FileStreamer:
    def __init__(self, output_dir="outputs"):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.folder = Path(output_dir) / f"session_{timestamp}"
        self.folder.mkdir(parents=True, exist_ok=True)
        self.transcripts = []
        self.insights_list = []
    
    async def stream(self, chunk: TranscriptChunk, result: InsightResult = None):
        self.transcripts.append({
            "start": chunk.start_time,
            "end": chunk.end_time,
            "text": chunk.text,
            "speaker": chunk.speaker
        })
        
        if result:
            for ins in result.insights:
                self.insights_list.append({
                    "type": ins.type.value,
                    "text": ins.text
                })
        
        self._write("transcript.json", self.transcripts)
        self._write("insights.json", self.insights_list)
    
    async def stream_summary(self, text):
        self._write("summary.json", {"summary": text})
        full = "\n".join(t["text"] for t in self.transcripts)
        (self.folder / "full.txt").write_text(full)
        print(f"\nSaved to: {self.folder}")
    
    async def close(self):
        pass
    
    def _write(self, name, data):
        (self.folder / name).write_text(json.dumps(data, indent=2))
