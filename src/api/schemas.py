"""
Pydantic schemas for API request/response models.
"""

from typing import Optional, List
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = Field(..., example="healthy")
    version: str = Field(..., example="0.1.0")


class ProcessingStatus(BaseModel):
    """Processing job status."""
    job_id: str
    status: str = Field(default="queued", description="queued, processing, completed, failed, cancelled")
    file_path: Optional[str] = None
    progress: float = Field(default=0.0, ge=0, le=100)
    error: Optional[str] = None


class TranscriptChunkResponse(BaseModel):
    """Transcript chunk in API response."""
    text: str
    start_time: float
    end_time: float
    confidence: float = 1.0
    speaker: Optional[str] = None


class InsightItemResponse(BaseModel):
    """Individual insight in API response."""
    type: str = Field(..., description="revenue, guidance, risk, outlook, etc.")
    text: str
    confidence: float = 1.0
    sentiment: str = Field(default="neutral", description="positive, negative, neutral")
    timestamp: float = 0.0


class TranscriptResponse(BaseModel):
    """Full transcript response."""
    job_id: str
    chunks: List[TranscriptChunkResponse]
    total_duration: float


class InsightResponse(BaseModel):
    """Insights response."""
    job_id: str
    insights: List[InsightItemResponse]
    rolling_summary: str


class StreamEventData(BaseModel):
    """Base model for SSE event data."""
    pass


class TranscriptEventData(StreamEventData):
    """Data for transcript SSE event."""
    text: str
    start_time: float
    end_time: float


class InsightEventData(StreamEventData):
    """Data for insight SSE event."""
    type: str
    text: str
    sentiment: str = "neutral"


class SummaryEventData(StreamEventData):
    """Data for summary SSE event."""
    summary: str


class CompleteEventData(StreamEventData):
    """Data for completion SSE event."""
    status: str = "completed"
    final_summary: str
    total_insights: int
    duration_processed: float
