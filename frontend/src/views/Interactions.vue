<template>
  <Layout title="Interactions">
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
        Interactions Management
        <v-spacer></v-spacer>
        <v-btn color="primary" @click="openDialog()">
          <v-icon left>mdi-plus</v-icon>
          Add Interaction
        </v-btn>
      </v-card-title>
      <v-card-text>
        <v-data-table
          :headers="headers"
          :items="interactions"
          :loading="loading"
        >
          <template v-slot:item.actions="{ item }">
            <v-icon small class="mr-2" @click="openDialog(item)">
              mdi-pencil
            </v-icon>
            <v-icon small @click="deleteInteraction(item.id)">
              mdi-delete
            </v-icon>
          </template>
        </v-data-table>
      </v-card-text>
    </v-card>

    <v-dialog v-model="dialog" max-width="600px">
      <v-card>
        <v-card-title>
          {{ editMode ? 'Edit Interaction' : 'Add Interaction' }}
        </v-card-title>
        <v-card-text>
          <v-form @submit.prevent="saveInteraction">
            <v-select
              v-model="form.application"
              :items="applications"
              item-title="company_name"
              item-value="id"
              label="Application (Optional)"
            ></v-select>
            <v-select
              v-model="form.interaction_type"
              :items="interactionTypes"
              label="Interaction Type"
              required
            ></v-select>
            <v-select
              v-model="form.direction"
              :items="directionOptions"
              label="Direction"
            ></v-select>
            <v-text-field
              v-model="form.subject"
              label="Subject"
              required
            ></v-text-field>
            <v-textarea
              v-model="form.notes"
              label="Notes"
              required
            ></v-textarea>
            <v-text-field
              v-model="form.interaction_date"
              label="Interaction Date"
              type="datetime-local"
              required
            ></v-text-field>
          </v-form>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn text :disabled="interactionSaving" @click="dialog = false">Cancel</v-btn>
          <v-btn
            color="primary"
            :loading="interactionSaving"
            :disabled="interactionSaving"
            @click="saveInteraction"
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
  name: 'Interactions',
  components: {
    Layout,
    ErrorSnackbar
  },
  data() {
    return {
      interactions: [],
      loading: false,
      dialog: false,
      editMode: false,
      showError: false,
      errorMessage: '',
      showSuccess: false,
      successMessage: '',
      interactionSaving: false,
      deletingInteractionId: null,
      skipNextActivatedRefresh: true,
      interactionTypes: [
        { title: 'Email', value: 'email' },
        { title: 'Phone Call', value: 'phone' },
        { title: 'Meeting', value: 'meeting' },
        { title: 'Interview', value: 'interview' },
        { title: 'Follow-up', value: 'follow_up' },
        { title: 'Other', value: 'other' }
      ],
      directionOptions: [
        { title: 'Inbound', value: 'inbound' },
        { title: 'Outbound', value: 'outbound' }
      ],
      applications: [],
      headers: [
        { title: 'Application', key: 'application_company_name' },
        { title: 'Type', key: 'interaction_type' },
        { title: 'Subject', key: 'subject' },
        { title: 'Date', key: 'interaction_date' },
        { title: 'Actions', key: 'actions', sortable: false }
      ],
      form: {
        application: null,
        interaction_type: '',
        direction: 'outbound',
        subject: '',
        notes: '',
        interaction_date: ''
      }
    }
  },
  async mounted() {
    await Promise.all([this.loadInteractions(), this.loadApplications()])
  },
  activated() {
    if (this.skipNextActivatedRefresh) {
      this.skipNextActivatedRefresh = false
      return
    }
    Promise.all([this.loadInteractions(), this.loadApplications()])
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
    async loadInteractions(options = {}) {
      const force = options.force === true
      const key = 'interactions'
      const e = getEntry(key)
      try {
        if (!force && !e.dirty && e.fetched) {
          this.interactions = e.data || []
          return
        }
        const { data } = await getOrFetch(key, '/interactions/', { force })
        this.interactions = data || []
      } catch (error) {
        const message = formatErrorMessage(error) || 'Failed to load interactions. Please refresh the page.'
        this.showErrorNotification(message)
      }
    },
    async loadApplications(options = {}) {
      const force = options.force === true
      const key = 'applications'
      const e = getEntry(key)
      try {
        if (!force && !e.dirty && e.fetched) {
          this.applications = e.data || []
          return
        }
        const { data } = await getOrFetch(key, '/applications/', { force })
        this.applications = data || []
      } catch (error) {
        const message = formatErrorMessage(error) || 'Failed to load applications.'
        this.showErrorNotification(message)
      }
    },
    openDialog(interaction = null) {
      if (interaction) {
        this.editMode = true
        this.form = { ...interaction }
        if (this.form.interaction_date) {
          const date = new Date(this.form.interaction_date)
          const localDateTime = new Date(date.getTime() - date.getTimezoneOffset() * 60000)
            .toISOString()
            .slice(0, 16)
          this.form.interaction_date = localDateTime
        }
      } else {
        this.editMode = false
        const now = new Date()
        const localDateTime = new Date(now.getTime() - now.getTimezoneOffset() * 60000)
          .toISOString()
          .slice(0, 16)
        this.form = {
          application: null,
          interaction_type: '',
          direction: 'outbound',
          subject: '',
          notes: '',
          interaction_date: localDateTime
        }
      }
      this.dialog = true
    },
    saveInteraction() {
      if (this.interactionSaving) return
      this.interactionSaving = true
      this.showError = false

      const form = { ...this.form }
      const errs = []
      if (!form.interaction_type) errs.push('Interaction type is required.')
      if (!form.subject || !String(form.subject).trim()) errs.push('Subject is required.')
      if (!form.notes || !String(form.notes).trim()) errs.push('Notes are required.')
      if (!form.interaction_date) errs.push('Interaction date is required.')
      if (errs.length) {
        this.showErrorNotification(errs.join(' '))
        this.interactionSaving = false
        return
      }

      const finish = () => {
        this.interactionSaving = false
      }

      try {
        if (this.editMode) {
          const idx = this.interactions.findIndex((i) => i.id === form.id)
          if (idx === -1) {
            finish()
            return
          }
          const snapshot = { ...this.interactions[idx] }
          const app = this.applications.find((a) => a.id === form.application)
          const updated = {
            ...this.interactions[idx],
            ...form,
            application_company_name: app
              ? app.company_name
              : this.interactions[idx].application_company_name,
          }
          this.interactions.splice(idx, 1, updated)
          putCached('interactions', [...this.interactions])
          this.dialog = false
          this.showSuccessNotification('Interaction updated successfully!')

          api
            .put(`/interactions/${form.id}/`, form)
            .then(({ data }) => {
              const i = this.interactions.findIndex((x) => x.id === form.id)
              if (i !== -1 && data && typeof data === 'object' && Object.keys(data).length > 0) {
                this.interactions.splice(i, 1, { ...this.interactions[i], ...data })
                putCached('interactions', [...this.interactions])
              }
              markDirty('interactions')
              markDirtyDashboardLists()
            })
            .catch((error) => {
              const i = this.interactions.findIndex((x) => x.id === form.id)
              if (i !== -1) this.interactions.splice(i, 1, snapshot)
              putCached('interactions', [...this.interactions])
              markDirty('interactions')
              this.showErrorNotification(
                formatErrorMessage(error) || 'Failed to save interaction. Please try again.'
              )
            })
            .finally(finish)
          return
        }

        const tempId = -Date.now()
        const app = this.applications.find((a) => a.id === form.application)
        const optimistic = {
          id: tempId,
          application: form.application,
          application_company_name: app ? app.company_name : undefined,
          interaction_type: form.interaction_type,
          direction: form.direction || 'outbound',
          subject: form.subject,
          notes: form.notes,
          interaction_date: form.interaction_date,
        }
        this.interactions = [optimistic, ...this.interactions]
        putCached('interactions', [...this.interactions])
        this.dialog = false
        this.showSuccessNotification('Interaction added')

        api
          .post('/interactions/', form)
          .then(({ data }) => {
            const idx = this.interactions.findIndex((i) => i.id === tempId)
            if (idx !== -1) {
              const merged =
                data && typeof data === 'object' ? { ...optimistic, ...data } : optimistic
              this.interactions.splice(idx, 1, merged)
              putCached('interactions', [...this.interactions])
            }
            markDirty('interactions')
            markDirtyDashboardLists()
          })
          .catch((error) => {
            const idx = this.interactions.findIndex((i) => i.id === tempId)
            if (idx !== -1) {
              this.interactions.splice(idx, 1)
              putCached('interactions', [...this.interactions])
            }
            markDirty('interactions')
            this.showErrorNotification(
              formatErrorMessage(error) || 'Failed to save interaction. Please try again.'
            )
          })
          .finally(finish)
      } catch (error) {
        finish()
        this.showErrorNotification(
          formatErrorMessage(error) || 'Failed to save interaction. Please try again.'
        )
      }
    },
    deleteInteraction(id) {
      if (!confirm('Are you sure you want to delete this interaction?')) return
      if (this.deletingInteractionId != null) return
      const idx = this.interactions.findIndex((i) => i.id === id)
      if (idx === -1) return
      const snapshot = this.interactions[idx]
      this.deletingInteractionId = id
      this.interactions.splice(idx, 1)
      putCached('interactions', [...this.interactions])
      this.showSuccessNotification('Interaction removed')

      api
        .delete(`/interactions/${id}/`)
        .then(() => {
          markDirty('interactions')
          markDirtyDashboardLists()
        })
        .catch((error) => {
          const at = Math.min(idx, this.interactions.length)
          this.interactions.splice(at, 0, snapshot)
          putCached('interactions', [...this.interactions])
          markDirty('interactions')
          this.showErrorNotification(
            formatErrorMessage(error) || 'Failed to delete interaction. Please try again.'
          )
        })
        .finally(() => {
          this.deletingInteractionId = null
        })
    }
  }
}
</script>
