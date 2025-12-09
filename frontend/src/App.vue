<template>
  <div class="app-shell">
    <Sidebar :files="files" :active-id="activeId" :doc-headers="docHeaders" @scrollTo="handleScrollTo" />

    <div class="main">
      <Home ref="homeRef" />
      <Footer />
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import Home from './views/Home.vue'
import Footer from './components/Footer.vue'
import Sidebar from './components/Sidebar.vue'

const homeRef = ref(null)

const files = computed(() => homeRef.value?.files ?? [])
const activeId = computed(() => homeRef.value?.activeId ?? '')
const docHeaders = computed(() => homeRef.value?.docHeaders ?? [])

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
  
  if (el) {
    el.scrollIntoView({ behavior: 'smooth', block: 'start' })
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
</style>
