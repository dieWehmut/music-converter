class PromptBuilder:
    """
    Hardcore Prompt：剧烈风格迁移 + 明显情绪差异
    """

    STYLE_INFO = {
        "rock": {
            "instrument": "distorted electric guitars, aggressive drums, heavy bass",
            "harmony": "rock power-chords",
            "feel": "energetic, raw, powerful"
        },
        "jazz": {
            "instrument": "saxophone, upright bass, jazz piano, brushed drums",
            "harmony": "extended jazz chords, swing rhythm",
            "feel": "smooth, expressive, relaxed"
        },
        "classical": {
            "instrument": "orchestral strings, brass, woodwinds, piano",
            "harmony": "classical orchestral harmony",
            "feel": "cinematic, elegant"
        },
        "pop": {
            "instrument": "bright synths, punchy drums, electronic bass",
            "harmony": "catchy pop chords",
            "feel": "clean, modern, upbeat"
        },
        "electronic": {
            "instrument": "synth leads, EDM drums, electronic bass",
            "harmony": "futuristic harmonic motion",
            "feel": "powerful, synthetic"
        },
    }

    EMOTION_INFO = {
        "angry":    "aggressive, intense, dark emotions",
        "funny":    "playful, quirky, humorous energy",
        "happy":    "bright, uplifting, joyful mood",
        "sad":      "melancholic, emotional, minor-key feeling",
        "scary":    "tense, suspenseful, dark atmosphere",
        "tender":   "warm, gentle, intimate tone"
    }

    @classmethod
    def build_prompt(cls, style, emotion):
        style = style.lower()
        emotion = emotion.lower()

        s = cls.STYLE_INFO[style]
        e = cls.EMOTION_INFO[emotion]

        prompt = (
            f"Create a hardcore {style} style reinterpretation expressing {e}. "
            f"Use {s['instrument']} with {s['harmony']}. "
            f"Strongly transform rhythm, harmony, instrumentation, and arrangement. "
            f"Do NOT reuse any original timbre or mix. "
            f"Preserve only the broad melodic contour, "
            f"but rebuild the accompaniment entirely in {style} style "
            f"with a {s['feel']} character."
        )

        return prompt
