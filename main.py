#!/usr/bin/env python3
"""
Real-Time Indian Concall Transcription & Insight Streaming

CLI entry point for the application.
Supports both CLI processing and starting the FastAPI server.
"""

import asyncio
import os
from pathlib import Path

import typer
from dotenv import load_dotenv
from rich.console import Console

# Load environment variables
load_dotenv()

# CLI app
cli = typer.Typer(
    name="concall",
    help="Real-Time Concall Transcription & Insight Streaming",
    add_completion=False,
)
console = Console()


@cli.command()
def serve(
    host: str = typer.Option("0.0.0.0", "--host", "-h", help="Host to bind to"),
    port: int = typer.Option(8000, "--port", "-p", help="Port to bind to"),
    reload: bool = typer.Option(False, "--reload", "-r", help="Enable hot reload"),
):
    """Start the FastAPI server."""
    import uvicorn
    
    console.print(f"[bold green]Starting server on {host}:{port}[/bold green]")
    console.print("[dim]API docs available at /docs[/dim]")
    
    uvicorn.run(
        "src.api.main:app",
        host=host,
        port=port,
        reload=reload,
    )


@cli.command()
def process(
    audio: Path = typer.Argument(..., help="Path to the audio file to process"),
    chunk_duration: float = typer.Option(
        float(os.getenv("CHUNK_DURATION_SECONDS", "5")),
        "--chunk-duration", "-c",
        help="Duration of each audio chunk in seconds"
    ),
    output: str = typer.Option(
        "console",
        "--output", "-o",
        help="Output method: console, json"
    ),
):
    """
    Process an audio file locally (CLI mode).
    
    This runs the transcription and insight pipeline directly,
    outputting results to the console.
    """
    if not audio.exists():
        console.print(f"[bold red]Error:[/bold red] Audio file not found: {audio}")
        raise typer.Exit(1)
    
    console.print("[bold blue]=" * 60 + "[/bold blue]")
    console.print("[bold]Real-Time Concall Transcription & Insight Streaming[/bold]")
    console.print("[bold blue]=" * 60 + "[/bold blue]")
    console.print(f"[dim]Audio file:[/dim] {audio}")
    console.print(f"[dim]Chunk duration:[/dim] {chunk_duration}s")
    console.print(f"[dim]Output method:[/dim] {output}")
    console.print("[bold blue]=" * 60 + "[/bold blue]\n")
    
    # Run the async processing
    asyncio.run(_process_audio(audio, chunk_duration, output))


async def _process_audio(audio_path: Path, chunk_duration: float, output: str):
    """Process audio file asynchronously."""
    from src.transcription.transcriber import StreamingTranscriber
    from src.insights.detector import InsightDetector
    from src.streaming.streamer import ConsoleStreamer, FileStreamer
    
    # Initialize components
    console.print("[dim]Initializing transcription model...[/dim]")
    transcriber = StreamingTranscriber(model_name="base")
    
    console.print("[dim]Initializing insight detector...[/dim]")
    detector = InsightDetector(use_llm=True)
    
    console.print("[dim]Starting processing...[/dim]\n")
    
    # Initialize streamers
    console_streamer = ConsoleStreamer()
    file_streamer = FileStreamer(output_dir="outputs")
    
    chunk_count = 0
    
    try:
        # Process audio chunks
        async for chunk in transcriber.process_audio(audio_path, chunk_duration):
            chunk_count += 1
            
            # Analyze for insights
            result = await detector.analyze(chunk)
            
            # Stream to both console and file
            await console_streamer.stream(chunk, result)
            await file_streamer.stream(chunk, result)
        
        # Final summary
        if chunk_count > 0:
            summary = detector.get_final_summary()
            await console_streamer.stream_summary(summary)
            await file_streamer.stream_summary(summary)
        else:
            console.print("[yellow]No audio chunks were processed.[/yellow]")
        
    except KeyboardInterrupt:
        console.print("\n[yellow]Processing interrupted by user.[/yellow]")
    except Exception as e:
        console.print(f"[red]Error during processing: {e}[/red]")
        raise
    finally:
        await console_streamer.close()
        await file_streamer.close()
        console.print("\n[green]Processing complete.[/green]")


@cli.command()
def version():
    """Show version information."""
    console.print("[bold]Concall Transcription[/bold] v0.1.0")


if __name__ == "__main__":
    cli()
