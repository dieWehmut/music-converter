<script setup>
import { ref, onMounted, nextTick, toRaw, markRaw } from 'vue'
import { getStyles, extractFeatures } from '../api/emotion'
import { convertAudio } from '../api/upload'
import UploadAudio from '../components/UploadAudio.vue'
import TargetEmotionSelector from '../components/TargetEmotionSelector.vue'
import EmotionResult from '../components/EmotionResult.vue'

const files = ref([])
const styles = ref([])
const selectedStyle = ref('')
const globalError = ref('')

const DB_NAME = 'music-converter-db'
const STORE_NAME = 'uploads'

function serializeTasksForStorage(tasks) {
  return tasks.map(task => {
    const raw = toRaw(task)
    const { active, resultUrl, ...rest } = raw || {}
    return rest
  })
}

function openDb() {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(DB_NAME, 1)

    request.onupgradeneeded = () => {
      const db = request.result
      if (!db.objectStoreNames.contains(STORE_NAME)) {
        db.createObjectStore(STORE_NAME, { keyPath: 'id' })
      }
    }

    request.onsuccess = () => resolve(request.result)
    request.onerror = () => reject(request.error)
  })
}

async function saveUpload(record) {
  const db = await openDb()
  return new Promise((resolve, reject) => {
    const tx = db.transaction(STORE_NAME, 'readwrite')
    const store = tx.objectStore(STORE_NAME)
    const request = store.put(record)

    request.onsuccess = () => resolve(request.result)
    request.onerror = () => reject(request.error)
  })
}

async function updateUpload(id, changes) {
  const db = await openDb()
  return new Promise((resolve, reject) => {
    const tx = db.transaction(STORE_NAME, 'readwrite')
    const store = tx.objectStore(STORE_NAME)
    const getRequest = store.get(id)

    getRequest.onsuccess = () => {
      const data = getRequest.result
      if (!data) {
        resolve()
        return
      }
      const updated = { ...data, ...changes }
      const putRequest = store.put(updated)

      putRequest.onsuccess = () => resolve(putRequest.result)
      putRequest.onerror = () => reject(putRequest.error)
    }

    getRequest.onerror = () => reject(getRequest.error)
  })
}

async function getAllUploads() {
  const db = await openDb()
  return new Promise((resolve, reject) => {
    const tx = db.transaction(STORE_NAME, 'readonly')
    const store = tx.objectStore(STORE_NAME)
    const request = store.getAll()

    request.onsuccess = () => resolve(request.result || [])
    request.onerror = () => reject(request.error)
  })
}

async function deleteUploadById(id) {
  const db = await openDb()
  return new Promise((resolve, reject) => {
    const tx = db.transaction(STORE_NAME, 'readwrite')
    const store = tx.objectStore(STORE_NAME)
    const request = store.delete(id)

    request.onsuccess = () => resolve()
    request.onerror = () => reject(request.error)
  })
}

onMounted(async () => {
  // load cached uploads first
  try {
    const cached = await getAllUploads()

    for (const record of cached) {
      const item = {
        id: record.id,
        file: record.blob,
        name: record.name,
        localUrl: record.blob instanceof Blob ? URL.createObjectURL(record.blob) : '',
        selectedStyle: record.selectedStyle || '',
        features: record.features || null,
        extracting: !!record.extracting,
        converting: false,
        tasks: Array.isArray(record.tasks)
          ? record.tasks.map(task => {
              let resultUrl = ''
              if (task.resultBlob instanceof Blob) {
                try {
                  resultUrl = URL.createObjectURL(task.resultBlob)
                } catch (error) {
                  console.warn('bad blob', error)
                }
              }
              return {
                ...task,
                resultUrl,
                status: task.status,
                active: false
              }
            })
          : [],
        error: ''
      }

      if (record.resultBlob && item.tasks.length === 0) {
        let resultUrl = ''

        if (record.resultBlob instanceof Blob) {
          try {
            resultUrl = URL.createObjectURL(record.resultBlob)
          } catch (error) {}
        }

        item.tasks.push({
          id: Date.now().toString(36),
          style: record.selectedStyle || 'unknown',
          status: 'success',
          resultBlob: record.resultBlob,
          resultUrl,
          error: '',
          active: false
        })
      }

      files.value.push(item)

      if (item.extracting && !item.features) {
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
    id: Date.now().toString(36) + Math.random().toString(36).slice(2, 8),
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

async function onFilesSelected(input) {
  if (!input) return

  const list = Array.isArray(input)
    ? input
    : input instanceof File
      ? [input]
      : []

  for (const file of list) {
    const rawItem = makeItem(file)
    files.value.push(rawItem)

    const item = files.value[files.value.length - 1]

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
  try {
    await updateUpload(item.id, { extracting: true })
  } catch (e) {}
  try {
    item.features = await extractFeatures(item.file)
    item.extracting = false
    await nextTick()
    try {
      await updateUpload(item.id, { features: item.features, extracting: false })
    } catch (e) {}
  } catch (e) {
    console.error(e)
    item.error = '提取特征失败：' + (e.message || e)
    try {
      await updateUpload(item.id, { extracting: false })
    } catch (e) {}
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
    
    const liveItem = files.value.find(f => f.id === item.id)
    if (liveItem) {
      const liveTask = liveItem.tasks.find(task => task.id === taskProxy.id)
      if (liveTask) {
        liveTask.status = 'success'
        liveTask.resultBlob = markRaw(blob)
        liveTask.resultUrl = URL.createObjectURL(blob)
        liveTask.error = ''
      }
    }

    try {
      await updateUpload(item.id, { tasks: serializeTasksForStorage(item.tasks) })
    } catch (e) {
      console.warn('Failed to save conversion result to cache', e)
    }
  } catch (e) {
    console.error('Conversion failed', e)
    const liveItem = files.value.find(f => f.id === item.id)
    if (liveItem) {
      const liveTask = liveItem.tasks.find(task => task.id === taskProxy.id)
      if (liveTask) {
        liveTask.status = 'error'
        liveTask.error = '转换失败：' + (e.message || e)
      }
    }
    
    try {
      await updateUpload(item.id, { tasks: serializeTasksForStorage(item.tasks) })
    } catch (e) {}
  } finally {
    taskProxy.active = false
  }
}

async function onConvertItem(item) {
  const reactiveItem = files.value.find(f => f.id === item.id) || item
  
  reactiveItem.error = ''
  if (!reactiveItem.file) return (reactiveItem.error = '无有效音频')
  
  const styleToUse = reactiveItem.selectedStyle || selectedStyle.value

  const resumableTask = reactiveItem.tasks.find(task => task.status === 'converting' && !task.active)
  if (resumableTask) {
    resumableTask.error = ''
    await runTask(reactiveItem, resumableTask)
    return
  }
  
  const newTaskRaw = {
    id: Date.now().toString(36) + Math.random().toString(36).slice(2, 5),
    style: styleToUse,
    status: 'converting',
    resultUrl: '',
    resultBlob: null,
    error: '',
    active: true
  }
  const newLength = reactiveItem.tasks.push(newTaskRaw)
  const taskProxy = reactiveItem.tasks[newLength - 1]
  
  try {
    await updateUpload(reactiveItem.id, { tasks: serializeTasksForStorage(reactiveItem.tasks) })
  } catch (e) {}

  await runTask(reactiveItem, taskProxy)
}

async function retryTask(item, task) {
  const reactiveItem = files.value.find(f => f.id === item.id) || item
  const taskProxy = reactiveItem.tasks.find(current => current.id === task.id)
  if (!taskProxy) return

  taskProxy.status = 'converting'
  taskProxy.error = ''
  
  try {
    await updateUpload(reactiveItem.id, { tasks: serializeTasksForStorage(reactiveItem.tasks) })
  } catch (e) {}

  await runTask(reactiveItem, taskProxy)
}

function removeItem(index) {
  const it = files.value[index]
  if (!it) return
  try {
    if (it.localUrl) URL.revokeObjectURL(it.localUrl)
  } catch (e) {}
  if (it.tasks) {
    for (const t of it.tasks) {
      try {
        if (t.resultUrl) URL.revokeObjectURL(t.resultUrl)
      } catch (e) {}
    }
  }
  try {
    deleteUploadById(it.id).catch(() => {})
  } catch (e) {}
  files.value.splice(index,1)
}
</script>

<template>
  <div class="page">
    <div class="container">
      <h1>Music Converter</h1>

      <div class="styles-debug card">
        <h3 class="styles-title">可用风格（styles）</h3>
        <div v-if="styles.length" class="styles-list">
          <span v-for="s in styles" :key="s" class="style-pill">{{ s }}</span>
        </div>
        <div v-else-if="globalError" class="error">加载风格失败：{{ globalError }}</div>
        <div v-else>加载中…</div>
      </div>

      <section class="card">
        <div class="center">
          <div class="row buttons-row">
            <UploadAudio @files="onFilesSelected">上传音频</UploadAudio>
            <div class="pill-control pill-control--neutral upload-count" v-if="files.length">已上传 {{ files.length }}</div>

            <div class="spacer"></div>
          </div>
        </div>

        <p v-if="globalError" class="error">{{ globalError }}</p>

        <div class="file-list">
          <div v-for="(item, idx) in files" :key="item.id" class="file-item card">
            <div class="file-header">
                <div class="file-left">
                  <div class="file-index">{{ idx + 1 }}</div>
                  <div class="file-title-row">
                  <div class="file-title">{{ item.name }}</div>
                  <TargetEmotionSelector v-model="item.selectedStyle" :styles="styles" @update:modelValue="onStyleChange(item)" />
                </div>
              </div>
              <div class="file-actions">
                <button class="btn btn--ghost btn--small" @click="removeItem(idx)">删除</button>
                <button class="btn btn--primary btn--small" @click="onConvertItem(item)" :disabled="item.extracting || item.tasks.some(t => t.active)">
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
                      <span class="task-style">目标风格: {{ task.style }}</span>
                      <span class="task-status" :class="task.status">
                        {{ task.status === 'converting' ? '转换中...' : task.status === 'success' ? '成功' : '失败' }}
                      </span>
                      <div v-if="task.status === 'error'" class="task-actions push-right">
                        <button class="btn btn--primary btn--xs" @click="retryTask(item, task)">重试</button>
                      </div>
                    </div>
                    <div v-if="task.status === 'success'" class="task-result">
                      <audio :src="task.resultUrl" controls></audio>
                      <a class="btn btn--ghost btn--xs download-btn" :href="task.resultUrl" :download="item.name + '.' + task.style + '.wav'">下载</a>
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
.page {
  min-height: 100vh;
  display: flex;
  justify-content: center;
  padding: 48px 16px 64px;
}

.container {
  width: 100%;
  max-width: 960px;
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.card {
  background: rgba(255, 255, 255, 0.92);
  border-radius: var(--radius-lg);
  border: 1px solid var(--color-card-border);
  box-shadow: var(--shadow-soft);
  padding: 24px;
  backdrop-filter: blur(6px);
}

h1 {
  margin: 0 0 8px;
  text-align: center;
  font-size: 34px;
  letter-spacing: -0.02em;
}

.row {
  display: flex;
  align-items: center;
  gap: 14px;
  flex-wrap: wrap;
}

.buttons-row {
  align-items: center;
  justify-content: flex-start;
  width: 100%;
}

.spacer {
  flex: 1;
}

.upload-count {
  margin-left: 8px;
}

.center {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.styles-debug {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.styles-title {
  margin: 0;
  font-size: 18px;
  color: var(--color-text);
}

.styles-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.style-pill {
  padding: 6px 14px;
  border-radius: var(--radius-full);
  background: rgba(37, 99, 235, 0.08);
  border: 1px solid rgba(37, 99, 235, 0.16);
  font-weight: 600;
  color: #1d4ed8;
}

.file-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
  margin-top: 16px;
}

.file-item {
  padding: 18px;
  border-radius: var(--radius-lg);
  background: var(--color-surface);
  border: 1px solid var(--color-card-border);
}

.file-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.file-left {
  display: flex;
  align-items: center;
  gap: 14px;
}

.file-title-row {
  display: flex;
  align-items: center;
  gap: 12px;
}

.file-index {
  width: 36px;
  height: 36px;
  border-radius: 12px;
  background: linear-gradient(165deg, rgba(59, 130, 246, 0.15), rgba(14, 165, 233, 0.1));
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  color: var(--color-text);
}

.file-title {
  font-weight: 600;
  font-size: 16px;
}

.file-actions {
  display: flex;
  gap: 10px;
}

.file-body {
  display: flex;
  flex-direction: column;
  gap: 14px;
  margin-top: 14px;
}

.audio-large audio {
  width: 100%;
  height: 70px;
  border-radius: var(--radius-md);
}

.meta {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.tasks-list {
  margin-top: 12px;
  border-top: 1px solid rgba(15, 23, 42, 0.08);
  padding-top: 12px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.task-item {
  background: rgba(248, 250, 252, 0.9);
  border-radius: var(--radius-md);
  padding: 12px;
  border: 1px solid rgba(15, 23, 42, 0.06);
}

.task-header {
  display: flex;
  align-items: center;
  gap: 12px;
  font-weight: 600;
}

.push-right {
  margin-left: auto;
}

.task-style {
  color: var(--color-text-muted);
}

.task-status {
  padding: 4px 10px;
  border-radius: var(--radius-full);
  font-size: 13px;
  font-weight: 600;
}

.task-status.converting {
  background: rgba(37, 99, 235, 0.12);
  color: #1d4ed8;
}

.task-status.success {
  background: rgba(34, 197, 94, 0.12);
  color: #16a34a;
}

.task-status.error {
  background: rgba(220, 38, 38, 0.12);
  color: #dc2626;
}

.task-result {
  display: flex;
  align-items: center;
  gap: 12px;
}

.task-result audio {
  height: 42px;
  flex: 1;
}

.download-btn {
  text-decoration: none;
}

.error {
  color: #dc2626;
}

.error.small {
  font-size: 12px;
  margin-top: 4px;
}

.styles-debug h3 {
  margin: 0;
}
</style>
