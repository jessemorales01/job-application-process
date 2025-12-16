<template>
  <v-app>
    <v-app-bar color="primary" dark>
      <v-app-bar-title>Job Application Tracker - {{ title }}</v-app-bar-title>
      <v-spacer></v-spacer>
      <v-btn icon @click="logout">
        <v-icon>mdi-logout</v-icon>
      </v-btn>
    </v-app-bar>

    <v-navigation-drawer permanent>
      <v-list>
        <v-list-item to="/dashboard" prepend-icon="mdi-view-dashboard" title="Dashboard"></v-list-item>
        <v-list-item to="/customers" prepend-icon="mdi-account-group" title="Customers"></v-list-item>
        <v-list-item to="/contacts" prepend-icon="mdi-card-account-details" title="Contacts"></v-list-item>
        <v-list-item to="/interactions" prepend-icon="mdi-comment-text-multiple" title="Interactions"></v-list-item>
        <v-list-item to="/applications" prepend-icon="mdi-briefcase" title="Applications"></v-list-item>
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
