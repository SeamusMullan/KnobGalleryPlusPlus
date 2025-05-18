<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps({
  knob: {
    type: Object,
    required: true
  }
})

const emit = defineEmits(['download'])

const downloadKnob = (): void => {
  emit('download', props.knob.id)
}

// Format license for display
const formatLicense = (license: string): string => {
  return license.replace(/-/g, ' ').replace('_', '.')
}

// Determine if a file is downloaded
const isDownloaded = computed(() => {
  return props.knob.downloaded && props.knob.local_path
})
</script>

<template>
  <div class="knob-preview">
    <div class="preview-header">
      <h2>{{ knob.file }}</h2>
    </div>

    <div class="preview-image">
      <img :src="`http://localhost:8000/static/thumbnails/${knob.id}.png`" :alt="knob.file" />
    </div>

    <button class="button" :disabled="isDownloaded" @click="downloadKnob">
      {{ isDownloaded ? 'Downloaded' : 'Download Knob File' }}
    </button>

    <div class="preview-details">
      <div class="detail-row">
        <div class="detail-label">Author</div>
        <div class="detail-value">{{ knob.author || 'Unknown' }}</div>
      </div>

      <div class="detail-row">
        <div class="detail-label">License</div>
        <div class="detail-value">
          <span class="license-badge">{{ formatLicense(knob.license) }}</span>
        </div>
      </div>

      <div class="detail-row">
        <div class="detail-label">Date</div>
        <div class="detail-value">{{ knob.date }}</div>
      </div>

      <div class="detail-row">
        <div class="detail-label">Size</div>
        <div class="detail-value">{{ knob.size || 'Unknown' }}</div>
      </div>

      <div v-if="knob.tags" class="detail-row">
        <div class="detail-label">Tags</div>
        <div class="detail-value">{{ knob.tags }}</div>
      </div>

      <div v-if="knob.comment" class="detail-row">
        <div class="detail-label">Comment</div>
        <div class="detail-value">{{ knob.comment }}</div>
      </div>

      <div v-if="knob.downloaded" class="detail-row">
        <div class="detail-label">Local Path</div>
        <div class="detail-value">{{ knob.local_path }}</div>
      </div>
    </div>
  </div>
</template>
