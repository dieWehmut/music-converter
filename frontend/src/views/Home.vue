<script setup>
import { ref, onMounted, nextTick, toRaw, markRaw } from 'vue'
import { getStyles, extractFeatures } from '../api/emotion'
import { convertAudio } from '../api/upload'
import AudioPlayer from '../components/AudioPlayer.vue'
import UploadAudio from '../components/UploadAudio.vue'
import TargetEmotionSelector from '../components/TargetEmotionSelector.vue'
import EmotionResult from '../components/EmotionResult.vue'
import WaveformCompare from '../components/WaveformCompare.vue'

const files = ref([]) // each item: { id, file, name, localUrl, features, extracting, converting, resultUrl, error }
const styles = ref([])
const selectedStyle = ref('')
const globalError = ref('')

// IndexedDB helpers for caching uploads across refresh
const DB_NAME = 'music-converter-db'
const STORE_NAME = 'uploads'

function serializeTasksForStorage(tasks) {
  return tasks.map(t => {
    const raw = toRaw(t)
    const { active, resultUrl, ...rest } = raw || {}
    return rest
  })
}

function openDb() {
  return new Promise((resolve, reject) => {
    const req = indexedDB.open(DB_NAME, 1)
    req.onupgradeneeded = () => {
      const db = req.result
      if (!db.objectStoreNames.contains(STORE_NAME)) {
        db.createObjectStore(STORE_NAME, { keyPath: 'id' })
      }
    }
    req.onsuccess = () => resolve(req.result)
    req.onerror = () => reject(req.error)
  })
}

async function saveUpload(record) {
  const db = await openDb()
  return new Promise((resolve, reject) => {
    const tx = db.transaction(STORE_NAME, 'readwrite')
    const store = tx.objectStore(STORE_NAME)
    const req = store.put(record)
    req.onsuccess = () => resolve(req.result)
    req.onerror = () => reject(req.error)
  })
}

async function updateUpload(id, changes) {
  const db = await openDb()
  return new Promise((resolve, reject) => {
    const tx = db.transaction(STORE_NAME, 'readwrite')
    const store = tx.objectStore(STORE_NAME)
    const getReq = store.get(id)
    getReq.onsuccess = () => {
      const data = getReq.result
      if (!data) {
        resolve() // nothing to update
        return
      }
      const updated = { ...data, ...changes }
      const putReq = store.put(updated)
      putReq.onsuccess = () => resolve(putReq.result)
      putReq.onerror = () => reject(putReq.error)
    }
    getReq.onerror = () => reject(getReq.error)
  })
}

async function getAllUploads() {
  const db = await openDb()
  return new Promise((resolve, reject) => {
    const tx = db.transaction(STORE_NAME, 'readonly')
    const store = tx.objectStore(STORE_NAME)
    const req = store.getAll()
    req.onsuccess = () => resolve(req.result || [])
    req.onerror = () => reject(req.error)
  })
}

async function deleteUploadById(id) {
  const db = await openDb()
  return new Promise((resolve, reject) => {
    const tx = db.transaction(STORE_NAME, 'readwrite')
    const store = tx.objectStore(STORE_NAME)
    const req = store.delete(id)
    req.onsuccess = () => resolve()
    req.onerror = () => reject(req.error)
  })
}

onMounted(async () => {
  // load cached uploads first
  try {
    const cached = await getAllUploads()
    for (const rec of cached) {
        // rec: { id, name, blob, selectedStyle, features, tasks, extracting }
        const item = {
          id: rec.id,
          file: rec.blob,
          name: rec.name,
          localUrl: (rec.blob instanceof Blob) ? URL.createObjectURL(rec.blob) : '',
          selectedStyle: rec.selectedStyle || '',
          features: rec.features || null,
          extracting: !!rec.extracting,
          converting: false, // always false on load, we don't auto-restart
          tasks: Array.isArray(rec.tasks) ? rec.tasks.map(t => {
            let rUrl = ''
            if (t.resultBlob instanceof Blob) {
                try { rUrl = URL.createObjectURL(t.resultBlob) } catch(e) { console.warn('bad blob', e) }
            }
            return {
                ...t,
                resultUrl: rUrl,
              status: t.status,
              active: false
            }
          }) : [],
          error: ''
        }
        // Migrate old single result to tasks if exists
        if (rec.resultBlob && item.tasks.length === 0) {
           let rUrl = ''
           if (rec.resultBlob instanceof Blob) {
              try { rUrl = URL.createObjectURL(rec.resultBlob) } catch(e){}
           }
           item.tasks.push({
             id: Date.now().toString(36),
             style: rec.selectedStyle || 'unknown',
             status: 'success',
             resultBlob: rec.resultBlob,
             resultUrl: rUrl,
             error: '',
             active: false
           })
        }

        files.value.push(item)
        // if extraction was in progress before refresh and features are not present, restart it
        if (item.extracting && !item.features) {
          // schedule next tick to avoid blocking mount
          setTimeout(() => doExtractFor(item), 50)
        }

    }
  } catch (e) {
    console.warn('no cached uploads or indexeddb not available', e)
  }

  try {
    const res = await getStyles()
    styles.value = Array.isArray(res) ? res : (res.styles || [])
    if (styles.value.length) {
      selectedStyle.value = styles.value[0]
      // initialize per-item selectedStyle when styles become available
      for (const it of files.value) {
        if (!it.selectedStyle) it.selectedStyle = styles.value[0]
      }
    }
  } catch (e) {
    console.warn('failed to load styles', e)
    globalError.value = '加载风格失败：' + (e.message || e)
  }
})

function makeItem(file) {
  return {
    id: Date.now().toString(36) + Math.random().toString(36).slice(2,8),
    file: markRaw(file),
    name: file.name,
    localUrl: URL.createObjectURL(file),
    selectedStyle: selectedStyle.value || (styles.value.length ? styles.value[0] : ''),
    features: null,
    extracting: false,
    converting: false,
    tasks: [],
    error: ''
  }
}

async function onFilesSelected(arr) {
  // arr can be an array of File or a single File (backcompat)
  let list = []
  if (!arr) return
  if (Array.isArray(arr)) list = arr
  else if (arr instanceof File) list = [arr]
  else return

  for (const f of list) {
    const rawItem = makeItem(f)
    files.value.push(rawItem)
    // use the reactive item from the array so changes trigger updates
    const item = files.value[files.value.length - 1]

    // mark as extracting and persist immediately so refresh shows state
    item.extracting = true
    try {
      await saveUpload({ 
        id: item.id, 
        name: item.name, 
        blob: item.file, 
        selectedStyle: item.selectedStyle || '', 
        features: null, 
        extracting: true, 
        tasks: [] 
      })
    } catch (e) {
      console.warn('saveUpload failed', e)
    }

    // start extracting for each
    doExtractFor(item)
  }
}

function onStyleChange(item) {
  try {
    updateUpload(item.id, { selectedStyle: item.selectedStyle })
  } catch (e) {
    console.warn('updateUpload style failed', e)
  }
}

async function doExtractFor(item) {
  item.error = ''
  item.extracting = true
  item.features = null
  // persist extracting state so refresh shows it
  try { await updateUpload(item.id, { extracting: true }) } catch (e) {}
  try {
    item.features = await extractFeatures(item.file)
    // immediately clear extracting so UI updates before DB write
    item.extracting = false
    await nextTick()
    // save features to cache and clear extracting
    try { await updateUpload(item.id, { features: item.features, extracting: false }) } catch(e){}
  } catch (e) {
    console.error(e)
    item.error = '提取特征失败：' + (e.message || e)
    try { await updateUpload(item.id, { extracting: false }) } catch(e){}
  } finally {
    item.extracting = false
  }
}

async function runTask(item, taskProxy) {
  taskProxy.active = true
  try {
    console.log('Starting conversion for', item.name, 'with style', taskProxy.style)
    
    const blob = await convertAudio(item.file, taskProxy.style)
    console.log('Conversion success, blob size:', blob.size)
    
    // Re-find the task in the reactive array to ensure we update the live object
    const liveItem = files.value.find(f => f.id === item.id)
    if (liveItem) {
        const liveTask = liveItem.tasks.find(t => t.id === taskProxy.id)
        if (liveTask) {
            liveTask.status = 'success'
            liveTask.resultBlob = markRaw(blob)
            liveTask.resultUrl = URL.createObjectURL(blob)
            liveTask.error = ''
        }
    }

    // Save result to cache
    try {
      await updateUpload(item.id, { tasks: serializeTasksForStorage(item.tasks) })
    } catch (e) {
      console.warn('Failed to save conversion result to cache', e)
    }
  } catch (e) {
    console.error('Conversion failed', e)
    // Re-find task for error update too
    const liveItem = files.value.find(f => f.id === item.id)
    if (liveItem) {
        const liveTask = liveItem.tasks.find(t => t.id === taskProxy.id)
        if (liveTask) {
            liveTask.status = 'error'
            liveTask.error = '转换失败：' + (e.message || e)
        }
    }
    
    try { 
      await updateUpload(item.id, { tasks: serializeTasksForStorage(item.tasks) }) 
    } catch(e){}
  } finally {
    taskProxy.active = false
  }
}

async function onConvertItem(item) {
  // Ensure we are working with the reactive object from the list
  const reactiveItem = files.value.find(f => f.id === item.id) || item
  
  reactiveItem.error = ''
  if (!reactiveItem.file) return (reactiveItem.error = '无有效音频')
  
  const styleToUse = reactiveItem.selectedStyle || selectedStyle.value

  // If there is a stored converting task that isn't actively running yet (e.g. after refresh), resume it
  const resumableTask = reactiveItem.tasks.find(t => t.status === 'converting' && !t.active)
  if (resumableTask) {
    resumableTask.error = ''
    await runTask(reactiveItem, resumableTask)
    return
  }
  
  // Create new task
  const newTaskRaw = {
    id: Date.now().toString(36) + Math.random().toString(36).slice(2,5),
    style: styleToUse,
    status: 'converting',
    resultUrl: '',
    resultBlob: null,
    error: '',
    active: true
  }
  const newLength = reactiveItem.tasks.push(newTaskRaw)
  const taskProxy = reactiveItem.tasks[newLength - 1]
  
  // Persist initial task state
  try { await updateUpload(reactiveItem.id, { tasks: serializeTasksForStorage(reactiveItem.tasks) }) } catch(e){}

  await runTask(reactiveItem, taskProxy)
}

async function retryTask(item, task) {
  const reactiveItem = files.value.find(f => f.id === item.id) || item
  const taskProxy = reactiveItem.tasks.find(t => t.id === task.id)
  if (!taskProxy) return

  taskProxy.status = 'converting'
  taskProxy.error = ''
  
  // Persist state change
  try { await updateUpload(reactiveItem.id, { tasks: serializeTasksForStorage(reactiveItem.tasks) }) } catch(e){}

  await runTask(reactiveItem, taskProxy)
}

function removeItem(index) {
  const it = files.value[index]
  if (!it) return
  try { if (it.localUrl) URL.revokeObjectURL(it.localUrl) } catch(e){}
  if (it.tasks) {
    for (const t of it.tasks) {
      try { if (t.resultUrl) URL.revokeObjectURL(t.resultUrl) } catch(e){}
    }
  }
  // remove from cache as well
  try { deleteUploadById(it.id).catch(()=>{}) } catch(e){}
  files.value.splice(index,1)
}
</script>

<template>
  <div class="page">
    <div class="container">
      <h1>Music Converter</h1>

      <div class="styles-debug card" style="margin-bottom:12px;padding:12px">
        <h3 style="margin:0 0 8px">可用风格（styles）</h3>
        <div v-if="styles.length" class="styles-list">
          <span v-for="s in styles" :key="s" class="style-pill">{{ s }}</span>
        </div>
        <div v-else-if="globalError" class="error">加载风格失败：{{ globalError }}</div>
        <div v-else>加载中…</div>
      </div>

      <section class="card">
        <div class="center">
          <div class="row buttons-row">
            <UploadAudio  @files="onFilesSelected">上传音频</UploadAudio>
            <div class="upload-count" v-if="files.length">已上传 {{ files.length }}</div>

            <div class="spacer"></div>
          </div>
        </div>

        <p v-if="globalError" class="error">{{ globalError }}</p>

        <div class="file-list">
          <div v-for="(item, idx) in files" :key="item.id" class="file-item card">
            <div class="file-header">
              <div class="file-left">
                <div class="file-index">{{ idx + 1 }}</div>
                <div style="display:flex;align-items:center;gap:12px">
                  <div class="file-title">{{ item.name }}</div>
                  <TargetEmotionSelector v-model="item.selectedStyle" :styles="styles" @update:modelValue="onStyleChange(item)" />
                </div>
              </div>
              <div class="file-actions">
                <button class="btn small" @click="removeItem(idx)">删除</button>
                <button class="btn small primary" @click="onConvertItem(item)" :disabled="item.extracting || item.tasks.some(t => t.active)">
                  {{ item.tasks.some(t => t.active) ? `转换中... ${item.tasks.filter(t => t.status === 'success').length}/${item.tasks.length}` : '转换' }}
                </button>
              </div>
            </div>

            <div class="file-body">
              <div class="audio-large">
                <audio :src="item.localUrl" controls preload="metadata"></audio>
              </div>

              <div class="meta">
                <div v-if="item.extracting">自动提取中…</div>
                <EmotionResult v-if="item.features" :features="item.features" />
                <div v-if="item.error" class="error">{{ item.error }}</div>
                
                <div v-if="item.tasks && item.tasks.length" class="tasks-list">
                  <h4>转换任务列表</h4>
                  <div v-for="task in item.tasks" :key="task.id" class="task-item">
                    <div class="task-header">
                      <span class="task-style">风格: {{ task.style }}</span>
                      <span class="task-status" :class="task.status">
                        {{ task.status === 'converting' ? '转换中...' : task.status === 'success' ? '成功' : '失败' }}
                      </span>
                      <div v-if="task.status === 'error'" class="task-actions" style="margin-left:auto">
                        <button class="btn small" @click="retryTask(item, task)">重试</button>
                      </div>
                    </div>
                    <div v-if="task.status === 'success'" class="task-result">
                      <audio :src="task.resultUrl" controls></audio>
                      <a class="download-btn" :href="task.resultUrl" :download="item.name + '.' + task.style + '.wav'">下载</a>
                    </div>
                    <div v-if="task.status === 'error'" class="error small">{{ task.error }}</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      
    </div>
  </div>
</template>

<style scoped>
.page{min-height:100vh;display:flex;align-items:center;justify-content:center;padding:36px;background:linear-gradient(180deg,#f8fafc,#eef2ff)}
.container{width:100%;max-width:820px;margin:0 auto;font-family:system-ui,-apple-system,'Segoe UI',Roboto,'Helvetica Neue',Arial;color:#0f172a}
.card{background:#fff;border-radius:14px;padding:18px;border:1px solid rgba(15,23,42,0.04);box-shadow:0 8px 30px rgba(2,6,23,0.06)}
h1{margin:0 0 16px;text-align:center;font-size:28px;color:#0f172a}
.file{display:block;margin-bottom:12px}
.row{display:flex;align-items:center;gap:12px;margin-top:8px}
.buttons-row{align-items:center}
.btn{
  display:inline-flex;align-items:center;gap:8px;padding:8px 12px;border-radius:10px;border:1px solid #e6eef8;background:#fff;color:#0f172a;cursor:pointer;transition:transform .06s ease,box-shadow .12s ease,background .12s;box-shadow:0 2px 6px rgba(2,6,23,0.06);
}
.btn:hover{transform:translateY(-3px);box-shadow:0 10px 30px rgba(2,6,23,0.09);background:#f8fbff}
.btn:active{transform:translateY(0);box-shadow:0 2px 6px rgba(2,6,23,0.06)}
.btn:disabled{opacity:0.7;cursor:not-allowed;transform:none;box-shadow:none}
.btn.primary{background:#2563eb;color:#fff;border:none}
.btn.primary:hover{background:#1e4fcf}

select{padding:8px;border-radius:8px;border:1px solid #e6eef8;background:#fbfdff}
.spacer{flex:1}
.upload-btn{display:inline-flex;align-items:center;gap:8px;padding:8px 10px;border-radius:8px;border:1px solid #e6eef8;background:#fff;color:#0f172a;cursor:pointer}
.upload-btn input[type=file]{position:absolute;left:-9999px}
select{padding:8px;border-radius:8px;border:1px solid #e6eef8;background:#fbfdff}
.convert-btn{display:inline-flex;align-items:center;gap:8px;padding:8px 10px;border-radius:8px;background:#2563eb;color:white;border:none;cursor:pointer}
.convert-btn:disabled{opacity:0.6;cursor:not-allowed}
.download-btn{display:inline-flex;align-items:center;gap:8px;padding:6px 10px;border-radius:8px;background:transparent;border:1px solid #e6eef8;color:#0f172a;text-decoration:none}
.features pre{background:#f8fafc;padding:8px;border-radius:8px;overflow:auto}
.status{margin-top:8px;color:#475569}
.error{color:#b91c1c}
.note{margin-top:14px;color:#64748b;font-size:13px;text-align:center}
.center{display:flex;flex-direction:column;align-items:center;justify-content:center;gap:14px;text-align:center}
.file-list{display:flex;flex-direction:column;gap:14px;margin-top:16px}
.file-item{padding:12px}
.file-header{display:flex;align-items:center;justify-content:space-between;width:100%;gap:12px}
.file-left{display:flex;align-items:center;gap:12px}
.file-index{width:30px;height:30px;border-radius:8px;background:linear-gradient(180deg,#fff,#f1f5f9);display:flex;align-items:center;justify-content:center;font-weight:700;color:#0f172a;border:1px solid rgba(15,23,42,0.06);box-shadow:0 4px 10px rgba(2,6,23,0.04)}
.file-title{font-weight:600}
.file-actions{display:flex;gap:8px}
.btn.small{padding:6px 8px;border-radius:8px}
.audio-large audio{width:100%;height:72px}
.upload-count{margin-left:12px;padding:6px 10px;border-radius:999px;background:linear-gradient(90deg,#eef2ff,#f0fdf4);color:#0f172a;border:1px solid rgba(15,23,42,0.04);font-weight:600}
.file-body{display:flex;flex-direction:column;gap:12px;margin-top:10px}
.meta{display:flex;flex-direction:column;gap:8px}
.result audio{width:100%}
.styles-list{display:flex;flex-wrap:wrap;gap:8px}
.style-pill{display:inline-block;padding:6px 10px;border-radius:999px;background:linear-gradient(90deg,#eef2ff,#f0fdf4);border:1px solid rgba(15,23,42,0.04);font-weight:600}
.tasks-list{margin-top:12px;border-top:1px solid #f1f5f9;padding-top:12px}
.task-item{background:#f8fafc;border-radius:8px;padding:10px;margin-bottom:8px;border:1px solid #e2e8f0}
.task-header{display:flex;justify-content:space-between;margin-bottom:8px;font-size:14px;font-weight:600}
.task-status.converting{color:#2563eb}
.task-status.success{color:#16a34a}
.task-status.error{color:#dc2626}
.task-result{display:flex;align-items:center;gap:12px}
.task-result audio{height:40px;flex:1}
.error.small{font-size:12px;margin-top:4px}
</style>
