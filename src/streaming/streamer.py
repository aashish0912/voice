"""
Streaming Output Module

Supports console output and file-based output.
"""

import json
import os
from abc import ABC, abstractmethod
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Optional, List

from src.insights.detector import InsightResult
from src.transcription.transcriber import TranscriptChunk


class BaseStreamer(ABC):
    """Abstract base class for streaming output."""
    
    @abstractmethod
    async def stream(
        self, 
        chunk: TranscriptChunk, 
        insights: Optional[InsightResult] = None
    ) -> None:
        """
        Stream a transcript chunk and its insights.
        
        Args:
            chunk: The transcribed audio chunk
            insights: Optional insights extracted from the chunk
        """
        pass
    
    @abstractmethod
    async def stream_summary(self, summary: str) -> None:
        """Stream a summary update."""
        pass
    
    @abstractmethod
    async def close(self) -> None:
        """Clean up resources."""
        pass


class ConsoleStreamer(BaseStreamer):
    """
    Stream output to console with formatting.
    
    This is the simplest implementation. Start here and optionally
    add SSE or WebSocket support.
    """
    
    def __init__(self, use_rich: bool = True):
        """
        Initialize console streamer.
        
        Args:
            use_rich: Whether to use rich library for formatting
        """
        self.use_rich = use_rich
        
        # Optional: Use rich for better formatting
        # try:
        #     from rich.console import Console
        #     from rich.panel import Panel
        #     self.console = Console()
        # except ImportError:
        #     self.use_rich = False
    
    async def stream(
        self, 
        chunk: TranscriptChunk, 
        insights: Optional[InsightResult] = None
    ) -> None:
        """Stream transcript and insights to console."""
        # TODO: Implement console streaming
        # 
        # Example output format:
        # 
        # ─────────────────────────────────────────
        # [00:05 - 00:10] Transcript:
        # "The revenue for this quarter was 500 crores..."
        # 
        # 📊 Insights:
        #   • [REVENUE] 500 crores mentioned
        #   • [GROWTH] Positive growth signal
        # 
        # 📝 Rolling Summary:
        # Company reported Q3 revenue of 500 crores...
        # ─────────────────────────────────────────
        
        timestamp = f"[{chunk.start_time:.0f}s - {chunk.end_time:.0f}s]"
        speaker_info = f" 🎤 {chunk.speaker}" if chunk.speaker else ""
        print(f"\n{'─' * 50}")
        print(f"{timestamp}{speaker_info} Transcript:")
        print(f'"{chunk.text}"')
        
        if insights:
            if insights.insights:
                print("\n📊 Insights:")
                for insight in insights.insights:
                    print(f"  • [{insight.type.value.upper()}] {insight.text}")
            
            if insights.rolling_summary:
                print(f"\n📝 Summary: {insights.rolling_summary}")
        
        print(f"{'─' * 50}")
    
    async def stream_summary(self, summary: str) -> None:
        """Stream a summary update."""
        print(f"\n{'=' * 50}")
        print("📋 FINAL SUMMARY")
        print(f"{'=' * 50}")
        print(summary)
        print(f"{'=' * 50}\n")
    
    async def close(self) -> None:
        """Clean up (no-op for console)."""
        pass


class FileStreamer(BaseStreamer):
    """
    Stream output to JSON files.
    
    Saves transcripts, insights, and summary to separate files.
    """
    
    def __init__(self, output_dir: str = "outputs"):
        """
        Initialize file streamer.
        
        Args:
            output_dir: Directory to save output files
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Create timestamped session folder
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.session_dir = self.output_dir / f"session_{timestamp}"
        self.session_dir.mkdir(exist_ok=True)
        
        # Data storage
        self.transcripts: List[dict] = []
        self.insights: List[dict] = []
    
    async def stream(
        self, 
        chunk: TranscriptChunk, 
        insights: Optional[InsightResult] = None
    ) -> None:
        """Save transcript and insights to memory, write incrementally."""
        transcript_data = {
            "start_time": chunk.start_time,
            "end_time": chunk.end_time,
            "text": chunk.text,
            "confidence": chunk.confidence,
            "speaker": chunk.speaker
        }
        self.transcripts.append(transcript_data)
        
        if insights and insights.insights:
            for insight in insights.insights:
                insight_data = {
                    "type": insight.type.value,
                    "text": insight.text,
                    "sentiment": insight.sentiment.value,
                    "timestamp": insight.timestamp,
                    "confidence": insight.confidence
                }
                self.insights.append(insight_data)
        
        # Write incrementally
        self._save_json("transcript.json", self.transcripts)
        self._save_json("insights.json", self.insights)
    
    async def stream_summary(self, summary: str) -> None:
        """Save final summary to file."""
        summary_data = {
            "summary": summary,
            "generated_at": datetime.now().isoformat(),
            "total_chunks": len(self.transcripts),
            "total_insights": len(self.insights)
        }
        self._save_json("summary.json", summary_data)
        
        # Also save full transcript as plain text
        full_text = "\n".join(t["text"] for t in self.transcripts)
        text_path = self.session_dir / "full_transcript.txt"
        text_path.write_text(full_text, encoding="utf-8")
        
        print(f"\n📁 Output saved to: {self.session_dir}")
    
    async def close(self) -> None:
        """Finalize file output."""
        pass
    
    def _save_json(self, filename: str, data: Any) -> None:
        """Save data to JSON file."""
        filepath = self.session_dir / filename
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)


class SSEStreamer(BaseStreamer):
    """
    Stream output via Server-Sent Events.
    
    TODO: Implement if you want to support web-based clients.
    
    This requires setting up a FastAPI server with SSE endpoints.
    """
    
    def __init__(self, port: int = 8000):
        self.port = port
        # TODO: Initialize FastAPI app and SSE mechanism
        
    async def stream(
        self, 
        chunk: TranscriptChunk, 
        insights: Optional[InsightResult] = None
    ) -> None:
        """Stream via SSE."""
        # TODO: Implement SSE streaming
        # 
        # Example with sse-starlette:
        # 
        # from sse_starlette.sse import EventSourceResponse
        # 
        # async def event_generator():
        #     data = {
        #         "type": "transcript",
        #         "chunk": asdict(chunk),
        #         "insights": asdict(insights) if insights else None,
        #     }
        #     yield {"data": json.dumps(data)}
        
        raise NotImplementedError("TODO: Implement SSE streaming")
    
    async def stream_summary(self, summary: str) -> None:
        """Stream summary via SSE."""
        raise NotImplementedError("TODO: Implement SSE summary streaming")
    
    async def close(self) -> None:
        """Clean up SSE resources."""
        raise NotImplementedError("TODO: Implement SSE cleanup")


class WebSocketStreamer(BaseStreamer):
    """
    Stream output via WebSocket.
    
    TODO: Implement if you want bidirectional communication.
    """
    
    def __init__(self, port: int = 8000):
        self.port = port
        # TODO: Initialize WebSocket server
        
    async def stream(
        self, 
        chunk: TranscriptChunk, 
        insights: Optional[InsightResult] = None
    ) -> None:
        """Stream via WebSocket."""
        raise NotImplementedError("TODO: Implement WebSocket streaming")
    
    async def stream_summary(self, summary: str) -> None:
        """Stream summary via WebSocket."""
        raise NotImplementedError("TODO: Implement WebSocket summary streaming")
    
    async def close(self) -> None:
        """Clean up WebSocket resources."""
        raise NotImplementedError("TODO: Implement WebSocket cleanup")
