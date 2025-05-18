<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps({
  totalItems: {
    type: Number,
    default: 0
  },
  scrapeStatus: {
    type: Object,
    default: () => ({
      in_progress: false,
      total_items: 0,
      completed_items: 0,
      success: false,
      error_message: null
    })
  }
})

// Computed properties
const scrapeProgress = computed(() => {
  if (!props.scrapeStatus.total_items) return 0
  return Math.round((props.scrapeStatus.completed_items / props.scrapeStatus.total_items) * 100)
})

const statusMessage = computed(() => {
  if (props.scrapeStatus.in_progress) {
    return `Scraping gallery: ${props.scrapeStatus.completed_items}/${props.scrapeStatus.total_items}`
  }

  if (props.scrapeStatus.error_message) {
    return `Error: ${props.scrapeStatus.error_message}`
  }

  return 'Ready'
})

const statusClass = computed(() => {
  if (props.scrapeStatus.in_progress) {
    return 'syncing'
  }

  if (props.scrapeStatus.error_message) {
    return 'offline'
  }

  return 'online'
})
</script>

<template>
  <div class="status-bar">
    <div class="status-left">
      <div class="status-indicator" :class="statusClass"></div>
      <div>{{ statusMessage }}</div>
      <div v-if="scrapeStatus.in_progress" class="progress-container">
        <div class="progress-bar">
          <div class="progress-bar-inner" :style="{ width: `${scrapeProgress}%` }"></div>
        </div>
        <div>{{ scrapeProgress }}%</div>
      </div>
    </div>

    <div class="status-right">
      <div>Total knobs: {{ totalItems }}</div>
    </div>
  </div>
</template>
