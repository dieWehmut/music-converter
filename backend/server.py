from fastapi import FastAPI, UploadFile, File, Form, HTTPException
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
import queue
import threading
import soundfile as sf

# 设置 HuggingFace 镜像，防止国内下载模型超时
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"

app = FastAPI(title="Music Converter - Priority Queue System")

# ==========================================
# 全局配置与变量
# ==========================================

# 1. 任务存储
TASKS = {}

# 2. 优先级队列 (PriorityQueue)
# 格式: (priority, timestamp, job_payload)
# priority 越小越先执行 (10 = High, 50 = Normal)
JOB_QUEUE = queue.PriorityQueue()

# 3. 全局 Pipeline 实例
_PIPELINE_INSTANCE = None

LOG = logging.getLogger("uvicorn.error")

# 4. 环境变量开关
# 开发模式 (Mock数据)
DEV_MODE = os.environ.get("MC_DEV_MODE", "0") == "1"

# 长音频允许开关
# "0" (False) -> 默认：阻止 > 20s 的音频，直接报错
# "1" (True)  -> 解锁：允许 > 20s 的音频，但优先级较低
ENABLE_LONG_AUDIO = os.environ.get("MC_ENABLE_LONG_AUDIO", "0") == "1"

# 5. CORS 设置 (使用你指定的列表)
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

# ==========================================
# 核心逻辑：Pipeline 加载与后台 Worker
# ==========================================

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
        raise HTTPException(status_code=503, detail="Server not configured with ML dependencies.")
    except Exception as e:
        LOG.exception("Failed to initialize pipeline")
        raise HTTPException(status_code=500, detail=f"Pipeline initialization failed: {e}")

def worker_loop():
    """
    后台消费者线程：
    一直运行，从优先级队列中取任务执行。
    保证 CPU 永远只处理一个任务，防止卡死。
    """
    LOG.info(f"🚀 Priority Worker started! Long Audio Enabled: {ENABLE_LONG_AUDIO}")
    
    while True:
        # 1. 阻塞等待任务
        # 取出元组: (优先级, 时间戳, 任务数据)
        priority, ts, job = JOB_QUEUE.get()
        
        task_id = job["task_id"]
        tmp_path = job["tmp_path"]
        target_style = job["target_style"]
        target_emotion = job["target_emotion"]
        out_dir = job["out_dir"]
        duration = job.get("duration", 0)

        p_label = "🔥HIGH" if priority < 50 else "🐢NORMAL"
        LOG.info(f"👷 Worker picked up {p_label} priority task: {task_id} (len={duration:.1f}s). Remaining: {JOB_QUEUE.qsize()}")

        # 2. 更新状态
        if task_id in TASKS:
            TASKS[task_id]["status"] = "processing"
        
        try:
            # 3. 加载模型
            pipeline = get_pipeline()
            
            LOG.info(f"Starting pipeline processing for {task_id}...")
            
            # 4. 执行推理 (耗时操作)
            # 传入绝对路径字符串
            best = pipeline.process(
                tmp_path, 
                target_style, 
                target_emotion, 
                output_dir=str(out_dir), 
                max_attempts=1
            )

            if not best:
                raise RuntimeError("Pipeline returned no output.")

            # 5. 验证结果文件
            best_path = Path(best).resolve()
            if not best_path.exists():
                # 尝试在 out_dir 查找相对路径
                possible = out_dir / Path(best).name
                if possible.exists():
                    best_path = possible.resolve()
                else:
                    raise RuntimeError(f"Generated file missing at {best_path}")

            # 6. 标记成功
            TASKS[task_id]["status"] = "success"
            TASKS[task_id]["result_path"] = str(best_path)
            LOG.info(f"✅ Task {task_id} finished successfully.")

        except Exception as e:
            LOG.exception(f"❌ Task {task_id} failed inside worker.")
            TASKS[task_id]["status"] = "failed"
            TASKS[task_id]["error"] = str(e)
        
        finally:
            # 7. 清理上传的临时文件
            try:
                if tmp_path and os.path.exists(tmp_path):
                    os.remove(tmp_path)
            except:
                pass
            
            # 标记队列任务完成
            JOB_QUEUE.task_done()

# 应用启动时开启 Worker 线程
@app.on_event("startup")
async def startup_event():
    t = threading.Thread(target=worker_loop, daemon=True)
    t.start()

# ==========================================
# API 接口
# ==========================================

@app.get("/")
async def root():
    status_text = "Allowed" if ENABLE_LONG_AUDIO else "Blocked (>20s)"
    return HTMLResponse(f"<h1>Music Converter Backend</h1><p>Mode: Priority Queue</p><p>Long Audio: {status_text}</p>")

@app.get("/health")
async def health():
    return "ok"

@app.get("/api/styles")
async def get_styles():
    try:
        from backend.inference import style_recognition as sr
        classes = []
        try:
            classes = list(sr._STYLE_ENCODER.classes_)
        except Exception:
            try:
                classes = list(sr._STYLE_MODEL.classes_)
            except Exception:
                classes = []
        if not classes:
            raise RuntimeError("no classes available")
        return {"styles": classes}
    except Exception as e:
        LOG.warning("get_styles fallback: %s", e)
        return {"styles": ["rock", "pop", "jazz", "electronic", "classical"]}

@app.get("/api/emotions")
async def get_emotions():
    try:
        from backend.inference import emotion_recognition as er
        classes = list(er.emotion_labels)
        if not classes:
            raise RuntimeError("no classes available")
        return {"emotions": classes}
    except Exception as e:
        LOG.warning("get_emotions fallback: %s", e)
        return {"emotions": ["happy", "sad", "angry", "funny", "scary", "tender"]}

@app.get("/api/tasks/{task_id}")
async def get_task_status(task_id: str):
    task = TASKS.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    response = task.copy()
    if task["status"] == "queued":
        p_val = task.get("priority_val", 50)
        p_text = "High Priority" if p_val < 50 else "Normal Priority"
        response["msg"] = f"Queued ({p_text}). Waiting for processor..."
        
    return response

@app.get("/api/tasks/{task_id}/download")
async def download_task_result(task_id: str):
    task = TASKS.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if task["status"] != "success":
        raise HTTPException(status_code=400, detail="Task not ready")
    
    path = Path(task["result_path"])
    if not path.exists():
         raise HTTPException(status_code=500, detail="File missing on server")
    return FileResponse(str(path), media_type="audio/wav", filename=path.name)

def _save_upload_to_temp(upload: UploadFile):
    suffix = Path(upload.filename or "").suffix or ".wav"
    tmp = Path(tempfile.gettempdir()) / f"mc_upload_{uuid.uuid4().hex}{suffix}"
    with tmp.open("wb") as f:
        shutil.copyfileobj(upload.file, f)
    return str(tmp)

@app.post("/api/features")
async def extract_features(file: UploadFile = File(...)):
    """特征提取接口"""
    # 如果是开发模式，返回 Mock 数据
    if DEV_MODE:
        return JSONResponse(content={
            "style": "rock",
            "emotion": "happy",
            "style_prob": {"rock": 0.8, "pop": 0.2},
            "emotion_prob": {"happy": 0.9, "sad": 0.1}
        })

    tmp_path = None
    try:
        tmp_path = _save_upload_to_temp(file)
        try:
            from backend.inference.analyze import analyzer
        except ImportError as ie:
            raise HTTPException(status_code=503, detail="ML dependencies missing.")

        result = await run_in_threadpool(analyzer.analyze, tmp_path)
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
    task_id: str = Form(None)
):
    """
    提交任务接口：
    1. 读取音频时长。
    2. 根据 ENABLE_LONG_AUDIO 决定是拒绝长任务还是降级长任务。
    3. 放入优先级队列。
    """
    if not task_id:
        task_id = uuid.uuid4().hex

    # Dev mode Mock
    if DEV_MODE:
        TASKS[task_id] = { "status": "success", "created_at": time.time(), "result_path": "backend/test_audio.wav" }
        return {"task_id": task_id, "status": "success"}

    tmp_path = None
    try:
        # 1. 保存临时文件
        tmp_path = _save_upload_to_temp(file)

        # 2. 读取音频时长
        try:
            info = sf.info(tmp_path)
            duration = info.duration
        except Exception:
            # 读取失败时清理文件并报错
            if tmp_path and os.path.exists(tmp_path):
                os.remove(tmp_path)
            raise HTTPException(status_code=400, detail="Cannot read audio duration (invalid file).")

        # ==========================================
        # ★★★ 逻辑判断区域 ★★★
        # ==========================================
        LIMIT_SECONDS = 20.0
        
        # 场景 A: 开关关闭 (默认) 且 超时 -> 拒绝任务 (返回 400)
        if not ENABLE_LONG_AUDIO and duration > LIMIT_SECONDS:
            print(f"🚫 [Block Mode] Rejected task {task_id}: Duration {duration:.2f}s > {LIMIT_SECONDS}s")
            
            if tmp_path and os.path.exists(tmp_path):
                os.remove(tmp_path)
                
            raise HTTPException(
                status_code=400, 
                detail=f"Audio too long ({duration:.1f}s). Max limit is {LIMIT_SECONDS}s."
            )

        # 场景 B: 允许通过，根据时长分配优先级
        # - 短任务 (<=20s) -> 优先级 10 (高)
        # - 长任务 (>20s)  -> 优先级 50 (低)
        if duration <= LIMIT_SECONDS:
            priority = 10 
            LOG.info(f"🚀 Short audio ({duration:.1f}s) -> HIGH Priority")
        else:
            priority = 50
            LOG.info(f"🐢 Long audio ({duration:.1f}s) -> NORMAL Priority")

        # ==========================================

        # 3. 准备输出目录 (绝对路径)
        out_dir = (Path("backend/output") / task_id).resolve()
        out_dir.mkdir(parents=True, exist_ok=True)

        # 4. 初始化任务状态
        TASKS[task_id] = { 
            "status": "queued", 
            "created_at": time.time(),
            "target_style": style,
            "target_emotion": emotion,
            "priority_val": priority
        }

        # 5. 构造任务包
        job_payload = {
            "task_id": task_id,
            "tmp_path": tmp_path,
            "target_style": style,
            "target_emotion": emotion,
            "out_dir": out_dir,
            "duration": duration
        }

        # 6. 放入优先级队列 (Priority, Timestamp, Payload)
        JOB_QUEUE.put((priority, time.time(), job_payload))
        
        LOG.info(f"📥 Task {task_id} enqueued. Queue size: {JOB_QUEUE.qsize()}")
        
        return {"task_id": task_id, "status": "queued"}

    except HTTPException as he:
        raise he
    except Exception as e:
        LOG.exception("convert_audio failed to enqueue")
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    # 启动服务
    uvicorn.run("backend.server:app", host="0.0.0.0", port=8000, reload=True)