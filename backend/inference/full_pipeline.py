# backend/inference/full_pipeline.py

from pathlib import Path

from .analyze import analyzer  # 已经在 analyze.py 里创建好的单例
from .melody_extractor import MelodyExtractor
from .generate_music import MusicGenerator
from .prompt_builder import PromptBuilder


class FullMusicPipeline:
    """
    完整音乐处理流程：
    1. 分析原歌曲 emotion + style
    2. 根据用户选择的目标风格 / 情绪构造 prompt
    3. 提取主旋律 melody.wav
    4. 用 MusicGen 根据 prompt + melody 生成新歌
    """

    def __init__(self, model_name: str = "facebook/musicgen-small"):
        self.analyzer = analyzer               # 复用已加载的模型
        self.melody_extractor = MelodyExtractor()
        self.music_generator = MusicGenerator(model_name=model_name)

    def process(
        self,
        audio_path: str,
        target_style: str,
        target_emotion: str,
        output_dir: str | None = None,
    ) -> dict:
        """
        :param audio_path: 原始音频路径
        :param target_style: 目标风格（如 "lofi", "jazz"...）
        :param target_emotion: 目标情绪（如 "calm", "sad"...）
        :param output_dir: 输出目录，不传则用 audio 所在目录
        :return: 一个字典，包含原风格/情绪、prompt、melody路径、生成结果路径
        """

        audio_path = Path(audio_path)
        if output_dir is None:
            output_dir = audio_path.parent
        else:
            output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # 1) 分析原歌曲的 emotion + style
        print("🎵 [Pipeline] Analyzing original audio ...")
        result = self.analyzer.analyze(str(audio_path))
        original_emotion = result["emotion"]
        original_style = result["style"]
        print(f"   原风格: {original_style}, 原情绪: {original_emotion}")

        # 2) 构造目标 prompt（根据目标风格 + 目标情绪）
        print("🎨 [Pipeline] Building prompt ...")
        prompt = PromptBuilder.build_prompt(target_style, target_emotion)
        print(f"   Prompt: {prompt}")

        # 3) 提取 melody.wav
        print("🎼 [Pipeline] Extracting melody ...")
        melody_path = output_dir / "melody.wav"
        melody_path = self.melody_extractor.extract_melody_to_wav(
            str(audio_path),
            output_path=str(melody_path)
        )

        # 4) 用 MusicGen 生成新音乐
        print("🚀 [Pipeline] Generating new music ...")
        output_path = output_dir / "generated_style_transfer.wav"
        output_path = self.music_generator.generate_with_melody(
            prompt=prompt,
            melody_path=melody_path,
            output_path=str(output_path)
        )

        return {
            "original_style": original_style,
            "original_emotion": original_emotion,
            "target_style": target_style,
            "target_emotion": target_emotion,
            "prompt": prompt,
            "melody_path": melody_path,
            "output_path": output_path,
        }


# 方便你直接在命令行测试
if __name__ == "__main__":
    test_audio = r"D:\idea_python\music_project\backend\test_audio.wav"

    pipeline = FullMusicPipeline()

    result = pipeline.process(
        audio_path=test_audio,
        target_style="lofi",
        target_emotion="calm",
        output_dir=r"D:\idea_python\music_project\backend\output"
    )

    print("\n✅ Pipeline 完成，结果：")
    for k, v in result.items():
        print(f"{k}: {v}")
