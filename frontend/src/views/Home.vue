<script setup>
import { ref, onMounted } from 'vue'
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
      // rec: { id, name, blob, selectedStyle, features }
      const item = {
        id: rec.id,
        file: rec.blob,
        name: rec.name,
        localUrl: URL.createObjectURL(rec.blob),
        selectedStyle: rec.selectedStyle || '',
        features: rec.features || null,
        extracting: false,
        converting: false,
        resultUrl: '',
        error: ''
      }
      files.value.push(item)
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
    file,
    name: file.name,
    localUrl: URL.createObjectURL(file),
    selectedStyle: '',
    features: null,
    extracting: false,
    converting: false,
    resultUrl: '',
    error: ''
  }
}

function onFilesSelected(arr) {
  // arr can be an array of File or a single File (backcompat)
  let list = []
  if (!arr) return
  if (Array.isArray(arr)) list = arr
  else if (arr instanceof File) list = [arr]
  else return

  for (const f of list) {
    const item = makeItem(f)
    files.value.push(item)
    // start extracting for each
    doExtractFor(item)
    // persist raw upload to IndexedDB
    try {
      saveUpload({ id: item.id, name: item.name, blob: item.file, selectedStyle: item.selectedStyle || '', features: null })
    } catch (e) {
      console.warn('saveUpload failed', e)
    }
  }
}

async function doExtractFor(item) {
  item.error = ''
  item.extracting = true
  item.features = null
  try {
    item.features = await extractFeatures(item.file)
    // save features to cache
    try { await saveUpload({ id: item.id, name: item.name, blob: item.file, selectedStyle: item.selectedStyle || '', features: item.features }) } catch(e){}
  } catch (e) {
    console.error(e)
    item.error = '提取特征失败：' + (e.message || e)
  } finally {
    item.extracting = false
  }
}

async function onConvertItem(item) {
  item.error = ''
  if (!item || !item.file) return (item.error = '无有效音频')
  item.converting = true
  try {
    const blob = await convertAudio(item.file, item.selectedStyle || selectedStyle.value)
    if (item.resultUrl) try { URL.revokeObjectURL(item.resultUrl) } catch(e){}
    item.resultUrl = URL.createObjectURL(blob)
  } catch (e) {
    console.error(e)
    item.error = '转换失败：' + (e.message || e)
  } finally {
    item.converting = false
  }
}

function removeItem(index) {
  const it = files.value[index]
  if (!it) return
  try { if (it.localUrl) URL.revokeObjectURL(it.localUrl) } catch(e){}
  try { if (it.resultUrl) URL.revokeObjectURL(it.resultUrl) } catch(e){}
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
                  <TargetEmotionSelector v-model="item.selectedStyle" :styles="styles" />
                </div>
              </div>
              <div class="file-actions">
                <button class="btn small" @click="removeItem(idx)">删除</button>
                <button class="btn small primary" @click="onConvertItem(item)" :disabled="item.converting || item.extracting">{{ item.converting ? '转换中…' : '转换' }}</button>
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
                <div v-if="item.resultUrl" class="result">
                  <h4>转换结果</h4>
                  <audio :src="item.resultUrl" controls></audio>
                  <a class="download-btn" :href="item.resultUrl" :download="item.name + '.converted.wav'">下载</a>
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
</style>
