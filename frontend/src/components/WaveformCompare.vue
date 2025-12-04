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
	min-height: 72px;
	background: linear-gradient(135deg, rgba(99, 102, 241, 0.08), rgba(59, 130, 246, 0.08));
	border-radius: var(--radius-md);
	margin: 16px 0;
	display: flex;
	align-items: center;
	justify-content: center;
	color: var(--color-text-muted);
	border: 1px dashed rgba(99, 102, 241, 0.4);
}
</style>
