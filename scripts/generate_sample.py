"""
Sample Audio Generator

Creates a simple test audio file with simulated earnings call content.
Uses gTTS if available, otherwise creates a silent WAV file.
"""

import wave
import struct
import os
from pathlib import Path


def create_sample_audio(output_path: str = "data/samples/sample_concall.wav"):
    """Create a sample audio file for testing."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Try using gTTS for realistic speech
    try:
        from gtts import gTTS
        
        # Simulated earnings call transcript
        text = """
        Good morning everyone and welcome to the Q3 earnings call.
        I am pleased to report that our revenue grew by 18 percent year on year,
        reaching 450 crores this quarter.
        Our EBITDA margin improved to 22 percent, up 200 basis points.
        Looking ahead, we expect continued momentum with guidance of 15 to 18 percent growth.
        However, we do see some headwinds from rising input costs.
        We remain confident in our market position and execution capabilities.
        Thank you for your continued support.
        """
        
        tts = gTTS(text=text, lang='en', slow=False)
        
        # Save as MP3 first, then convert
        mp3_path = output_path.with_suffix('.mp3')
        tts.save(str(mp3_path))
        
        # Convert to WAV using pydub
        from pydub import AudioSegment
        audio = AudioSegment.from_mp3(str(mp3_path))
        audio.export(str(output_path), format="wav")
        
        # Clean up MP3
        mp3_path.unlink()
        
        print(f"Created sample audio: {output_path}")
        return output_path
        
    except ImportError:
        pass
    
    # Fallback: create a simple sine wave audio file
    sample_rate = 16000
    duration = 30  # seconds
    frequency = 440  # Hz
    
    samples = []
    for i in range(int(sample_rate * duration)):
        # Generate sine wave
        import math
        value = int(32767.0 * math.sin(2.0 * math.pi * frequency * i / sample_rate))
        samples.append(value)
    
    # Write WAV file
    with wave.open(str(output_path), 'w') as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        
        for sample in samples:
            wav_file.writeframes(struct.pack('h', sample))
    
    print(f"Created sample audio (tone): {output_path}")
    return output_path


if __name__ == "__main__":
    create_sample_audio()
