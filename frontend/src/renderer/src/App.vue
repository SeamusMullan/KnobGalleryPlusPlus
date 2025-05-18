<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import KnobGallery from './components/KnobGallery.vue'
import KnobPreview from './components/KnobPreview.vue'
import TopBar from './components/TopBar.vue'
import StatusBar from './components/StatusBar.vue'

// API base URL
const API_BASE_URL = 'http://localhost:8000'

// App state

const loading = ref(false)
const error = ref<string | null>(null)
const knobs = ref<unknown[]>([])
const selectedKnob = ref<unknown | null>(null)
const scrapeStatus = ref<unknown>({
  in_progress: false,
  total_items: 0,
  completed_items: 0,
  success: false,
  error_message: null
})
const page = ref(1)
const totalPages = ref(1)
const totalItems = ref(0)
const downloadInProgress = ref(false)

// Computed properties
const isScrapingInProgress = computed(() => scrapeStatus.value.in_progress)

// Methods
const fetchKnobs = async (pageNum = 1): Promise<void> => {
  loading.value = true
  error.value = null

  try {
    const response = await fetch(`${API_BASE_URL}/data/knobs?page=${pageNum}&limit=50`)
    if (!response.ok) {
      throw new Error(`Failed to fetch knobs: ${response.statusText}`)
    }

    const data = await response.json()
    knobs.value = data.knobs
    page.value = data.page
    totalPages.value = data.total_pages
    totalItems.value = data.total
  } catch (err) {
    error.value = err.message
    console.error('Error fetching knobs:', err)
  } finally {
    loading.value = false
  }
}

const checkScrapeStatus = async (): Promise<void> => {
  try {
    const response = await fetch(`${API_BASE_URL}/data/scrape/status`)
    if (!response.ok) {
      throw new Error(`Failed to fetch scrape status: ${response.statusText}`)
    }

    scrapeStatus.value = await response.json()

    // Continue checking if scraping is in progress
    if (scrapeStatus.value.in_progress) {
      setTimeout(checkScrapeStatus, 2000)
    } else if (scrapeStatus.value.success) {
      // If scraping completed successfully, refresh knobs
      await fetchKnobs()
    }
  } catch (err) {
    console.error('Error checking scrape status:', err)
  }
}

const startScraping = async (): Promise<void> => {
  try {
    const response = await fetch(`${API_BASE_URL}/data/scrape`, {
      method: 'POST'
    })

    if (!response.ok) {
      throw new Error(`Failed to start scraping: ${response.statusText}`)
    }

    const data = await response.json()
    scrapeStatus.value = data.status

    // Start polling for status updates
    setTimeout(checkScrapeStatus, 2000)
  } catch (err) {
    error.value = err.message
    console.error('Error starting scrape:', err)
  }
}

const downloadKnob = async (knobId: number): Promise<void> => {
  downloadInProgress.value = true
  try {
    const response = await fetch(`${API_BASE_URL}/data/knobs/${knobId}/download`, {
      method: 'POST'
    })

    if (!response.ok) {
      throw new Error(`Failed to download knob: ${response.statusText}`)
    }

    // Refresh the selected knob to update download status
    if (selectedKnob.value && selectedKnob.value.id === knobId) {
      await selectKnob(knobId)
    }

    return await response.json()
  } catch (err) {
    console.error('Error downloading knob:', err)
    return { error: err.message }
  } finally {
    downloadInProgress.value = false
  }
}

const selectKnob = async (knobId: number): Promise<void> => {
  try {
    const response = await fetch(`${API_BASE_URL}/data/preview/${knobId}`)
    if (!response.ok) {
      throw new Error(`Failed to get knob preview: ${response.statusText}`)
    }

    const data = await response.json()
    selectedKnob.value = data.knob
  } catch (err) {
    console.error('Error selecting knob:', err)
  }
}

// Download all thumbnails
const downloadAllThumbnails = async (): Promise<void> => {
  try {
    const response = await fetch(`${API_BASE_URL}/data/thumbnails/download`, {
      method: 'POST'
    })

    if (!response.ok) {
      throw new Error(`Failed to start thumbnail download: ${response.statusText}`)
    }

    const data = await response.json()
    console.log('Started downloading thumbnails:', data.message)
  } catch (err) {
    error.value = err.message
    console.error('Error downloading thumbnails:', err)
  }
}

// Initialize
onMounted(async () => {
  await fetchKnobs()
  await checkScrapeStatus()
})
</script>

<template>
  <div class="app-container">
    <TopBar
      :is-scraping="isScrapingInProgress"
      @start-scraping="startScraping"
      @refresh="fetchKnobs"
      @download-thumbnails="downloadAllThumbnails"
    />

    <div class="main-content">
      <div v-if="loading" class="loading">Loading knobs...</div>
      <div v-else-if="error" class="error">
        {{ error }}
      </div>
      <div v-else class="gallery-container">
        <KnobGallery
          :knobs="knobs"
          :current-page="page"
          :total-pages="totalPages"
          @select-knob="selectKnob"
          @page-change="fetchKnobs"
        />

        <KnobPreview v-if="selectedKnob" :knob="selectedKnob" :download-in-progress="downloadInProgress" @download="downloadKnob" />
      </div>
    </div>

    <StatusBar :total-items="totalItems" :scrape-status="scrapeStatus" />
  </div>
</template>
