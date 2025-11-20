import os
from pathlib import Path

from .analyze import analyzer
from .prompt_builder import PromptBuilder
from .melody_extractor import MelodyExtractor
from .generate_music import MusicGenerator


class FullMusicPipeline:
    def __init__(self):
        self.analyzer = analyzer
        self.prompt_builder = PromptBuilder()
        self.melody_extractor = MelodyExtractor()
        self.music_generator = MusicGenerator()

    def process(self, audio_path, target_style, target_emotion, output_dir="output"):
        audio_path = Path(audio_path)
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        print("🔍 [1/4] Analyzing input audio...")
        analysis = self.analyzer.analyze(str(audio_path))
        print("Input Style:", analysis["style"])
        print("Input Emotion:", analysis["emotion"])

        print("\n🧠 [2/4] Building hardcore prompt...")
        prompt = self.prompt_builder.build_prompt(target_style, target_emotion)
        print(prompt)

        print("\n🎼 [3/4] Extracting hardcore melody contour...")
        melody_path = self.melody_extractor.extract_melody_to_wav(
            str(audio_path),
            output_path=output_dir / "melody.wav"
        )

        print("\n🎶 [4/4] Generating transformed music...")
        output_audio_path = output_dir / "generated_style_transfer.wav"

        self.music_generator.generate_with_melody(
            prompt=prompt,
            melody_path=str(melody_path),
            output_path=str(output_audio_path),
            max_new_tokens=768
        )

        print("\n🎉 Done! New song saved at:", output_audio_path)

        return {
            "analysis": analysis,
            "prompt": prompt,
            "output": str(output_audio_path)
        }


if __name__ == "__main__":
    print("\n===============================")
    print(" 🚀 Hardcore Full Pipeline Start ")
    print("===============================\n")

    pipeline = FullMusicPipeline()

    INPUT_AUDIO = r"D:\idea_python\music_project\backend\test_audio.wav"
    TARGET_STYLE = "rock"
    TARGET_EMOTION = "happy"

    pipeline.process(
        audio_path=INPUT_AUDIO,
        target_style=TARGET_STYLE,
        target_emotion=TARGET_EMOTION,
        output_dir=r"D:\idea_python\music_project\backend\output"
    )
