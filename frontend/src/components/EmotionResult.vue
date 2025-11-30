<template>
	<div class="emotion-result" v-if="features">
		<h3>提取到的特征</h3>
		<pre>{{ JSON.stringify(features, null, 2) }}</pre>
	</div>
</template>

<script setup>
const props = defineProps({
	features: { type: Object, default: null }
})
</script>

<style scoped>
.emotion-result pre {
	background: #f8fafc;
	padding: 8px;
	border-radius: 8px;
	overflow: auto;
}
</style>
