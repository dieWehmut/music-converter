from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse, PlainTextResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.concurrency import run_in_threadpool
from pathlib import Path
import tempfile
import shutil
import uuid
import logging
import os
import time

os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
app = FastAPI(title="Music Converter - Dev API")

# In-memory task store
# Structure: { task_id: { "status": "pending"|"processing"|"success"|"failed", "result_path": str, "error": str, "created_at": float } }
TASKS = {}

# Dev mode: when set to '1', server returns mock responses so frontend can be
# integrated without heavy ML dependencies. Enable with environment variable:
#   set MC_DEV_MODE=1
DEV_MODE = os.environ.get("MC_DEV_MODE", "0") == "1"

# Allow requests from common frontend dev origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://music-converter-production.up.railway.app",
        "https://music-converter-test.vercel.app",
        "https://music-converter.hc-dsw-nexus.me",
        "https://diewehmut-music-converter.hf.space",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

LOG = logging.getLogger("uvicorn.error")

# Global pipeline instance to avoid re-loading models on every request
_PIPELINE_INSTANCE = None

def get_pipeline():
    global _PIPELINE_INSTANCE
    if _PIPELINE_INSTANCE is not None:
        return _PIPELINE_INSTANCE
    
    try:
        from backend.inference.full_pipeline import FullMusicPipeline
        LOG.info("Loading FullMusicPipeline...")
        _PIPELINE_INSTANCE = FullMusicPipeline()
        LOG.info("FullMusicPipeline loaded.")
        return _PIPELINE_INSTANCE
    except ImportError as ie:
        LOG.warning("get_pipeline import failed: %s", ie)
        raise HTTPException(status_code=503, detail="Server not configured with ML dependencies (torch/tensorflow). Rebuild with INSTALL_HEAVY=true or use dev mode.")
    except Exception as e:
        LOG.exception("Failed to initialize pipeline")
        raise HTTPException(status_code=500, detail=f"Pipeline initialization failed: {e}")


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


@app.get("/api/emotions")
async def get_emotions():
    """返回可用的情绪列表。"""
    try:
        from backend.inference import emotion_recognition as er
        classes = list(er.emotion_labels)
        if not classes:
            raise RuntimeError("no classes available")
        return {"emotions": classes}
    except Exception as e:
        LOG.warning("get_emotions fallback: %s", e)
        # fallback list
        return {"emotions": ["happy", "sad", "angry", "funny", "scary", "tender"]}


@app.get("/")
async def root():
    """Basic root page to verify the backend is serving requests."""
    return HTMLResponse(content="<html><body><h1>Music Converter Backend</h1><p>OK</p></body></html>", status_code=200)


@app.get("/health")
async def health():
    """Lightweight health endpoint for uptime checks."""
    return PlainTextResponse("ok", status_code=200)


@app.get("/api/tasks/{task_id}")
async def get_task_status(task_id: str):
    task = TASKS.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@app.get("/api/tasks/{task_id}/download")
async def download_task_result(task_id: str):
    task = TASKS.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if task["status"] != "success":
        raise HTTPException(status_code=400, detail="Task not ready")
    
    path = Path(task["result_path"])
    if not path.exists():
         raise HTTPException(status_code=500, detail="File missing")
    return FileResponse(str(path), media_type="audio/wav", filename=path.name)


def _save_upload_to_temp(upload: UploadFile):
    suffix = Path(upload.filename or "").suffix or ".wav"
    tmp = Path(tempfile.gettempdir()) / f"mc_upload_{uuid.uuid4().hex}{suffix}"
    with tmp.open("wb") as f:
        shutil.copyfileobj(upload.file, f)
    return str(tmp)


@app.post("/api/features")
async def extract_features(file: UploadFile = File(...)):
    """上传音频，返回分析结果（style/emotion/probabilities）"""
    # DEV_MODE: 优先尝试真实分析，若依赖不可用则回退到 mock
    if DEV_MODE:
        tmp_path = None
        try:
            tmp_path = _save_upload_to_temp(file)
            try:
                from backend.inference.analyze import analyzer
            except ImportError as ie:
                LOG.warning("extract_features analyzer import failed (dev fallback): %s", ie)
                mock = {
                    "style": "rock",
                    "emotion": "happy",
                    "style_prob": {"rock": 0.7, "pop": 0.15, "jazz": 0.05, "electronic": 0.05, "classical": 0.05},
                    "emotion_prob": {"happy": 0.6, "sad": 0.1, "angry": 0.05, "funny": 0.05, "scary": 0.05, "tender": 0.15}
                }
                try:
                    mock["uploaded_filename"] = file.filename
                except Exception:
                    pass
                return JSONResponse(content=mock)

            # 尝试真实分析
            result = await run_in_threadpool(analyzer.analyze, tmp_path)
            if isinstance(result, dict) and result.get("error"):
                raise RuntimeError(result.get("error"))
            return JSONResponse(content=result)
        except FileNotFoundError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            LOG.exception("extract_features failed (dev real attempt)")
            raise HTTPException(status_code=500, detail=str(e))
        finally:
            try:
                if tmp_path:
                    Path(tmp_path).unlink(missing_ok=True)
            except Exception:
                pass

    tmp_path = None
    try:
        tmp_path = _save_upload_to_temp(file)
        try:
            from backend.inference.analyze import analyzer
        except ImportError as ie:
            LOG.warning("extract_features import failed: %s", ie)
            raise HTTPException(status_code=503, detail="Server not configured with ML dependencies (torch/tensorflow). Rebuild with INSTALL_HEAVY=true or use dev mode.")

        result = await run_in_threadpool(analyzer.analyze, tmp_path)
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


def process_conversion(task_id: str, tmp_path: str, target_style: str, target_emotion: str, out_dir: Path):
    TASKS[task_id]["status"] = "processing"
    try:
        # Use global pipeline instance
        pipeline = get_pipeline()
        LOG.info("Starting pipeline for %s -> style=%s emotion=%s", tmp_path, target_style, target_emotion)
        # Reduce max_attempts to 1 for faster generation
        best = pipeline.process(tmp_path, target_style, target_emotion, output_dir=str(out_dir), max_attempts=1)

        if not best:
            raise RuntimeError("generation failed or no output produced")
        
        # Ensure best is an absolute path or relative to CWD so FileResponse can find it
        best_path = Path(best).resolve()
        if not best_path.exists():
                # Fallback: try to find it relative to out_dir if it was returned as relative path
                best_path = out_dir / Path(best).name
                if not best_path.exists():
                    # Fallback: try to find it in CWD
                    best_path = Path(Path(best).name).resolve()

        if not best_path.exists():
            LOG.error(f"Generated file not found at {best_path} (original: {best})")
            raise RuntimeError(f"Generated file not found: {best}")

        TASKS[task_id]["status"] = "success"
        TASKS[task_id]["result_path"] = str(best_path)
        LOG.info(f"Task {task_id} completed successfully. Result: {best_path}")

    except Exception as e:
        LOG.exception(f"Task {task_id} failed")
        TASKS[task_id]["status"] = "failed"
        TASKS[task_id]["error"] = str(e)
    finally:
        try:
            if tmp_path:
                Path(tmp_path).unlink(missing_ok=True)
        except Exception:
            pass


@app.post("/api/convert")
async def convert_audio(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    style: str = Form(None),
    emotion: str = Form(None),
    task_id: str = Form(None)
):
    """上传音频并启动转换任务（异步）。返回 task_id 用于轮询状态。"""
    
    if not task_id:
        task_id = uuid.uuid4().hex

    # Dev mode: return mock success immediately
    if DEV_MODE:
        # ... (dev mode logic omitted for brevity, assuming dev mode users don't need persistence as much or we can mock it too)
        # For simplicity, let's just run the dev logic synchronously and return success if DEV_MODE is on, 
        # BUT to support the new frontend polling, we should probably mock the task flow too.
        # However, to keep changes minimal, let's just use the real flow but with mock pipeline if needed.
        # Actually, let's just stick to the real flow. If DEV_MODE is on, the pipeline might be mocked inside get_pipeline?
        # No, get_pipeline loads real pipeline.
        # Let's just keep the old synchronous dev mode block for now, but wrap it in a task?
        # No, let's just return the file directly if DEV_MODE is on, breaking the polling contract?
        # The frontend expects JSON {task_id} now.
        # So we MUST update DEV_MODE to return JSON.
        
        TASKS[task_id] = { "status": "success", "created_at": time.time(), "result_path": "backend/test_audio.wav" } # Mock path
        # Ensure mock file exists
        mock_path = Path("backend/test_audio.wav")
        if not mock_path.exists():
             # Create a dummy file
             with open(mock_path, "wb") as f: f.write(b"RIFF....WAVEfmt ...data....")
        
        return {"task_id": task_id, "status": "success"}

    tmp_path = None
    try:
        tmp_path = _save_upload_to_temp(file)

        # Use unique output directory to prevent overwriting
        out_dir = Path("backend/output") / task_id
        out_dir.mkdir(parents=True, exist_ok=True)

        # 使用提供的 style / emotion，若为空则传 None 给 pipeline (pipeline 会自动使用原音频的属性)
        target_style = style
        target_emotion = emotion
        
        # Init task
        TASKS[task_id] = { "status": "pending", "created_at": time.time() }

        # Start background task
        background_tasks.add_task(process_conversion, task_id, tmp_path, target_style, target_emotion, out_dir)

        return {"task_id": task_id, "status": "pending"}

    except Exception as e:
        LOG.exception("convert_audio failed")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("backend.server:app", host="0.0.0.0", port=8000, reload=True)