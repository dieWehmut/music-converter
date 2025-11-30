from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import tempfile
import shutil
import uuid
import logging
import os

app = FastAPI(title="Music Converter - Dev API")

# Dev mode: when set to '1', server returns mock responses so frontend can be
# integrated without heavy ML dependencies. Enable with environment variable:
#   set MC_DEV_MODE=1
DEV_MODE = os.environ.get("MC_DEV_MODE", "0") == "1"

# Allow requests from common frontend dev origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

LOG = logging.getLogger("uvicorn.error")


@app.get("/api/styles")
async def get_styles():
    """返回可用的风格列表。优先从 style encoder 中读取，否则返回常见风格的备选列表。"""
    try:
        from backend.inference import style_recognition as sr
        classes = []
        try:
            classes = list(sr._STYLE_ENCODER.classes_)
        except Exception:
            # 如果 encoder 对象不可用，尝试通过模型预测的 classes 属性
            try:
                classes = list(sr._STYLE_MODEL.classes_)
            except Exception:
                classes = []
        if not classes:
            raise RuntimeError("no classes available")
        return {"styles": classes}
    except Exception as e:
        LOG.warning("get_styles fallback: %s", e)
        # fallback list
        return {"styles": ["rock", "pop", "jazz", "electronic", "classical"]}


def _save_upload_to_temp(upload: UploadFile):
    suffix = Path(upload.filename or "").suffix or ".wav"
    tmp = Path(tempfile.gettempdir()) / f"mc_upload_{uuid.uuid4().hex}{suffix}"
    with tmp.open("wb") as f:
        shutil.copyfileobj(upload.file, f)
    return str(tmp)


@app.post("/api/features")
async def extract_features(file: UploadFile = File(...)):
    """上传音频，返回分析结果（style/emotion/probabilities）"""
    # Dev mode: return mock features so frontend can integrate without heavy deps
    if DEV_MODE:
        mock = {
            "style": "rock",
            "emotion": "happy",
            "style_prob": {"rock": 0.7, "pop": 0.15, "jazz": 0.05, "electronic": 0.05, "classical": 0.05},
            "emotion_prob": {"happy": 0.6, "sad": 0.1, "angry": 0.05, "funny": 0.05, "scary": 0.05, "tender": 0.15}
        }
        # include uploaded filename so frontend can confirm the server received the file
        try:
            mock["uploaded_filename"] = file.filename
        except Exception:
            pass
        return JSONResponse(content=mock)

    tmp_path = None
    try:
        tmp_path = _save_upload_to_temp(file)
        from backend.inference.analyze import analyzer

        result = analyzer.analyze(tmp_path)
        # If analyzer returned an error dict, surface it as 500
        if isinstance(result, dict) and result.get("error"):
            raise RuntimeError(result.get("error"))
        return JSONResponse(content=result)
    except FileNotFoundError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        LOG.exception("extract_features failed")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        try:
            if tmp_path:
                Path(tmp_path).unlink(missing_ok=True)
        except Exception:
            pass


@app.post("/api/convert")
async def convert_audio(
    file: UploadFile = File(...),
    style: str = Form(None),
    emotion: str = Form(None),
):
    """上传音频并返回转换后的 wav 文件（同步阻塞实现，适用于本地开发测试）。

    注意：生成可能耗时较长，开发时可以接受，生产请改为后台任务/worker。
    """
    # Dev mode: return example file immediately (copy of test_audio.wav)
    if DEV_MODE:
        # In dev mode, return the uploaded file back to the client so the frontend
        # can verify the actual uploaded audio is being sent. This avoids always
        # returning the repository sample file and makes local testing clearer.
        try:
            tmp_out = _save_upload_to_temp(file)
            # try to infer media type from suffix
            media_type = "audio/wav"
            try:
                suff = Path(tmp_out).suffix.lower()
                if suff == ".mp3":
                    media_type = "audio/mpeg"
                elif suff == ".ogg":
                    media_type = "audio/ogg"
                elif suff == ".flac":
                    media_type = "audio/flac"
            except Exception:
                pass
            return FileResponse(str(tmp_out), media_type=media_type, filename=Path(tmp_out).name)
        except Exception:
            # fallback to original sample if uploaded file could not be used
            sample = Path(__file__).resolve().parent / "test_audio.wav"
            if not sample.exists():
                sample = Path(__file__).resolve().parent.parent / "test_audio.wav"
            if not sample.exists():
                sample = Path(__file__).resolve().parent.parent.parent / "backend" / "test_audio.wav"
            if not sample.exists():
                raise HTTPException(status_code=500, detail="dev sample audio not found")
            tmp_out = Path(tempfile.gettempdir()) / f"mc_generated_{uuid.uuid4().hex}.wav"
            shutil.copyfile(sample, tmp_out)
            return FileResponse(str(tmp_out), media_type="audio/wav", filename=tmp_out.name)

    tmp_path = None
    try:
        tmp_path = _save_upload_to_temp(file)

        out_dir = Path("backend/output")
        out_dir.mkdir(parents=True, exist_ok=True)

        from backend.inference.full_pipeline import FullMusicPipeline

        pipeline = FullMusicPipeline()
        # 使用提供的 style / emotion，若为空则使用默认值
        target_style = style or "rock"
        target_emotion = emotion or "happy"

        LOG.info("Starting pipeline for %s -> style=%s emotion=%s", tmp_path, target_style, target_emotion)
        best = pipeline.process(tmp_path, target_style, target_emotion, output_dir=str(out_dir))

        if not best:
            raise HTTPException(status_code=500, detail="generation failed or no output produced")

        return FileResponse(best, media_type="audio/wav", filename=Path(best).name)
    except HTTPException:
        raise
    except Exception as e:
        LOG.exception("convert_audio failed")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        try:
            if tmp_path:
                Path(tmp_path).unlink(missing_ok=True)
        except Exception:
            pass


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("backend.server:app", host="0.0.0.0", port=8000, reload=True)
