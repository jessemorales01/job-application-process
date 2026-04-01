<template>
  <v-app>
    <ErrorSnackbar
      v-model="showError"
      :message="errorMessage"
      type="error"
    />
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
        <v-list-item to="/applications" prepend-icon="mdi-briefcase" title="Applications"></v-list-item>
      </v-list>
    </v-navigation-drawer>

    <v-main>
      <v-container>
        <h1>Welcome to Job Application Tracker</h1>
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
import ErrorSnackbar from '../components/ErrorSnackbar.vue'
import { formatErrorMessage } from '../utils/errorHandler'
import { getOrFetch, clearAllCaches } from '../services/listResourceCache'

export default {
  name: 'Dashboard',
  components: {
    ErrorSnackbar
  },
  data() {
    return {
      stats: {
        jobOffers: 0,
        activities: 0,
        applications: 0
      },
      showError: false,
      errorMessage: '',
      skipNextActivatedRefresh: true
    }
  },
  async mounted() {
    await this.loadStats()
  },
  activated() {
    if (this.skipNextActivatedRefresh) {
      this.skipNextActivatedRefresh = false
      return
    }
    this.loadStats()
  },
  methods: {
    showErrorNotification(message) {
      this.errorMessage = message
      this.showError = true
    },
    async loadStats() {
      try {
        const [jobOffers, assessments, interactions, applications] = await Promise.all([
          getOrFetch('jobOffers', '/job-offers/'),
          getOrFetch('assessments', '/assessments/'),
          getOrFetch('interactions', '/interactions/'),
          getOrFetch('applications', '/applications/')
        ])
        const jo = jobOffers.data || []
        const as = assessments.data || []
        const inter = interactions.data || []
        const app = applications.data || []
        this.stats.jobOffers = jo.length
        this.stats.activities = as.length + inter.length
        this.stats.applications = app.length
      } catch (error) {
        const message = formatErrorMessage(error) || 'Failed to load dashboard statistics. Please refresh the page.'
        this.showErrorNotification(message)
      }
    },
    logout() {
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      clearAllCaches()
      this.$router.push('/login')
    }
  }
}
</script>
