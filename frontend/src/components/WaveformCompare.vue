<template>
	<div class="waveform-compare">
		<slot>波形对比区域</slot>
	</div>
</template>

<script setup>
// 预留 props，可后续扩展
</script>

<style scoped>
.waveform-compare {
	min-height: 60px;
	background: #f3f6fa;
	border-radius: 8px;
	margin: 12px 0;
	display: flex;
	align-items: center;
	justify-content: center;
	color: #64748b;
}
</style>
