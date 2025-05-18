<script setup lang="ts">
import { ref, computed } from 'vue'

const props = defineProps({
  knobs: {
    type: Array,
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
          <img :src="`http://localhost:8000/static/thumbnails/${knob.id}.png`" :alt="knob.file" />
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
