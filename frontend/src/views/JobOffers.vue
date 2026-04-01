<template>
  <Layout title="Job Offers">
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
        Job Offers Management
        <v-spacer></v-spacer>
        <v-btn color="primary" @click="openDialog()">
          <v-icon left>mdi-plus</v-icon>
          Add Job Offer
        </v-btn>
      </v-card-title>
      <v-card-text>
        <v-data-table
          :headers="headers"
          :items="jobOffers"
          :loading="loading"
        >
          <template v-slot:item.actions="{ item }">
            <v-icon small class="mr-2" @click="openDialog(item)">
              mdi-pencil
            </v-icon>
            <v-icon small @click="deleteJobOffer(item.id)">
              mdi-delete
            </v-icon>
          </template>
          <template v-slot:item.status="{ item }">
            <v-chip :color="getStatusColor(item.status)" small>
              {{ getStatusLabel(item.status) }}
            </v-chip>
          </template>
          <template v-slot:item.offer_date="{ item }">
            {{ item.offer_date ? new Date(item.offer_date).toLocaleDateString() : '' }}
          </template>
          <template v-slot:item.response_deadline="{ item }">
            {{ item.response_deadline ? new Date(item.response_deadline).toLocaleDateString() : '' }}
          </template>
        </v-data-table>
      </v-card-text>
    </v-card>

    <!-- Dialog for Add/Edit -->
    <v-dialog v-model="dialog" max-width="600px">
      <v-card>
        <v-card-title>
          {{ editMode ? 'Edit Job Offer' : 'Add Job Offer' }}
        </v-card-title>
        <v-card-text>
          <v-form @submit.prevent="saveJobOffer">
            <v-select
              v-model="form.application"
              :items="applications"
              item-title="title"
              item-value="id"
              label="Application"
              required
              @update:model-value="onApplicationSelected"
            ></v-select>
            <v-text-field
              v-model="form.company_name"
              label="Company Name"
              required
              :readonly="!!form.application"
            ></v-text-field>
            <v-text-field
              v-model="form.position"
              label="Position"
              required
              hint="e.g., Software Engineer, Senior Developer"
              :readonly="!!form.application"
            ></v-text-field>
            <v-text-field
              v-model="form.salary_range"
              label="Salary Range"
              required
              hint="e.g., '120k', '100k-130k'"
              :readonly="!!form.application"
            ></v-text-field>
            <v-text-field
              v-model="form.offered"
              label="Offered"
              hint="The actual salary/compensation offered (e.g., '125k', '110k + equity')"
            ></v-text-field>
            <v-text-field
              v-model="form.offer_date"
              label="Offer Date"
              type="date"
            ></v-text-field>
            <v-text-field
              v-model="form.start_date"
              label="Start Date"
              type="date"
            ></v-text-field>
            <v-text-field
              v-model="form.response_deadline"
              label="Response Deadline"
              type="date"
            ></v-text-field>
            <v-select
              v-model="form.status"
              :items="statusOptions"
              label="Status"
              required
            ></v-select>
            <v-textarea
              v-model="form.notes"
              label="Notes"
            ></v-textarea>
          </v-form>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn text :disabled="jobOfferSaving" @click="dialog = false">Cancel</v-btn>
          <v-btn
            color="primary"
            :loading="jobOfferSaving"
            :disabled="jobOfferSaving"
            @click="saveJobOffer"
          >
            Save
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </Layout>
</template>

<script>
import Layout from '../components/Layout.vue'
import ErrorSnackbar from '../components/ErrorSnackbar.vue'
import api from '../services/api'
import { formatErrorMessage } from '../utils/errorHandler'
import {
  getEntry,
  getOrFetch,
  markDirty,
  markDirtyDashboardLists,
  putCached,
} from '../services/listResourceCache'

export default {
  name: 'JobOffers',
  components: {
    Layout,
    ErrorSnackbar
  },
  data() {
    return {
      jobOffers: [],
      loading: false,
      dialog: false,
      editMode: false,
      showError: false,
      errorMessage: '',
      showSuccess: false,
      successMessage: '',
      statusOptions: [
        { title: 'Pending', value: 'pending' },
        { title: 'Accepted', value: 'accepted' },
        { title: 'Rejected', value: 'rejected' },
        { title: 'Negotiating', value: 'negotiating' }
      ],
      headers: [
        { title: 'Company', key: 'company_name' },
        { title: 'Position', key: 'position' },
        { title: 'Salary Range', key: 'salary_range' },
        { title: 'Offered', key: 'offered' },
        { title: 'Offer Date', key: 'offer_date' },
        { title: 'Status', key: 'status' },
        { title: 'Response Deadline', key: 'response_deadline' },
        { title: 'Actions', key: 'actions', sortable: false }
      ],
      applications: [],
      form: {
        company_name: '',
        position: '',
        salary_range: '',
        offered: '',
        application: null,
        offer_date: '',
        start_date: '',
        response_deadline: '',
        status: 'pending',
        notes: ''
      },
      skipNextActivatedRefresh: true,
      jobOfferSaving: false,
      deletingJobOfferId: null
    }
  },
  async mounted() {
    await Promise.all([
      this.loadJobOffers(),
      this.loadApplications()
    ])
  },
  activated() {
    if (this.skipNextActivatedRefresh) {
      this.skipNextActivatedRefresh = false
      return
    }
    Promise.all([this.loadJobOffers(), this.loadApplications()])
  },
  methods: {
    showErrorNotification(message) {
      this.errorMessage = message
      this.showError = true
    },
    showSuccessNotification(message) {
      this.successMessage = message
      this.showSuccess = true
    },
    async loadJobOffers(options = {}) {
      const force = options.force === true
      const key = 'jobOffers'
      const e = getEntry(key)
      if (!force && !e.dirty && e.fetched) {
        this.jobOffers = e.data || []
        return
      }
      if (e.fetched) {
        this.jobOffers = e.data || []
      }
      this.loading = !e.fetched
      try {
        const { data } = await getOrFetch(key, '/job-offers/', { force })
        this.jobOffers = data || []
      } catch (error) {
        const message = formatErrorMessage(error) || 'Failed to load job offers. Please refresh the page.'
        this.showErrorNotification(message)
      } finally {
        this.loading = false
      }
    },
    mapApplicationOptions(rows) {
      return (rows || []).map((app) => ({
        ...app,
        title: `${app.company_name}${app.position ? ` - ${app.position}` : ''}`,
      }))
    },
    async loadApplications(options = {}) {
      const force = options.force === true
      const key = 'applications'
      const e = getEntry(key)
      try {
        if (!force && !e.dirty && e.fetched) {
          this.applications = this.mapApplicationOptions(e.data)
          return
        }
        const { data } = await getOrFetch(key, '/applications/', { force })
        this.applications = this.mapApplicationOptions(data)
      } catch (error) {
        const message = formatErrorMessage(error) || 'Failed to load applications.'
        this.showErrorNotification(message)
      }
    },
    onApplicationSelected(applicationId) {
      if (applicationId && !this.editMode) {
        const selectedApp = this.applications.find(app => app.id === applicationId)
        if (selectedApp) {
          this.form.company_name = selectedApp.company_name || ''
          this.form.position = selectedApp.position || ''
          this.form.salary_range = selectedApp.salary_range || ''
        }
      }
    },
    openDialog(jobOffer = null) {
      if (jobOffer) {
        this.editMode = true
        this.form = { ...jobOffer }
        // Format dates for date inputs
        if (this.form.offer_date) {
          this.form.offer_date = this.form.offer_date.split('T')[0]
        }
        if (this.form.start_date) {
          this.form.start_date = this.form.start_date.split('T')[0]
        }
        if (this.form.response_deadline) {
          this.form.response_deadline = this.form.response_deadline.split('T')[0]
        }
      } else {
        this.editMode = false
        this.form = {
          company_name: '',
          position: '',
          salary_range: '',
          offered: '',
          application: null,
          offer_date: '',
          start_date: '',
          response_deadline: '',
          status: 'pending',
          notes: ''
        }
      }
      this.dialog = true
    },
    saveJobOffer() {
      if (this.jobOfferSaving) return
      this.jobOfferSaving = true
      this.showError = false

      const form = { ...this.form }
      const errs = []
      if (!form.company_name || !String(form.company_name).trim()) errs.push('Company name is required.')
      if (!form.position || !String(form.position).trim()) errs.push('Position is required.')
      if (!form.salary_range || !String(form.salary_range).trim()) errs.push('Salary range is required.')
      if (!form.status) errs.push('Status is required.')
      if (!this.editMode && (form.application == null || form.application === '')) {
        errs.push('Application is required.')
      }
      if (errs.length) {
        this.showErrorNotification(errs.join(' '))
        this.jobOfferSaving = false
        return
      }

      const finish = () => {
        this.jobOfferSaving = false
      }

      try {
        if (this.editMode) {
          const idx = this.jobOffers.findIndex((j) => j.id === form.id)
          if (idx === -1) {
            finish()
            return
          }
          const snapshot = { ...this.jobOffers[idx] }
          const updated = { ...this.jobOffers[idx], ...form }
          this.jobOffers.splice(idx, 1, updated)
          putCached('jobOffers', [...this.jobOffers])
          this.dialog = false
          this.showSuccessNotification('Job offer updated successfully!')

          api
            .put(`/job-offers/${form.id}/`, form)
            .then(({ data }) => {
              const i = this.jobOffers.findIndex((x) => x.id === form.id)
              if (i !== -1 && data && typeof data === 'object' && Object.keys(data).length > 0) {
                this.jobOffers.splice(i, 1, { ...this.jobOffers[i], ...data })
                putCached('jobOffers', [...this.jobOffers])
              }
              markDirty('jobOffers')
              markDirtyDashboardLists()
            })
            .catch((error) => {
              const i = this.jobOffers.findIndex((x) => x.id === form.id)
              if (i !== -1) this.jobOffers.splice(i, 1, snapshot)
              putCached('jobOffers', [...this.jobOffers])
              markDirty('jobOffers')
              this.showErrorNotification(
                formatErrorMessage(error) || 'Failed to save job offer. Please try again.'
              )
            })
            .finally(finish)
          return
        }

        const tempId = -Date.now()
        const optimistic = { ...form, id: tempId }
        this.jobOffers = [optimistic, ...this.jobOffers]
        putCached('jobOffers', [...this.jobOffers])
        this.dialog = false
        this.showSuccessNotification('Job offer added')

        api
          .post('/job-offers/', form)
          .then(({ data }) => {
            const idx = this.jobOffers.findIndex((j) => j.id === tempId)
            if (idx !== -1) {
              const merged =
                data && typeof data === 'object' ? { ...optimistic, ...data } : optimistic
              this.jobOffers.splice(idx, 1, merged)
              putCached('jobOffers', [...this.jobOffers])
            }
            markDirty('jobOffers')
            markDirtyDashboardLists()
          })
          .catch((error) => {
            const idx = this.jobOffers.findIndex((j) => j.id === tempId)
            if (idx !== -1) {
              this.jobOffers.splice(idx, 1)
              putCached('jobOffers', [...this.jobOffers])
            }
            markDirty('jobOffers')
            this.showErrorNotification(
              formatErrorMessage(error) || 'Failed to save job offer. Please try again.'
            )
          })
          .finally(finish)
      } catch (error) {
        finish()
        this.showErrorNotification(
          formatErrorMessage(error) || 'Failed to save job offer. Please try again.'
        )
      }
    },
    deleteJobOffer(id) {
      if (!confirm('Are you sure you want to delete this job offer?')) return
      if (this.deletingJobOfferId != null) return

      const idx = this.jobOffers.findIndex((j) => j.id === id)
      if (idx === -1) return
      const snapshot = this.jobOffers[idx]
      this.deletingJobOfferId = id
      this.jobOffers.splice(idx, 1)
      putCached('jobOffers', [...this.jobOffers])
      this.showSuccessNotification('Job offer removed')

      api
        .delete(`/job-offers/${id}/`)
        .then(() => {
          markDirty('jobOffers')
          markDirtyDashboardLists()
        })
        .catch((error) => {
          const at = Math.min(idx, this.jobOffers.length)
          this.jobOffers.splice(at, 0, snapshot)
          putCached('jobOffers', [...this.jobOffers])
          markDirty('jobOffers')
          this.showErrorNotification(
            formatErrorMessage(error) || 'Failed to delete job offer. Please try again.'
          )
        })
        .finally(() => {
          this.deletingJobOfferId = null
        })
    },
    getStatusColor(status) {
      const colors = {
        pending: 'orange',
        accepted: 'green',
        rejected: 'red',
        negotiating: 'blue'
      }
      return colors[status] || 'grey'
    },
    getStatusLabel(status) {
      const labels = {
        pending: 'Pending',
        accepted: 'Accepted',
        rejected: 'Rejected',
        negotiating: 'Negotiating'
      }
      return labels[status] || status
    }
  }
}
</script>

