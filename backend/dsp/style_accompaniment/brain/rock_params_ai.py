# backend/dsp/style_accompaniment/brain/rock_params_ai.py

class RockParamsAI:
    """
    Rock 情绪大脑：
    输入:
        style: 目前先不管（上层可传 "rock"）
        emotion: sad/angry/funny/happy/tender/scary
        features: {
            "tempo": float,
            "energy": 0~1,
            "brightness": 0~1
        }
    输出:
        {
            "combo": "rock_angry",
            "tempo": float,
            "guitar": {...},
            "bass": {...},
            "drums": {...},
            "mix": {...}
        }
    """

    SUPPORTED_EMOTIONS = ["sad", "angry", "funny", "happy", "tender", "scary"]

    def _norm_emotion(self, emotion: str) -> str:
        e = (emotion or "").lower().strip()
        if e not in self.SUPPORTED_EMOTIONS:
            # 不认识的情绪都当成 happy 处理
            return "happy"
        return e

    def generate_all_params(self, style: str, emotion: str, features: dict) -> dict:
        tempo = float(features.get("tempo", 120.0) or 120.0)
        energy = float(features.get("energy", 0.5))
        brightness = float(features.get("brightness", 0.5))

        emotion = self._norm_emotion(emotion)
        combo = f"rock_{emotion}"

        # ----------- 情绪模板（旋律密度 + 力度 + 空间感） --------------

        if emotion == "angry":
            guitar = {
                "riff_density": 0.95,      # 几乎每小节都有 riff
                "fill_prob": 0.5,          # 一半小节结尾有 fill
                "variation_prob": 0.6,     # 经常换 riff
                "palm_mute": True,
                "distortion": 0.9,
            }
            bass = {
                "note_density": 0.9,
                "octave_prob": 0.7,
            }
            drums = {
                "loop_energy": 1.0,
                "fill_rate": 0.45,        # 越大 => 越多 fill
                "double_kick": True,
            }
            mix = {
                "eq_high": +0.4,
                "eq_low": +0.2,
                "reverb": 0.12,
                "saturation": 0.9,
                "stereo_width": 0.6,
            }

        elif emotion == "happy":
            guitar = {
                "riff_density": 0.8,
                "fill_prob": 0.35,
                "variation_prob": 0.5,
                "palm_mute": False,
                "distortion": 0.6,
            }
            bass = {
                "note_density": 0.8,
                "octave_prob": 0.4,
            }
            drums = {
                "loop_energy": 0.9,
                "fill_rate": 0.3,
                "double_kick": False,
            }
            mix = {
                "eq_high": +0.3,
                "eq_low": 0.0,
                "reverb": 0.18,
                "saturation": 0.5,
                "stereo_width": 0.7,
            }

        elif emotion == "funny":
            guitar = {
                "riff_density": 0.75,
                "fill_prob": 0.5,
                "variation_prob": 0.8,   # riff 经常乱跳
                "palm_mute": False,
                "distortion": 0.5,
            }
            bass = {
                "note_density": 0.85,
                "octave_prob": 0.8,       # 跳八度多，看起来“逗比”
            }
            drums = {
                "loop_energy": 0.8,
                "fill_rate": 0.4,
                "double_kick": False,
            }
            mix = {
                "eq_high": +0.2,
                "eq_low": -0.1,
                "reverb": 0.2,
                "saturation": 0.4,
                "stereo_width": 0.8,
            }

        elif emotion == "sad":
            guitar = {
                "riff_density": 0.35,     # riff 少
                "fill_prob": 0.15,
                "variation_prob": 0.3,
                "palm_mute": False,
                "distortion": 0.25,
            }
            bass = {
                "note_density": 0.5,
                "octave_prob": 0.1,
            }
            drums = {
                "loop_energy": 0.4,
                "fill_rate": 0.12,
                "double_kick": False,
            }
            mix = {
                "eq_high": -0.1,
                "eq_low": +0.1,
                "reverb": 0.35,
                "saturation": 0.25,
                "stereo_width": 0.5,
            }

        elif emotion == "tender":
            guitar = {
                "riff_density": 0.3,
                "fill_prob": 0.1,
                "variation_prob": 0.25,
                "palm_mute": False,
                "distortion": 0.15,
            }
            bass = {
                "note_density": 0.4,
                "octave_prob": 0.05,
            }
            drums = {
                "loop_energy": 0.35,
                "fill_rate": 0.08,
                "double_kick": False,
            }
            mix = {
                "eq_high": -0.15,
                "eq_low": 0.0,
                "reverb": 0.4,
                "saturation": 0.2,
                "stereo_width": 0.55,
            }

        else:  # scary
            guitar = {
                "riff_density": 0.7,
                "fill_prob": 0.5,
                "variation_prob": 0.9,    # 变化最大
                "palm_mute": True,
                "distortion": 0.85,
            }
            bass = {
                "note_density": 0.6,
                "octave_prob": 0.3,
            }
            drums = {
                "loop_energy": 0.9,
                "fill_rate": 0.5,
                "double_kick": False,
            }
            mix = {
                "eq_high": +0.15,
                "eq_low": +0.25,
                "reverb": 0.3,
                "saturation": 0.8,
                "stereo_width": 0.4,
            }

        # 用原曲特征做微调（让 test_audio 真正有用）
        # energy 越大 -> riff 和鼓越激烈
        energy_scale = 0.5 + energy  # 0.5~1.5
        guitar["riff_density"] = float(
            max(0.1, min(1.0, guitar["riff_density"] * energy_scale))
        )
        bass["note_density"] = float(
            max(0.1, min(1.0, bass["note_density"] * energy_scale))
        )
        drums["loop_energy"] = float(
            max(0.2, min(1.2, drums["loop_energy"] * energy_scale))
        )

        # tempo 微调：高能量 -> 稍微加快
        tempo *= (0.9 + 0.2 * energy)

        return {
            "combo": combo,
            "tempo": float(tempo),
            "guitar": guitar,
            "bass": bass,
            "drums": drums,
            "mix": mix,
        }
