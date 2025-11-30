<template>
	<div class="target-emotion-selector">
		<select v-model="modelValue" @change="onChange">
			<option v-for="s in styles" :key="s" :value="s">{{ s }}</option>
		</select>
	</div>
</template>

<script setup>
import { computed } from 'vue'
const props = defineProps({
	styles: { type: Array, default: () => [] },
	modelValue: { type: String, default: '' }
})
const emit = defineEmits(['update:modelValue'])
const modelValue = computed({
	get: () => props.modelValue,
	set: v => emit('update:modelValue', v)
})
function onChange(e) {
	emit('update:modelValue', e.target.value)
}
</script>

<style scoped>
select {
	padding: 8px;
	border-radius: 8px;
	border: 1px solid #e6eef8;
	background: #fbfdff;
}
</style>
