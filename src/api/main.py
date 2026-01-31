"""
FastAPI Application for Real-Time Concall Transcription & Insight Streaming

This module provides REST API and SSE endpoints for:
- Uploading and processing audio files
- Streaming transcription results
- Streaming insights in real-time
"""

import asyncio
import os
from pathlib import Path
from typing import AsyncGenerator

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sse_starlette.sse import EventSourceResponse

from src.api.schemas import (
    HealthResponse,
    ProcessingStatus,
    TranscriptResponse,
    InsightResponse,
)

# Create FastAPI app
app = FastAPI(
    title="Concall Transcription & Insight Streaming",
    description="Real-time Indian conference call transcription and insight extraction",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage for processing status (use Redis in production)
processing_jobs: dict[str, ProcessingStatus] = {}


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(status="healthy", version="0.1.0")


@app.post("/upload")
async def upload_audio(file: UploadFile = File(...)):
    """
    Upload an audio file for processing.
    
    Returns a job_id that can be used to stream results.
    """
    # Validate file type
    allowed_types = ["audio/wav", "audio/mpeg", "audio/mp4", "audio/x-m4a", "audio/flac"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed: {allowed_types}"
        )
    
    # Save uploaded file
    upload_dir = Path("data/uploads")
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    import uuid
    job_id = str(uuid.uuid4())
    file_path = upload_dir / f"{job_id}_{file.filename}"
    
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)
    
    # Initialize job status
    processing_jobs[job_id] = ProcessingStatus(
        job_id=job_id,
        status="queued",
        file_path=str(file_path),
        progress=0.0,
    )
    
    return {"job_id": job_id, "status": "queued", "message": "File uploaded successfully"}


@app.get("/stream/{job_id}")
async def stream_results(job_id: str):
    """
    Stream transcription and insights via Server-Sent Events (SSE).
    
    Subscribe to this endpoint to receive real-time updates as the audio is processed.
    
    Event types:
    - transcript: New transcript chunk
    - insight: New insight detected
    - summary: Rolling summary update
    - complete: Processing finished
    - error: Processing error
    """
    if job_id not in processing_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    async def event_generator() -> AsyncGenerator[dict, None]:
        """Generate SSE events for the job."""
        job = processing_jobs[job_id]
        
        # TODO: Implement actual processing pipeline
        # This is a placeholder that demonstrates the SSE format
        
        # Update status to processing
        job.status = "processing"
        yield {
            "event": "status",
            "data": '{"status": "processing", "message": "Starting transcription..."}'
        }
        
        # TODO: Replace with actual transcription + insight pipeline
        # 
        # from src.transcription.transcriber import StreamingTranscriber
        # from src.insights.detector import InsightDetector
        # 
        # transcriber = StreamingTranscriber()
        # detector = InsightDetector()
        # 
        # async for chunk in transcriber.process_audio(job.file_path):
        #     # Send transcript
        #     yield {
        #         "event": "transcript",
        #         "data": json.dumps({
        #             "text": chunk.text,
        #             "start_time": chunk.start_time,
        #             "end_time": chunk.end_time,
        #         })
        #     }
        #     
        #     # Get and send insights
        #     result = await detector.analyze(chunk)
        #     if result.insights:
        #         yield {
        #             "event": "insight",
        #             "data": json.dumps({
        #                 "insights": [asdict(i) for i in result.insights],
        #                 "summary": result.rolling_summary,
        #             })
        #         }
        
        # Placeholder: Simulate processing with sample events
        import json
        
        sample_chunks = [
            {"text": "Good morning everyone, welcome to the Q3 earnings call.", "start": 0, "end": 5},
            {"text": "Our revenue this quarter grew by 15 percent year over year.", "start": 5, "end": 10},
            {"text": "We are seeing strong demand across all segments.", "start": 10, "end": 15},
        ]
        
        for i, chunk in enumerate(sample_chunks):
            await asyncio.sleep(1)  # Simulate processing time
            
            yield {
                "event": "transcript",
                "data": json.dumps({
                    "text": chunk["text"],
                    "start_time": chunk["start"],
                    "end_time": chunk["end"],
                })
            }
            
            # Simulate insight detection
            if "revenue" in chunk["text"].lower() or "percent" in chunk["text"].lower():
                yield {
                    "event": "insight",
                    "data": json.dumps({
                        "type": "revenue",
                        "text": "Revenue growth of 15% YoY mentioned",
                        "sentiment": "positive",
                    })
                }
            
            job.progress = (i + 1) / len(sample_chunks) * 100
        
        # Send completion
        job.status = "completed"
        yield {
            "event": "complete",
            "data": json.dumps({
                "status": "completed",
                "summary": "Q3 earnings call: 15% YoY revenue growth with strong demand across segments.",
            })
        }
    
    return EventSourceResponse(event_generator())


@app.get("/status/{job_id}")
async def get_status(job_id: str):
    """Get the current status of a processing job."""
    if job_id not in processing_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = processing_jobs[job_id]
    return {
        "job_id": job.job_id,
        "status": job.status,
        "progress": job.progress,
    }


@app.delete("/job/{job_id}")
async def cancel_job(job_id: str):
    """Cancel a processing job."""
    if job_id not in processing_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = processing_jobs[job_id]
    job.status = "cancelled"
    
    # Clean up file if exists
    if job.file_path and Path(job.file_path).exists():
        Path(job.file_path).unlink()
    
    del processing_jobs[job_id]
    
    return {"message": "Job cancelled successfully"}


# CLI mode - can also run from command line
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
