# backend/inference/full_pipeline.py
# FullPipeline Ultimate Version
# - Integrated Scoring System v4 (0~100)
# - Friendly PromptBuilder support
# - Melody-aware multi-attempt generation
# - Auto early-stop at high score

from pathlib import Path
import numpy as np
import librosa
from scipy.spatial.distance import jensenshannon

from backend.inference.analyze import analyzer
from backend.inference.prompt_builder import PromptBuilder
from backend.inference.melody_extractor import MelodyExtractor
from backend.inference.melody_transformer import MelodyTransformer
from backend.inference.generate_music import MusicGenerator


# ============================================================
# 评分体系逻辑（与 evaluate_generated v4 一致）
# ============================================================

def gain_score(gain):
    if gain >= 0.35: return 20
    elif gain >= 0.20: return 16
    elif gain >= 0.10: return 12
    elif gain >= 0.00: return 8
    else: return 3


def escape_score(escape):
    if escape >= 0.45: return 20
    elif escape >= 0.25: return 15
    elif escape >= 0.10: return 10
    elif escape >= 0.00: return 5
    else: return 0


def js_score(js):
    if js >= 0.40: return 20
    elif js >= 0.30: return 16
    elif js >= 0.20: return 12
    elif js >= 0.10: return 8
    else: return 3


def confidence_score(conf):
    if conf >= 0.75: return 20
    elif conf >= 0.60: return 15
    elif conf >= 0.45: return 10
    else: return 5


def compute_final_score(orig, gen, target_style, target_emotion):
    """计算 0~100 综合分"""

    sp_orig = orig["style_prob"]
    sp_gen = gen["style_prob"]
    ep_orig = orig["emotion_prob"]
    ep_gen = gen["emotion_prob"]

    # --- 安全转换：将可能为 list/array 的值映射为单个 float（取均值）
    def _prob_dict_to_vector(d):
        import numpy as _np
        vec = []
        for v in (d or {}).values():
            try:
                if hasattr(v, "__iter__") and not isinstance(v, (str, bytes)):
                    # convert sequence to numeric list and take mean
                    vv = _np.array(v, dtype=float)
                    val = float(_np.mean(vv))
                else:
                    val = float(v)
            except Exception:
                try:
                    val = float(_np.array(v).astype(float).mean())
                except Exception:
                    val = 0.0
            vec.append(val)
        return _np.array(vec, dtype=float)

    # --- Gains ---
    style_gain = sp_gen.get(target_style, 0) - sp_orig.get(target_style, 0)
    emo_gain = ep_gen.get(target_emotion, 0) - ep_orig.get(target_emotion, 0)

    # --- Escape original style ---
    escape = sp_orig.get(orig["style"], 0) - sp_gen.get(orig["style"], 0)

    # --- JS Divergence ---
    js_style = jensenshannon(
        _prob_dict_to_vector(sp_orig),
        _prob_dict_to_vector(sp_gen)
    )
    js_emo = jensenshannon(
        _prob_dict_to_vector(ep_orig),
        _prob_dict_to_vector(ep_gen)
    )
    js_total = (js_style + js_emo) / 2

    # --- Confidence ---
    confidence = (max(sp_gen.values()) + max(ep_gen.values())) / 2

    # --- Sub-scores ---
    sg = gain_score(style_gain)
    eg = gain_score(emo_gain)
    esc = escape_score(escape)
    js_s = js_score(js_total)
    cf = confidence_score(confidence)

    total = sg + eg + esc + js_s + cf

    result = {
        "total": total,
        "style_gain": style_gain,
        "emotion_gain": emo_gain,
        "escape": escape,
        "js": js_total,
        "confidence": confidence,
        "details": (sg, eg, esc, js_s, cf),
    }
    return result


# ============================================================
# Full pipeline
# ============================================================

class FullMusicPipeline:

    def __init__(self):
        self.analyzer = analyzer
        self.prompt_builder = PromptBuilder()
        self.melody_extractor = MelodyExtractor()
        self.melody_transformer = MelodyTransformer()
        self.music_gen = MusicGenerator()

    @staticmethod
    def guidance_for_attempt(a):
        return {1: 3.8, 2: 3.6, 3: 3.4}.get(a, 3.2)

    # ----------------------------------
    # Melody info
    # ----------------------------------
    def build_melody_info(self, audio_path):

        tmp = self.melody_extractor.extract_melody_to_wav(
            audio_path,
            strength=0.9,
            weaken_level=0,
            output_path="backend/output/_tmp_analysis_melody.wav",
        )

        y_full, sr_full = self.melody_extractor._load_audio(audio_path)
        tonic_pc, mode, key_name = self.melody_extractor._detect_key(y_full, sr_full)

        y, sr = self.melody_extractor._load_audio(tmp)
        f0 = self.melody_extractor._extract_f0(y, sr)

        if f0 is None:
            f0_valid = np.array([])
        else:
            f0_valid = f0[~np.isnan(f0)]
            if f0_valid.size == 0:
                f0_valid = np.array([])

        scorer = self.prompt_builder.scorer

        if len(f0_valid):
            pitch_range = float(np.max(f0_valid) - np.min(f0_valid))
        else:
            pitch_range = 0.0

        if f0 is None or f0_valid.size == 0:
            hook_score = 0.0
            scale_corr = 0.0
            contour_score = 0.0
        else:
            hook_score = float(scorer.hook_score(f0))
            scale_corr = float(scorer.scale_score(f0))
            contour_score = float(scorer.contour_score(f0))

        rhythm_score = float(scorer.rhythm_score(y, sr))

        return {
            "key": key_name,
            "f0_valid": f0_valid,
            "pitch_range": pitch_range,
            "hook_score": hook_score,
            "rhythm_score": rhythm_score,
            "scale_corr": scale_corr,
            "contour_score": contour_score,
        }

    # ----------------------------------
    # Main process
    # ----------------------------------
    def process(self, audio_path, target_style, target_emotion,
                output_dir="backend/output", max_attempts=4):

        audio_path = Path(audio_path)
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # ======================================================
        # ★★★ 新增：打印原音乐 style / emotion
        # ======================================================
        print("🔍 Analyzing original audio…")
        orig = self.analyzer.analyze(str(audio_path))
        print(f"🎵 Original Style:   {orig['style']}")
        print(f"😊 Original Emotion: {orig['emotion']}")

        # --- Melody info ---
        print("\n🎼 Extracting melody info…")
        try:
            melody_info = self.build_melody_info(str(audio_path))
        except Exception as e:
            print("[WARN] melody info failed:", e)
            melody_info = {
                "key": "unknown",
                "pitch_range": 0,
                "hook_score": 0,
                "rhythm_score": 0,
                "scale_corr": 0,
                "contour_score": 0,
            }

        # ======================================================
        # ★★★ 新增：best-of 初始化
        # ======================================================
        best_score = -1
        best_output = None
        best_result = None

        print("\n🎶 Multi-attempt generation…")
        for attempt in range(1, max_attempts + 1):

            print(f"\n========== Attempt {attempt}/{max_attempts} ==========")

            # --- prompt ---
            prompt = self.prompt_builder.build_prompt(
                melody_info=melody_info,
                target_style=target_style,
                target_emotion=target_emotion,
                attempt=attempt,
                creativity=1.0,
            )

            print("\n🧠 Prompt:")
            print(prompt)

            # --- melody extract ---
            raw = self.melody_extractor.extract_melody_to_wav(
                str(audio_path),
                target_style=target_style,
                target_emotion=target_emotion,
                strength=0.9,
                output_path=output_dir / f"melody_attempt_{attempt}.wav",
                weaken_level=attempt - 1,
            )

            # --- melody transform ---
            transformed = self.melody_transformer.transform(
                raw,
                attempt=attempt,
                prev_score=best_score,
            )

            # --- generate ---
            out_file = output_dir / f"generated_attempt_{attempt}.wav"
            print("\n🎧 Generating MusicGen output…")

            self.music_gen.generate_with_melody(
                prompt=prompt,
                melody_path=str(transformed),
                output_path=str(out_file),
                target_seconds=15.0,
                guidance_scale=self.guidance_for_attempt(attempt),
                temperature=1.0,
                top_p=0.95,
                do_sample=True,
            )

            # --- analyze ---
            gen = self.analyzer.analyze(str(out_file))

            # --- score ---
            score_info = compute_final_score(orig, gen, target_style, target_emotion)
            score_total = score_info["total"]

            print("\n📊 Score Breakdown:")
            print(f"  Total Score:  {score_total:.2f} / 100")
            print(f"  Style Gain:   {score_info['style_gain']:+.3f}")
            print(f"  Emotion Gain: {score_info['emotion_gain']:+.3f}")
            print(f"  Escape:       {score_info['escape']:+.3f}")
            print(f"  JS Diverg.:   {score_info['js']:.3f}")
            print(f"  Confidence:   {score_info['confidence']:.3f}")

            # ======================================================
            # ★★★ 新增：best-of，仅 3 行
            # ======================================================
            if score_total > best_score:
                best_score = score_total
                best_output = str(out_file)
                best_result = gen

            # --- early stop（你的逻辑，不动） ---
            if score_total >= 90:
                print("✨ High-quality result achieved (A+). Early stop.")
                break

        print("\n🎉 Final Result")
        print("Best Score:", best_score)
        if best_result is not None:
            print("Best Style:", best_result.get("style"))
            print("Best Emotion:", best_result.get("emotion"))
        else:
            print("Best Style: N/A")
            print("Best Emotion: N/A")
        print("Best File:", best_output)

        return best_output


# ============================================================
# Run
# ============================================================

if __name__ == "__main__":
    pipeline = FullMusicPipeline()
    pipeline.process(
        audio_path="backend/test_audio.wav",
        target_style="rock",
        target_emotion="happy",
        output_dir="backend/output",
        max_attempts=4,
    )
