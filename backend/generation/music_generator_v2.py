import torch
from transformers import AutoProcessor, MusicgenForConditionalGeneration

from backend.param_ai.rock_params_ai import RockParamsAI


class MusicGeneratorV2:
    """
    使用 Param AI + MusicGen 生成音乐
    """

    def __init__(self, model_name="facebook/musicgen-small", device=None):
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")

        print(f"[MusicGen] Loading model: {model_name} on {self.device}")

        self.processor = AutoProcessor.from_pretrained(model_name)
        self.model = MusicgenForConditionalGeneration.from_pretrained(
            model_name
        ).to(self.device)

    def generate(self, prompt: str, length_s: int = 12, output_path="output_music.wav"):
        """
        根据 prompt 生成音乐
        """

        print("\n===== Prompt 用于生成音乐 =====")
        print(prompt)
        print("================================\n")

        inputs = self.processor(
            text=[prompt],
            padding=True,
            return_tensors="pt",
        ).to(self.device)

        audio_values = self.model.generate(
            **inputs,
            max_new_tokens=int(50 * length_s),   # 控制生成时长
        )

        # 保存为 wav
        sampling_rate = self.model.config.audio_encoder.sampling_rate
        audio = audio_values[0].cpu().numpy()

        from scipy.io.wavfile import write
        write(output_path, sampling_rate, audio)

        print(f"[MusicGen] 生成成功！已保存到：{output_path}")
        return output_path


def generate_rock_music(emotion="angry", length_s=12, output="rock_ai.wav"):
    """
    用 RockParamsAI 生成音乐（测试用）
    """
    params = RockParamsAI(emotion=emotion, length_s=length_s)
    prompt = params.build_prompt()

    gen = MusicGeneratorV2()
    return gen.generate(prompt, length_s, output)
