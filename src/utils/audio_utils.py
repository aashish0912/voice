"""
Audio file loading and processing utilities.
"""
import os
from pathlib import Path
import numpy as np

# ffmpeg path setup
ffmpeg = os.getenv("FFMPEG_PATH")
if ffmpeg and os.path.isdir(ffmpeg):
    os.environ["PATH"] = ffmpeg + os.pathsep + os.environ.get("PATH", "")


def load_audio(path, target_sr=16000):
    path = Path(path)
    ext = path.suffix.lower()
    
    if ext in ['.mp3', '.m4a', '.ogg', '.flac']:
        from pydub import AudioSegment
        audio = AudioSegment.from_file(str(path))
        audio = audio.set_channels(1).set_frame_rate(target_sr)
        samples = np.array(audio.get_array_of_samples())
        return samples.astype(np.float32) / 32768.0, target_sr
    
    import soundfile as sf
    data, sr = sf.read(str(path))
    
    if len(data.shape) > 1:
        data = data.mean(axis=1)
    
    if sr != target_sr:
        length = int(len(data) / sr * target_sr)
        data = np.interp(
            np.linspace(0, len(data)-1, length),
            np.arange(len(data)),
            data
        )
    
    return data.astype(np.float32), target_sr


def split_into_chunks(audio, sr, chunk_sec):
    chunk_size = int(chunk_sec * sr)
    
    for i in range(0, len(audio), chunk_size):
        chunk = audio[i:i + chunk_size]
        start = i / sr
        end = min((i + chunk_size) / sr, len(audio) / sr)
        yield chunk, start, end
