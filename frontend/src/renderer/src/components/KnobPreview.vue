<script setup lang="ts">
import { computed } from 'vue'

// Define the Knob interface based on the backend model
interface Knob {
  id: number
  file: string
  author?: string
  license: string
  date: string
  comment?: string
  tags?: string
  size?: string
  thumbnail_url?: string
  download_url?: string
  local_path?: string
  local_thumbnail_path?: string
  downloaded?: boolean
}

const props = defineProps({
  knob: {
    type: Object as () => Knob,
    required: true
  },
  downloadInProgress: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['download'])

// Open folder for the knob file
const openFolder = (): void => {
  if (props.knob.local_path && window.api?.openFolder) {
    window.api.openFolder(props.knob.local_path)
  }
}

const downloadKnob = (): void => {
  emit('download', props.knob.id)
}

// Format license for display
const formatLicense = (license: string): string => {
  return license.replace(/-/g, ' ').replace('_', '.')
}

// Handle image loading errors
const onImageError = (event: Event): void => {
  // When local image fails to load, try the original source
  const img = event.target as HTMLImageElement

  // Set up a counter to prevent infinite loops with onerror handlers
  let attemptCount = 0
  const maxAttempts = 2

  const tryFallback = (): void => {
    attemptCount++
    if (attemptCount > maxAttempts) {
      // If we've tried too many times, use the placeholder
      img.src =
        'data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="200" height="200" viewBox="0 0 200 200"><rect width="200" height="200" fill="#eee"/><text x="50%" y="50%" dominant-baseline="middle" text-anchor="middle" font-family="sans-serif" font-size="14px" fill="#999">Image Not Available</text></svg>'
      img.onerror = null // Prevent any further error handling
      return
    }

    if (attemptCount === 1 && props.knob.thumbnail_url) {
      // First try the thumbnail URL from the API
      console.log(
        `Attempt ${attemptCount}: Using fallback image from API for knob ${props.knob.id}: ${props.knob.thumbnail_url}`
      )
      img.onerror = tryFallback // Set up for next attempt
      img.src = props.knob.thumbnail_url
    } else {
      // Second attempt, try the constructed URL
      const fallbackUrl = `https://www.g200kg.com/en/webknobman/img/${props.knob.file}.png`
      console.log(
        `Attempt ${attemptCount}: Using constructed fallback for knob ${props.knob.id}: ${fallbackUrl}`
      )
      img.onerror = tryFallback // Set up for final attempt
      img.src = fallbackUrl
    }
  }

  // Start the fallback process
  tryFallback()
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
      <img
        :key="`knob-preview-${knob.id}`"
        :src="`http://localhost:8000/static/thumbnails/${knob.id}.png?v=${Date.now()}`"
        :alt="knob.file"
        @error="onImageError"
      />
    </div>

    <button
      v-if="isDownloaded && knob.local_path"
      class="button"
      style="margin-bottom: 10px"
      @click="openFolder"
    >
      Open Folder
    </button>

    <button class="button" :disabled="isDownloaded || downloadInProgress" @click="downloadKnob">
      <span v-if="downloadInProgress && !isDownloaded">
        <svg
          width="18"
          height="18"
          viewBox="0 0 50 50"
          style="vertical-align: middle; margin-right: 6px"
        >
          <circle
            cx="25"
            cy="25"
            r="20"
            fill="none"
            stroke="#fff"
            stroke-width="5"
            stroke-linecap="round"
            stroke-dasharray="31.415, 31.415"
            transform="rotate(72.0001 25 25)"
          >
            <animateTransform
              attributeName="transform"
              type="rotate"
              from="0 25 25"
              to="360 25 25"
              dur="0.8s"
              repeatCount="indefinite"
            />
          </circle>
        </svg>
        Downloading...
      </span>
      <span v-else>
        {{ isDownloaded ? 'Downloaded' : 'Download Knob File' }}
      </span>
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
