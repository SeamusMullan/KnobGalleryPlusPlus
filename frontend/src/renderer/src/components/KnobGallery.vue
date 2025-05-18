<script setup lang="ts">
import { ref, computed } from 'vue'

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
  knobs: {
    type: Array as () => Knob[],
    required: true
  },
  currentPage: {
    type: Number,
    default: 1
  },
  totalPages: {
    type: Number,
    default: 1
  }
})

const emit = defineEmits(['select-knob', 'page-change'])

const selectedKnobId = ref<number | null>(null)

const selectKnob = (knobId: number): void => {
  selectedKnobId.value = knobId
  emit('select-knob', knobId)
}

const goToPage = (page: number): void => {
  if (page < 1 || page > props.totalPages) return
  emit('page-change', page)
}

const onImageError = (event: Event, knob: Knob): void => {
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
        'data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100" viewBox="0 0 100 100"><rect width="100" height="100" fill="#eee"/><text x="50%" y="50%" dominant-baseline="middle" text-anchor="middle" font-family="sans-serif" font-size="14px" fill="#999">No Image</text></svg>'
      img.onerror = null // Prevent any further error handling
      return
    }

    if (attemptCount === 1 && knob.thumbnail_url) {
      // First try the thumbnail URL from the API
      console.log(
        `Attempt ${attemptCount}: Using fallback image from API for knob ${knob.id}: ${knob.thumbnail_url}`
      )
      img.onerror = tryFallback // Set up for next attempt
      img.src = knob.thumbnail_url
    } else {
      // Second attempt, try the constructed URL
      const fallbackUrl = `https://www.g200kg.com/en/webknobman/img/${knob.file}.png`
      console.log(
        `Attempt ${attemptCount}: Using constructed fallback for knob ${knob.id}: ${fallbackUrl}`
      )
      img.onerror = tryFallback // Set up for final attempt
      img.src = fallbackUrl
    }
  }

  // Start the fallback process
  tryFallback()
}

const paginationItems = computed(() => {
  const items = []
  const currentPage = props.currentPage
  const totalPages = props.totalPages

  // Always show first page
  items.push(1)

  if (currentPage > 3) {
    items.push('...')
  }

  // Pages around current page
  for (let i = Math.max(2, currentPage - 1); i <= Math.min(totalPages - 1, currentPage + 1); i++) {
    items.push(i)
  }

  if (currentPage < totalPages - 2) {
    items.push('...')
  }

  // Always show last page if there is more than one page
  if (totalPages > 1) {
    items.push(totalPages)
  }

  return items
})
</script>

<template>
  <div class="knob-gallery-container">
    <div class="knob-gallery">
      <div
        v-for="knob in knobs"
        :key="knob.id"
        class="knob-card"
        :class="{ selected: selectedKnobId === knob.id }"
        @click="selectKnob(knob.id)"
      >
        <div class="knob-thumbnail">
          <img
            :key="`knob-gallery-${knob.id}`"
            :src="`http://localhost:8000/static/thumbnails/${knob.id}.png`"
            :alt="knob.file"
            @error="onImageError($event, knob)"
          />
        </div>
        <div class="knob-info">
          <h3 class="knob-name">{{ knob.file }}</h3>
          <p v-if="knob.author" class="knob-author">by {{ knob.author }}</p>
        </div>
      </div>
    </div>

    <div v-if="totalPages > 1" class="pagination">
      <button class="page-button" :disabled="currentPage === 1" @click="goToPage(currentPage - 1)">
        &laquo;
      </button>

      <template v-for="(item, index) in paginationItems">
        <button
          v-if="typeof item === 'number'"
          :key="`page-btn-${item}-${index}`"
          class="page-button"
          :class="{ 'current-page': item === currentPage }"
          @click="goToPage(item)"
        >
          {{ item }}
        </button>
        <span v-else :key="`ellipsis-${index}`" class="pagination-ellipsis">{{ item }}</span>
      </template>

      <button
        class="page-button"
        :disabled="currentPage === totalPages"
        @click="goToPage(currentPage + 1)"
      >
        &raquo;
      </button>
    </div>
  </div>
</template>
