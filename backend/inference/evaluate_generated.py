<<<<<<< HEAD
# backend/inference/evaluate_generated.py

from pathlib import Path
import numpy as np
from scipy.spatial.distance import jensenshannon

from backend.inference.analyze import analyzer


# =========================
# 用户可修改
# =========================
ORIGINAL_AUDIO = r"backend/test_audio.wav"
GENERATED_AUDIO = r"backend/output/generated_final.wav"
TARGET_STYLE = "rock"
TARGET_EMOTION = "happy"
# =========================


# ---------- 工具函数 ----------
def gain_score(gain):
    if gain >= 0.35:
        return 20
    elif gain >= 0.20:
        return 16
    elif gain >= 0.10:
        return 12
    elif gain >= 0.00:
        return 8
    else:
        return 3


def escape_score(escape):
    if escape >= 0.45:
        return 20
    elif escape >= 0.25:
        return 15
    elif escape >= 0.10:
        return 10
    elif escape >= 0:
        return 5
    else:
        return 0


def js_score(js):
    if js >= 0.40:
        return 20
    elif js >= 0.30:
        return 16
    elif js >= 0.20:
        return 12
    elif js >= 0.10:
        return 8
    else:
        return 3


def confidence_score(conf):
    if conf >= 0.75:
        return 20
    elif conf >= 0.60:
        return 15
    elif conf >= 0.45:
        return 10
    else:
        return 5


def pretty(v):
    return f"{v:+.3f}"


# =============== 主程序 ===============
def main():
    print("\n==============================")
    print("   Evaluation System v4")
    print("==============================\n")

    # ---- analyze original ----
    print("Analyzing ORIGINAL audio…\n")
    orig = analyzer.analyze(ORIGINAL_AUDIO)
    print(f"Original Style:   {orig['style']}")
    print(f"Original Emotion: {orig['emotion']}")

    # ---- analyze generated ----
    print("\nAnalyzing GENERATED audio…\n")
    if not Path(GENERATED_AUDIO).exists():
        print("❌ File not found:", GENERATED_AUDIO)
        return

    gen = analyzer.analyze(GENERATED_AUDIO)
    print(f"Generated Style:   {gen['style']}")
    print(f"Generated Emotion: {gen['emotion']}")

    # ---- extract probabilities ----
    sp_orig = orig["style_prob"]
    sp_gen = gen["style_prob"]

    ep_orig = orig["emotion_prob"]
    ep_gen = gen["emotion_prob"]

    # ---- gains ----
    style_gain = sp_gen.get(TARGET_STYLE, 0) - sp_orig.get(TARGET_STYLE, 0)
    emo_gain = ep_gen.get(TARGET_EMOTION, 0) - ep_orig.get(TARGET_EMOTION, 0)

    # ---- escape ----
    escape = sp_orig.get(orig["style"], 0) - sp_gen.get(orig["style"], 0)

    # ---- JS divergence ----
    # Safe conversion of probability dicts to numeric vectors (handle sequence values)
    def _prob_dict_to_vector(d):
        import numpy as _np
        vec = []
        for v in (d or {}).values():
            try:
                if hasattr(v, "__iter__") and not isinstance(v, (str, bytes)):
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

    js_style = jensenshannon(
        _prob_dict_to_vector(sp_orig),
        _prob_dict_to_vector(sp_gen)
    )

    js_emo = jensenshannon(
        _prob_dict_to_vector(ep_orig),
        _prob_dict_to_vector(ep_gen)
    )

    js_total = (js_style + js_emo) / 2

    # ---- confidence ----
    conf = (max(sp_gen.values()) + max(ep_gen.values())) / 2

    # ---- individual scores ----
    sg = gain_score(style_gain)
    eg = gain_score(emo_gain)
    esc = escape_score(escape)
    js_s = js_score(js_total)
    cf = confidence_score(conf)

    FINAL = sg + eg + esc + js_s + cf

    print("\n==============================")
    print("     SCORING RESULTS")
    print("==============================\n")

    print(f"🎸 Style Gain:       {pretty(style_gain)}   → {sg}/20")
    print(f"🎭 Emotion Gain:     {pretty(emo_gain)}     → {eg}/20")
    print(f"↗ Escape Original:  {pretty(escape)}        → {esc}/20")
    print(f"📊 JS Divergence:    {js_total:.3f}         → {js_s}/20")
    print(f"🔮 Confidence:       {conf:.3f}             → {cf}/20")

    print("\n⭐ Final Score:", FINAL, "/ 100")

    if FINAL >= 90:
        print("✨ A+ 完美转换！")
    elif FINAL >= 75:
        print("👍 A 质量很高，风格迁移稳定")
    elif FINAL >= 60:
        print("🙂 B 有明显变化，但还可再加强")
    elif FINAL >= 40:
        print("⚠️ C 转换较弱，可尝试重新生成")
    else:
        print("❌ D 失败，需要调整 Prompt / Melody")

    print("\nEvaluation v4 complete.\n")


if __name__ == "__main__":
    main()
=======
# backend/inference/evaluate_generated.py

from pathlib import Path
from backend.inference.analyze import analyzer   # 使用你的 Analyzer 单例

# ============================
# 用户可修改路径
# ============================
ORIGINAL_AUDIO = r"D:\idea_python\music_project\backend\test_audio.wav"
GENERATED_AUDIO = r"D:\idea_python\music_project\backend\output\generated_style_transfer.wav"
# ============================


def compare_style_emotion(orig, gen):
    lines = []

    # Style diff
    if orig["style"] != gen["style"]:
        lines.append(f"🎸 Style changed: {orig['style']} → {gen['style']}")
    else:
        lines.append(f"🎸 Style unchanged: {orig['style']}")

    # Emotion diff
    if orig["emotion"] != gen["emotion"]:
        lines.append(f"🎭 Emotion changed: {orig['emotion']} → {gen['emotion']}")
    else:
        lines.append(f"🎭 Emotion unchanged: {orig['emotion']}")

    return "\n".join(lines)


def main():
    print("\n==============================")
    print("      Evaluate Generated Audio")
    print("==============================\n")

    # ========= 原歌 ==========
    print("🎼 Analyzing ORIGINAL audio...\n")
    orig = analyzer.analyze(ORIGINAL_AUDIO)

    print(f"Original Style:   {orig['style']}")
    print(f"Original Emotion: {orig['emotion']}")

    # ========= 生成歌 ==========
    print("\n🎶 Analyzing GENERATED audio...\n")

    if not Path(GENERATED_AUDIO).exists():
        print(f"❌ ERROR: File not found:\n{GENERATED_AUDIO}")
        return

    gen = analyzer.analyze(GENERATED_AUDIO)

    print(f"Generated Style:   {gen['style']}")
    print(f"Generated Emotion: {gen['emotion']}")

    # ========= 对比 ==========
    print("\n==============================")
    print("           DIFFERENCE")
    print("==============================\n")
    print(compare_style_emotion(orig, gen))

    print("\n🎯 Evaluation complete.\n")


if __name__ == "__main__":
    main()
>>>>>>> cb02a3d (portionwise_failed_model_v3)
