<template>
	<div class="emotion-result" v-if="features">


		<div class="chart-grid">
			<div class="chart-card" v-if="styleSegments.length">
				<div class="chart-title">风格占比</div>
				<div class="chart-main">
					<div class="chart-figure" :style="{ '--chart-bg': styleGradient }">
						<div class="chart-center">Style</div>
						<div class="chart-labels">
							<div
								v-for="segment in styleSegments"
								:key="segment?.label || 'style-'+$index"
								v-if="(segment?.percent ?? 0) >= 5"
								class="chart-label"
								:style="segmentLabelStyle(segment)"
							>
								{{ Math.round(segment?.percent ?? 0) }}%
							</div>
						</div>
					</div>
					<div class="legend">
						<div class="legend-item" v-for="segment in styleSegments" :key="segment.label">
							<span class="dot" :style="{ backgroundColor: segment.color }"></span>
							<span class="legend-label">{{ segment.label }}</span>
							<span class="legend-value">{{ Math.round(segment.percent) }}%</span>
						</div>
					</div>
				</div>
			</div>
			<div class="chart-card empty" v-else>
				<div class="chart-title">风格占比</div>
				<p class="empty-text">暂无风格概率数据</p>
			</div>

			<div class="chart-card" v-if="emotionSegments.length">
				<div class="chart-title">情绪占比</div>
				<div class="chart-main">
					<div class="chart-figure" :style="{ '--chart-bg': emotionGradient }">
						<div class="chart-center">Emotion</div>
						<div class="chart-labels">
							<div
								v-for="segment in emotionSegments"
								:key="segment?.label || 'emotion-'+$index"
								v-if="(segment?.percent ?? 0) >= 5"
								class="chart-label"
								:style="segmentLabelStyle(segment)"
							>
								{{ Math.round(segment?.percent ?? 0) }}%
							</div>
						</div>
					</div>
					<div class="legend">
						<div class="legend-item" v-for="segment in emotionSegments" :key="segment.label">
							<span class="dot" :style="{ backgroundColor: segment.color }"></span>
							<span class="legend-label">{{ segment.label }}</span>
							<span class="legend-value">{{ Math.round(segment.percent) }}%</span>
						</div>
					</div>
				</div>
			</div>
			<div class="chart-card empty" v-else>
				<div class="chart-title">情绪占比</div>
				<p class="empty-text">暂无情绪概率数据</p>
			</div>
		</div>
	</div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
	features: { type: Object, default: null }
})

const palette = ['#38bdf8', '#f472b6', '#facc15', '#34d399', '#c084fc', '#fb7185']

function buildSegments(probMap) {
	if (!probMap) return []
	const entries = Object.entries(probMap).filter(([, value]) => typeof value === 'number' && value > 0)
	const total = entries.reduce((sum, [, value]) => sum + value, 0)
	if (!total) return []

	let cursor = 0
	return entries.map(([label, value], index) => {
		const ratio = value / total
		const start = cursor * 360
		cursor += ratio
		const end = cursor * 360
		return {
			label,
			value,
			percent: ratio * 100,
			start,
			end,
			color: palette[index % palette.length]
		}
	})
}

function buildGradient(segments) {
	if (!segments.length) return 'conic-gradient(#e2e8f0 0deg, #e2e8f0 360deg)'
	const stops = segments.map(seg => `${seg.color} ${seg.start}deg ${seg.end}deg`).join(', ')
	return `conic-gradient(${stops})`
}

// 计算每个扇区中点位置，用于放置百分比标签
function segmentLabelStyle(segment) {
	if (!segment || typeof segment.percent !== 'number') {
		return { transform: 'translate(-50%, -50%)' }
	}
	// 取扇区中点角度
	const midAngle = (segment.start + segment.end) / 2
	// CSS 中 0deg 在右侧，这里减去 90deg 让 0deg 指向上方，便于视觉分布
	const rad = ((midAngle - 90) * Math.PI) / 180
	// 标签距离圆心的半径，数值基于当前图形尺寸微调
	const radius = 55
	const x = Math.cos(rad) * radius
	const y = Math.sin(rad) * radius

	return {
		transform: `translate(-50%, -50%) translate(${x}px, ${y}px)`
	}
}

const styleSegments = computed(() => buildSegments(props.features?.style_prob))
const emotionSegments = computed(() => buildSegments(props.features?.emotion_prob))

const styleGradient = computed(() => buildGradient(styleSegments.value))
const emotionGradient = computed(() => buildGradient(emotionSegments.value))

// 导出给模板使用
// eslint-disable-next-line no-unused-vars
const _segmentLabelStyle = segmentLabelStyle
</script>

<style scoped>
	.emotion-result {
		display: flex;
		flex-direction: column;
		gap: 20px;
		padding: 20px;
		background: var(--color-surface-muted);
		border-radius: var(--radius-lg);
		border: 1px solid var(--color-card-border);
		box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.7);
	}

	.header {
		display: flex;
		flex-direction: column;
		gap: 10px;
	}

	.header h3 {
		margin: 0;
		color: var(--color-text);
		font-size: 20px;
	}

	.tags {
		display: flex;
		flex-wrap: wrap;
		gap: 10px;
	}

	.tag {
		font-size: 13px;
		font-weight: 600;
		color: var(--color-text);
		background: var(--color-surface);
		border-color: var(--color-outline);
	}

	.tag.subtle {
		color: var(--color-text-muted);
	}

	.chart-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
		gap: 18px;
	}

	.chart-card {
		background: var(--color-surface);
		border-radius: var(--radius-lg);
		border: 1px solid var(--color-card-border);
		padding: 18px;
		display: flex;
		flex-direction: column;
		gap: 16px;
		box-shadow: var(--shadow-soft);
	}

	.chart-main {
		display: flex;
		align-items: center;
		gap: 18px;
	}

	.chart-card.empty {
		align-items: center;
		justify-content: center;
		min-height: 260px;
	}

	.chart-title {
		font-weight: 600;
		color: var(--color-text);
	}

	.chart-figure {
		width: 190px;
		height: 190px;
		margin: 0 auto;
		border-radius: 50%;
		background: #e2e8f0;
		display: flex;
		align-items: center;
		justify-content: center;
		position: relative;
		/* remove inner white ring to avoid white border */
		box-shadow: none;
		transition: transform 260ms cubic-bezier(.2,.9,.2,1), box-shadow 260ms ease;
		will-change: transform;
		cursor: default;
	}

	/* rotating background layer */
	.chart-figure::before {
		content: '';
		position: absolute;
		inset: 0;
		border-radius: 50%;
		background-image: var(--chart-bg);
		background-size: cover;
		background-position: center;
		z-index: 0;
		will-change: transform;
		animation: spin 8s linear infinite;
	}

	.chart-figure:hover::before {
		animation-play-state: paused;
	}

	.chart-figure:hover {
		transform: scale(1.18);
	}

	/* ensure content sits above rotating layer */
	.chart-figure > * {
		position: relative;
		z-index: 2;
	}

	@keyframes spin {
		from { transform: rotate(0deg); }
		to { transform: rotate(360deg); }
	}

	.chart-labels {
		position: absolute;
		inset: 0;
		pointer-events: none;
	}

	.chart-label {
		position: absolute;
		left: 50%;
		top: 50%;
		font-size: 11px;
		font-weight: 600;
		color: #0f172a;
		text-shadow: 0 1px 2px rgba(15, 23, 42, 0.4);
	}

	.chart-center {
		width: 74px;
		height: 74px;
		border-radius: 50%;
		background: #fff;
		display: flex;
		align-items: center;
		justify-content: center;
		font-weight: 600;
		color: var(--color-text-muted);
		box-shadow: 0 10px 25px rgba(15, 23, 42, 0.12);
	}

	.legend {
		display: flex;
		flex-direction: column;
		gap: 10px;
	}

	.legend-item {
		display: flex;
		align-items: center;
		gap: 10px;
		font-size: 14px;
		color: var(--color-text);
	}

	.dot {
		width: 10px;
		height: 10px;
		border-radius: 50%;
		box-shadow: 0 2px 6px rgba(15, 23, 42, 0.16);
	}

	.legend-label {
		flex: 1;
	}

	.legend-value {
		font-weight: 600;
	}

	.empty-text {
		color: var(--color-text-muted);
		margin: 0;
	}

	@media (max-width: 600px) {
		.chart-main {
			flex-direction: column;
			align-items: center;
		}

		.chart-figure {
			width: 150px;
			height: 150px;
		}

		.chart-center {
			width: 62px;
			height: 62px;
		}
	}
</style>
