# backend/dsp/style_accompaniment/pipeline/rock_remix_builder.py
from pathlib import Path
import numpy as np
import librosa

# 你自己的两个模型接口（保持和项目里一致）
from backend.inference.style_recognition import predict_style
from backend.inference.emotion_recognition import predict_emotion

# 我们刚刚写的这些模块
from backend.dsp.style_accompaniment.brain.rock_params_ai import RockParamsAI
from backend.dsp.style_accompaniment.generators.rock_drum_generator import RockDrumGenerator
from backend.dsp.style_accompaniment.generators.rock_bass_generator import RockBassGenerator
from backend.dsp.style_accompaniment.generators.rock_guitar_generator import RockGuitarGenerator
from backend.dsp.style_accompaniment.mixer.smart_mixer import SmartMixer


class RockRemixBuilder:
    """
    完整 Rock 风格转换总控：

        输入用户的原始音乐 audio_path
      -> 使用你训练的 style / emotion 模型分析原曲
      -> 提取原曲的 tempo / energy / brightness
      -> RockParamsAI 根据【目标风格 + 目标情绪 + 原曲特征】生成参数
      -> 吉他 / Bass / 鼓 生成对应轨道
      -> SmartMixer 混成一条 Rock 伴奏

    注意：目前目标风格固定为 "rock"，后面可以扩展成多风格。
    """

    def __init__(self,
                 length_s: float = 10.0,
                 target_style: str = "rock"):
        """
        :param length_s: 生成音乐长度（秒）
        :param target_style: 目标风格，目前先固定 "rock"
        """
        self.length_s = float(length_s)
        self.target_style = target_style

        # 核心推理 AI
        self.params_ai = RockParamsAI()

        # 生成器
        self.drum_gen = RockDrumGenerator()
        self.bass_gen = RockBassGenerator()
        self.guitar_gen = RockGuitarGenerator()

        # 智能混音
        self.mixer = SmartMixer()

    # -------------------- 内部：模型封装 --------------------

    def _run_style_model(self, audio_path: str):
        """
        封装一下 style 模型，兼容 字符串 / (label, prob) / dict 输出。
        """
        res = predict_style(audio_path)
        if isinstance(res, dict):
            label = res.get("label") or res.get("style")
            probs = res.get("probs") or res.get("prob")
            return str(label), probs
        if isinstance(res, (list, tuple)):
            if len(res) >= 2:
                return str(res[0]), res[1]
            return str(res[0]), None
        return str(res), None

    def _run_emotion_model(self, audio_path: str):
        """
        封装一下 emotion 模型，兼容 字符串 / (label, prob) / dict 输出。
        """
        res = predict_emotion(audio_path)
        if isinstance(res, dict):
            label = res.get("label") or res.get("emotion")
            probs = res.get("probs") or res.get("prob")
            return str(label), probs
        if isinstance(res, (list, tuple)):
            if len(res) >= 2:
                return str(res[0]), res[1]
            return str(res[0]), None
        return str(res), None

    def _extract_basic_features(self, audio_path: str) -> dict:
        """
        从原曲中提取：
            - tempo（大概的 BPM）
            - energy（能量，基于 RMS）
            - brightness（亮度，基于谱心）
        这些是方向 A 中 test_audio 的“高层特征作用”。
        """
        y, sr = librosa.load(audio_path, sr=None, mono=True)

        # tempo
        tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
        if tempo <= 0:
            tempo = 120.0

        # energy
        rms = librosa.feature.rms(y=y).mean()
        energy = float(np.clip(rms / 0.1, 0.0, 1.0))

        # brightness
        centroid = librosa.feature.spectral_centroid(y=y, sr=sr).mean()
        brightness = float(np.clip(centroid / 6000.0, 0.0, 1.0))

        return {
            "tempo": float(tempo),
            "energy": energy,
            "brightness": brightness,
        }

    # -------------------- 对外主入口 --------------------

    def build(self,
              audio_path: str,
              target_emotion: str | None = None) -> str:
        """
        :param audio_path: 用户上传的原始音乐路径
        :param target_emotion: 目标情绪，如果为 None 就用模型识别到的 emotion
        :return: 最终生成的 rock 伴奏 wav 路径
        """
        audio_path = str(Path(audio_path).resolve())
        print(f"[RockBuilder] 输入音频: {audio_path}")

        # 1) 使用你训练的模型分析原曲
        original_style, style_probs = self._run_style_model(audio_path)
        original_emotion, emo_probs = self._run_emotion_model(audio_path)

        print(f"[RockBuilder] 原曲识别结果: style={original_style}, emotion={original_emotion}")

        # 如果用户指定了目标情绪，就覆盖
        used_emotion = target_emotion or original_emotion
        used_style = self.target_style or original_style

        print(f"[RockBuilder] 目标风格: {used_style}, 目标情绪: {used_emotion}")

        # 2) 提取原曲能量 / 亮度 / tempo
        features = self._extract_basic_features(audio_path)
        print(f"[RockBuilder] 提取特征: {features}")

        # 3) 由 RockParamsAI 生成所有参数（真正的 AI 推理核心）
        params = self.params_ai.generate_all_params(
            style=used_style,
            emotion=used_emotion,
            features=features
        )

        print(f"[RockBuilder] AI 生成参数组合: {params['combo']}")
        print(f"[RockBuilder] Guitar Params: {params['guitar']}")
        print(f"[RockBuilder] Bass Params:   {params['bass']}")
        print(f"[RockBuilder] Drums Params:  {params['drums']}")
        print(f"[RockBuilder] Mix Params:    {params['mix']}")

        tempo = params["tempo"]

        # 4) 生成每一条乐器轨道
        print("[RockBuilder] 生成鼓轨...")
        drum_path = self.drum_gen.generate(
            tempo=tempo,
            drum_params=params["drums"],
            length_s=self.length_s
        )

        print("[RockBuilder] 生成 Bass 轨...")
        bass_path = self.bass_gen.generate(
            tempo=tempo,
            bass_params=params["bass"],
            length_s=self.length_s
        )

        print("[RockBuilder] 生成吉他轨...")
        guitar_path = self.guitar_gen.generate(
            guitar_params=params["guitar"],
            length_s=self.length_s
        )

        # 5) 智能混音
        print("[RockBuilder] 智能混音中...")
        final_path = self.mixer.mix(
            stems={
                "drums": drum_path,
                "bass":  bass_path,
                "guitar": guitar_path,
            },
            mix_params=params["mix"]
        )

        print(f"[RockBuilder] ✅ 完成 Rock 伴奏生成: {final_path}")
        return final_path


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Rock Style Conversion (Direction A) - Command Line Runner"
    )

    parser.add_argument(
        "-i", "--input",
        type=str,
        required=True,
        help="输入音频文件路径"
    )

    parser.add_argument(
        "-e", "--emotion",
        type=str,
        default=None,
        help="目标情绪（happy/sad/angry/tender/funny/scary）。不填则使用模型识别"
    )

    parser.add_argument(
        "-l", "--length",
        type=float,
        default=10.0,
        help="生成长度（秒）"
    )

    args = parser.parse_args()

    builder = RockRemixBuilder(length_s=args.length, target_style="rock")

    print(f"🎵 生成风格: rock\n🎭 目标情绪: {args.emotion}\n📄 输入: {args.input}")

    out = builder.build(
        audio_path=args.input,
        target_emotion=args.emotion
    )

    print(f"🎉 输出文件: {out}")

