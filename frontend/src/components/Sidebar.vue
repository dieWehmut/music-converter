<template>
  <div class="sidebar">
    <div class="toc-header">
      <div class="toc-left">
        <span class="toc-icon">☰</span>
        <span class="toc-title">目录</span>
      </div>
      <span class="toc-count">{{ activeIndexDisplay }}</span>
    </div>

    <div class="toc-body">
      <!-- Section 1: Dashboard -->
      <div class="toc-section">
        <div 
          class="toc-section-title clickable" 
          :class="{ active: activeId === 'dashboard' }"
          @click="$emit('scrollTo', 'dashboard')"
        >
          1. 控制面板
        </div>
      </div>

      <!-- Section 2: Uploaded Audio -->
      <div class="toc-section">
        <div 
          class="toc-section-title clickable" 
          :class="{ active: activeId === 'uploads' }"
          @click="$emit('scrollTo', 'uploads')"
        >
          <span>2. 已上传音频</span>
          <span class="section-count" v-if="files.length">{{ files.length }}</span>
        </div>
        
        <div v-if="!files.length" class="empty-tip">暂无上传文件</div>

        <div v-for="(file, fIdx) in files" :key="file.id" class="toc-group">
          <!-- Parent Item (File) -->
          <div 
            class="toc-row parent-row"
            :class="{ active: activeId === file.id }"
            @click="$emit('scrollTo', file.id)"
          >
            <span class="toc-text">2.{{ fIdx + 1 }}. {{ file.name || '未命名音频' }}</span>
          </div>

          <!-- Children Items (Tasks) -->
          <div v-if="file.tasks && file.tasks.length" class="toc-children">
            <div
              v-for="(task, tIdx) in file.tasks"
              :key="task.id"
              class="toc-row child-row"
              :class="{ active: activeId === task.id }"
              @click.stop="$emit('scrollTo', task.id)"
            >
              <span class="toc-index">2.{{ fIdx + 1 }}.{{ tIdx + 1 }}</span>
              <span class="toc-text">{{ task.style || '未设定风格' }}</span>
              <!-- Status indicator (dot) -->
              <span class="status-dot" :class="task.status" :title="task.status"></span>
            </div>
          </div>
        </div>
      </div>

      <!-- Section 3: Documentation -->
      <div class="toc-section">
        <div 
          class="toc-section-title clickable" 
          :class="{ active: activeId === 'readme' }"
          @click="$emit('scrollTo', 'readme')"
        >
          3. 说明文档
        </div>

        <div v-if="docHeaders.length" class="toc-group">
          <div
            v-for="(header, hIdx) in docHeaders"
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
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  files: { type: Array, default: () => [] },
  activeId: { type: String, default: '' },
  docHeaders: { type: Array, default: () => [] }
})

defineEmits(['scrollTo'])

const flatItemList = computed(() => {
  const list = []
  list.push('dashboard')
  list.push('uploads')
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

.toc-left {
  display: flex;
  align-items: center;
  gap: 10px;
  color: #475569;
}

.toc-icon {
  font-size: 20px;
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
  padding-left: 12px;
}

.toc-row {
  display: flex;
  align-items: center;
  padding: 6px 12px;
  border-radius: 8px;
  cursor: pointer;
  color: #64748b;
  transition: all 0.15s ease;
  font-size: 15px;
  line-height: 1.5;
  margin-bottom: 1px;
}

.toc-row:hover {
  color: #334155;
  background: rgba(0,0,0,0.03);
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
  padding-left: 24px;
}

.doc-row {
  font-size: 14px;
  padding-left: 12px;
}

.doc-row.level-1 {
  font-weight: 600;
  color: #334155;
}

.doc-row.level-2 {
  padding-left: 24px;
}

.doc-row.level-3 {
  padding-left: 36px;
  font-size: 13px;
}

.doc-row.level-4 {
  padding-left: 48px;
  font-size: 13px;
  color: #64748b;
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
</style>
