<script setup lang="ts">
import { ref } from 'vue'

const props = defineProps({
  isScraping: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['start-scraping', 'refresh', 'download-thumbnails', 'open-settings'])

const showSettings = () => {
  emit('open-settings')
}
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
      <button class="button settings-button" @click="showSettings">
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <circle cx="12" cy="12" r="3"></circle>
          <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path>
        </svg>
        Settings
      </button>
    </div>
  </div>
</template>

<style scoped>
.settings-button {
  display: flex;
  align-items: center;
  gap: 6px;
}
</style>
