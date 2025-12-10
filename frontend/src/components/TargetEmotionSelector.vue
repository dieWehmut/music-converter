<template>
	<div class="target-emotion-selector" ref="container" :class="{ open: isOpen }" :style="triggerWidth ? { width: triggerWidth + 'px' } : undefined">
		<button
			type="button"
			class="pill-control pill-control--neutral selector-trigger"
			@keydown="onTriggerKeydown"
			@click="toggleDropdown"
			:aria-expanded="isOpen"
			aria-haspopup="listbox"
		>
			<span class="current-label">{{ currentLabel }}</span>
			<span class="chevron" aria-hidden="true"></span>
		</button>

		<transition name="fade-scale">
			<ul
				v-if="isOpen"
				class="selector-menu"
				role="listbox"
				:aria-activedescendant="activeOptionId"
			>
				<li
					v-for="(style, index) in styles"
					:key="style"
					:id="`style-option-${style}`"
					class="selector-option"
					:class="{ active: style === modelValue, hover: index === hoverIndex }"
					role="option"
					:aria-selected="style === modelValue"
					@click="selectStyle(style)"
				>
					<span>{{ style }}</span>
					<span v-if="style === modelValue" class="check" aria-hidden="true">✔</span>
				</li>
			</ul>
		</transition>
	</div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount, watch, nextTick } from 'vue'

const props = defineProps({
	styles: { type: Array, default: () => [] },
	modelValue: { type: String, default: '' },
	placeholder: { type: String, default: '选择风格' }
})

const emit = defineEmits(['update:modelValue'])

const container = ref(null)
const isOpen = ref(false)
const hoverIndex = ref(-1)

const triggerWidth = ref(null)

async function computeTriggerWidth() {
	await nextTick()
	const el = container.value
	if (!el) return
	const triggerEl = el.querySelector('.selector-trigger')
	if (!triggerEl) return
	const cs = getComputedStyle(triggerEl)
	const font = `${cs.fontWeight} ${cs.fontSize} ${cs.fontFamily}`
	const span = document.createElement('span')
	span.style.position = 'absolute'
	span.style.visibility = 'hidden'
	span.style.whiteSpace = 'nowrap'
	span.style.font = font
	document.body.appendChild(span)
	let max = 0
	const items = (props.styles && props.styles.length) ? props.styles : [currentLabel.value]
	const padLeft = parseFloat(cs.paddingLeft) || 16
	const padRight = parseFloat(cs.paddingRight) || 16
	for (const s of items) {
		span.textContent = s
		const w = span.offsetWidth
		if (w > max) max = w
	}
	document.body.removeChild(span)
	const chevronWidth = 28 // include spacing for chevron and some gap
	const extra = padLeft + padRight + chevronWidth + 8
	const computedWidth = Math.ceil(max + extra)
	// enforce sensible min/max so it doesn't become too wide
	const MIN_W = 120
	const MAX_W = 260
	triggerWidth.value = Math.min(MAX_W, Math.max(MIN_W, computedWidth))
}

function handleResize() {
	computeTriggerWidth()
}

const modelValue = computed(() => props.modelValue)
const currentLabel = computed(() => modelValue.value || props.styles[0] || props.placeholder)
const activeOptionId = computed(() => (modelValue.value ? `style-option-${modelValue.value}` : undefined))

function toggleDropdown() {
	isOpen.value = !isOpen.value
	if (isOpen.value) {
		setHoverIndexByValue(modelValue.value)
	}
}

function closeDropdown() {
	isOpen.value = false
}

function selectStyle(value) {
	emit('update:modelValue', value)
	closeDropdown()
}

function setHoverIndexByValue(value) {
	if (!props.styles.length) {
		hoverIndex.value = -1
		return
	}
	const idx = props.styles.indexOf(value)
	hoverIndex.value = idx >= 0 ? idx : 0
}

function onTriggerKeydown(event) {
	if (!isOpen.value && (event.key === 'ArrowDown' || event.key === 'Enter' || event.key === ' ')) {
		event.preventDefault()
		isOpen.value = true
		setHoverIndexByValue(modelValue.value)
		return
	}

	if (!isOpen.value) return

	switch (event.key) {
		case 'ArrowDown':
			if (hoverIndex.value < props.styles.length - 1) hoverIndex.value++
			event.preventDefault()
			break
		case 'ArrowUp':
			if (hoverIndex.value > 0) hoverIndex.value--
			event.preventDefault()
			break
		case 'Enter':
		case ' ': {
			const option = props.styles[hoverIndex.value]
			if (option) selectStyle(option)
			event.preventDefault()
			break
		}
		case 'Escape':
			closeDropdown()
			event.preventDefault()
			break
	}
}

function handleClickOutside(event) {
	if (container.value && !container.value.contains(event.target)) {
		closeDropdown()
	}
}

onMounted(() => {
	document.addEventListener('click', handleClickOutside)
	computeTriggerWidth()
	window.addEventListener('resize', handleResize)
})

onBeforeUnmount(() => {
	document.removeEventListener('click', handleClickOutside)
	window.removeEventListener('resize', handleResize)
})

watch(
	() => props.modelValue,
	value => {
		setHoverIndexByValue(value)
	}
)

watch(() => props.styles, () => computeTriggerWidth(), { deep: true })
</script>

<style scoped>
.target-emotion-selector {
	position: relative;
	display: inline-flex;
	flex-direction: column;
	width: auto; /* let inline style or content decide */
	min-width: 120px;
	z-index: 20;
}

.selector-trigger {
	width: 100%;
	display: inline-flex;
	align-items: center;
	justify-content: center;
	position: relative;
	padding: 0 16px;
	height: 40px;
	background: linear-gradient(120deg, rgba(99, 102, 241, 0.08), rgba(59, 130, 246, 0.12));
	border: 1px solid rgba(15, 23, 42, 0.14);
	color: var(--color-text);
	border-radius: 12px;
	transition: all 0.2s ease;
	z-index: 2;
}

.target-emotion-selector.open .selector-trigger {
	background: #fff;
	border-radius: 16px 16px 0 0;
	border-bottom-color: transparent;
	box-shadow: 0 4px 12px rgba(15, 23, 42, 0.05);
}

.selector-trigger:focus-visible {
	outline: none;
	box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.2);
}

.current-label {
	font-weight: 600;
	font-size: 15px;
	position: absolute;
	left: 50%;
	transform: translateX(-50%);
	text-align: center;
	max-width: calc(100% - 44px);
	overflow: hidden;
	text-overflow: ellipsis;
	white-space: nowrap;
}

.chevron {
	width: 8px;
	height: 8px;
	border-left: 2px solid var(--color-text-muted);
	border-bottom: 2px solid var(--color-text-muted);
	transform: rotate(-45deg);
	transition: transform 0.2s ease;
	margin-top: -2px;
	position: absolute;
	right: 12px;
}

.target-emotion-selector.open .chevron {
	transform: rotate(135deg);
	margin-top: 2px;
}

.selector-menu {
	position: absolute;
	top: 100%;
	left: 0;
	width: 100%;
	margin: 0;
	margin-top: -1px;
	padding: 4px 0 8px;
	list-style: none;
	background: #fff;
	border-radius: 0 0 16px 16px;
	box-shadow: 0 10px 25px -5px rgba(15, 23, 42, 0.15), 0 8px 10px -6px rgba(15, 23, 42, 0.1);
	border: 1px solid rgba(15, 23, 42, 0.14);
	border-top: none;
	z-index: 1;
	overflow: hidden;
}

.selector-option {
	display: flex;
	align-items: center;
	justify-content: center; /* center the option text */
	position: relative;
	padding: 10px 16px;
	font-size: 15px;
	font-weight: 500;
	color: var(--color-text);
	cursor: pointer;
	transition: background 0.1s ease;
}

.selector-option:hover,
.selector-option.hover {
	background: rgba(37, 99, 235, 0.06);
	color: #1d4ed8;
}

.selector-option.active {
	color: #1d4ed8;
	font-weight: 600;
	background: rgba(37, 99, 235, 0.04);
}

.check {
	font-size: 12px;
	color: #1d4ed8;
	font-weight: bold;
	position: absolute;
	right: 12px;
}

.fade-scale-enter-active,
.fade-scale-leave-active {
	transition: opacity 0.2s ease, transform 0.2s ease;
}

.fade-scale-enter-from,
.fade-scale-leave-to {
	opacity: 0;
	transform: translateY(-10px);
}
</style>
