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

<template>
  <div>
    <p v-if="loading">Loading...</p>
    <p v-else-if="error">{{ error }}</p>
    <div v-else>
      <p>Total rows: {{ healthData.length }}</p>
      <ul>
        <li v-for="(item, index) in healthData.slice(0, 5)" :key="index">
          {{ item.year }} - {{ item.sex }} - {{ item.cancer_type }} - {{ item.cases }} -
          {{ item.deaths }}
        </li>
      </ul>
    </div>
  </div>
</template>
