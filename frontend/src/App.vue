<template>
  <router-view v-slot="{ Component }">
    <keep-alive
      :key="layoutKey"
      include="Dashboard,JobOffers,Activities,Applications,ReviewQueue,Settings"
    >
      <component :is="Component" />
    </keep-alive>
  </router-view>
</template>

<script>
import { listCacheSessionId } from './services/listResourceCache'

export default {
  name: 'App',
  computed: {
    layoutKey() {
      return listCacheSessionId.value
    }
  }
}
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}
</style>

