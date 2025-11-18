# backend/inference/prompt_builder.py

class PromptBuilder:
    """
    根据目标风格 + 目标情绪，自动生成 MusicGen prompt 文本
    """

    # 可以按你模型的 style label 来写
    STYLE_TEMPLATES = {
        "rock": "rock style with distorted electric guitars, punchy drums and energetic bass",
        "jazz": "smooth jazz style with saxophone, upright bass and soft drums",
        "classical": "classical orchestral style with strings and piano",
        "pop": "modern pop style with bright synths and punchy drums",
        "lofi": "lofi chillhop style with soft drums, warm pads and vinyl noise",
        "soundtrack": "cinematic soundtrack style with strings and atmospheric textures",
    }

    EMOTION_TEMPLATES = {
        "happy": "bright, uplifting and positive mood",
        "sad": "slow, melancholic and emotional mood",
        "angry": "aggressive, intense and powerful feeling",
        "tender": "warm, gentle and intimate feeling",
        "scary": "dark, tense and suspenseful atmosphere",
        "funny": "playful, quirky and light-hearted mood",
        "calm": "calm, relaxing and peaceful mood",
    }

    @classmethod
    def build_prompt(cls, target_style: str, target_emotion: str) -> str:
        s = target_style.lower()
        e = target_emotion.lower()

        style_part = cls.STYLE_TEMPLATES.get(s, s + " style")
        emo_part = cls.EMOTION_TEMPLATES.get(e, e + " mood")

        prompt = (
            f"A {emo_part} {s} track. "
            f"Use {style_part}. "
            f"Strongly emphasize the {emo_part}. "
            f"Avoid copying the original timbre or arrangement; "
            f"re-interpret the original melody with new harmony and new rhythm."
        )
        return prompt
