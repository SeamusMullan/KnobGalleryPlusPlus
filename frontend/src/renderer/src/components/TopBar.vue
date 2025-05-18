<script setup lang="ts">
// eslint-disable-next-line @typescript-eslint/no-unused-vars
import { ref, computed } from 'vue'

// eslint-disable-next-line @typescript-eslint/no-unused-vars
const props = defineProps({
  isScraping: {
    type: Boolean,
    default: false
  }
})

// eslint-disable-next-line @typescript-eslint/no-unused-vars
const emit = defineEmits(['start-scraping', 'refresh', 'download-thumbnails'])
</script>

<template>
  <div class="top-bar">
    <h1>KnobGallery++</h1>

    <div class="top-bar-actions">
      <button class="button" :disabled="isScraping" @click="$emit('refresh')">Refresh</button>
      <button class="button" :disabled="isScraping" @click="$emit('start-scraping')">
        {{ isScraping ? 'Scraping...' : 'Scrape Gallery' }}
      </button>
      <button class="button" :disabled="isScraping" @click="$emit('download-thumbnails')">
        Download All Thumbnails
      </button>
    </div>
  </div>
</template>
