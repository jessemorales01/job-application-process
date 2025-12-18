<template>
  <Layout title="Settings">
    <ErrorSnackbar
      v-model="showError"
      :message="errorMessage"
      type="error"
      :multiline="true"
    />
    <ErrorSnackbar
      v-model="showSuccess"
      :message="successMessage"
      type="success"
    />
    <v-card>
      <v-card-title>
        Settings
      </v-card-title>
      <v-card-text>
        <v-card class="mb-4">
          <v-card-title>
            <v-icon left>mdi-email</v-icon>
            Email Connection
          </v-card-title>
          <v-card-text>
            <div v-if="loading" class="text-center py-4">
              <v-progress-circular indeterminate color="primary"></v-progress-circular>
              <p class="mt-2">Loading email account...</p>
            </div>

            <div v-else-if="emailAccount">
              <!-- Connected Account Display -->
              <v-alert type="success" class="mb-4">
                <div class="d-flex align-center">
                  <v-icon left>mdi-check-circle</v-icon>
                  <div>
                    <strong>Email Account Connected</strong>
                    <div class="text-caption mt-1">
                      {{ emailAccount.email }} ({{ emailAccount.provider }})
                    </div>
                  </div>
                </div>
              </v-alert>

              <v-list>
                <v-list-item>
                  <v-list-item-title>Email</v-list-item-title>
                  <v-list-item-subtitle>{{ emailAccount.email }}</v-list-item-subtitle>
                </v-list-item>
                <v-list-item>
                  <v-list-item-title>Provider</v-list-item-title>
                  <v-list-item-subtitle>{{ emailAccount.provider }}</v-list-item-subtitle>
                </v-list-item>
                <v-list-item>
                  <v-list-item-title>Status</v-list-item-title>
                  <v-list-item-subtitle>
                    <v-chip :color="emailAccount.is_active ? 'success' : 'error'" small>
                      {{ emailAccount.is_active ? 'Active' : 'Inactive' }}
                    </v-chip>
                  </v-list-item-subtitle>
                </v-list-item>
                <v-list-item v-if="emailAccount.last_sync_at">
                  <v-list-item-title>Last synced</v-list-item-title>
                  <v-list-item-subtitle>
                    {{ formatDate(emailAccount.last_sync_at) }}
                  </v-list-item-subtitle>
                </v-list-item>
              </v-list>

              <v-divider class="my-4"></v-divider>

              <v-btn
                color="error"
                @click="disconnectEmail"
                :loading="disconnecting"
                :disabled="disconnecting"
              >
                <v-icon left>mdi-link-off</v-icon>
                Disconnect Email Account
              </v-btn>
            </div>

            <div v-else>
              <!-- No Account Connected -->
              <v-alert type="info" class="mb-4">
                <div class="d-flex align-center">
                  <v-icon left>mdi-information</v-icon>
                  <div>
                    <strong>No Email Account Connected</strong>
                    <div class="text-caption mt-1">
                      Connect your email to automatically detect job applications and updates.
                    </div>
                  </div>
                </div>
              </v-alert>

              <v-btn
                color="primary"
                @click="connectEmail"
                :loading="connecting"
                :disabled="connecting"
              >
                <v-icon left>mdi-email-plus</v-icon>
                Connect Email Account
              </v-btn>
            </div>
          </v-card-text>
        </v-card>
      </v-card-text>
    </v-card>
  </Layout>
</template>

<script>
import api from '../services/api'
import Layout from '../components/Layout.vue'
import ErrorSnackbar from '../components/ErrorSnackbar.vue'
import { formatErrorMessage } from '../utils/errorHandler'

export default {
  name: 'Settings',
  components: {
    Layout,
    ErrorSnackbar
  },
  data() {
    return {
      emailAccount: null,
      loading: false,
      connecting: false,
      disconnecting: false,
      showError: false,
      errorMessage: '',
      showSuccess: false,
      successMessage: ''
    }
  },
  async mounted() {
    await this.loadEmailAccount()
    await this.handleOAuthCallback()
  },
  methods: {
    async loadEmailAccount() {
      this.loading = true
      this.showError = false
      try {
        const response = await api.get('/email-accounts/')
        // API returns null if no account, or the account object if exists
        this.emailAccount = response.data || null
      } catch (error) {
        this.showError = true
        this.errorMessage = formatErrorMessage(error)
      } finally {
        this.loading = false
      }
    },
    async connectEmail() {
      this.connecting = true
      this.showError = false
      try {
        // Get OAuth authorization URL
        // The redirect_uri must be the backend callback URL (matches Google Cloud Console)
        // The backend will handle the OAuth callback
        const backendUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000'
        const response = await api.get('/email-accounts/oauth/initiate/', {
          params: {
            redirect_uri: `${backendUrl}/api/email-accounts/oauth/callback/`
          }
        })
        const { authorization_url } = response.data
        
        // Redirect to OAuth URL
        window.location.href = authorization_url
      } catch (error) {
        this.connecting = false
        this.showError = true
        this.errorMessage = formatErrorMessage(error)
      }
    },
    async handleOAuthCallback() {
      // Check if we have OAuth callback result in URL (from backend redirect)
      const urlParams = new URLSearchParams(window.location.search)
      const oauthSuccess = urlParams.get('oauth_success')
      const oauthError = urlParams.get('oauth_error')

      if (oauthSuccess === 'true') {
        // Backend successfully processed OAuth callback
        this.connecting = false
        this.showError = false
        
        // Reload email account to show connected status
        await this.loadEmailAccount()

        // Show success message
        this.showSuccess = true
        this.successMessage = 'Email account connected successfully!'

        // Clean up URL parameters
        window.history.replaceState({}, document.title, '/settings')
      } else if (oauthError) {
        // Backend returned an error
        this.connecting = false
        this.showError = true
        this.errorMessage = decodeURIComponent(oauthError)

        // Clean up URL parameters
        window.history.replaceState({}, document.title, '/settings')
      }
      // If neither parameter exists, this is not an OAuth callback
    },
    async disconnectEmail() {
      if (!this.emailAccount) return

      if (!confirm('Are you sure you want to disconnect this email account? This will stop automatic email detection.')) {
        return
      }

      this.disconnecting = true
      this.showError = false
      try {
        await api.delete(`/email-accounts/${this.emailAccount.id}/`)
        
        // Clear email account
        this.emailAccount = null

        // Show success message
        this.showSuccess = true
        this.successMessage = 'Email account disconnected successfully.'
      } catch (error) {
        this.showError = true
        this.errorMessage = formatErrorMessage(error)
      } finally {
        this.disconnecting = false
      }
    },
    formatDate(dateString) {
      if (!dateString) return 'Never'
      const date = new Date(dateString)
      return date.toLocaleString()
    }
  }
}
</script>

<style scoped>
.v-list-item {
  padding: 8px 0;
}
</style>

