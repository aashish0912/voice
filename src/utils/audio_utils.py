"""
Audio Utility Functions

Helper functions for audio processing.
"""

import os
from pathlib import Path
from typing import Iterator, Tuple, Union

import numpy as np

# Set ffmpeg path from environment if available
_ffmpeg_path = os.getenv("FFMPEG_PATH")
if _ffmpeg_path and os.path.isdir(_ffmpeg_path):
    os.environ["PATH"] = _ffmpeg_path + os.pathsep + os.environ.get("PATH", "")


def load_audio(
    audio_path: Union[str, Path], 
    sample_rate: int = 16000
) -> Tuple[np.ndarray, int]:
    """
    Load an audio file and return as numpy array.
    
    Supports WAV, MP3, and other formats via pydub.
    
    Args:
        audio_path: Path to the audio file
        sample_rate: Target sample rate (default: 16000 for Whisper)
        
    Returns:
        Tuple of (audio_data, sample_rate)
    """
    audio_path = Path(audio_path)
    ext = audio_path.suffix.lower()
    
    # For MP3 and other formats, use pydub
    if ext in ['.mp3', '.m4a', '.ogg', '.flac']:
        from pydub import AudioSegment
        
        audio_seg = AudioSegment.from_file(str(audio_path))
        
        # Convert to mono
        if audio_seg.channels > 1:
            audio_seg = audio_seg.set_channels(1)
        
        # Resample to target rate
        audio_seg = audio_seg.set_frame_rate(sample_rate)
        
        # Convert to numpy array
        samples = np.array(audio_seg.get_array_of_samples())
        audio = samples.astype(np.float32) / 32768.0  # Normalize to [-1, 1]
        
        return audio, sample_rate
    
    # For WAV, use soundfile (faster)
    import soundfile as sf
    
    audio, sr = sf.read(str(audio_path))
    
    # Convert to mono if stereo
    if len(audio.shape) > 1:
        audio = audio.mean(axis=1)
    
    # Resample if needed
    if sr != sample_rate:
        duration = len(audio) / sr
        new_length = int(duration * sample_rate)
        indices = np.linspace(0, len(audio) - 1, new_length)
        audio = np.interp(indices, np.arange(len(audio)), audio)
        sr = sample_rate
    
    return audio.astype(np.float32), sr


def split_into_chunks(
    audio: np.ndarray, 
    sample_rate: int, 
    chunk_duration: float
) -> Iterator[Tuple[np.ndarray, float, float]]:
    """
    Split audio into chunks of specified duration.
    
    Args:
        audio: Audio data as numpy array
        sample_rate: Sample rate of the audio
        chunk_duration: Duration of each chunk in seconds
        
    Yields:
        Tuple of (audio_chunk, start_time, end_time)
    """
    chunk_samples = int(chunk_duration * sample_rate)
    total_samples = len(audio)
    
    for i in range(0, total_samples, chunk_samples):
        chunk = audio[i:i + chunk_samples]
        start_time = i / sample_rate
        end_time = min((i + chunk_samples) / sample_rate, total_samples / sample_rate)
        yield chunk, start_time, end_time


def get_audio_duration(audio_path: Union[str, Path]) -> float:
    """
    Get the duration of an audio file in seconds.
    
    Args:
        audio_path: Path to the audio file
        
    Returns:
        Duration in seconds
    """
    import soundfile as sf
    
    info = sf.info(str(audio_path))
    return info.duration


def convert_audio_format(
    input_path: Union[str, Path],
    output_path: Union[str, Path],
    output_format: str = "wav"
) -> Path:
    """
    Convert audio file to a different format.
    
    Useful for handling various input formats (mp3, m4a, etc.)
    
    Args:
        input_path: Path to input audio file
        output_path: Path for output file
        output_format: Target format (default: wav)
        
    Returns:
        Path to the converted file
    """
    from pydub import AudioSegment
    
    audio = AudioSegment.from_file(str(input_path))
    audio.export(str(output_path), format=output_format)
    return Path(output_path)

