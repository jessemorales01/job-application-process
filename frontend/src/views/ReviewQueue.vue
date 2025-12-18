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
      type="success"
    />
    <v-card>
      <v-card-title>
        Auto-Detected Applications Review
        <v-spacer></v-spacer>
        <v-btn
          color="primary"
          @click="loadDetectedItems"
          :loading="loading"
          :disabled="loading"
        >
          <v-icon left>mdi-refresh</v-icon>
          Refresh
        </v-btn>
      </v-card-title>
      <v-card-text>
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
              :loading="processingItem === item.id"
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
            :disabled="!selectedApplicationId"
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
      loadingApplications: false,
      processingItem: null,
      showError: false,
      errorMessage: '',
      showSuccess: false,
      successMessage: '',
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
      ]
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
  methods: {
    async loadDetectedItems() {
      this.loading = true
      this.showError = false
      try {
        const params = {}
        if (this.selectedStatus) {
          params.status = this.selectedStatus
        }
        
        const response = await api.get('/auto-detected-applications/', { params })
        this.detectedItems = response.data || []
      } catch (error) {
        this.showError = true
        this.errorMessage = formatErrorMessage(error)
      } finally {
        this.loading = false
      }
    },
    async acceptItem(item) {
      this.processingItem = item.id
      this.showError = false
      try {
        const response = await api.post(`/auto-detected-applications/${item.id}/accept/`)
        
        this.showSuccess = true
        this.successMessage = `Application created successfully for ${item.company_name}!`
        
        // Reload list
        await this.loadDetectedItems()
        
        // Navigate to Applications page to see the new application
        // Use setTimeout to allow success message to be visible briefly
        setTimeout(() => {
          this.$router.push('/applications')
        }, 1500)
      } catch (error) {
        this.showError = true
        this.errorMessage = formatErrorMessage(error)
      } finally {
        this.processingItem = null
      }
    },
    async rejectItem(item) {
      this.processingItem = item.id
      this.showError = false
      try {
        await api.post(`/auto-detected-applications/${item.id}/reject/`)
        
        this.showSuccess = true
        this.successMessage = `Detected item rejected: ${item.company_name}`
        
        // Reload list
        await this.loadDetectedItems()
      } catch (error) {
        this.showError = true
        this.errorMessage = formatErrorMessage(error)
      } finally {
        this.processingItem = null
      }
    },
    async openMergeDialog(item) {
      this.selectedItem = item
      this.selectedApplicationId = null
      this.showMergeDialog = true
      this.loadingApplications = true
      
      try {
        const response = await api.get('/applications/')
        this.applications = response.data || []
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
    async mergeItem() {
      if (!this.selectedItem || !this.selectedApplicationId) return

      this.processingItem = this.selectedItem.id
      this.showError = false
      try {
        await api.post(`/auto-detected-applications/${this.selectedItem.id}/merge/`, {
          application_id: this.selectedApplicationId
        })
        
        this.showSuccess = true
        this.successMessage = `Detected item merged with existing application!`
        
        this.closeMergeDialog()
        // Reload list
        await this.loadDetectedItems()
      } catch (error) {
        this.showError = true
        this.errorMessage = formatErrorMessage(error)
      } finally {
        this.processingItem = null
      }
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

