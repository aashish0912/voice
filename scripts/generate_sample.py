"""
Sample Audio Generator

Creates simulated earnings call content with multiple speakers.
Uses gTTS with different accents to distinguish speakers.
"""

import os
from pathlib import Path

def create_multi_speaker_sample(output_path: str = "data/samples/multi_speaker.mp3"):
    """Create a multi-speaker conversation sample."""
    try:
        from gtts import gTTS
        from pydub import AudioSegment
        
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Dialogue segments
        dialogue = [
            ("Good morning everyone. This is the CEO speaking. We had a fantastic quarter with revenue up 20% year on year.", "co.in"), # CEO (Indian)
            ("Hi, this is Analyst form JP Morgan. Could you comment on the margin pressure due to raw material costs?", "us"),       # Analyst (US)
            ("Sure. While costs have risen, we offset them with price hikes. Our EBITDA margins remain healthy at 25%.", "co.in"),   # CEO
            ("That is helpful, thank you. One more question on the new plant expansion.", "us"),                                     # Analyst
            ("The new plant in Gujarat will be operational by Q4. We expect it to add 500 crores to our top line.", "co.in")     # CEO
        ]
        
        combined_audio = AudioSegment.empty()
        
        print("Generating multi-speaker audio...")
        
        for i, (text, lang_tld) in enumerate(dialogue):
            print(f"Generating segment {i+1}...")
            tts = gTTS(text=text, lang='en', tld=lang_tld, slow=False)
            
            temp_file = f"temp_{i}.mp3"
            tts.save(temp_file)
            
            segment = AudioSegment.from_mp3(temp_file)
            combined_audio += segment
            combined_audio += AudioSegment.silent(duration=3000) # 3s pause between speakers (for clear diarization)
            
            os.remove(temp_file)
            
        combined_audio.export(str(output_path), format="mp3")
        print(f"Created multi-speaker audio: {output_path}")
        return output_path

    except ImportError as e:
        print(f"Error: {e}. Please run: pip install gtts pydub")
        return None

if __name__ == "__main__":
    create_multi_speaker_sample()
