<script setup>
import { defineProps, defineEmits } from 'vue'

const props = defineProps({
  current: { type: Number, default: 0 },
  duration: { type: Number, default: 0 }
})

const emit = defineEmits(['seek'])

function onClick(e) {
  const rect = e.currentTarget.getBoundingClientRect()
  const x = e.clientX - rect.left
  const p = Math.max(0, Math.min(1, x / rect.width))
  emit('seek', p * props.duration)
}
</script>

<template>
  <div class="progress" @click="onClick">
    <div class="bar" :style="{ width: (duration ? (current/duration*100) : 0) + '%' }"></div>
  </div>
</template>

<style scoped>
.progress {
  width: 100%;
  height: 12px;
  background: rgba(15, 23, 42, 0.08);
  border-radius: var(--radius-full);
  cursor: pointer;
  position: relative;
  overflow: hidden;
}

.bar {
  height: 100%;
  background: linear-gradient(120deg, #60a5fa, #2563eb);
  border-radius: inherit;
  box-shadow: var(--shadow-inner);
}
</style>
