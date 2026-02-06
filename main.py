import asyncio
from pathlib import Path
import typer
from dotenv import load_dotenv

load_dotenv()

async def process(audio_path: Path, chunk_size: float):
    from src.transcription.transcriber import StreamingTranscriber
    from src.insights.detector import InsightDetector
    from src.streaming.streamer import ConsoleStreamer, FileStreamer
    
    transcriber, detector = StreamingTranscriber(), InsightDetector()
    console_out, file_out = ConsoleStreamer(), FileStreamer()
    
    full_transcript = []
    try:
        async for chunk in transcriber.process_audio(audio_path, chunk_size):
            full_transcript.append(chunk.text)
            result = await detector.analyze(chunk)
            await console_out.stream(chunk, result)
            await file_out.stream(chunk, result)
        
        if full_transcript:
            final_result = await detector.get_final_summary(" ".join(full_transcript))
            await console_out.stream_final_summary(final_result)
            await file_out.stream_final_summary(final_result)
            
    except Exception as e:
        print(f"Error: {e}")

def main(audio: Path = typer.Argument(..., help="Audio file path"), chunk: float = typer.Option(5.0, "-c", help="Chunk size")):
    if not audio.exists(): raise typer.Exit("File not found")
    print(f"Processing: {audio}")
    asyncio.run(process(audio, chunk))

if __name__ == "__main__":
    typer.run(main)
 
