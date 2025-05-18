<script setup lang="ts">
import { ref, computed } from 'vue'

const props = defineProps({
  isScraping: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['start-scraping', 'refresh'])
</script>

<template>
  <div class="top-bar">
    <h1>KnobGallery++</h1>

    <div class="top-bar-actions">
      <button class="button" @click="$emit('refresh')" :disabled="isScraping">Refresh</button>
      <button class="button" @click="$emit('start-scraping')" :disabled="isScraping">
        {{ isScraping ? 'Scraping...' : 'Scrape Gallery' }}
      </button>
    </div>
  </div>
</template>
