<template>
  <div class="app-shell">
    <Home />
    <Footer />
  </div>
</template>

<script setup>
import Home from './views/Home.vue'
import Footer from './components/Footer.vue'
</script>

<style scoped>
.app-shell {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}

.app-shell > :last-child {
  margin-top: auto;
}
</style>
