<<<<<<< HEAD
<<<<<<< HEAD
import numpy as np
from backend.inference.melody_scorer import MelodyScorer


class PromptBuilder:
    """
    Friendly-Prompt 版本（音乐结构友好 + 正向引导）
    不使用任何负面词语，不再出现：
        - unknown pitch range
        - unclear contour
        - weak hook
        - irregular rhythm
        - loosely related to scale
    避免让 MusicGen 往“黑暗/恐怖/混乱”方向生成。
    """

    def __init__(self):
        # 给 full_pipeline 用的旋律评分器
        self.scorer = MelodyScorer()

    # -----------------------------
    # Melody Element Description
    # -----------------------------

    def describe_pitch_range(self, pr):
        if pr < 40:
            return "a smooth and gentle pitch range"
        elif pr < 120:
            return "a moderate and expressive pitch range"
        else:
            return "a wide and energetic pitch range"

    def describe_contour(self, contour_score):
        if contour_score > 0.65:
            return "a clear and flowing melodic contour"
        elif contour_score > 0.35:
            return "a lightly shaped melodic contour"
        else:
            return "a simple contour with room for creative expansion"

    def describe_hook(self, hook_score):
        if hook_score > 0.45:
            return "a memorable melodic hook"
        elif hook_score > 0.25:
            return "a mildly recognizable hook"
        else:
            return "a simple motif that can be further developed"

    def describe_rhythm(self, rhythm_score):
        if rhythm_score > 0.55:
            return "a stable rhythmic pattern"
        elif rhythm_score > 0.35:
            return "a light rhythmic motion"
        else:
            return "a flexible rhythm that allows stylistic reinterpretation"

    def describe_scale(self, scale_corr):
        if scale_corr > 0.6:
            return "closely aligned with a musical scale"
        elif scale_corr > 0.35:
            return "generally aligned with a musical scale"
        else:
            return "melodically open, suitable for stylistic adaptation"

    # -----------------------------
    # Style-specific description（核心增强）
    # -----------------------------

    def describe_style(self, target_style: str):
        """
        根据 target_style 返回:
        - core_name: 展示用名字（放在 **...** 里）
        - focus_block: 多行 bullet，用于 "Focus on:" 部分
        """
        s = (target_style or "").strip().lower()

        if s == "rock":
            core = "energetic rock"
            focus = """- distorted electric guitars with overdrive and palm-muted riffs
- punchy acoustic or electronic drums with a strong backbeat on 2 and 4
- tight bass line locking with the kick drum
- clearly defined verse–chorus structure with powerful transitions"""
        elif s == "jazz":
            core = "swing jazz"
            focus = """- swing rhythm with a laid-back groove (triplet feel)
- walking bass lines outlining extended chords
- piano or guitar comping with jazz harmony (7th, 9th, 11th chords)
- light acoustic drums with ride cymbal patterns and subtle fills"""
        elif s == "electronic":
            core = "modern electronic"
            focus = """- punchy electronic kick drum and snare in a steady beat
- deep sub bass and sidechain-style pumping groove
- bright synth leads and pads with clear stereo width
- electronic sound design elements such as risers, sweeps and effects"""
        elif s == "pop":
            core = "modern pop"
            focus = """- clean and bright production with a polished mix
- catchy chord progressions and memorable hooks
- tight pop drums with clear kick, snare and hi-hats
- layered synths, guitars or keys supporting the vocal-style melody"""
        elif s == "classical":
            core = "orchestral classical"
            focus = """- orchestral instrumentation such as strings, woodwinds and brass
- structured harmonic progression with clear phrases
- dynamic shaping with crescendos and decrescendos
- expressive legato lines and voice leading between parts"""
        else:
            core = target_style or "a clear musical"
            focus = """- instrumentation that strongly reflects the chosen style
- characteristic rhythm and harmony patterns of the style
- phrasing and arrangement that clearly define the genre"""

        return core, focus

    # -----------------------------
    # Build Full Prompt
    # -----------------------------

    def build_prompt(
        self,
        melody_info,
        target_style,
        target_emotion,
        creativity=1.0,
        attempt=1,
    ):
        """
        melody_info 字典字段:
            - pitch_range
            - hook_score
            - contour_score
            - rhythm_score
            - scale_corr
            - key
        """

        pr_desc = self.describe_pitch_range(melody_info["pitch_range"])
        hook_desc = self.describe_hook(melody_info["hook_score"])
        contour_desc = self.describe_contour(melody_info["contour_score"])
        rhythm_desc = self.describe_rhythm(melody_info["rhythm_score"])
        scale_desc = self.describe_scale(melody_info["scale_corr"])

        # 旋律部分
        melody_part = f"""
### Melody Characteristics
The extracted melody features:
- {pr_desc}
- {contour_desc}
- {hook_desc}
- {rhythm_desc}
- {scale_desc}
- key signature: {melody_info.get("key", "unknown")}
"""

        # 风格说明（风格增强）
        style_name, style_focus = self.describe_style(target_style)
        style_part = f"""
### Target Style
Rewrite the music into **{style_name}** style.

Focus on:
{style_focus}
"""

        # 情绪说明（原逻辑保留）
        emotion_part = f"""
### Target Emotion
The emotional direction should be: **{target_emotion}**.

Include:
- emotional tone and expressive phrasing that match {target_emotion}
- energy level and atmosphere consistent with {target_emotion}
"""

        # 生成要求
        requirements = f"""
### Requirements
- Preserve the recognizable melodic identity while allowing creative variation.
- Adapt harmony, rhythm, and instrumentation strongly toward **{style_name}**.
- Maintain emotional color consistent with **{target_emotion}**.
- Avoid silence, ensure smooth transitions between sections.
- Produce musically coherent, structured output with clear genre characteristics.
"""

        # 提示 MusicGen 进行逐轮改善
        meta = f"### Generation Attempt: {attempt}\nCreativity Level: {creativity:.2f}\n"

        final_prompt = (
            "You are transforming music based on structured melodic analysis.\n\n"
            + meta
            + melody_part
            + style_part
            + emotion_part
            + requirements
        )

        return final_prompt
=======
# backend/inference/prompt_builder.py

=======
>>>>>>> 368ab93 (need_test_try)
class PromptBuilder:
    """
    Stable prompt builder for MusicGen.
    Keep prompt short, clear, effective.
    """

    def build(self, style, emotion, melody_info):
        key = melody_info.get("key", "C")
        scale = melody_info.get("scale", "major")
        tempo = melody_info.get("tempo", 120)

        prompt = (
            f"A {style} music track with a {emotion} mood. "
            f"Key: {key} {scale}. "
            f"Tempo: around {tempo} BPM. "
            "Coherent structure, clear melody, studio-quality sound."
        )
<<<<<<< HEAD

    @classmethod
    def build_prompt(
        cls,
        target_style: str,
        target_emotion: str,
        orig_style: str | None = None,
        orig_emotion: str | None = None,
        style_prob: dict | None = None,
        emotion_prob: dict | None = None,
        attempt: int = 1,
    ) -> str:
        target_style = (target_style or "").lower().strip()
        target_emotion = (target_emotion or "").lower().strip()

        style_desc = cls._describe_style(target_style)
        emotion_desc = cls.EMOTION_PROFILE.get(target_emotion, target_emotion)

        # 1) 原歌曲描述（来自你的模型）
        header_parts = []
        if orig_style or orig_emotion:
            parts = []
            if orig_style:
                parts.append(f"{orig_style} style")
            if orig_emotion:
                parts.append(f"{orig_emotion} emotion")
            header_parts.append(
                "The input audio is automatically analyzed as having "
                f"{' and '.join(parts)}. "
            )

        if style_prob:
            header_parts.append(f"Style distribution: {style_prob}. ")
        if emotion_prob:
            header_parts.append(f"Emotion distribution: {emotion_prob}. ")

        header_parts.append(
            f"Transform it into {target_style} style music expressing {emotion_desc}. "
        )
        header = "".join(header_parts)

        # 2) 风格模板
        style_part = (
            f"In the target {target_style} style, use the following characteristics: "
            f"{style_desc} "
        )

        # 3) 旋律保留比例随 attempt 变化
        if attempt <= 1:
            melody_part = (
                "Preserve around 60–70% of the original melodic contour so the track is clearly "
                "recognizable, but re-orchestrate it in the target style. "
            )
        elif attempt == 2:
            melody_part = (
                "Preserve around 40–60% of the original melodic contour, allowing noticeable "
                "variation in rhythm and phrasing while staying recognizable. "
            )
        elif attempt == 3:
            melody_part = (
                "Preserve only around 20–40% of the original melodic contour, focusing more on "
                "the target style and emotion while keeping a subtle hint of the original idea. "
            )
        else:
            melody_part = (
                "Preserve only a small trace of the original melodic contour; prioritize the "
                "target style and emotion, letting the music evolve more freely. "
            )

        # 4) 风格/情绪强化
        if attempt <= 1:
            strength = (
                f"Clearly emphasize {target_style} style and {target_emotion} emotion, while "
                "keeping the musical flow smooth and coherent. "
            )
        elif attempt == 2:
            strength = (
                f"Make the {target_style} style and {target_emotion} emotion very obvious to the "
                "listener, even more than in the original track. "
            )
        elif attempt == 3:
            strength = (
                f"Strongly prioritize {target_style} aesthetics and {target_emotion} expression, "
                "even if it changes the original character. "
            )
        else:
            strength = (
                f"Aggressively push towards pure {target_style} aesthetics with unmistakable "
                f"{target_emotion} emotion, letting the music feel like a strong stylistic remake. "
            )

        # 5) 防静音 + 连续性 + 质量
        quality = (
            "Ensure continuous musical texture throughout the entire duration, with no silent or "
            "empty sections and no sudden dropouts of energy. High-quality studio mix, balanced EQ, "
            "wide stereo image, expressive dynamics, instrumental only, no vocals, no noise or clipping. "
        )

        return header + style_part + melody_part + strength + quality
>>>>>>> 0cf27b1 (failed_v4)
=======
        return prompt
>>>>>>> 368ab93 (need_test_try)
