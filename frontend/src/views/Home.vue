<script setup>
import { ref, onMounted, nextTick, toRaw, markRaw, watch, onUnmounted, computed } from 'vue'
import { marked } from 'marked'
import { getStyles, extractFeatures } from '../api/emotion'
import { convertAudio } from '../api/upload'
import UploadAudio from '../components/UploadAudio.vue'
import TargetEmotionSelector from '../components/TargetEmotionSelector.vue'
import EmotionResult from '../components/EmotionResult.vue'

const files = ref([])
const styles = ref([])
const selectedStyle = ref('')
const globalError = ref('')
const activeId = ref('')
const readmeHtml = ref('')
const docHeaders = ref([])

// expose will be declared after recentTasks is created to avoid temporal-deadzone errors

function toggleItemTasks(item) {
  if (!item) return
  // keep this state transient (not persisted) on the item object
  if (typeof item.tasksCollapsed === 'undefined') item.tasksCollapsed = false
  item.tasksCollapsed = !item.tasksCollapsed
}

const DB_NAME = 'music-converter-db'
const STORE_NAME = 'uploads'

function serializeTasksForStorage(tasks) {
  return tasks.map(task => {
    const raw = toRaw(task)
    const { active, resultUrl, showAnalysis, analysisLoading, analysisHover, ...rest } = raw || {}
    return rest
  })
}

function escapeRegExp(string) {
  return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
}

/**
 * Ensure unique style names for tasks within the same item.
 * If duplicates of `baseStyle` exist, convert existing unnumbered entries to `baseStyle(1)`
 * and assign sequential numbers to the new task (and any further duplicates).
 */
function ensureUniqueStyleNames(item, baseStyle, newTask) {
  if (!item) return
  if (!item.tasks) item.tasks = []
  const tasks = item.tasks
  const used = new Set()
  const unnumberedIdx = []

  const re = new RegExp('^' + escapeRegExp(baseStyle) + '\\((\\d+)\\)$')

  for (let i = 0; i < tasks.length; i++) {
    const s = tasks[i].style || ''
    if (s === baseStyle) {
      unnumberedIdx.push(i)
    } else {
      const m = s.match(re)
      if (m) used.add(parseInt(m[1], 10))
    }
  }

  // assign numbers to any unnumbered existing entries, choosing the smallest available ints
  let nextNum = 1
  for (const idx of unnumberedIdx) {
    while (used.has(nextNum)) nextNum++
    tasks[idx].style = `${baseStyle}(${nextNum})`
    used.add(nextNum)
    nextNum++
  }

  // determine style for the new task
  if (used.size === 0 && unnumberedIdx.length === 0) {
    // no existing duplicates at all
    newTask.style = baseStyle
  } else {
    // pick the smallest available integer
    while (used.has(nextNum)) nextNum++
    newTask.style = `${baseStyle}(${nextNum})`
    // used.add(nextNum) // not strictly necessary here
  }
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

const recentTasks = computed(() => {
  const list = []
  for (const f of files.value) {
    if (f.tasks && f.tasks.length) {
      for (const t of f.tasks) {
        list.push({
          taskId: t.id,
          fileName: f.name || '未命名',
          style: t.style || '',
          status: t.status || '',
          createdAt: t.createdAt || null
        })
      }
    }
  }
  const last = list.slice(-10).reverse()
  return last.map((t, idx) => ({
    ...t,
    index: idx + 1,
    sectionId: `dashboard.recent.${idx + 1}`
  }))
})

// UI collapse state for dashboard sections
const overviewCollapsed = ref(false)
const stylesCollapsed = ref(false)
const recentCollapsed = ref(false)

function toggleOverview() {
  overviewCollapsed.value = !overviewCollapsed.value
}

function toggleStyles() {
  stylesCollapsed.value = !stylesCollapsed.value
}

function toggleRecent() {
  recentCollapsed.value = !recentCollapsed.value
}

function formatRecentTime(value) {
  if (!value) return ''
  let d
  try {
    d = typeof value === 'string' ? new Date(value) : new Date(Number(value))
    if (Number.isNaN(d.getTime())) return ''
  } catch (e) {
    return ''
  }
  const now = new Date()
  const isSameDay =
    d.getFullYear() === now.getFullYear() &&
    d.getMonth() === now.getMonth() &&
    d.getDate() === now.getDate()

  const hh = String(d.getHours()).padStart(2, '0')
  const mm = String(d.getMinutes()).padStart(2, '0')
  if (isSameDay) return `${hh}:${mm}`
  const month = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${month}-${day} ${hh}:${mm}`
}

async function scrollToTask(id) {
  if (!id) return

  // try to locate the task element first
  let el = document.querySelector(`[data-task-id="${id}"]`)

  // if the task exists inside a collapsed file, expand that file's tasks first
  if (el) {
    const fileEl = el.closest('[data-file-id]')
    if (fileEl) {
      const fid = fileEl.dataset.fileId
      const item = files.value.find(f => f.id === fid)
      if (item && item.tasksCollapsed) {
        item.tasksCollapsed = false
        await nextTick()
        // re-query the element after DOM update
        el = document.querySelector(`[data-task-id="${id}"]`)
      }
    }
  }

  if (!el) el = document.querySelector(`[data-file-id="${id}"]`)
  if (!el) el = document.querySelector(`[data-section-id="${id}"]`)
  if (el) {
    el.scrollIntoView({ behavior: 'smooth', block: 'center' })
  }
}

function handleRecentClick(t) {
  if (!t) return
  // set activeId to the dashboard section first so sidebar highlights the 1.3.x
  activeId.value = t.sectionId
  // scroll dashboard recent row into view (so the section anchor is observed)
  const secEl = document.querySelector(`[data-section-id="${t.sectionId}"]`)
  if (secEl) secEl.scrollIntoView({ behavior: 'smooth', block: 'center' })
  // then scroll to the actual task (expand file if necessary)
  // call scrollToTask without awaiting so UI remains responsive
  scrollToTask(t.taskId)
}

// Expose reactive state to parent components (App.vue) after recentTasks is defined
defineExpose({ files, activeId, docHeaders, styles, recentTasks })

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

let observer = null
function observeElements() {
  if (observer) observer.disconnect()
  
  observer = new IntersectionObserver((entries) => {
    // We want the element that is most visible or closest to the top
    // But simple intersection with a top margin works well for "scrolled to"
    const visible = entries.find(entry => entry.isIntersecting)
    if (visible) {
      // Prefer section anchors (dashboard.*) so sidebar entries (例如 1.3.x)
      // remain the canonical active id when both a dashboard anchor and
      // a specific task element are visible.
      const sid = visible.target.dataset.sectionId
      const did = visible.target.dataset.docHeader
      const fid = visible.target.dataset.fileId
      const tid = visible.target.dataset.taskId

      if (sid) activeId.value = sid
      else if (did) activeId.value = did
      else if (fid) activeId.value = fid
      else if (tid) activeId.value = tid
    }
  }, {
    rootMargin: '-10% 0px -80% 0px', 
    threshold: 0
  })

  const targets = document.querySelectorAll('[data-file-id], [data-task-id], [data-section-id], [data-doc-header]')
  targets.forEach(el => observer.observe(el))
}

watch(files, async () => {
  await nextTick()
  observeElements()
}, { deep: true })

onUnmounted(() => {
  if (observer) observer.disconnect()
})

function handleMarkdownClick(e) {
  if (e.target.classList.contains('copy-btn')) {
    const btn = e.target
    const pre = btn.nextElementSibling
    if (pre && pre.tagName === 'PRE') {
      const code = pre.textContent
      navigator.clipboard.writeText(code).then(() => {
        btn.innerText = 'Copied!'
        btn.classList.add('copied')
        setTimeout(() => {
          btn.innerText = 'Copy'
          btn.classList.remove('copied')
        }, 2000)
      })
    }
  }
}

onMounted(async () => {
  const toc = []
  const counters = [0, 0, 0, 0, 0, 0]
  
  const renderer = {
    heading({ text, depth, raw }) {
      const id = raw.toLowerCase().trim().replace(/[\s]+/g, '-').replace(/[^\w\u4e00-\u9fa5-]/g, '')
      
      if (depth >= 1 && depth <= 6) {
        counters[depth - 1]++
        for (let i = depth; i < 6; i++) counters[i] = 0
        
        let number = '3'
        for (let i = 0; i < depth; i++) {
          number += '.' + counters[i]
        }
        toc.push({ id, text, level: depth, number })
      }
      
      return `<h${depth} id="${id}" data-doc-header="${id}">${text}</h${depth}>`
    },
    code({ text, lang }) {
      const escapedText = text.replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
      const langClass = lang ? `language-${lang}` : '';
      const langAttr = lang ? ` data-lang="${lang}"` : '';
      return `<div class="code-wrapper"><button class="copy-btn">Copy</button><pre${langAttr}><code class="${langClass}">${escapedText}</code></pre></div>`
    }
  }
  
  marked.use({ renderer })
  
  try {
    const res = await fetch('https://api.github.com/repos/dieWehmut/music-converter/readme', {
      headers: { 'Accept': 'application/vnd.github.raw' }
    })
    if (res.ok) {
      const text = await res.text()
      readmeHtml.value = marked.parse(text)
    }
  } catch (e) {
    console.error('Failed to fetch README:', e)
  }

  docHeaders.value = toc

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
        showAnalysis: true,
        tasks: Array.isArray(record.tasks)
          ? record.tasks.map(task => {
              let resultUrl = ''
              try {
                if (task.resultBlob instanceof Blob) {
                  resultUrl = URL.createObjectURL(task.resultBlob)
                }
              } catch (error) {
                console.warn('bad blob', error)
              }
              return {
                ...task,
                resultUrl,
                status: task.status,
                active: false,
                analysis: task.analysis || null,
                showAnalysis: false,
                analysisLoading: false,
                analysisHover: false
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
          createdAt: Date.now(),
          resultBlob: record.resultBlob,
          resultUrl,
          error: '',
          active: false,
          analysis: record.analysis || null,
          showAnalysis: false,
          analysisLoading: false,
          analysisHover: false
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
  
  await nextTick()
  observeElements()
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
    showAnalysis: true,
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

async function toggleTaskAnalysis(item, task) {
  task.showAnalysis = !task.showAnalysis
  if (!task.showAnalysis) return

  if (!task.analysis && task.resultBlob) {
    task.analysisLoading = true
    try {
      const features = await extractFeatures(task.resultBlob)
      task.analysis = features
      try {
        await updateUpload(item.id, { tasks: serializeTasksForStorage(item.tasks) })
      } catch (e) {}
    } catch (e) {
      console.error('分析转换后音频失败', e)
      task.analysis = null
      task.error = '分析失败：' + (e.message || e)
    } finally {
      task.analysisLoading = false
    }
  }
}

// 当用户将鼠标悬浮在“查看分析”区域时显示预览，并在必要时触发分析
async function handleAnalysisHoverEnter(item, task) {
  task.analysisHover = true
  if (!task.analysis && task.resultBlob && !task.analysisLoading) {
    task.analysisLoading = true
    try {
      const features = await extractFeatures(task.resultBlob)
      task.analysis = features
      try {
        await updateUpload(item.id, { tasks: serializeTasksForStorage(item.tasks) })
      } catch (e) {}
    } catch (e) {
      console.error('Hover 分析失败', e)
      task.analysis = null
    } finally {
      task.analysisLoading = false
    }
  }
}

function handleAnalysisHoverLeave(task) {
  task.analysisHover = false
}

function toggleOriginalAnalysis(item) {
  if (!item.features) return
  item.showAnalysis = !item.showAnalysis
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

    // persist immediate conversion result
    try {
      await updateUpload(item.id, { tasks: serializeTasksForStorage(item.tasks) })
    } catch (e) {
      console.warn('Failed to save conversion result to cache', e)
    }

    // 自动对转换后的音频进行风格/情绪分析（懒加载时也可触发）
    try {
      const liveItemAfter = files.value.find(f => f.id === item.id)
      const liveTaskAfter = liveItemAfter && liveItemAfter.tasks.find(t => t.id === taskProxy.id)
      if (liveTaskAfter && liveTaskAfter.resultBlob) {
        liveTaskAfter.analysisLoading = true
        try {
          const analysis = await extractFeatures(liveTaskAfter.resultBlob)
          liveTaskAfter.analysis = analysis
        } catch (ae) {
          console.error('自动分析转换后音频失败', ae)
          liveTaskAfter.analysis = null
          // keep task.error as-is; do not mark conversion as failed
        } finally {
          liveTaskAfter.analysisLoading = false
        }

        try {
          await updateUpload(item.id, { tasks: serializeTasksForStorage(item.tasks) })
        } catch (e) {
          console.warn('Failed to save analysis result to cache', e)
        }
      }
    } catch (err) {
      console.error('保存自动分析结果时出错', err)
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
    createdAt: Date.now(),
    resultUrl: '',
    resultBlob: null,
    error: '',
    analysis: null,
    showAnalysis: false,
    analysisLoading: false,
    analysisHover: false,
    active: true
  }
  // handle automatic numbering for duplicate styles
  ensureUniqueStyleNames(reactiveItem, styleToUse, newTaskRaw)

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
  // animate removal: mark item.removing then remove after animation completes
  try {
    it.removing = true
    // persist state if desired
    deleteUploadById(it.id).catch(() => {})
  } catch (e) {}
  setTimeout(() => {
    try { deleteUploadById(it.id).catch(() => {}) } catch (e) {}
    files.value.splice(index,1)
  }, 260)
}

function removeTask(item, task) {
  const reactiveItem = files.value.find(f => f.id === item.id) || item
  if (!reactiveItem || !reactiveItem.tasks) return
  const idx = reactiveItem.tasks.findIndex(t => t.id === task.id)
  if (idx === -1) return
  const t = reactiveItem.tasks[idx]
  try {
    if (t.resultUrl) URL.revokeObjectURL(t.resultUrl)
  } catch (e) {}
  // remove from array and persist
  reactiveItem.tasks.splice(idx, 1)
  try {
    updateUpload(reactiveItem.id, { tasks: serializeTasksForStorage(reactiveItem.tasks) }).catch(() => {})
  } catch (e) {}
}
</script>

<template>
  <div class="page">
    <div class="container">
      <h1>Music Converter</h1>

      <div class="styles-debug card" data-section-id="dashboard">

        <div class="dashboard-overview" data-section-id="dashboard.overview">
          <div class="section-header">
            <h3 class="styles-title">功能概览</h3>
            <button class="collapse-section-btn" :class="{ collapsed: overviewCollapsed }" @click.stop="toggleOverview" :aria-expanded="!overviewCollapsed" title="收起/展开概览">
              <svg viewBox="0 0 24 24" width="18" height="18" fill="currentColor" aria-hidden="true"><path d="M7.41 8.59L12 13.17l4.59-4.58L18 10l-6 6-6-6 1.41-1.41z"/></svg>
            </button>
          </div>
          <transition name="collapse">
            <div class="dashboard-desc" v-show="!overviewCollapsed">
            <p>本工具用于将上传的音频片段转换为不同音乐风格并提供情绪/风格的可视化分析。操作尽量在本地完成以保护隐私，结果可在页面内预览或下载。</p>
            <ul class="dashboard-desc-list">
              <li data-section-id="dashboard.overview.upload">
                <span class="desc-bullet"></span>
                <div class="desc-content">
                  <strong>上传音频</strong>
                  <span class="desc-text">支持本地上传，上传后会自动提取音频特征用于后续分析与转换。</span>
                </div>
              </li>
              <li data-section-id="dashboard.overview.style">
                <span class="desc-bullet"></span>
                <div class="desc-content">
                  <strong>风格选择</strong>
                  <span class="desc-text">从可用风格中选择目标风格，支持同一文件多次转换（系统会自动编号重复风格）。</span>
                </div>
              </li>
              <li data-section-id="dashboard.overview.preview">
                <span class="desc-bullet"></span>
                <div class="desc-content">
                  <strong>实时预览</strong>
                  <span class="desc-text">对已完成的转换可直接播放预览并查看情绪/风格占比图。</span>
                </div>
              </li>
              <li data-section-id="dashboard.overview.analysis">
                <span class="desc-bullet"></span>
                <div class="desc-content">
                  <strong>分析功能</strong>
                  <span class="desc-text">提供原音与转换后音频的风格与情绪占比，可在悬浮或详情面板中查看。</span>
                </div>
              </li>
              <li data-section-id="dashboard.overview.tasks">
                <span class="desc-bullet"></span>
                <div class="desc-content">
                  <strong>任务管理</strong>
                  <span class="desc-text">支持对转换任务逐条删除、重试或折叠，列表会保存到本地以便刷新后继续使用。</span>
                </div>
              </li>
              <li data-section-id="dashboard.overview.download">
                <span class="desc-bullet"></span>
                <div class="desc-content">
                  <strong>下载</strong>
                  <span class="desc-text">转换成功后可导出音频文件到本地。</span>
                </div>
              </li>
            </ul>
            </div>
          </transition>
        </div>

        <div class="dashboard-styles" data-section-id="dashboard.styles">
          <div class="section-header">
            <h3 class="styles-title">可用风格（styles）</h3>
            <button class="collapse-section-btn" :class="{ collapsed: stylesCollapsed }" @click.stop="toggleStyles" :aria-expanded="!stylesCollapsed" title="收起/展开风格列表">
              <svg viewBox="0 0 24 24" width="18" height="18" fill="currentColor" aria-hidden="true"><path d="M7.41 8.59L12 13.17l4.59-4.58L18 10l-6 6-6-6 1.41-1.41z"/></svg>
            </button>
          </div>
          <transition name="collapse">
            <div v-show="!stylesCollapsed">
              <div v-if="styles.length" class="styles-list-vertical">
                <div
                  v-for="(s, si) in styles"
                  :key="s"
                  class="style-row"
                  :data-section-id="'dashboard.styles.' + (si + 1)"
                >
                  <span class="style-num">{{ si + 1 }}</span>
                  <span class="style-name">{{ s }}</span>
                </div>
              </div>
              <div v-else-if="globalError" class="error">加载风格失败：{{ globalError }}</div>
              <div v-else>加载中…</div>
            </div>
          </transition>
        </div>

        <div class="dashboard-recent" data-section-id="dashboard.recent">
          <div class="section-header">
            <h4 class="styles-title">最近任务</h4>
            <button class="collapse-section-btn" :class="{ collapsed: recentCollapsed }" @click.stop="toggleRecent" :aria-expanded="!recentCollapsed" title="收起/展开最近任务">
              <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor" aria-hidden="true"><path d="M7.41 8.59L12 13.17l4.59-4.58L18 10l-6 6-6-6 1.41-1.41z"/></svg>
            </button>
          </div>
          <transition name="collapse">
            <div v-show="!recentCollapsed">
              <div v-if="recentTasks.length">
                <div
                  v-for="(t, i) in recentTasks"
                  :key="t.taskId"
                  class="recent-task"
                  role="button"
                  tabindex="0"
                  @click="handleRecentClick(t)"
                  @keydown.enter.prevent="handleRecentClick(t)"
                  :data-section-id="t.sectionId"
                >
                  <span class="recent-task-index">({{ t.index }})</span>
                  <span class="recent-task-file">{{ t.fileName }}</span>
                  <span class="recent-task-sep">—</span>
                  <span class="recent-task-style">{{ t.style }}</span>
                  <span class="status-dot" :class="t.status" :title="t.status" style="margin-left:8px"></span>
                  <span class="recent-task-time" v-if="formatRecentTime(t.createdAt)">{{ formatRecentTime(t.createdAt) }}</span>
                </div>
              </div>
              <div v-else class="empty-tip">暂无最近任务</div>
            </div>
          </transition>
        </div>

        <div class="dashboard-actions">
          <UploadAudio @files="onFilesSelected">上传音频</UploadAudio>
          <div class="pill-control pill-control--neutral upload-count" v-if="files.length">已上传 {{ files.length }}</div>
        </div>

      </div>

      <section class="card">
        <p v-if="globalError" class="error">{{ globalError }}</p>

        <div class="file-list" data-section-id="uploads">
          <div
            v-for="(item, idx) in files"
            :key="item.id"
            class="file-item card"
            :data-file-id="item.id"
          >
            <div class="file-header">
                <div class="file-left">
                  <div class="file-index">{{ idx + 1 }}</div>
                  <div class="file-title-row">
                  <div class="file-title">{{ item.name }}</div>
                  <TargetEmotionSelector v-model="item.selectedStyle" :styles="styles" @update:modelValue="onStyleChange(item)" />
                </div>
              </div>
              <div class="file-actions">
                <button class="btn btn--success btn--small" @click="onConvertItem(item)" :disabled="item.extracting || item.tasks.some(t => t.active)"
                  :class="{ 'btn--animating': item.tasks.some(t => t.active) }">
                  {{ item.tasks.some(t => t.active) ? `转换中... ${item.tasks.filter(t => t.status === 'success').length}/${item.tasks.length}` : '转换' }}
                </button>
                <button class="btn btn--info btn--small" @click="toggleOriginalAnalysis(item)">
                  {{ item.showAnalysis ? '收起分析' : '查看分析' }}
                </button>
                <button class="btn btn--danger btn--small" @click="removeItem(idx)">删除</button>
              </div>
            </div>

            <div class="file-body">
              <div class="audio-large">
                <audio :src="item.localUrl" controls preload="metadata"></audio>
              </div>

              <div class="meta">
                <div v-if="item.extracting">自动提取中…</div>
                <div v-if="item.features" class="origin-analysis">
                  <transition name="fade-slide" mode="out-in">
                    <EmotionResult v-if="item.showAnalysis" :features="item.features" />
                  </transition>
                </div>
                <div v-if="item.error" class="error">{{ item.error }}</div>
                
                <div v-if="item.tasks && item.tasks.length" class="tasks-list">
                  <div class="tasks-header-row">
                    <h4>转换任务列表</h4>
                    <button class="collapse-all-btn" :class="{ collapsed: item.tasksCollapsed }" @click="toggleItemTasks(item)" :aria-expanded="!item.tasksCollapsed" title="收起/展开转换任务">
                      <svg viewBox="0 0 24 24" width="18" height="18" fill="currentColor" aria-hidden="true"><path d="M7.41 8.59L12 13.17l4.59-4.58L18 10l-6 6-6-6 1.41-1.41z"/></svg>
                    </button>
                  </div>

                  <transition name="collapse">
                    <div class="tasks-container" v-show="!item.tasksCollapsed">
                      <template v-for="(task, tIdx) in item.tasks" :key="task.id">
                      <div class="task-item" :data-task-id="task.id">
                        <div class="task-header">
                          <span class="task-index">({{ tIdx + 1 }})</span>
                          <span class="task-style">目标风格: {{ task.style }}</span>
                          <span class="task-status" :class="task.status">
                            {{ task.status === 'converting' ? '转换中...' : task.status === 'success' ? '成功' : '失败' }}
                          </span>
                          <div v-if="task.status === 'error'" class="task-actions push-right">
                            <button class="btn btn--success btn--xs" @click="retryTask(item, task)">重试</button>
                          </div>
                        </div>

                        <div v-if="task.status === 'success'" class="task-result">
                          <audio :src="task.resultUrl" controls></audio>

                          <div class="analysis-hover-wrap" @mouseenter="handleAnalysisHoverEnter(item, task)" @mouseleave="handleAnalysisHoverLeave(task)">
                            <button class="btn btn--info btn--xs analysis-toggle" @click="toggleTaskAnalysis(item, task)"
                              :class="{ 'btn--animating': task.analysisLoading || task.showAnalysis }" :disabled="task.analysisLoading">
                              <span v-if="task.analysisLoading">分析中…</span>
                              <span v-else>{{ task.showAnalysis ? '收起分析' : '查看分析' }}</span>
                            </button>

                            <div v-if="task.analysisHover" class="analysis-preview">
                              <div v-if="task.analysis">
                                <EmotionResult :features="task.analysis" />
                              </div>
                              <div v-else-if="task.analysisLoading">正在分析…</div>
                              <div v-else class="error small">暂无分析结果</div>
                            </div>
                          </div>

                          <button class="btn btn--danger btn--xs" @click="removeTask(item, task)">删除</button>
                        </div>

                        <div v-if="task.status === 'error'" class="error small">{{ task.error }}</div>

                        <transition name="fade-slide" mode="out-in">
                          <div v-if="task.showAnalysis" class="analysis-panel">
                            <EmotionResult v-if="task.analysis" :features="task.analysis" />
                            <div v-else-if="task.analysisLoading">正在分析…</div>
                            <div v-else-if="!task.resultBlob" class="error small">没有可分析的音频</div>
                          </div>
                        </transition>
                      </div>
                      </template>
                    </div>
                  </transition>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section class="card readme-section" v-if="readmeHtml" data-section-id="readme">
        <div class="markdown-body" v-html="readmeHtml" @click="handleMarkdownClick"></div>
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

.dashboard-desc {
  margin-top: 12px;
  padding: 12px;
  background: rgba(246, 249, 252, 0.8);
  border-radius: 10px;
  border: 1px solid rgba(226,232,240,0.6);
  color: var(--color-text);
  font-size: 14px;
}
.dashboard-desc h3 {
  margin: 0 0 8px;
  font-size: 16px;
}
.dashboard-desc p {
  margin: 0 0 8px;
  color: var(--color-text-muted);
}
.dashboard-desc-list {
  margin: 0;
  padding: 0;
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.dashboard-desc-list li {
  display: flex;
  align-items: flex-start;
  gap: 8px;
}
.dashboard-desc-list .desc-bullet {
  width: 8px;
  height: 8px;
  border-radius: 999px;
  background: #60a5fa;
  margin-top: 6px;
  flex-shrink: 0;
}
.dashboard-desc-list .desc-content {
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.dashboard-desc-list .desc-content strong {
  font-size: 14px;
  color: var(--color-text);
}
.dashboard-desc-list .desc-text {
  font-size: 13px;
  color: var(--color-text-muted);
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.collapse-section-btn {
  width: 36px;
  height: 36px;
  border-radius: 8px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: 1px solid rgba(15,23,42,0.06);
  background: transparent;
  cursor: pointer;
  color: var(--color-text-muted);
  transition: transform 160ms ease, background 120ms ease, color 120ms ease;
}
.collapse-section-btn:hover { background: rgba(0,0,0,0.03); color: var(--color-text); }
.collapse-section-btn.collapsed { transform: rotate(-90deg); }

.style-pill {
  padding: 6px 14px;
  border-radius: var(--radius-full);
  background: rgba(37, 99, 235, 0.08);
  border: 1px solid rgba(37, 99, 235, 0.16);
  font-weight: 600;
  color: #1d4ed8;
}

.styles-list-vertical {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-top: 8px;
}
.style-row {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 10px;
  border-radius: 8px;
  background: rgba(248,250,252,0.9);
  border: 1px solid rgba(226,232,240,0.6);
}
.style-num {
  width: 28px;
  height: 28px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 6px;
  background: rgba(59,130,246,0.08);
  color: #1d4ed8;
  font-weight: 700;
}
.style-name {
  color: var(--color-text);
  font-weight: 600;
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

.tasks-header-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.collapse-all-btn {
  width: 36px;
  height: 36px;
  border-radius: 8px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: 1px solid rgba(15,23,42,0.06);
  background: transparent;
  cursor: pointer;
  color: var(--color-text-muted);
  transition: transform 180ms ease, background 160ms ease, color 160ms ease;
}
.collapse-all-btn:hover {
  background: rgba(0,0,0,0.03);
}
.collapse-all-btn.collapsed {
  transform: rotate(-90deg);
}

/* Collapse transition for tasks list */
.collapse-enter-active, .collapse-leave-active {
  transition: max-height 240ms ease, opacity 200ms ease, transform 200ms ease;
  overflow: hidden;
}
.collapse-enter-from, .collapse-leave-to {
  max-height: 0;
  opacity: 0;
  transform: translateY(-6px);
}
.collapse-enter-to, .collapse-leave-from {
  max-height: 1000px; /* large enough */
  opacity: 1;
  transform: none;
}

.task-item {
  background: rgba(248, 250, 252, 0.9);
  border-radius: var(--radius-md);
  padding: 12px;
  border: 1px solid rgba(15, 23, 42, 0.06);
  position: relative;
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

.task-index {
  font-weight: 700;
  color: var(--color-text-muted);
  margin-right: 8px;
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

.analysis-toggle {
  margin-left: 8px;
}

.analysis-panel {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px dashed rgba(15,23,42,0.06);
}

.origin-analysis {
  margin-top: 10px;
}

.origin-analysis-header {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 6px;
}

.analysis-hover-wrap {
  position: relative;
  display: inline-block;
}

.analysis-preview {
  position: absolute;
  right: 0;
  bottom: 100%;
  transform: translateY(-8px);
  width: 360px;
  max-width: 80vw;
  z-index: 40;
  background: white;
  border-radius: var(--radius-md);
  box-shadow: 0 8px 30px rgba(2,6,23,0.12);
  padding: 12px;
}

/* Override EmotionResult layout inside the hover preview to be horizontal */
.analysis-preview :deep(.chart-grid) {
  grid-template-columns: 1fr 1fr !important;
  gap: 12px !important;
}

.analysis-preview :deep(.chart-figure) {
  width: 120px !important;
  height: 120px !important;
  box-shadow: inset 0 0 0 8px #fff !important;
}

.analysis-preview :deep(.chart-center) {
  width: 52px !important;
  height: 52px !important;
  font-size: 12px !important;
}

.analysis-preview :deep(.chart-card) {
  padding: 10px !important;
}

/* 在悬浮分析预览中，让饼图与图例垂直排列，避免图像挤到中间错位 */
.analysis-preview :deep(.chart-main) {
  flex-direction: column !important;
  align-items: center !important;
}

.analysis-preview :deep(.legend) {
  width: 100%;
}

/* Convert button anim */
.btn--animating {
  animation: btnPulse 1s infinite;
}

@keyframes btnPulse {
  0% { transform: translateY(0); box-shadow: 0 3px 8px rgba(91,107,146,0.28); }
  50% { transform: translateY(-2px); box-shadow: 0 8px 18px rgba(91,107,146,0.28); }
  100% { transform: translateY(0); box-shadow: 0 3px 8px rgba(91,107,146,0.28); }
}

/* File removal animation */
.file-item {
  transition: opacity 240ms ease, transform 240ms ease, height 240ms ease, margin 240ms ease, padding 240ms ease;
}
.file-item.removing {
  opacity: 0;
  transform: translateY(8px) scale(0.995);
  margin: 0 !important;
  padding-top: 0 !important;
  padding-bottom: 0 !important;
  height: 0 !important;
  overflow: hidden;
}

/* Transition for analysis panel */
.fade-slide-enter-active, .fade-slide-leave-active {
  transition: opacity 260ms ease, transform 260ms ease;
}
.fade-slide-enter-from, .fade-slide-leave-to {
  opacity: 0;
  transform: translateY(-6px);
}
.fade-slide-enter-to, .fade-slide-leave-from {
  opacity: 1;
  transform: translateY(0);
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

.dashboard-actions {
  margin-top: 16px;
  display: flex;
  align-items: center;
  gap: 14px;
  padding-top: 16px;
  border-top: 1px solid rgba(0,0,0,0.05);
}

.dashboard-recent {
  margin-top: 4px;
}
.dashboard-recent .recent-task {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: var(--color-text-muted);
  margin-bottom: 4px;
  padding: 6px 8px;
  border-radius: 8px;
  transition: background 160ms ease, color 160ms ease, transform 120ms ease;
  cursor: pointer;
}
.dashboard-recent .recent-task:hover {
  background: rgba(59,130,246,0.04); /* 轻微的蓝色背景 */
  color: var(--color-text);
  transform: translateX(4px);
}
.dashboard-recent .recent-task:active {
  transform: translateX(1px) scale(0.998);
}
.recent-task-index {
  color: var(--color-text);
  font-weight: 600;
}
.recent-task-time {
  margin-left: auto;
  font-size: 12px;
  color: var(--color-text-muted);
}

.readme-section {
  margin-top: 24px;
  /* subtle entrance for the readme block when it appears */
  animation: readmeFade 420ms ease both;
}

/* page entrance */
.page {
  animation: pageFadeUp 420ms cubic-bezier(.2,.9,.2,1) both;
}

@keyframes pageFadeUp {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}

@keyframes readmeFade {
  from { opacity: 0; transform: translateY(6px); }
  to { opacity: 1; transform: translateY(0); }
}

.markdown-body {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif, "Apple Color Emoji", "Segoe UI Emoji";
  font-size: 16px;
  line-height: 1.75;
  color: #334155;
  word-wrap: break-word;
}

/* Polished markdown tweaks */
.markdown-body {
  -webkit-font-smoothing: antialiased;
  font-feature-settings: "liga" 1;
}

.markdown-body :deep(h1),
.markdown-body :deep(h2),
.markdown-body :deep(h3) {
  scroll-margin-top: 48px;
}

.markdown-body :deep(h2), .markdown-body :deep(h3) {
  padding-bottom: 6px;
  margin-top: 28px;
  margin-bottom: 10px;
  border-bottom: 1px solid rgba(226,232,240,0.6);
  padding-left: 6px;
}

.markdown-body :deep(code) {
  background: rgba(15,23,42,0.04);
  padding: 2px 6px;
  border-radius: 6px;
  font-size: 0.92em;
  color: #0f172a;
}

.markdown-body :deep(pre) {
  border-radius: 10px;
  overflow: auto;
  box-shadow: 0 8px 20px rgba(2,6,23,0.06);
  background: linear-gradient(180deg, #0f172a, #0b1220);
  color: #e6eef8;
  padding: 12px;
  position: relative;
}

.markdown-body :deep(blockquote) {
  border-left: 4px solid rgba(59,130,246,0.12);
  background: rgba(59,130,246,0.03);
  padding: 12px 16px;
  border-radius: 6px;
}

/* Code wrapper label + styling */
.markdown-body .code-wrapper {
  position: relative;
  margin: 12px 0;
}
.markdown-body .code-wrapper pre {
  margin: 0;
  padding: 14px;
  border-radius: 8px;
  background: linear-gradient(180deg, rgba(2,6,23,0.9), rgba(6,10,22,0.85));
  color: #e6eef8;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, 'Roboto Mono', 'Courier New', monospace;
  font-size: 13px;
  line-height: 1.5;
  overflow: auto;
}
.markdown-body .code-wrapper pre[data-lang]::before {
  content: attr(data-lang);
  position: absolute;
  right: 12px;
  top: 8px;
  font-size: 12px;
  color: rgba(230,238,248,0.85);
  background: rgba(255,255,255,0.04);
  padding: 4px 8px;
  border-radius: 6px;
  border: 1px solid rgba(255,255,255,0.04);
}
.markdown-body .code-wrapper .copy-btn {
  position: absolute;
  right: 12px;
  top: 8px;
  z-index: 12;
  background: rgba(255,255,255,0.06);
  border: 1px solid rgba(255,255,255,0.06);
  color: #e6eef8;
  padding: 6px 8px;
  border-radius: 6px;
  cursor: pointer;
}
.markdown-body .code-wrapper .copy-btn.copied { background: #16a34a; border-color: #16a34a; }

/* Table polish */
.markdown-body :deep(table) {
  border-collapse: separate;
  border-spacing: 0;
  width: 100%;
}
.markdown-body :deep(table thead) th {
  background: linear-gradient(90deg, rgba(59,130,246,0.06), rgba(16,185,129,0.03));
  color: #0f172a;
  font-weight: 700;
}
.markdown-body :deep(table tbody tr:nth-child(odd)) {
  background: rgba(246,249,252,0.6);
}
.markdown-body :deep(table td), .markdown-body :deep(table th) {
  border-bottom: 1px solid rgba(226,232,240,0.6);
}

.markdown-body :deep(ul), .markdown-body :deep(ol) {
  padding-left: 1.25em;
}
.markdown-body :deep(li) {
  margin-bottom: 8px;
}
.markdown-body :deep(li)::marker {
  color: rgba(59,130,246,0.9);
  font-weight: 700;
}

.markdown-body :deep(table) {
  border-collapse: collapse;
  overflow: hidden;
  border-radius: 8px;
  box-shadow: 0 8px 18px rgba(2,6,23,0.04);
}
.markdown-body :deep(table thead) th {
  background: #f8fafc;
}
.markdown-body :deep(table th), .markdown-body :deep(table td) {
  padding: 10px 12px;
}

.markdown-body :deep(img) {
  display: block;
  margin: 18px auto;
  border-radius: 8px;
  box-shadow: 0 6px 22px rgba(2,6,23,0.06);
}

.markdown-body :deep(h1),
.markdown-body :deep(h2),
.markdown-body :deep(h3),
.markdown-body :deep(h4),
.markdown-body :deep(h5),
.markdown-body :deep(h6) {
  margin-top: 32px;
  margin-bottom: 16px;
  font-weight: 700;
  line-height: 1.3;
  color: #1e293b;
  border: none;
}

.markdown-body :deep(h1) {
  font-size: 2.25em;
  margin-top: 0;
  letter-spacing: -0.02em;
}

.markdown-body :deep(h2) {
  font-size: 1.75em;
  letter-spacing: -0.01em;
  margin-top: 48px;
}

.markdown-body :deep(h3) {
  font-size: 1.4em;
  margin-top: 32px;
}

.markdown-body :deep(p) {
  margin-top: 0;
  margin-bottom: 20px;
}

.markdown-body :deep(a) {
  color: #3b82f6;
  text-decoration: none;
  font-weight: 500;
}

.markdown-body :deep(a:hover) {
  text-decoration: underline;
}

.markdown-body :deep(ul),
.markdown-body :deep(ol) {
  margin-top: 0;
  margin-bottom: 20px;
  padding-left: 1.5em;
}

.markdown-body :deep(li) {
  margin-bottom: 8px;
}

.markdown-body :deep(blockquote) {
  margin: 24px 0;
  padding: 16px 24px;
  color: #475569;
  background: #f8fafc;
  border-left: 4px solid #cbd5e1;
  border-radius: 4px;
}

.markdown-body :deep(code) {
  padding: 0.2em 0.4em;
  margin: 0;
  font-size: 0.9em;
  background-color: #f1f5f9;
  border-radius: 4px;
  color: #0f172a;
  font-family: ui-monospace, SFMono-Regular, SF Mono, Menlo, Consolas, Liberation Mono, monospace;
}

.markdown-body :deep(pre) {
  padding: 0;
  overflow: auto;
  font-size: 0.9em;
  line-height: 1.5;
  background-color: #1e293b;
  color: #e2e8f0;
  border-radius: 8px;
  margin-bottom: 24px;
}

.markdown-body :deep(.code-wrapper) {
  position: relative;
  background-color: #1e293b;
  border-radius: 8px;
  margin-bottom: 24px;
}

.markdown-body :deep(.code-wrapper pre) {
  margin-bottom: 0;
  padding: 20px;
  border-radius: 8px;
}

.markdown-body :deep(.copy-btn) {
  position: absolute;
  top: 8px;
  right: 8px;
  padding: 5px 10px;
  font-size: 12px;
  font-weight: 500;
  color: #e2e8f0;
  background: rgba(255, 255, 255, 0.15);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s;
  opacity: 1;
  z-index: 10;
}

.markdown-body :deep(.copy-btn:hover) {
  background: rgba(255, 255, 255, 0.25);
  border-color: rgba(255, 255, 255, 0.3);
  color: #fff;
}

.markdown-body :deep(.copy-btn.copied) {
  background: #22c55e;
  color: #fff;
  border-color: #22c55e;
}

.markdown-body :deep(pre code) {
  background-color: transparent;
  padding: 0;
  color: inherit;
  white-space: pre;
}

.markdown-body :deep(img) {
  max-width: 100%;
  box-sizing: content-box;
  background-color: #fff;
  border-radius: 8px;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
  margin: 24px 0;
}

.markdown-body :deep(hr) {
  height: 1px;
  padding: 0;
  margin: 48px 0;
  background-color: #e2e8f0;
  border: 0;
}

.markdown-body :deep(table) {
  border-spacing: 0;
  border-collapse: collapse;
  margin-top: 0;
  margin-bottom: 24px;
  width: 100%;
  overflow: auto;
  display: block;
}

.markdown-body :deep(table th),
.markdown-body :deep(table td) {
  padding: 12px 16px;
  border: 1px solid #e2e8f0;
}

.markdown-body :deep(table th) {
  font-weight: 600;
  background-color: #f8fafc;
  color: #1e293b;
}

.markdown-body :deep(table tr) {
  background-color: #ffffff;
  border-top: 1px solid #e2e8f0;
}

.markdown-body :deep(table tr:nth-child(2n)) {
  background-color: #f8fafc;
}

/* Enhanced heading emoji + hover effects */

.markdown-body :deep(h1),
.markdown-body :deep(h2),
.markdown-body :deep(h3) {
  transition: transform 180ms cubic-bezier(.2,.9,.2,1), color 160ms ease, text-shadow 200ms ease;
  position: relative;
}
.markdown-body :deep(h1):hover,
.markdown-body :deep(h2):hover,
.markdown-body :deep(h3):hover {
  transform: translateX(6px) scale(1.01);
  color: #0b1220;
  text-shadow: 0 8px 30px rgba(2,6,23,0.06);
}
.markdown-body :deep(h1)::after,
.markdown-body :deep(h2)::after,

.markdown-body :deep(h1):hover::after,
.markdown-body :deep(h2):hover::after,
.markdown-body :deep(h3):hover::after { opacity: 1; transform: translateY(-1px) scale(1); }

/* Fancy horizontal rule with emoji */
.markdown-body :deep(hr) {
  height: 2px;
  padding: 0;
  margin: 48px 0;
  background: linear-gradient(90deg, rgba(59,130,246,0.18), rgba(16,185,129,0.10));
  border: 0;
  position: relative;
  border-radius: 6px;
}
.markdown-body :deep(hr)::before {
  content: "✨";
  position: absolute;
  left: 50%;
  top: -10px;
  transform: translateX(-50%);
  background: white;
  padding: 4px 8px;
  border-radius: 999px;
  font-size: 12px;
  box-shadow: 0 6px 18px rgba(2,6,23,0.06);
}

/* Code block: stronger left accent, language badge and refined copy button */
.markdown-body .code-wrapper {
  position: relative;
  margin: 16px 0 24px;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 10px 30px rgba(2,6,23,0.06);
  border-left: 6px solid rgba(59,130,246,0.14);
}
.markdown-body .code-wrapper pre {
  margin: 0;
  padding: 18px 16px 18px 20px;
  background: linear-gradient(180deg, #091223, #071021);
  color: #eaf3ff;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, 'Roboto Mono', monospace;
  font-size: 13px;
  line-height: 1.5;
}
.markdown-body .code-wrapper pre[data-lang]::after {
  content: attr(data-lang);
  position: absolute;
  right: 12px;
  top: 10px;
  font-size: 12px;
  color: rgba(230,238,248,0.95);
  background: rgba(255,255,255,0.04);
  padding: 4px 8px;
  border-radius: 8px;
  border: 1px solid rgba(255,255,255,0.04);
}
.markdown-body .code-wrapper .copy-btn {
  position: absolute;
  left: 12px;
  top: 10px;
  z-index: 12;
  background: rgba(255,255,255,0.06);
  border: 1px solid rgba(255,255,255,0.06);
  color: #e6eef8;
  padding: 6px 8px;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 600;
  font-size: 12px;
}
.markdown-body .code-wrapper .copy-btn.copied { background: #16a34a; border-color: #16a34a; }

/* Inline code emphasis */
.markdown-body :deep(code) {
  background: linear-gradient(90deg, rgba(59,130,246,0.04), rgba(2,6,23,0.01));
  padding: 3px 8px;
  border-radius: 8px;
  font-weight: 600;
  color: #071128;
}

/* Subtle drop emoji for blockquote */
.markdown-body :deep(blockquote) {
  border-left: 6px solid rgba(59,130,246,0.12);
  background: linear-gradient(90deg, rgba(59,130,246,0.02), rgba(2,6,23,0.01));
}

/* small typography tweaks */
.markdown-body {
  letter-spacing: -0.01em;
  color: #0f172a;
}

[data-section-id],
[data-file-id],
[data-task-id],
[data-doc-header] {
  scroll-margin-top: 24px;
}
</style>
