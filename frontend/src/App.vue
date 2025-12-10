<template>
  <div class="app-shell" :class="{ 'no-sidebar': !isSidebarVisible }">
    <Sidebar :files="files" :active-id="activeId" :doc-headers="docHeaders" :styles-count="stylesCount" :styles="stylesArr" :emotions-count="emotionsCount" :emotions="emotionsArr" :recent-tasks="recentTasks" @scrollTo="handleScrollTo" @uploadFiles="handleUploadFiles" @toggleSidebar="toggleSidebar" />

    <div class="main">
      <Home ref="homeRef" />
      <Footer @scrollTo="scrollToThirdParty" />
    </div>

    <div class="floating-tools">
      <button class="float-btn" @click="toggleSidebar" :title="isSidebarVisible ? '切换单栏' : '切换双栏'">
        <svg v-if="isSidebarVisible" xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect><line x1="9" y1="3" x2="9" y2="21"></line></svg>
        <svg v-else xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect></svg>
      </button>
      <button class="float-btn" @click="scrollToNextMain" title="下一个主标题">
        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="7 13 12 18 17 13"></polyline><polyline points="7 6 12 11 17 6"></polyline></svg>
      </button>
      <button class="float-btn" @click="scrollToPrevMain" title="上一个主标题">
        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="17 11 12 6 7 11"></polyline><polyline points="17 18 12 13 7 18"></polyline></svg>
      </button>
      <button class="float-btn" @click="scrollToTop" title="回到顶部">
        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="19" x2="12" y2="5"></line><polyline points="5 12 12 5 19 12"></polyline></svg>
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import Home from './views/Home.vue'
import Footer from './components/Footer.vue'
import Sidebar from './components/Sidebar.vue'

const homeRef = ref(null)
const isSidebarVisible = ref(true)

const files = computed(() => homeRef.value?.files ?? [])
const activeId = computed(() => homeRef.value?.activeId ?? '')
const docHeaders = computed(() => homeRef.value?.docHeaders ?? [])
const stylesArr = computed(() => homeRef.value?.styles ?? [])
const stylesCount = computed(() => Array.isArray(stylesArr.value) ? stylesArr.value.length : 0)
const emotionsArr = computed(() => homeRef.value?.emotions ?? [])
const emotionsCount = computed(() => Array.isArray(emotionsArr.value) ? emotionsArr.value.length : 0)
const recentTasks = computed(() => homeRef.value?.recentTasks ?? [])

function toggleSidebar() {
  isSidebarVisible.value = !isSidebarVisible.value
}

function scrollToTop() {
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

function scrollToNextMain() {
  const current = activeId.value
  let currentSectionIndex = 0 // Default to dashboard (0)

  // Check if in Uploads (1)
  const isUploads = current === 'uploads' || 
                    files.value.some(f => f.id === current || (f.tasks && f.tasks.some(t => t.id === current)))
  
  // Check if in Readme (2)
  const isReadme = current === 'readme' ||
                   docHeaders.value.some(h => h.id === current)

  if (isReadme) currentSectionIndex = 2
  else if (isUploads) currentSectionIndex = 1
  
  const sections = ['dashboard', 'uploads', 'readme']
  const nextIndex = currentSectionIndex + 1
  
  if (nextIndex < sections.length) {
    handleScrollTo(sections[nextIndex])
  } else {
    // no next main section — scroll to page bottom
    const docEl = document.documentElement || document.body
    const bottom = Math.max(docEl.scrollHeight, docEl.offsetHeight)
    window.scrollTo({ top: bottom, behavior: 'smooth' })
  }
}

function scrollToPrevMain() {
  const current = activeId.value
  let currentSectionIndex = 0 // Default to dashboard (0)

  // Check if in Uploads (1)
  const isUploads = current === 'uploads' || 
                    files.value.some(f => f.id === current || (f.tasks && f.tasks.some(t => t.id === current)))
  
  // Check if in Readme (2)
  const isReadme = current === 'readme' ||
                   docHeaders.value.some(h => h.id === current)

  if (isReadme) currentSectionIndex = 2
  else if (isUploads) currentSectionIndex = 1
  
  const sections = ['dashboard', 'uploads', 'readme']
  const prevIndex = currentSectionIndex - 1
  
  if (prevIndex >= 0) {
    handleScrollTo(sections[prevIndex])
  } else {
    // no previous main section — scroll to top
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }
}

function scrollToThirdParty() {
  // Find the README header whose text matches "Third-Party Notice"
  const target = docHeaders.value.find(h => h.text === 'Third-Party Notice')
    || docHeaders.value.find(h => h.id === 'third-party-notice')

  const id = target?.id || 'third-party-notice'
  handleScrollTo(id)
}

function handleScrollTo(id) {
  let el = document.querySelector(`[data-file-id="${id}"]`)
  if (!el) {
    el = document.querySelector(`[data-task-id="${id}"]`)
  }
  if (!el) {
    el = document.querySelector(`[data-section-id="${id}"]`)
  }
  if (!el) {
    el = document.querySelector(`[data-doc-header="${id}"]`)
  }
  // fallback to plain id attribute
  if (!el) {
    el = document.getElementById(id)
  }
  
  if (el) {
    el.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }
}

function handleUploadFiles(files) {
  // forward upload files to Home view's handler if available
  if (homeRef.value && typeof homeRef.value.onFilesSelected === 'function') {
    homeRef.value.onFilesSelected(files)
  }
}
</script>

<style scoped>
.app-shell {
  display: flex;
  min-height: 100vh;
}

.main {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.main > :last-child {
  margin-top: auto;
}

.floating-tools {
  position: fixed;
  /* place in the very small right-bottom corner */
  bottom: 45px;
  right: 8px;
  display: flex;
  flex-direction: column;
  gap: 6px; /* smaller gap between buttons */
  z-index: 1000;
}

.float-btn {
  width: 36px; /* smaller square */
  height: 36px;
  border-radius: 8px; /* slightly rounded square */
  background: #5b6b92;
  border: none;
  box-shadow: 0 3px 8px rgba(91,107,146,0.28);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: transform 0.14s, box-shadow 0.14s, background 0.14s;
  color: white;
  padding: 0;
  line-height: 0;
}

.float-btn:hover {
  background: #475569;
  transform: translateY(-2px);
  box-shadow: 0 6px 12px rgba(91,107,146,0.36);
}

/* Sidebar / layout transitions (use deep selector to reach child .sidebar) */
:deep(.sidebar) {
  transition: width 260ms cubic-bezier(.2,.9,.2,1), opacity 240ms ease, transform 260ms ease, padding 240ms ease;
}

.app-shell.no-sidebar :deep(.sidebar) {
  /* keep a narrow handle so the ☰ remains visible in the same place */
  width: 56px !important;
  padding: 12px 8px !important;
  opacity: 1;
  transform: none;
  overflow: visible;
  box-shadow: none;
}

/* hide the main toc content but keep header (so the hamburger stays) */
.app-shell.no-sidebar :deep(.sidebar) .toc-body,
.app-shell.no-sidebar :deep(.sidebar) .toc-right,
.app-shell.no-sidebar :deep(.sidebar) .toc-title,
.app-shell.no-sidebar :deep(.sidebar) .sidebar-upload-btn.header-upload {
  display: none !important;
}

/* make sure header area still shows the icon centered */
.app-shell.no-sidebar :deep(.sidebar) .toc-header {
  padding: 12px 8px !important;
  justify-content: flex-start;
}

/* subtle shift for main when sidebar collapses */
.main {
  transition: margin 260ms cubic-bezier(.2,.9,.2,1), transform 260ms cubic-bezier(.2,.9,.2,1);
}

.app-shell.no-sidebar .main {
  transform: translateX(0);
}

/* small focus/entrance for floating tools */
.floating-tools {
  transition: transform 260ms ease, opacity 240ms ease;
}
</style>
