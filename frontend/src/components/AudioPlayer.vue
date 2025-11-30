<script setup>
import { ref, watch } from 'vue'

const props = defineProps({
  src: { type: String, default: '' },
  label: { type: String, default: '' }
})

const audio = ref(null)

watch(() => props.src, () => {
  if (audio.value) {
    audio.value.pause()
    audio.value.currentTime = 0
  }
})
</script>

<template>
  <div class="player">
    <div class="meta">
      <strong>{{ label || '本地音频' }}</strong>
    </div>
    <audio ref="audio" :src="src" controls style="width:100%"></audio>
  </div>
</template>

<style scoped>
.player{display:flex;flex-direction:column;gap:8px;width:100%;max-width:720px}
.meta{display:flex;justify-content:center}
.controls{display:flex;align-items:center;gap:12px}
</style>
