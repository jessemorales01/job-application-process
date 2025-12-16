<template>
  <v-app>
    <v-app-bar color="primary" dark>
      <v-app-bar-title>CRM Dashboard</v-app-bar-title>
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
        <v-list-item to="/leads" prepend-icon="mdi-trending-up" title="Leads"></v-list-item>
      </v-list>
    </v-navigation-drawer>

    <v-main>
      <v-container>
        <h1>Welcome to CRM Dashboard</h1>
        <v-row class="mt-5">
          <v-col cols="12" md="3">
            <v-card>
              <v-card-title>
                <v-icon left>mdi-account-group</v-icon>
                Customers
              </v-card-title>
              <v-card-text>
                <div class="text-h4">{{ stats.customers }}</div>
              </v-card-text>
            </v-card>
          </v-col>
          <v-col cols="12" md="3">
            <v-card>
              <v-card-title>
                <v-icon left>mdi-card-account-details</v-icon>
                Contacts
              </v-card-title>
              <v-card-text>
                <div class="text-h4">{{ stats.contacts }}</div>
              </v-card-text>
            </v-card>
          </v-col>
          <v-col cols="12" md="3">
            <v-card>
              <v-card-title>
                <v-icon left>mdi-comment-text-multiple</v-icon>
                Interactions
              </v-card-title>
              <v-card-text>
                <div class="text-h4">{{ stats.interactions }}</div>
              </v-card-text>
            </v-card>
          </v-col>
          <v-col cols="12" md="3">
            <v-card>
              <v-card-title>
                <v-icon left>mdi-briefcase</v-icon>
                Applications
              </v-card-title>
              <v-card-text>
                <div class="text-h4">{{ stats.applications }}</div>
              </v-card-text>
            </v-card>
          </v-col>
        </v-row>
      </v-container>
    </v-main>
  </v-app>
</template>

<script>
import api from '../services/api'

export default {
  name: 'Dashboard',
  data() {
    return {
      stats: {
        customers: 0,
        contacts: 0,
        interactions: 0,
        applications: 0
      }
    }
  },
  async mounted() {
    await this.loadStats()
  },
  methods: {
    async loadStats() {
      try {
        const [customers, contacts, interactions, applications] = await Promise.all([
          api.get('/customers/'),
          api.get('/contacts/'),
          api.get('/interactions/'),
          api.get('/applications/')
        ])
        this.stats.customers = customers.data.length
        this.stats.contacts = contacts.data.length
        this.stats.interactions = interactions.data.length
        this.stats.applications = applications.data.length
      } catch (error) {
        console.error('Error loading stats:', error)
      }
    },
    logout() {
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      this.$router.push('/login')
    }
  }
}
</script>
