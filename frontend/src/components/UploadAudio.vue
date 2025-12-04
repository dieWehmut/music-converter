<template>
  <div>
		<button type="button" :class="['pill-control', 'pill-control--primary', 'upload-btn', $attrs.class]" @click="openFileDialog">
      <slot>上传音频</slot>
    </button>
    <input ref="fileInput" class="visually-hidden" type="file" accept="audio/*" multiple @change="onFileChange" />
  </div>
</template>

<script setup>
import { ref } from 'vue'
const emit = defineEmits(['file-selected', 'file', 'files'])
const fileInput = ref(null)

function openFileDialog() {
	if (fileInput.value) fileInput.value.click()
}

function onFileChange(e) {
	const fl = e.target.files
	if (!fl) {
		emit('files', [])
		emit('file', null)
		emit('file-selected', null)
		return
	}
	const arr = Array.from(fl)
	// backward compatible: emit first file as single-file events
	const first = arr[0] || null
	emit('file-selected', first)
	emit('file', first)
	// new event for multiple files
	  emit('files', arr)
}
</script>

<style scoped>
	.upload-btn {
		box-shadow: none;
	}
.visually-hidden {
	position: absolute !important;
	height: 1px; width: 1px;
	overflow: hidden;
	clip: rect(1px, 1px, 1px, 1px);
	white-space: nowrap;
}
</style>
