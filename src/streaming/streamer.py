import json
from datetime import datetime
from pathlib import Path

class ConsoleStreamer:
    async def stream(self, chunk, result=None):
        print(f"\n[{chunk.start_time:.0f}s-{chunk.end_time:.0f}s] {chunk.speaker or ''}\n  \"{chunk.text}\"")
        if result:
            for i in result.insights: print(f"  >> {i['type']}: {i['text']}")
            if result.rolling_summary: print(f"  Summary: {result.rolling_summary[:100]}...")

    async def stream_final_summary(self, res):
        print(f"\n{'='*50}\nFINAL SUMMARY\n{'='*50}\n{res.get('summary')}")
        for i in res.get('insights', []): print(f"  • {i['type']}: {i['text']}")

class FileStreamer:
    def __init__(self, out_dir="outputs"):
        self.path = Path(out_dir) / f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.path.mkdir(parents=True, exist_ok=True)
        self.data = {"transcripts": [], "insights": []}

    async def stream(self, chunk, result=None):
        self.data["transcripts"].append({"start": chunk.start_time, "end": chunk.end_time, "text": chunk.text, "speaker": chunk.speaker})
        if result:
            self.data["insights"].extend(result.insights)
            if result.rolling_summary: self._save("summary.json", {"summary": result.rolling_summary, "chunks": len(self.data["transcripts"])})
        
        self._save("transcript.json", self.data["transcripts"])
        self._save("insights.json", self.data["insights"])

    async def stream_final_summary(self, res):
        fin = {**res, "chunks": len(self.data["transcripts"])}
        self._save("final_summary.json", fin)
        self._save("summary.json", {"summary": res.get("summary"), "chunks": len(self.data["transcripts"])})
        self._save("insights.json", res.get("insights", []))
        (self.path / "full.txt").write_text("\n".join(t["text"] for t in self.data["transcripts"]))
        print(f"\nSaved to: {self.path}")

    def _save(self, name, data): (self.path / name).write_text(json.dumps(data, indent=2))
 
