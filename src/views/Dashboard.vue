<template>
  <h1>Dashboard Page1</h1>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { api } from '@/api'

const healthData = ref([])
const loading = ref(true)
const error = ref(null)

async function loadHealthData() {
  try {
    loading.value = true
    error.value = null

    const res = await api.getHealthAll()
    healthData.value = res.items || []
    console.log('health data:', res)
  } catch (err) {
    console.error(err)
    error.value = err.message
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadHealthData()
})
</script>
