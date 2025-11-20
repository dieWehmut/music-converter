<<<<<<< HEAD
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

            import soundfile as sf
            import shutil
            import numpy as np

            # ====================================================
            # ★★★ 路径修复逻辑 (核心) ★★★
            # ====================================================
            # 1. 强制将输入路径转换为绝对路径
            audio_path = Path(audio_path).resolve()

            # 2. 处理输出路径：确保基于当前工作目录生成绝对路径
            # 如果传入的是相对路径 (如 "backend/output")，将其转换为绝对路径
            if Path(output_dir).is_absolute():
                output_dir = Path(output_dir)
            else:
                output_dir = (Path.cwd() / output_dir).resolve()

            # 3. 创建输出目录 (关键：必须加 parents=True 防止父目录不存在报错)
            output_dir.mkdir(parents=True, exist_ok=True)
            
            print(f"📂 Audio Path: {audio_path}")
            print(f"📂 Output Dir: {output_dir}")

            # ====================================================

            print("🔍 Analyzing original audio…")
            orig = self.analyzer.analyze(str(audio_path))
            print(f"🎵 Original Style:   {orig['style']}")
            print(f"😊 Original Emotion: {orig['emotion']}")

            if not target_style:
                target_style = orig['style']
            if not target_emotion:
                target_emotion = orig['emotion']

            # 1. 读取原音频完整数据
            print("📏 Checking duration...")
            y_full, sr_full = librosa.load(str(audio_path), sr=32000, mono=True)
            total_duration = librosa.get_duration(y=y_full, sr=sr_full)
            print(f"🕒 Total Duration: {total_duration:.2f}s")

            # --- Melody info (基于全曲提取特征，保持整体风格一致) ---
            print("\n🎼 Extracting global melody info…")
            try:
                melody_info = self.build_melody_info(str(audio_path))
            except Exception as e:
                print("[WARN] melody info failed:", e)
                melody_info = {"key": "C major", "pitch_range": 50, "hook_score": 0.5, "rhythm_score": 0.5, "scale_corr": 0.5, "contour_score": 0.5}

            best_score = -1
            best_output = None
            best_result = None

            # ====================================================
            # 开始尝试 (Attempts Loop)
            # ====================================================
            print(f"\n🎶 Multi-attempt generation ({max_attempts} attempts)...")
            
            for attempt in range(1, max_attempts + 1):
                print(f"\n========== Attempt {attempt}/{max_attempts} ==========")

                # 构建 Prompt (全曲通用)
                prompt = self.prompt_builder.build_prompt(
                    melody_info=melody_info,
                    target_style=target_style,
                    target_emotion=target_emotion,
                    attempt=attempt,
                    creativity=1.0,
                )
                print("🧠 Prompt (Summary):", prompt.split('\n')[1] if len(prompt.split('\n'))>1 else "...")

                # ================================================
                # ★★★ 分段处理逻辑 (Slicing) ★★★
                # ================================================
                
                # 临时文件夹，用于存放切片
                temp_seg_dir = output_dir / "temp_segments"
                
                # ★★★ 修复：必须加 parents=True，否则如果 output_dir 刚创建，这里可能会报错 ★★★
                temp_seg_dir.mkdir(parents=True, exist_ok=True)
                
                full_generated_audio = []
                
                # 按 30秒 切片循环
                segment_length_samples = 30 * sr_full
                total_segments = int(np.ceil(len(y_full) / segment_length_samples))

                for i in range(total_segments):
                    start_sample = i * segment_length_samples
                    end_sample = min((i + 1) * segment_length_samples, len(y_full))
                    
                    # 1. 切出当前 30s 片段
                    y_seg = y_full[start_sample:end_sample]
                    seg_duration = len(y_seg) / sr_full
                    
                    if seg_duration < 0.5: continue # 跳过极短碎片

                    # 2. 保存这个片段为临时文件 (供 melody_extractor 读取)
                    seg_input_path = temp_seg_dir / f"seg_input_{attempt}_{i}.wav"
                    
                    # ★★★ 修复：传给 sf.write 必须是 str ★★★
                    sf.write(str(seg_input_path), y_seg, sr_full)

                    print(f"  -> Processing Segment {i+1}/{total_segments} ({seg_duration:.1f}s)...")

                    # 3. 提取该片段的旋律
                    seg_melody_path = self.melody_extractor.extract_melody_to_wav(
                        str(seg_input_path),
                        target_style=target_style,
                        target_emotion=target_emotion,
                        strength=0.9,
                        output_path=temp_seg_dir / f"seg_mel_{attempt}_{i}.wav",
                        weaken_level=attempt - 1
                    )

                    # 4. 旋律变换
                    seg_trans_path = self.melody_transformer.transform(
                        seg_melody_path,
                        attempt=attempt
                    )

                    # 5. 生成该片段 (target_seconds 动态设为该片段长度)
                    seg_out_path = temp_seg_dir / f"seg_out_{attempt}_{i}.wav"
                    
                    self.music_gen.generate_with_melody(
                        prompt=prompt,
                        melody_path=str(seg_trans_path),
                        output_path=str(seg_out_path), # ★★★ 传 str ★★★
                        target_seconds=seg_duration,   # <--- 动态时长 (<=30s)
                        guidance_scale=self.guidance_for_attempt(attempt),
                        temperature=1.0,
                        top_p=0.95,
                        do_sample=True,
                    )

                    # 6. 读取生成结果存入列表
                    y_gen_seg, _ = librosa.load(str(seg_out_path), sr=32000, mono=True)
                    full_generated_audio.append(y_gen_seg)

                # ================================================
                # 拼接所有片段
                # ================================================
                print("🔗 Stitching segments together...")
                if len(full_generated_audio) > 0:
                    final_y = np.concatenate(full_generated_audio)
                else:
                    final_y = np.zeros(32000) # fallback

                # 保存最终完整文件
                final_out_file = output_dir / f"generated_attempt_{attempt}.wav"
                sf.write(str(final_out_file), final_y, 32000)

                # 清理临时文件 (可选，保持目录整洁)
                try:
                    shutil.rmtree(str(temp_seg_dir))
                except:
                    pass

                # ================================================
                # 评分与分析 (对拼接后的完整音频进行评分)
                # ================================================
                gen = self.analyzer.analyze(str(final_out_file))
                score_info = compute_final_score(orig, gen, target_style, target_emotion)
                score_total = score_info["total"]

                print(f"📊 Attempt {attempt} Score: {score_total:.2f} / 100")

                if score_total > best_score:
                    best_score = score_total
                    best_output = str(final_out_file)
                    best_result = gen

                if score_total >= 90:
                    print("✨ High-quality result achieved. Early stop.")
                    break

            print("\n🎉 Final Result")
            print("Best Score:", best_score)
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
=======
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
>>>>>>> decbe0b (style_emo_model_v2)
