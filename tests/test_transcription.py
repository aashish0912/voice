"""
Tests for the transcription module.

Run with: pytest tests/test_transcription.py
"""

import pytest
from pathlib import Path

from src.transcription.transcriber import StreamingTranscriber, TranscriptChunk


class TestTranscriptChunk:
    """Tests for TranscriptChunk dataclass."""
    
    def test_create_chunk(self):
        """Test creating a transcript chunk."""
        chunk = TranscriptChunk(
            text="Revenue grew by 15 percent this quarter.",
            start_time=0.0,
            end_time=5.0,
            confidence=0.95
        )
        
        assert chunk.text == "Revenue grew by 15 percent this quarter."
        assert chunk.start_time == 0.0
        assert chunk.end_time == 5.0
        assert chunk.confidence == 0.95
        assert chunk.speaker is None  # Default


class TestStreamingTranscriber:
    """Tests for StreamingTranscriber."""
    
    def test_init(self):
        """Test transcriber initialization."""
        transcriber = StreamingTranscriber(model_name="tiny")
        assert transcriber.model_name == "tiny"
    
    @pytest.mark.skip(reason="TODO: Implement after transcription is complete")
    async def test_process_audio(self):
        """Test audio processing."""
        # TODO: Add tests once implementation is complete
        pass


# TODO: Add more tests as you implement functionality
