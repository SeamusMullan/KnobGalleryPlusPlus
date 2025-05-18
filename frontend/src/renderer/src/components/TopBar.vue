<script setup lang="ts">
import { ref, computed } from 'vue'

const props = defineProps({
  isScraping: {
    type: Boolean,
    default: false
  }
})

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
