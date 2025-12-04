<template>
	<footer class="footer">
		<div class="survival-time">
			Uptime:
			<span class="time-number">{{ time.days }}</span>d
			<span class="time-number">{{ time.hours }}</span>h
			<span class="time-number">{{ time.minutes }}</span>m
			<span class="time-number">{{ time.seconds }}</span>s
			<svg class="uptime-icon" viewBox="0 0 24 24" aria-hidden="true">
				<path d="M12 2a10 10 0 100 20 10 10 0 000-20zm1 11H7a1 1 0 110-2h5V6a1 1 0 112 0v7z" />
			</svg>
		</div>

		<div class="hub-buttons">
			<a
				href="https://github.com/dieWehmut/music-converter"
				target="_blank"
				rel="noopener"
				class="hub-button x"
				title="AI 导论项目 GitHub 仓库"
			>
				<svg viewBox="0 0 24 24" class="social-icon" aria-hidden="true">
					<path d="M12 .296a12 12 0 00-3.797 23.4c.6.11.82-.26.82-.577 0-.285-.01-1.04-.016-2.04-3.338.726-4.042-1.61-4.042-1.61-.546-1.385-1.333-1.755-1.333-1.755-1.09-.745.083-.73.083-.73 1.205.085 1.84 1.237 1.84 1.237 1.07 1.835 2.807 1.305 3.492.998.108-.775.418-1.305.762-1.605-2.665-.305-5.466-1.335-5.466-5.93 0-1.31.468-2.38 1.236-3.22-.124-.304-.536-1.527.117-3.183 0 0 1.008-.322 3.3 1.23a11.5 11.5 0 016 0c2.29-1.552 3.297-1.23 3.297-1.23.655 1.656.243 2.879.12 3.183.77.84 1.235 1.91 1.235 3.22 0 4.61-2.803 5.62-5.475 5.92.43.37.814 1.096.814 2.21 0 1.595-.014 2.88-.014 3.275 0 .32.216.694.825.576A12 12 0 0012 .296z" />
				</svg>
			</a>
		</div>
	</footer>
</template>

<script setup>
import { onBeforeUnmount, onMounted, reactive } from 'vue'

const startAt = new Date('2025-11-13T16:00:00+08:00').getTime()

const time = reactive({
	days: '0',
	hours: '00',
	minutes: '00',
	seconds: '00'
})

let timer = null

function tick() {
	const now = Date.now()
	let diff = Math.max(0, Math.floor((now - startAt) / 1000))

	const days = Math.floor(diff / 86400)
	diff -= days * 86400
	const hours = Math.floor(diff / 3600)
	diff -= hours * 3600
	const minutes = Math.floor(diff / 60)
	const seconds = diff - minutes * 60

	time.days = String(days)
	time.hours = String(hours).padStart(2, '0')
	time.minutes = String(minutes).padStart(2, '0')
	time.seconds = String(seconds).padStart(2, '0')
}

onMounted(() => {
	tick()
	timer = setInterval(tick, 1000)
})

onBeforeUnmount(() => {
	if (timer) {
		clearInterval(timer)
		timer = null
	}
})
</script>

<style scoped>
.footer {
	max-width: 1080px;
	margin: 0 auto;
	padding: 18px 12px 28px;
	text-align: center;
	background: transparent;
}

.survival-time {
	margin-bottom: 12px;
	color: #000;
}

.time-number {
	font-weight: 700;
	padding: 0 4px;
}

.hub-buttons {
	display: flex;
	gap: 10px;
	align-items: center;
	justify-content: center;
}

.hub-button {
	width: 44px;
	height: 44px;
	border-radius: 8px;
	display: inline-flex;
	align-items: center;
	justify-content: center;
	transition: all 0.2s ease;
	background: transparent;
  border: none;
}

.hub-button.x:hover {
	background-color: #000;
	border-color: #000;
}

.hub-button .social-icon {
	width: 24px;
	height: 24px;
	fill: #000;
	transition: transform 0.12s ease, fill 0.12s ease;
	animation: float 6s ease-in-out infinite;
}

.hub-button:hover .social-icon {
	fill: #fff;
	transform: translateY(-1px) scale(1.05);
}

.uptime-icon {
	width: 16px;
	height: 16px;
	fill: rgba(255, 255, 255, 0.95);
	vertical-align: middle;
	margin-left: 6px;
}

@keyframes float {
	0% {
		transform: translateY(0);
	}
	50% {
		transform: translateY(-6px);
	}
	100% {
		transform: translateY(0);
	}
}

@media (prefers-reduced-motion: reduce) {
	.hub-button .social-icon {
		animation: none;
	}
}
</style>
