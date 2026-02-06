from pathlib import Path
import numpy as np

def load_audio(path, sr=16000):
    try:
        from pydub import AudioSegment
        a = AudioSegment.from_file(str(path)).set_channels(1).set_frame_rate(sr)
        return np.array(a.get_array_of_samples()).astype(np.float32) / 32768.0, sr
    except:
        import soundfile as sf
        d, s = sf.read(str(path))
        return d if len(d.shape)==1 else d.mean(axis=1), s

def split_into_chunks(audio, sr, sec):
    size = int(sec * sr)
    for i in range(0, len(audio), size):
        yield audio[i:i+size], i/sr, min((i+size)/sr, len(audio)/sr)
