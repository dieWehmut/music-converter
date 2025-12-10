<template>
  <div class="sidebar">
    <div class="toc-header">
        <div class="toc-left">
          <span class="toc-icon" @click="handleToggle" title="切换侧栏" role="button" tabindex="0">☰</span>
        <span class="toc-title">目录</span>
        <UploadAudio class="sidebar-upload-btn header-upload" @files="handleUploadFiles" title="上传音频" aria-label="上传音频">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
            <path d="M12 3v12" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M8 7l4-4 4 4" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M21 21H3" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
        </UploadAudio>
      </div>
      <div class="toc-right">
        <span class="toc-count">{{ activeIndexDisplay }}</span>
      </div>
    </div>

    <div class="toc-body" ref="tocBody">
      <!-- Section 1: Dashboard -->
      <div class="toc-section">
        <div 
          class="toc-section-title clickable" 
          :class="{ active: activeId === 'dashboard' }"
          @click="$emit('scrollTo', 'dashboard')"
        >
          <div class="title-left">
            <span>1. 控制面板</span>
          </div>
          <div 
            class="collapse-btn" 
            :class="{ collapsed: collapsedIds.has('dashboard') }"
            @click.stop="toggleCollapse('dashboard')"
          >
            <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor"><path d="M7.41 8.59L12 13.17l4.59-4.58L18 10l-6 6-6-6 1.41-1.41z"/></svg>
          </div>
        </div>

        <transition name="collapse">
          <div v-show="!collapsedIds.has('dashboard')" class="toc-group dashboard-group">
            <!-- 1.1 概览（父级，可收缩 1.1.x） -->
            <div 
              class="toc-row parent-row"
              :class="{ active: activeId === 'dashboard.overview' }"
              @click="$emit('scrollTo', 'dashboard.overview')"
            >
              <span class="toc-index">1.1</span>
              <span class="toc-text">功能概览</span>
              <div 
                class="collapse-btn" 
                :class="{ collapsed: collapsedIds.has('dashboard.overview') }"
                @click.stop="toggleCollapse('dashboard.overview')"
              >
                <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor"><path d="M7.41 8.59L12 13.17l4.59-4.58L18 10l-6 6-6-6 1.41-1.41z"/></svg>
              </div>
            </div>

            <!-- 概览下的 1.1.x 子项 -->
            <transition name="collapse">
              <div class="toc-children" v-show="!collapsedIds.has('dashboard.overview')">
                <div
                  class="toc-row child-row dashboard-subitem"
                  :class="{ active: activeId === 'dashboard.overview.upload' }"
                  @click.stop="$emit('scrollTo', 'dashboard.overview.upload')"
                >
                  <span class="toc-index">1.1.1</span>
                  <span class="toc-text">上传音频</span>
                </div>
                <div
                  class="toc-row child-row dashboard-subitem"
                  :class="{ active: activeId === 'dashboard.overview.style' }"
                  @click.stop="$emit('scrollTo', 'dashboard.overview.style')"
                >
                  <span class="toc-index">1.1.2</span>
                  <span class="toc-text">风格与情绪选择</span>
                </div>
                <div
                  class="toc-row child-row dashboard-subitem"
                  :class="{ active: activeId === 'dashboard.overview.preview' }"
                  @click.stop="$emit('scrollTo', 'dashboard.overview.preview')"
                >
                  <span class="toc-index">1.1.3</span>
                  <span class="toc-text">实时预览</span>
                </div>
                <div
                  class="toc-row child-row dashboard-subitem"
                  :class="{ active: activeId === 'dashboard.overview.analysis' }"
                  @click.stop="$emit('scrollTo', 'dashboard.overview.analysis')"
                >
                  <span class="toc-index">1.1.4</span>
                  <span class="toc-text">分析功能</span>
                </div>
                <div
                  class="toc-row child-row dashboard-subitem"
                  :class="{ active: activeId === 'dashboard.overview.tasks' }"
                  @click.stop="$emit('scrollTo', 'dashboard.overview.tasks')"
                >
                  <span class="toc-index">1.1.5</span>
                  <span class="toc-text">任务管理</span>
                </div>
                <div
                  class="toc-row child-row dashboard-subitem"
                  :class="{ active: activeId === 'dashboard.overview.download' }"
                  @click.stop="$emit('scrollTo', 'dashboard.overview.download')"
                >
                  <span class="toc-index">1.1.6</span>
                  <span class="toc-text">下载</span>
                </div>
              </div>
            </transition>

            <!-- 1.2 可用风格 / 情绪 （父） -->
            <div
              class="toc-row parent-row"
              :class="{ active: activeId === 'dashboard.options' }"
              @click.stop="$emit('scrollTo', 'dashboard.options')"
            >
              <span class="toc-index">1.2</span>
              <span class="toc-text">转换变量</span>
              <div class="stat-badge" v-if="(stylesCount || emotionsCount)">{{ (stylesCount || 0) + (emotionsCount || 0) }}</div>
              <div 
                class="collapse-btn" 
                :class="{ collapsed: collapsedIds.has('dashboard.options') }"
                @click.stop="toggleCollapse('dashboard.options')"
              >
                <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor"><path d="M7.41 8.59L12 13.17l4.59-4.58L18 10l-6 6-6-6 1.41-1.41z"/></svg>
              </div>
            </div>

            <transition name="collapse">
              <div class="toc-children" v-show="!collapsedIds.has('dashboard.options')">
                <!-- 1.2.1 可用风格 -->
                <div
                  class="toc-row parent-row"
                  :class="{ active: activeId === 'dashboard.styles' }"
                  @click.stop="$emit('scrollTo', 'dashboard.styles')"
                >
                  <span class="toc-index">1.2.1</span>
                  <span class="toc-text">styles</span>
                  <div class="stat-badge" v-if="stylesCount">{{ stylesCount }}</div>
                  <div 
                    class="collapse-btn" 
                    :class="{ collapsed: collapsedIds.has('dashboard.styles') }"
                    @click.stop="toggleCollapse('dashboard.styles')"
                  >
                    <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor"><path d="M7.41 8.59L12 13.17l4.59-4.58L18 10l-6 6-6-6 1.41-1.41z"/></svg>
                  </div>
                </div>

                <transition name="collapse">
                  <div class="toc-children" v-show="!collapsedIds.has('dashboard.styles')">
                    <div v-if="props.styles && props.styles.length">
                      <div
                        v-for="(s, si) in props.styles"
                        :key="s"
                        class="toc-row child-row style-subitem"
                        :class="{ active: activeId === ('dashboard.styles.' + (si + 1)) }"
                        @click.stop="$emit('scrollTo', 'dashboard.styles.' + (si + 1))"
                      >
                        <span class="toc-index">1.2.1.{{ si + 1 }}</span>
                        <span class="toc-text">{{ s }}</span>
                      </div>
                    </div>
                    <div v-else class="empty-tip">暂无风格</div>
                  </div>
                </transition>

                <!-- 1.2.2 可用情绪 -->
                <div
                  class="toc-row parent-row"
                  :class="{ active: activeId === 'dashboard.emotions' }"
                  @click.stop="$emit('scrollTo', 'dashboard.emotions')"
                >
                  <span class="toc-index">1.2.2</span>
                  <span class="toc-text">emotions</span>
                  <div class="stat-badge" v-if="emotionsCount">{{ emotionsCount }}</div>
                  <div 
                    class="collapse-btn" 
                    :class="{ collapsed: collapsedIds.has('dashboard.emotions') }"
                    @click.stop="toggleCollapse('dashboard.emotions')"
                  >
                    <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor"><path d="M7.41 8.59L12 13.17l4.59-4.58L18 10l-6 6-6-6 1.41-1.41z"/></svg>
                  </div>
                </div>

                <transition name="collapse">
                  <div class="toc-children" v-show="!collapsedIds.has('dashboard.emotions')">
                    <div v-if="props.emotions && props.emotions.length">
                      <div
                        v-for="(e, ei) in props.emotions"
                        :key="e"
                        class="toc-row child-row emotion-subitem"
                        :class="{ active: activeId === ('dashboard.emotions.' + (ei + 1)) }"
                        @click.stop="$emit('scrollTo', 'dashboard.emotions.' + (ei + 1))"
                      >
                        <span class="toc-index">1.2.2.{{ ei + 1 }}</span>
                        <span class="toc-text">{{ e }}</span>
                      </div>
                    </div>
                    <div v-else class="empty-tip">暂无情绪</div>
                  </div>
                </transition>
              </div>
            </transition>

            <!-- 1.3 最近任务 -->
            <div
              class="toc-row parent-row"
              :class="{ active: activeId === 'dashboard.recent' }"
              @click.stop="$emit('scrollTo', 'dashboard.recent')"
            >
              <span class="toc-index">1.3</span>
              <span class="toc-text">最近任务</span>
              <div class="stat-badge">{{ totalTasksCount }}</div>
              <div 
                class="collapse-btn" 
                :class="{ collapsed: collapsedIds.has('dashboard.recent') }" 
                @click.stop="toggleCollapse('dashboard.recent')"
              >
                <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor"><path d="M7.41 8.59L12 13.17l4.59-4.58L18 10l-6 6-6-6 1.41-1.41z"/></svg>
              </div>
            </div>

            <!-- recent tasks children (1.3.1, 1.3.2, ...) -->
            <transition name="collapse">
              <div class="toc-children" v-show="!collapsedIds.has('dashboard.recent')">
                <div v-if="recentTasks && recentTasks.length">
                  <div
                    v-for="(t, ri) in recentTasks"
                    :key="t.sectionId"
                    class="toc-row child-row recent-subitem"
                    :class="{ active: activeId === t.sectionId }"
                    @click.stop="$emit('scrollTo', t.sectionId)"
                  >
                    <span class="toc-index">1.3.{{ ri + 1 }}</span>
                    <span class="toc-text">{{ t.fileName }} — {{ t.style }}<span v-if="t.emotion"> / {{ t.emotion }}</span></span>
                    <span class="status-dot" :class="t.status" :title="t.status"></span>
                  </div>
                </div>
                <div v-else class="empty-tip">暂无最近任务</div>
              </div>
            </transition>

            <div class="dashboard-stats">
              <div class="dashboard-stat">
                <div class="stat-label">转换中</div>
                <div class="stat-value converting">{{ convertingCount }}</div>
              </div>
              <div class="dashboard-stat">
                <div class="stat-label">失败</div>
                <div class="stat-value error">{{ errorCount }}</div>
              </div>
              <div class="dashboard-stat">
                <div class="stat-label">待处理</div>
                <div class="stat-value">{{ pendingCount }}</div>
              </div>
            </div>
          </div>
        </transition>
      </div>

      <!-- Section 2: Uploaded Audio -->
      <div class="toc-section">
        <div 
          class="toc-section-title clickable" 
          :class="{ active: activeId === 'uploads' }"
          @click="$emit('scrollTo', 'uploads')"
        >
          <div class="title-left">
            <span>2. 已上传音频</span>
            <span class="section-count" v-if="files.length">{{ files.length }}</span>
          </div>
          <!-- upload button placed to the right of the count; stop click propagation so title click isn't triggered -->
          <!-- upload button moved to header -->
          <div 
            class="collapse-btn" 
            :class="{ collapsed: collapsedIds.has('uploads') }"
            @click.stop="toggleCollapse('uploads')"
          >
            <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor"><path d="M7.41 8.59L12 13.17l4.59-4.58L18 10l-6 6-6-6 1.41-1.41z"/></svg>
          </div>
        </div>
        
        <transition name="collapse">
          <div v-show="!collapsedIds.has('uploads')">
            <div v-if="!files.length" class="empty-tip">暂无上传文件</div>

            <div v-for="(file, fIdx) in files" :key="file.id" class="toc-group">
            <!-- Parent Item (File) -->
            <div 
              class="toc-row parent-row"
              :class="{ active: activeId === file.id }"
              @click="$emit('scrollTo', file.id)"
            >
              <span class="toc-text">2.{{ fIdx + 1 }}. {{ file.name || '未命名音频' }}</span>
              <div 
                v-if="file.tasks && file.tasks.length"
                class="collapse-btn" 
                :class="{ collapsed: collapsedIds.has(file.id) }"
                @click.stop="toggleCollapse(file.id)"
              >
                <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor"><path d="M7.41 8.59L12 13.17l4.59-4.58L18 10l-6 6-6-6 1.41-1.41z"/></svg>
              </div>
            </div>

            <!-- Children Items (Tasks) -->
            <transition name="collapse">
              <div v-if="file.tasks && file.tasks.length" v-show="!collapsedIds.has(file.id)" class="toc-children">
                <div
                v-for="(task, tIdx) in file.tasks"
                :key="task.id"
                class="toc-row child-row"
                :class="{ active: activeId === task.id }"
                @click.stop="$emit('scrollTo', task.id)"
              >
                <span class="toc-index">2.{{ fIdx + 1 }}.{{ tIdx + 1 }}</span>
                <span class="toc-text">{{ formatTaskLabel(file, task) }}</span>
                <!-- Status indicator (dot) -->
                <span class="status-dot" :class="task.status" :title="task.status"></span>
                </div>
              </div>
            </transition>
          </div>
          </div>
        </transition>
      </div>

      <!-- Section 3: Documentation -->
      <div class="toc-section">
        <div 
          class="toc-section-title clickable" 
          :class="{ active: activeId === 'readme' }"
          @click="$emit('scrollTo', 'readme')"
        >
          <div class="title-left">
            <span>3. 说明文档</span>
          </div>
          <div 
            class="collapse-btn" 
            :class="{ collapsed: collapsedIds.has('readme') }"
            @click.stop="toggleCollapse('readme')"
          >
            <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor"><path d="M7.41 8.59L12 13.17l4.59-4.58L18 10l-6 6-6-6 1.41-1.41z"/></svg>
          </div>
        </div>

        <transition name="collapse">
          <div v-show="!collapsedIds.has('readme')" v-if="docHeaders.length" class="toc-group">
            <div
              v-for="(header, hIdx) in visibleDocHeaders"
              :key="header.id"
              class="toc-row doc-row"
              :class="[
                { active: activeId === header.id },
                'level-' + header.level
              ]"
              @click.stop="$emit('scrollTo', header.id)"
            >
              <span class="toc-index">{{ header.number }}</span>
              <span class="toc-text">{{ header.text }}</span>
              <div 
                v-if="header.hasChildren"
                class="collapse-btn" 
                :class="{ collapsed: header.isCollapsed }"
                @click.stop="toggleCollapse(header.id)"
              >
                <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor"><path d="M7.41 8.59L12 13.17l4.59-4.58L18 10l-6 6-6-6 1.41-1.41z"/></svg>
              </div>
            </div>
          </div>
        </transition>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, watch, nextTick } from 'vue'

import UploadAudio from './UploadAudio.vue'

const props = defineProps({
  files: { type: Array, default: () => [] },
  activeId: { type: String, default: '' },
  docHeaders: { type: Array, default: () => [] },
  stylesCount: { type: Number, default: 0 },
  styles: { type: Array, default: () => [] },
  emotionsCount: { type: Number, default: 0 },
  emotions: { type: Array, default: () => [] },
  recentTasks: { type: Array, default: () => [] }
})

const emit = defineEmits(['scrollTo', 'uploadFiles', 'toggleSidebar'])

const recentTasks = computed(() => props.recentTasks || [])

function handleUploadFiles(files) {
  // forward upload files event to parent
  emit('uploadFiles', files)
}

function handleToggle() {
  emit('toggleSidebar')
}

const flatItemList = computed(() => {
  const list = []
  list.push('dashboard')
  list.push('dashboard.overview')
  list.push('dashboard.overview.upload')
  list.push('dashboard.overview.style')
  list.push('dashboard.overview.preview')
  list.push('dashboard.overview.analysis')
  list.push('dashboard.overview.tasks')
  list.push('dashboard.overview.download')
  // styles group (1.2.1)
  // styles group (1.2.1)
  list.push('dashboard.options')
  list.push('dashboard.styles')
  props.styles && props.styles.forEach((s, i) => list.push('dashboard.styles.' + (i + 1)))
  // emotions group (1.2.2)
  list.push('dashboard.emotions')
  props.emotions && props.emotions.forEach((e, i) => list.push('dashboard.emotions.' + (i + 1)))
  list.push('dashboard.recent')
  list.push('uploads')
  // include recent tasks (1.3.1, 1.3.2 ...)
  props.recentTasks && props.recentTasks.forEach(t => list.push(t.sectionId))
  props.files.forEach(file => {
    list.push(file.id)
    if (file.tasks) {
      file.tasks.forEach(task => list.push(task.id))
    }
  })
  list.push('readme')
  props.docHeaders.forEach(h => list.push(h.id))
  return list
})

const activeIndexDisplay = computed(() => {
  const idx = flatItemList.value.indexOf(props.activeId)
  return idx !== -1 ? idx + 1 : ''
})

const collapsedIds = ref(new Set())

// Format task label showing style / emotion and append (n) when there are duplicates
function formatTaskLabel(file, task) {
  if (!file || !file.tasks) {
    return `${task.style || '未设定风格'}${task.emotion ? ' / ' + task.emotion : ''}`
  }
  const same = file.tasks.filter(t => (t.style || '') === (task.style || '') && (t.emotion || '') === (task.emotion || ''))
  const base = `${task.style || '未设定风格'}${task.emotion ? ' / ' + task.emotion : ''}`
  if (same.length <= 1) return base
  const idx = same.findIndex(t => t.id === task.id)
  return `${base}(${idx + 1})`
}

const toggleCollapse = (id) => {
  if (collapsedIds.value.has(id)) {
    collapsedIds.value.delete(id)
  } else {
    collapsedIds.value.add(id)
  }
}

const visibleDocHeaders = computed(() => {
  const headers = props.docHeaders
  const result = []
  let collapseLevel = Infinity
  
  for (let i = 0; i < headers.length; i++) {
    const h = headers[i]
    const next = headers[i+1]
    const hasChildren = next && next.level > h.level
    
    let isVisible = true
    if (collapseLevel !== Infinity) {
      if (h.level > collapseLevel) {
        isVisible = false
      } else {
        collapseLevel = Infinity
      }
    }
    
    if (isVisible) {
      if (collapsedIds.value.has(h.id)) {
        collapseLevel = h.level
      }
      result.push({
        ...h,
        hasChildren,
        isCollapsed: collapsedIds.value.has(h.id)
      })
    }
  }
  return result
})

// Dashboard statistics derived from files/tasks
const totalFilesCount = computed(() => props.files ? props.files.length : 0)
const totalTasksCount = computed(() => {
  if (!props.files) return 0
  return props.files.reduce((sum, f) => sum + (f.tasks ? f.tasks.length : 0), 0)
})
const convertingCount = computed(() => {
  if (!props.files) return 0
  return props.files.reduce((sum, f) => sum + (f.tasks ? f.tasks.filter(t => t.status === 'converting').length : 0), 0)
})
const errorCount = computed(() => {
  if (!props.files) return 0
  return props.files.reduce((sum, f) => sum + (f.tasks ? f.tasks.filter(t => t.status === 'error').length : 0), 0)
})
const pendingCount = computed(() => Math.max(0, totalTasksCount.value - convertingCount.value - errorCount.value))

const tocBody = ref(null)

watch(() => props.activeId, async (id) => {
  if (!id) return
  await nextTick()
  const container = tocBody.value
  if (!container) return
  const el = container.querySelector('.active')
  if (el) {
    // calculate desired scrollTop so the active element appears centered in the container
    const containerRect = container.getBoundingClientRect()
    const elRect = el.getBoundingClientRect()
    // element's offsetTop relative to the container's scrollTop
    const offsetTop = el.offsetTop
    const target = offsetTop - (container.clientHeight / 2) + (el.clientHeight / 2)
    const maxScroll = Math.max(0, container.scrollHeight - container.clientHeight)
    const top = Math.max(0, Math.min(target, maxScroll))
    container.scrollTo({ top, behavior: 'smooth' })
  }
})
</script>

<style scoped>
.sidebar {
  width: 280px;
  background: #f1f5f9;
  border-right: 1px solid #e2e8f0;
  display: flex;
  flex-direction: column;
  height: 100vh;
  position: sticky;
  top: 0;
  flex-shrink: 0;
  user-select: none;
}

.toc-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 24px 20px 16px;
  background: transparent;
}

.toc-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.toc-actions {
  display: flex;
  align-items: center;
}

/* Header upload button styling (green circular) */
.sidebar-upload-btn.header-upload {
  /* rectangular button matching title height */
  height: 34px; /* match visual height of the title text */
  padding: 0 12px;
  min-width: 40px;
  border-radius: 8px;
  background: #10b981; /* green */
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  box-shadow: 0 8px 22px rgba(16,185,129,0.12);
  border: none;
  margin-left: 8px; /* sit closer to the title */
  line-height: 1;
  transition: transform 140ms ease, box-shadow 140ms ease;
}
.sidebar-upload-btn.header-upload svg { stroke: currentColor; }
.sidebar-upload-btn.header-upload:hover { transform: translateY(-2px); box-shadow: 0 10px 26px rgba(16,185,129,0.16); }

.toc-left {
  display: flex;
  align-items: center;
  gap: 10px;
  color: #475569;
}

.toc-icon {
  font-size: 20px;
  cursor: pointer;
}

.toc-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border-radius: 8px;
  transition: transform 160ms ease, box-shadow 160ms ease, background 120ms ease;
}
.toc-icon:hover {
  transform: translateY(-3px) scale(1.03);
  box-shadow: 0 8px 22px rgba(59,130,246,0.12);
  background: rgba(59,130,246,0.06);
  color: #334155;
}
.toc-icon:focus {
  outline: 2px solid rgba(59,130,246,0.18);
  outline-offset: 2px;
}

.toc-title {
  font-size: 18px;
  font-weight: 600;
  letter-spacing: 0.02em;
}

.toc-count {
  font-size: 28px;
  font-style: italic;
  color: #94a3b8;
  font-weight: 300;
  font-family: serif;
}

.toc-body {
  flex: 1;
  overflow-y: auto;
  padding: 0 16px 32px;
}

.toc-body::-webkit-scrollbar {
  width: 6px;
}

.toc-body::-webkit-scrollbar-track {
  background: transparent;
}

.toc-body::-webkit-scrollbar-thumb {
  background-color: rgba(148, 163, 184, 0.3);
  border-radius: 10px;
}

.toc-body::-webkit-scrollbar-thumb:hover {
  background-color: rgba(148, 163, 184, 0.5);
}

.toc-section {
  margin-bottom: 24px;
}

.toc-section-title {
  font-size: 15px;
  color: #475569;
  margin-bottom: 8px;
  padding: 8px 12px;
  border-radius: 8px;
  transition: all 0.15s ease;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.section-count {
  font-size: 14px;
  background: rgba(0,0,0,0.06);
  padding: 2px 10px;
  border-radius: 12px;
  color: #64748b;
  font-weight: 600;
}

.toc-section-title.active .section-count {
  background: rgba(255,255,255,0.2);
  color: #fff;
}

.toc-section-title.clickable {
  cursor: pointer;
}

.toc-section-title.clickable:hover {
  color: #334155;
  background: rgba(0,0,0,0.03);
}

.toc-section-title.active {
  background-color: #5b6b92;
  color: #ffffff;
  box-shadow: 0 4px 12px -2px rgba(91, 107, 146, 0.4);
  font-weight: 500;
}

.toc-group {
  margin-bottom: 4px;
  padding-left: 0;
  margin-left: 24px;
  border-left: 2px solid #cbd5e1;
}

.toc-children {
  margin-left: 24px;
  border-left: 2px solid #cbd5e1;
  padding-left: 0;
}

.toc-row {
  position: relative;
  display: flex;
  align-items: center;
  padding: 6px 12px;
  border-radius: 6px;
  cursor: pointer;
  color: #64748b;
  transition: all 0.15s ease;
  font-size: 15px;
  line-height: 1.5;
  margin-bottom: 2px;
  margin-left: 12px;
  width: calc(100% - 12px);
}

.toc-row::before {
  content: '';
  position: absolute;
  left: -14px;
  top: 50%;
  width: 14px;
  height: 2px;
  background-color: #cbd5e1;
}

.toc-row:hover {
  color: var(--color-text);
  background: rgba(59,130,246,0.04); /* subtle blue like recent tasks */
  transform: translateX(4px);
  box-shadow: 0 6px 18px rgba(59,130,246,0.06);
}
.toc-row:active {
  transform: translateX(1px) scale(0.998);
}

.toc-row.active {
  background-color: #5b6b92;
  color: #ffffff;
  box-shadow: 0 4px 12px -2px rgba(91, 107, 146, 0.4);
  font-weight: 500;
}

.toc-row.active .toc-index {
  opacity: 0.9;
  color: rgba(255,255,255,0.9);
}

.toc-row.active .status-dot {
  box-shadow: 0 0 0 2px rgba(255,255,255,0.2);
}

.parent-row {
  margin-top: 4px;
}

.child-row {
  font-size: 14px;
  padding-left: 12px;
}

.doc-row {
  font-size: 14px;
  padding-left: 12px;
  color: #475569;
}

.doc-row.level-1 {
  font-weight: 600;
  color: #334155;
}

.doc-row.level-2 {
  margin-left: 24px;
  width: calc(100% - 24px);
}

.doc-row.level-2::before {
  left: -26px;
  width: 26px;
}

.doc-row.level-3 {
  margin-left: 36px;
  width: calc(100% - 36px);
  font-size: 13px;
}

.doc-row.level-3::before {
  left: -38px;
  width: 38px;
}

.doc-row.level-4 {
  margin-left: 48px;
  width: calc(100% - 48px);
  font-size: 13px;
}

.doc-row.level-4::before {
  left: -50px;
  width: 50px;
}

.toc-index {
  margin-right: 8px;
  color: #94a3b8;
  font-variant-numeric: tabular-nums;
}

.toc-text {
  flex: 1;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.status-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #cbd5e1;
  margin-left: 8px;
  flex-shrink: 0;
}

.status-dot.success { background: #22c55e; }
.status-dot.converting { background: #3b82f6; }
.status-dot.error { background: #ef4444; }

.empty-tip {
  text-align: center;
  color: #94a3b8;
  margin-top: 16px;
  margin-bottom: 16px;
  font-size: 14px;
}

.title-left {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
  overflow: hidden;
}

.collapse-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  border-radius: 4px;
  cursor: pointer;
  color: #94a3b8;
  transition: all 0.2s ease;
  margin-left: 8px;
  flex-shrink: 0;
}

.collapse-btn:hover {
  background: rgba(0,0,0,0.05);
  color: #64748b;
}

.collapse-btn.collapsed {
  transform: rotate(-90deg);
}

.toc-row .collapse-btn {
  margin-left: auto;
  width: 20px;
  height: 20px;
}

.sidebar-upload {
  display: flex;
  align-items: center;
  margin-left: 8px;
}

.sidebar-upload-btn {
  --btn-padding-x: 2px;
  padding: 0;
  font-size: 0; /* hide any leftover text */
  border-radius: 6px;
  width: 30px !important;
  height: 20px !important;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  line-height: 1;
}

/* Dashboard specific styles */
.dashboard-group {
  padding-top: 4px;
}
.stat-badge {
  background: rgba(0,0,0,0.06);
  color: #334155;
  padding: 2px 8px;
  border-radius: 999px;
  font-weight: 600;
  font-size: 13px;
}
.dashboard-stats {
  display: flex;
  gap: 4px; /* 进一步缩小块间间距，使三项更靠近 */
  margin-top: 8px;
  align-items: stretch;
  justify-content: center; /* 水平居中三项内容 */
  /* 使“转换中”与上方“最近任务”文字左侧大致对齐 */
  margin-left: 44px;
  /* 外层卡片样式，突显统计块 */
  background: linear-gradient(180deg, rgba(255,255,255,0.02), rgba(255,255,255,0.01));
  padding: 6px; /* 略减内边距以更紧凑 */
  border-radius: 10px;
  border: 1px solid rgba(16,185,129,0.14); /* 轻柔的绿色边框 */
  box-shadow: 0 6px 18px rgba(16,185,129,0.04); /* 绿色轻微阴影，营造浮起感 */
}
.dashboard-stat {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0px;
  padding: 0px 6px; /* 稍微增加左右内边距以防文字拥挤 */
  border-radius: 6px;
  min-width: 10px; /* 进一步减小最小宽度，使三项更紧凑 */
  background: transparent;
}
.dashboard-stat .stat-label {
  font-size: 12px;
  color: #94a3b8;
  text-align: center;
}
.dashboard-stat .stat-value {
  font-size: 16px;
  font-weight: 700;
  text-align: center;
  display: block;
  min-width: 28px;
}
.dashboard-stat .stat-value.converting { color: #3b82f6 }
.dashboard-stat .stat-value.error { color: #ef4444 }
.dashboard-stat .stat-value.success { color: #10b981 }
.dashboard-links { display:flex; gap:10px; margin-top:8px }
.dashboard-links .link { color:#64748b; font-size:13px; cursor:pointer }
.dashboard-links .link:hover { color:#334155 }
.dashboard-subitem {
  font-size: 13px;
}

.recent-subitem {
  font-size: 13px;
  color: #64748b;
}

/* Hover-enlarge effects for all sidebar titles and entries */
.toc-title,
.toc-section-title .title-left > span,
.toc-row .toc-text,
.doc-row .toc-text {
  display: inline-block;
  transition: transform 180ms cubic-bezier(.2,.9,.2,1), color 140ms ease, text-shadow 200ms ease;
  transform-origin: left center;
}

/* Header title (目录) */
.toc-title:hover {
  transform: scale(1.06) translateX(2px);
  color: #334155;
  text-shadow: 0 8px 20px rgba(2,6,23,0.06);
}

/* Section titles */
.toc-section-title.clickable:hover .title-left > span {
  transform: scale(1.04) translateX(4px);
  color: #0f172a;
}

/* Rows (parents/children/doc rows) enlarge the text when hovered */
.toc-row:hover .toc-text,
.doc-row:hover .toc-text {
  transform: scale(1.03) translateX(4px);
  color: var(--color-text);
}

/* Keep existing hover translate but make the text scale more prominent */
.toc-row:hover {
  transform: translateX(4px);
}

/* Collapse transition for Vue <transition name="collapse"> */
.collapse-enter-active, .collapse-leave-active {
  transition: max-height 220ms ease, opacity 180ms ease, transform 180ms ease;
  overflow: hidden;
}
.collapse-enter-from, .collapse-leave-to {
  max-height: 0;
  opacity: 0;
  transform: translateY(-6px);
}
.collapse-enter-to, .collapse-leave-from {
  max-height: 1000px; /* large enough to fit content */
  opacity: 1;
  transform: none;
}

/* Make the collapse icon rotate smoothly */
.collapse-btn {
  transition: transform 200ms ease, background 200ms ease, color 200ms ease;
  transform-origin: center;
}

</style>
