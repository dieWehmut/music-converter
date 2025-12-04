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
.player {
  display: flex;
  flex-direction: column;
  gap: 12px;
  width: 100%;
  max-width: 720px;
  padding: 16px;
  border-radius: var(--radius-md);
  background: rgba(255, 255, 255, 0.9);
  border: 1px solid rgba(15, 23, 42, 0.06);
}

.meta {
  display: flex;
  justify-content: center;
  color: var(--color-text);
  font-weight: 600;
}

audio {
  width: 100%;
  border-radius: 12px;
  background: #000;
}
</style>
