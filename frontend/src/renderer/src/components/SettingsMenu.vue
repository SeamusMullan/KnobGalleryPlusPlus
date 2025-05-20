<template>
  <div class="settings-modal" v-if="isVisible">
    <div class="settings-content">
      <div class="settings-header">
        <h2>Settings</h2>
        <button class="close-button" @click="close">×</button>
      </div>

      <div class="settings-body">
        <div class="settings-group">
          <h3>Storage</h3>

          <div class="setting-item">
            <label for="downloadDir">Download Directory</label>
            <div class="dir-input">
              <input
                type="text"
                id="downloadDir"
                v-model="localSettings.download_dir"
                :disabled="isLoading"
              />
              <button class="button browse-btn" @click="browseFolder" :disabled="isLoading">
                Browse...
              </button>
            </div>
          </div>
        </div>

        <div class="settings-group">
          <h3>Download Settings</h3>

          <div class="setting-item">
            <label for="maxWorkers">Max Download Workers</label>
            <input
              type="number"
              id="maxWorkers"
              v-model.number="localSettings.max_download_workers"
              :disabled="isLoading"
              min="1"
            />
            <div class="setting-description">
              Number of worker threads for downloads (recommended:
              {{ defaultSettings.max_download_workers }})
            </div>
          </div>

          <div class="setting-item">
            <label for="maxConcurrent">Max Concurrent Downloads</label>
            <input
              type="number"
              id="maxConcurrent"
              v-model.number="localSettings.max_concurrent_downloads"
              :disabled="isLoading"
              min="1"
            />
            <div class="setting-description">
              Maximum number of concurrent downloads (recommended:
              {{ defaultSettings.max_concurrent_downloads }})
            </div>
          </div>

          <div class="setting-item">
            <label for="batchSize">Download Batch Size</label>
            <input
              type="number"
              id="batchSize"
              v-model.number="localSettings.download_batch_size"
              :disabled="isLoading"
              min="1"
            />
            <div class="setting-description">
              Number of knobs to download in each batch (recommended:
              {{ defaultSettings.download_batch_size }})
            </div>
          </div>

          <div class="setting-item">
            <label for="retryAttempts">Download Retry Attempts</label>
            <input
              type="number"
              id="retryAttempts"
              v-model.number="localSettings.download_retry_attempts"
              :disabled="isLoading"
              min="0"
            />
            <div class="setting-description">
              Number of retry attempts for failed downloads (recommended:
              {{ defaultSettings.download_retry_attempts }})
            </div>
          </div>
        </div>
      </div>

      <div class="settings-footer">
        <button class="button secondary" @click="resetToDefaults" :disabled="isLoading">
          Reset to Defaults
        </button>

        <div class="action-buttons">
          <button class="button" @click="close">Cancel</button>
          <button class="button primary" @click="saveSettings" :disabled="isLoading || !hasChanges">
            <span v-if="isLoading">
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
                  stroke="currentColor"
                  stroke-width="5"
                  stroke-dasharray="30 90"
                  transform="rotate(0 25 25)"
                >
                  <animateTransform
                    attributeName="transform"
                    attributeType="XML"
                    type="rotate"
                    dur="1s"
                    from="0 25 25"
                    to="360 25 25"
                    repeatCount="indefinite"
                  />
                </circle>
              </svg>
              Saving...
            </span>
            <span v-else>Save Changes</span>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue'

// API base URL
const API_BASE_URL = 'http://localhost:8000'

const props = defineProps({
  isVisible: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['close', 'settings-saved'])

// State
const isLoading = ref(false)
const localSettings = ref({
  download_dir: '',
  max_download_workers: 0,
  max_concurrent_downloads: 0,
  download_batch_size: 0,
  download_retry_attempts: 0
})
const currentSettings = ref({
  download_dir: '',
  max_download_workers: 0,
  max_concurrent_downloads: 0,
  download_batch_size: 0,
  download_retry_attempts: 0
})
const defaultSettings = ref({
  download_dir: '',
  max_download_workers: 0,
  max_concurrent_downloads: 0,
  download_batch_size: 0,
  download_retry_attempts: 0
})
const error = ref<string | null>(null)

// Computed properties
const hasChanges = computed(() => {
  return JSON.stringify(localSettings.value) !== JSON.stringify(currentSettings.value)
})

// Methods
const loadSettings = async () => {
  isLoading.value = true
  error.value = null

  try {
    // Load current settings
    const response = await fetch(`${API_BASE_URL}/settings/`)
    if (!response.ok) {
      throw new Error(`Failed to fetch settings: ${response.statusText}`)
    }

    const data = await response.json()
    currentSettings.value = { ...data }
    localSettings.value = { ...data }

    // Load default settings
    const defaultsResponse = await fetch(`${API_BASE_URL}/settings/defaults`)
    if (!defaultsResponse.ok) {
      throw new Error(`Failed to fetch default settings: ${defaultsResponse.statusText}`)
    }

    defaultSettings.value = await defaultsResponse.json()
  } catch (err) {
    error.value = err.message
    console.error('Error loading settings:', err)
  } finally {
    isLoading.value = false
  }
}

const saveSettings = async () => {
  isLoading.value = true
  error.value = null

  try {
    const response = await fetch(`${API_BASE_URL}/settings/update`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(localSettings.value)
    })

    if (!response.ok) {
      throw new Error(`Failed to update settings: ${response.statusText}`)
    }

    // Update current settings with response data
    const updatedSettings = await response.json()
    currentSettings.value = { ...updatedSettings }
    localSettings.value = { ...updatedSettings }

    emit('settings-saved', updatedSettings)
    close()
  } catch (err) {
    error.value = err.message
    console.error('Error saving settings:', err)
  } finally {
    isLoading.value = false
  }
}

const resetToDefaults = () => {
  localSettings.value = { ...defaultSettings.value }
}

const browseFolder = async () => {
  if (window.api?.selectDirectory) {
    try {
      const selectedPath = await window.api.selectDirectory()
      if (selectedPath) {
        localSettings.value.download_dir = selectedPath
      }
    } catch (err) {
      console.error('Error selecting directory:', err)
    }
  } else {
    console.warn('Directory selection is not available in this environment')
  }
}

const close = () => {
  emit('close')
}

// Load settings when the component becomes visible
watch(
  () => props.isVisible,
  (isVisible) => {
    if (isVisible) {
      loadSettings()
    }
  }
)

// Initial load
onMounted(() => {
  if (props.isVisible) {
    loadSettings()
  }
})
</script>

<style>
.settings-modal {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
}

.settings-content {
  background-color: var(--color-background);
  width: 600px;
  max-width: 90%;
  max-height: 90%;
  border-radius: 8px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.settings-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  border-bottom: 1px solid var(--color-border);
}

.settings-header h2 {
  margin: 0;
  font-size: 1.5rem;
}

.close-button {
  background: none;
  border: none;
  font-size: 24px;
  cursor: pointer;
  color: var(--color-text);
  opacity: 0.7;
}

.close-button:hover {
  opacity: 1;
}

.settings-body {
  padding: 20px;
  overflow-y: auto;
  flex: 1;
}

.settings-footer {
  padding: 15px 20px;
  border-top: 1px solid var(--color-border);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.action-buttons {
  display: flex;
  gap: 10px;
}

.settings-group {
  margin-bottom: 25px;
}

.settings-group h3 {
  margin-top: 0;
  margin-bottom: 15px;
  font-size: 1.1rem;
  color: var(--color-heading);
  font-weight: 600;
}

.setting-item {
  margin-bottom: 15px;
}

.setting-item label {
  display: block;
  margin-bottom: 5px;
  font-weight: 500;
}

.setting-description {
  margin-top: 5px;
  font-size: 0.9rem;
  color: var(--color-text-light);
}

.setting-item input[type='text'],
.setting-item input[type='number'] {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid var(--color-border);
  border-radius: 4px;
  background-color: var(--color-background-soft);
  color: var(--color-text);
}

.dir-input {
  display: flex;
  gap: 8px;
}

.dir-input input[type='text'] {
  flex: 1;
}

.browse-btn {
  white-space: nowrap;
}

button.button {
  padding: 8px 16px;
  border-radius: 4px;
  cursor: pointer;
  font-weight: 500;
  transition: background-color 0.2s;
  background-color: var(--color-background-soft);
  color: var(--color-text);
  border: 1px solid var(--color-border);
}

button.button:hover:not(:disabled) {
  background-color: var(--color-background-mute);
}

button.button.primary {
  background-color: var(--color-primary);
  color: white;
  border: none;
}

button.button.primary:hover:not(:disabled) {
  background-color: var(--color-primary-darker);
}

button.button.secondary {
  background-color: transparent;
  border: 1px solid var(--color-border);
}

button.button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
</style>
