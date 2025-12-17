<template>
  <v-app>
    <v-app-bar color="primary" dark>
      <v-app-bar-title>Job Process Tracker - {{ title }}</v-app-bar-title>
      <v-spacer></v-spacer>
      <v-btn icon @click="logout">
        <v-icon>mdi-logout</v-icon>
      </v-btn>
    </v-app-bar>

    <v-navigation-drawer permanent>
      <v-list>
        <v-list-item to="/dashboard" prepend-icon="mdi-view-dashboard" title="Dashboard"></v-list-item>
        <v-list-item to="/job-offers" prepend-icon="mdi-briefcase-check" title="Job Offers"></v-list-item>
        <v-list-item to="/activities" prepend-icon="mdi-clipboard-text-multiple" title="Activities"></v-list-item>
        <v-list-item to="/applications" prepend-icon="mdi-briefcase" title="Applications"></v-list-item>
        <v-list-item to="/settings" prepend-icon="mdi-cog" title="Settings"></v-list-item>
      </v-list>
    </v-navigation-drawer>

    <v-main>
      <v-container fluid>
        <slot></slot>
      </v-container>
    </v-main>
  </v-app>
</template>

<script>
export default {
  name: 'Layout',
  props: {
    title: {
      type: String,
      default: 'Dashboard'
    }
  },
  methods: {
    logout() {
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      this.$router.push('/login')
    }
  }
}
</script>
