<template>
  <h1>AI Chat Page</h1>
  <div>{{ products}}</div>
</template>


<script setup>
import { ref, onMounted } from 'vue'
import { api } from '@/api'
const products = ref(null);
onMounted(async () => {
  products.value = await api.getMapLocation('2361');
  console.log(products.value)
})

</script>
