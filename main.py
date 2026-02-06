#!/usr/bin/env python3
"""
Main entry point for the transcription tool.
Run with: python main.py <audio_file>
"""
import asyncio
from pathlib import Path
import typer
from dotenv import load_dotenv
from rich.console import Console

load_dotenv()
console = Console()


def main(
    audio: Path = typer.Argument(..., help="Path to audio file"),
    chunk: float = typer.Option(5.0, "-c", "--chunk", help="Chunk size in seconds"),
):
    if not audio.exists():
        console.print(f"[red]File not found: {audio}[/red]")
        raise typer.Exit(1)
    
    console.print(f"\n[bold]Audio Transcription[/bold]")
    console.print(f"File: {audio}")
    console.print(f"Chunk size: {chunk}s\n")
    
    asyncio.run(process(audio, chunk))


async def process(audio_path: Path, chunk_size: float):
    from src.transcription.transcriber import StreamingTranscriber
    from src.insights.detector import InsightDetector
    from src.streaming.streamer import ConsoleStreamer, FileStreamer
    
    transcriber = StreamingTranscriber()
    detector = InsightDetector()
    console_out = ConsoleStreamer()
    file_out = FileStreamer()
    
    n = 0
    try:
        async for chunk in transcriber.process_audio(audio_path, chunk_size):
            n += 1
            result = await detector.analyze(chunk)
            await console_out.stream(chunk, result)
            await file_out.stream(chunk, result)
        
        if n > 0:
            summary = detector.get_final_summary()
            await console_out.stream_summary(summary)
            await file_out.stream_summary(summary)
    
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
    
    console.print("\n[green]Done.[/green]")


if __name__ == "__main__":
    typer.run(main)
