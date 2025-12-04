<template>
	<div class="target-emotion-selector" ref="container" :class="{ open: isOpen }">
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
import { ref, computed, onMounted, onBeforeUnmount, watch } from 'vue'

const props = defineProps({
	styles: { type: Array, default: () => [] },
	modelValue: { type: String, default: '' }
})

const emit = defineEmits(['update:modelValue'])

const container = ref(null)
const isOpen = ref(false)
const hoverIndex = ref(-1)

const modelValue = computed(() => props.modelValue)
const currentLabel = computed(() => modelValue.value || props.styles[0] || '选择风格')
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
})

onBeforeUnmount(() => {
	document.removeEventListener('click', handleClickOutside)
})

watch(
	() => props.modelValue,
	value => {
		setHoverIndexByValue(value)
	}
)
</script>

<style scoped>
.target-emotion-selector {
	position: relative;
	display: inline-flex;
	flex-direction: column;
}

	.selector-trigger {
		width: 130px;
		display: inline-flex;
		justify-content: center;
		position: relative;
		padding-right: 38px;
		padding-left: 20px;
	background: linear-gradient(120deg, rgba(99, 102, 241, 0.08), rgba(59, 130, 246, 0.12));
	border: 1.5px solid rgba(15, 23, 42, 0.14);
	color: var(--color-text);
}

.selector-trigger:focus-visible {
	outline: none;
	box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.2);
}

.chevron {
	width: 10px;
	height: 10px;
	border-left: 2px solid var(--color-text);
	border-bottom: 2px solid var(--color-text);
	transform: rotate(-45deg);
	position: absolute;
	right: 16px;
	top: 50%;
	transform-origin: center;
	translate: 0 -50%;
}

.target-emotion-selector.open .chevron {
	transform: rotate(135deg);
}

	.selector-menu {
	position: absolute;
	top: calc(100% + 6px);
	left: 0;
	min-width: 150px;
	width: max-content;
	max-width: 220px;
	margin: 0;
	padding: 6px 0;
	list-style: none;
	background: #fff;
	border-radius: 14px;
	box-shadow: 0 20px 40px rgba(15, 23, 42, 0.18);
	border: 1px solid rgba(15, 23, 42, 0.08);
	z-index: 20;
}

.selector-option {
	display: flex;
	align-items: center;
	justify-content: space-between;
	padding: 10px 16px;
	font-weight: 500;
	color: var(--color-text);
	cursor: pointer;
}

.selector-option.hover {
	background: rgba(37, 99, 235, 0.08);
}

.selector-option.active {
	color: #1d4ed8;
	font-weight: 600;
}

.check {
	font-size: 12px;
	color: #1d4ed8;
}

.fade-scale-enter-active,
.fade-scale-leave-active {
	transition: opacity 0.15s ease, transform 0.15s ease;
}

.fade-scale-enter-from,
.fade-scale-leave-to {
	opacity: 0;
	transform: translateY(-4px);
}
</style>
