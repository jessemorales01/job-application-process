<template>
  <Layout title="Review Queue">
    <ErrorSnackbar
      v-model="showError"
      :message="errorMessage"
      type="error"
      :multiline="true"
    />
    <ErrorSnackbar
      v-model="showSuccess"
      :message="successMessage"
      :type="successNotificationType"
      :multiline="successNotificationType === 'warning'"
    />
    <v-card>
      <v-card-title>
        Auto-Detected Applications Review
        <v-spacer></v-spacer>
        <v-btn
          color="secondary"
          class="mr-2"
          @click="syncInbox"
          :loading="syncing"
          :disabled="loading || syncing"
        >
          <v-icon left>mdi-email-sync</v-icon>
          Sync inbox
        </v-btn>
        <v-btn
          color="primary"
          @click="reloadList"
          :loading="loading"
          :disabled="loading || syncing"
        >
          <v-icon left>mdi-refresh</v-icon>
          Reload list
        </v-btn>
      </v-card-title>
      <v-card-text>
        <p class="text-caption text-medium-emphasis mb-2">
          <strong>Sync inbox</strong> fetches mail from Gmail and creates review items (can take several minutes).
          <strong>Reload list</strong> only refreshes this table from the server (no new email fetch).
        </p>
        <v-select
          v-model="selectedStatus"
          :items="statusOptions"
          item-title="label"
          item-value="value"
          label="Filter by Status"
          clearable
          class="mb-4"
          @update:model-value="loadDetectedItems"
        ></v-select>

        <div v-if="loading" class="text-center py-4">
          <v-progress-circular indeterminate color="primary"></v-progress-circular>
          <p class="mt-2">Loading detected items...</p>
        </div>

        <div v-else-if="detectedItems.length === 0" class="text-center py-8">
          <v-icon size="48" color="grey">mdi-email-check-outline</v-icon>
          <p class="mt-2 text-grey">No detected items found</p>
          <p class="text-caption text-grey">New email-detected applications will appear here for review</p>
        </div>

        <v-data-table
          v-else
          :headers="headers"
          :items="detectedItems"
          :items-per-page="25"
          class="elevation-1"
        >
          <template v-slot:item.company_name="{ item }">
            <strong>{{ item.company_name }}</strong>
            <div v-if="item.position" class="text-caption text-grey">
              {{ item.position }}
            </div>
          </template>

          <template v-slot:item.confidence_score="{ item }">
            <v-chip :color="getConfidenceColor(item.confidence_score)" small>
              {{ Math.round(item.confidence_score * 100) }}%
            </v-chip>
          </template>

          <template v-slot:item.status="{ item }">
            <v-chip :color="getStatusColor(item.status)" small>
              {{ item.status }}
            </v-chip>
          </template>

          <template v-slot:item.detected_at="{ item }">
            {{ formatDate(item.detected_at) }}
          </template>

          <template v-slot:item.actions="{ item }">
            <v-btn
              v-if="item.status === 'pending'"
              color="success"
              small
              class="mr-2"
              @click="acceptItem(item)"
            >
              <v-icon left small>mdi-check</v-icon>
              Accept
            </v-btn>
            <v-btn
              v-if="item.status === 'pending'"
              color="error"
              small
              class="mr-2"
              @click="rejectItem(item)"
              :loading="processingItem === item.id"
            >
              <v-icon left small>mdi-close</v-icon>
              Reject
            </v-btn>
            <v-btn
              v-if="item.status === 'pending'"
              color="primary"
              small
              @click="openMergeDialog(item)"
              :loading="processingItem === item.id"
            >
              <v-icon left small>mdi-link</v-icon>
              Merge
            </v-btn>
          </template>
        </v-data-table>
      </v-card-text>
    </v-card>

    <!-- Merge Dialog -->
    <v-dialog v-model="showMergeDialog" max-width="600px">
      <v-card>
        <v-card-title>
          Merge with Existing Application
        </v-card-title>
        <v-card-text>
          <p class="text-caption text-medium-emphasis mb-3">
            Use Merge when this email matches an application you already track (e.g. duplicate thread). The review row is
            closed and linked to that card—no new application is created.
          </p>
          <p class="mb-4">
            Merge detected application <strong>{{ selectedItem?.company_name }}</strong> with an existing application.
          </p>
          <v-select
            v-model="selectedApplicationId"
            :items="applicationOptions"
            item-title="label"
            item-value="id"
            label="Select Application"
            :loading="loadingApplications"
          ></v-select>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn text @click="closeMergeDialog">Cancel</v-btn>
          <v-btn
            color="primary"
            @click="mergeItem"
            :loading="processingItem === selectedItem?.id"
            :disabled="!canSubmitMerge"
          >
            Merge
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </Layout>
</template>

<script>
import api from '../services/api'
import Layout from '../components/Layout.vue'
import ErrorSnackbar from '../components/ErrorSnackbar.vue'
import { formatErrorMessage } from '../utils/errorHandler'
import { formatSyncNotification } from '../utils/emailSyncNotification'
import {
  getEntry,
  getOrFetch,
  autoDetectedKey,
  markDirty,
  markDirtyAutoDetected,
  markDirtyDashboardLists,
  putCached,
} from '../services/listResourceCache'
import {
  EMAIL_SYNC_MAX_RESULTS,
  EMAIL_SYNC_TIMEOUT_MS,
} from '../constants/emailSync'

/** DRF list may be a bare array or paginated `{ results: [...] }`. */
function normalizeApplicationsListResponse(data) {
  if (Array.isArray(data)) return data
  if (data && typeof data === 'object' && Array.isArray(data.results)) {
    return data.results
  }
  return []
}

/**
 * Coerce merge target to a positive integer Application PK for the API.
 * Rejects arrays/objects-without-id (Vuetify edge cases) and non-finite numbers.
 */
function resolveMergeApplicationId(selectedValue) {
  if (selectedValue == null || selectedValue === '') return null
  if (Array.isArray(selectedValue)) return null
  if (typeof selectedValue === 'object') {
    const parsedId = Number(selectedValue.id)
    return Number.isFinite(parsedId) && parsedId > 0 ? parsedId : null
  }
  const parsedId = Number(selectedValue)
  return Number.isFinite(parsedId) && parsedId > 0 ? parsedId : null
}

export default {
  name: 'ReviewQueue',
  components: {
    Layout,
    ErrorSnackbar
  },
  data() {
    return {
      detectedItems: [],
      loading: false,
      syncing: false,
      loadingApplications: false,
      processingItem: null,
      showError: false,
      errorMessage: '',
      showSuccess: false,
      successMessage: '',
      successNotificationType: 'success',
      selectedStatus: 'pending',
      showMergeDialog: false,
      selectedItem: null,
      selectedApplicationId: null,
      applications: [],
      headers: [
        { title: 'Company', key: 'company_name', sortable: true },
        { title: 'Confidence', key: 'confidence_score', sortable: true },
        { title: 'Status', key: 'status', sortable: true },
        { title: 'Detected At', key: 'detected_at', sortable: true },
        { title: 'Actions', key: 'actions', sortable: false, align: 'end' }
      ],
      statusOptions: [
        { label: 'Pending', value: 'pending' },
        { label: 'Accepted', value: 'accepted' },
        { label: 'Rejected', value: 'rejected' },
        { label: 'Merged', value: 'merged' }
      ],
      skipNextActivatedRefresh: true
    }
  },
  computed: {
    applicationOptions() {
      return this.applications.map(app => ({
        id: app.id,
        label: `${app.company_name}${app.position ? ` - ${app.position}` : ''}`
      }))
    }
  },
  async mounted() {
    await this.loadDetectedItems()
  },
  activated() {
    if (this.skipNextActivatedRefresh) {
      this.skipNextActivatedRefresh = false
      return
    }
    this.loadDetectedItems()
  },
  methods: {
    reloadList() {
      return this.loadDetectedItems({ force: true })
    },
    async syncInbox() {
      this.syncing = true
      this.showError = false
      let response = null
      try {
        response = await api.post(
          '/email-accounts/sync/',
          { max_results: EMAIL_SYNC_MAX_RESULTS },
          { timeout: EMAIL_SYNC_TIMEOUT_MS }
        )
      } catch (error) {
        this.showError = true
        this.errorMessage = formatErrorMessage(error)
        return
      } finally {
        this.syncing = false
      }

      const { type, message } = formatSyncNotification(response.data)
      this.successNotificationType = type
      this.showSuccess = true
      this.successMessage = message
      markDirty('emailAccount')
      markDirtyAutoDetected()
      markDirtyDashboardLists()
      await this.loadDetectedItems({ force: true })
    },
    async loadDetectedItems(options = {}) {
      const force = options.force === true
      const key = autoDetectedKey(this.selectedStatus)
      const e = getEntry(key)
      const params = {}
      if (this.selectedStatus) {
        params.status = this.selectedStatus
      }

      this.showError = false
      if (!force && !e.dirty && e.fetched) {
        this.detectedItems = Array.isArray(e.data) ? e.data : []
        return
      }
      if (e.fetched) {
        this.detectedItems = Array.isArray(e.data) ? e.data : []
      }

      // Always show table loading during a network fetch (including force after sync).
      // Previously `loading = !e.fetched` hid the spinner when refreshing an already-loaded list.
      this.loading = true
      try {
        const { data } = await getOrFetch(
          key,
          '/auto-detected-applications/',
          { params, force }
        )
        this.detectedItems = Array.isArray(data) ? data : []
      } catch (error) {
        this.showError = true
        this.errorMessage = formatErrorMessage(error)
      } finally {
        this.loading = false
      }
    },
    acceptItem(item) {
      this.showError = false
      const idx = this.detectedItems.findIndex((r) => r.id === item.id)
      if (idx === -1) return

      const snapshot = { ...item }
      const key = autoDetectedKey(this.selectedStatus)
      this.detectedItems.splice(idx, 1)
      putCached(key, [...this.detectedItems])

      this.successNotificationType = 'success'
      this.showSuccess = true
      this.successMessage = 'Navigating to Application Stages'

      markDirty('applications')
      markDirtyDashboardLists()

      const navDelayMs = 320
      setTimeout(() => {
        this.$router.push('/applications')
      }, navDelayMs)

      api
        .post(`/auto-detected-applications/${item.id}/accept/`)
        .then(() => {
          markDirtyAutoDetected()
          putCached(key, [...this.detectedItems])
        })
        .catch((error) => {
          markDirtyAutoDetected()
          if (this.$route.name === 'ReviewQueue') {
            const at = Math.min(idx, this.detectedItems.length)
            this.detectedItems.splice(at, 0, snapshot)
            putCached(key, [...this.detectedItems])
          }
          this.showSuccess = false
          this.showError = true
          this.errorMessage = formatErrorMessage(error)
        })
    },
    rejectItem(item) {
      if (this.processingItem != null) return
      this.processingItem = item.id
      this.showError = false

      const idx = this.detectedItems.findIndex((r) => r.id === item.id)
      if (idx === -1) {
        this.processingItem = null
        return
      }
      const snapshot = { ...item }
      const key = autoDetectedKey(this.selectedStatus)
      this.detectedItems.splice(idx, 1)
      putCached(key, [...this.detectedItems])
      this.showSuccess = true
      this.successMessage = `Rejected: ${item.company_name}`

      api
        .post(`/auto-detected-applications/${item.id}/reject/`)
        .then(() => {
          markDirtyAutoDetected()
          putCached(key, [...this.detectedItems])
        })
        .catch((error) => {
          markDirtyAutoDetected()
          if (this.$route.name === 'ReviewQueue') {
            const at = Math.min(idx, this.detectedItems.length)
            this.detectedItems.splice(at, 0, snapshot)
            putCached(key, [...this.detectedItems])
          }
          this.showSuccess = false
          this.showError = true
          this.errorMessage = formatErrorMessage(error)
        })
        .finally(() => {
          this.processingItem = null
        })
    },
    async openMergeDialog(item) {
      this.selectedItem = item
      this.selectedApplicationId = null
      this.showMergeDialog = true
      this.loadingApplications = true
      
      try {
        const { data } = await getOrFetch('applications', '/applications/')
        this.applications = normalizeApplicationsListResponse(data)
      } catch (error) {
        this.showError = true
        this.errorMessage = formatErrorMessage(error)
      } finally {
        this.loadingApplications = false
      }
    },
    closeMergeDialog() {
      this.showMergeDialog = false
      this.selectedItem = null
      this.selectedApplicationId = null
    },
    mergeItem() {
      if (!this.selectedItem || this.processingItem != null) return

      const applicationId = resolveMergeApplicationId(this.selectedApplicationId)
      if (applicationId == null) {
        this.showError = true
        this.errorMessage =
          'Select an application card to merge into (from your Applications list).'
        return
      }

      const item = this.selectedItem
      this.processingItem = item.id
      this.showError = false

      const idx = this.detectedItems.findIndex((r) => r.id === item.id)
      const snapshot = { ...item }
      const key = autoDetectedKey(this.selectedStatus)
      if (idx !== -1) {
        this.detectedItems.splice(idx, 1)
        putCached(key, [...this.detectedItems])
      }
      this.closeMergeDialog()
      this.showSuccess = true
      this.successMessage = 'Merged with existing application'

      api
        .post(`/auto-detected-applications/${item.id}/merge/`, {
          application_id: applicationId,
        })
        .then(() => {
          markDirtyAutoDetected()
          putCached(key, [...this.detectedItems])
          markDirty('applications')
          markDirtyDashboardLists()
        })
        .catch((error) => {
          markDirtyAutoDetected()
          if (this.$route.name === 'ReviewQueue' && idx !== -1) {
            const at = Math.min(idx, this.detectedItems.length)
            this.detectedItems.splice(at, 0, snapshot)
            putCached(key, [...this.detectedItems])
          }
          this.showSuccess = false
          this.showError = true
          this.errorMessage = formatErrorMessage(error)
        })
        .finally(() => {
          this.processingItem = null
        })
    },
    getConfidenceColor(score) {
      if (score >= 0.8) return 'success'
      if (score >= 0.6) return 'warning'
      return 'error'
    },
    getStatusColor(status) {
      const colors = {
        pending: 'warning',
        accepted: 'success',
        rejected: 'error',
        merged: 'info'
      }
      return colors[status] || 'grey'
    },
    formatDate(dateString) {
      if (!dateString) return 'N/A'
      const date = new Date(dateString)
      return date.toLocaleString()
    }
  }
}
</script>

<style scoped>
.v-data-table {
  margin-top: 16px;
}
</style>

