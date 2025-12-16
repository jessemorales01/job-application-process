<template>
  <v-app>
    <v-app-bar color="primary" dark>
      <v-app-bar-title>Job Process Tracker</v-app-bar-title>
      <v-spacer></v-spacer>
      <v-btn icon @click="logout">
        <v-icon>mdi-logout</v-icon>
      </v-btn>
    </v-app-bar>

    <v-navigation-drawer permanent>
      <v-list>
        <v-list-item to="/dashboard" prepend-icon="mdi-view-dashboard" title="Dashboard"></v-list-item>
        <v-list-item to="/job-offers" prepend-icon="mdi-briefcase-check" title="Job Offers"></v-list-item>
        <v-list-item to="/leads" prepend-icon="mdi-trending-up" title="Leads"></v-list-item>
      </v-list>
    </v-navigation-drawer>

    <v-main>
      <v-container>
        <h1>Welcome to Job Process Tracker</h1>
        <v-row class="mt-5">
          <v-col cols="12" md="3">
            <v-card>
              <v-card-title>
                <v-icon left>mdi-briefcase-check</v-icon>
                Job Offers
              </v-card-title>
              <v-card-text>
                <div class="text-h4">{{ stats.jobOffers }}</div>
              </v-card-text>
            </v-card>
          </v-col>
          <v-col cols="12" md="3">
            <v-card>
              <v-card-title>
                <v-icon left>mdi-clipboard-text-multiple</v-icon>
                Activities
              </v-card-title>
              <v-card-text>
                <div class="text-h4">{{ stats.activities }}</div>
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
        jobOffers: 0,
        activities: 0,
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
        const [jobOffers, assessments, interactions, applications] = await Promise.all([
          api.get('/job-offers/'),
          api.get('/assessments/'),
          api.get('/interactions/'),
          api.get('/applications/')
        ])
        this.stats.jobOffers = jobOffers.data.length
        this.stats.activities = assessments.data.length + interactions.data.length
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
