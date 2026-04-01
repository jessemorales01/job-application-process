<template>
  <Layout title="Activities">
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
        Activities Management
        <v-spacer></v-spacer>
        <v-btn color="primary" class="mr-2" @click="openAssessmentDialog()">
          <v-icon left>mdi-plus</v-icon>
          Add Assessment
        </v-btn>
        <v-btn color="primary" @click="openInteractionDialog()">
          <v-icon left>mdi-plus</v-icon>
          Add Interaction
        </v-btn>
      </v-card-title>
      <v-card-text>
        <v-select
          v-model="selectedApplication"
          :items="applicationOptions"
          item-title="label"
          item-value="id"
          label="Filter by Job Opportunity (Optional)"
          clearable
          class="mb-4"
        ></v-select>
        
        <v-data-table
          :headers="headers"
          :items="filteredActivities"
          :loading="loading"
          :items-per-page="25"
        >
          <template v-slot:item.type="{ item }">
            <v-chip :color="getTypeColor(item.type)" small>
              {{ item.type }}
            </v-chip>
          </template>
          <template v-slot:item.application_info="{ item }">
            {{ item.application_company_name || item.application?.company_name || 'N/A' }}
          </template>
          <template v-slot:item.deadline="{ item }">
            <span v-if="item.deadline">
              {{ new Date(item.deadline).toLocaleDateString() }}
              <v-chip 
                v-if="isDeadlineApproaching(item.deadline)" 
                :color="getDeadlineColor(item.deadline)" 
                x-small 
                class="ml-2"
              >
                {{ getDeadlineLabel(item.deadline) }}
              </v-chip>
            </span>
            <span v-else>-</span>
          </template>
          <template v-slot:item.status="{ item }">
            <v-chip v-if="item.status" :color="getStatusColor(item.status)" small>
              {{ getStatusLabel(item.status) }}
            </v-chip>
            <span v-else>-</span>
          </template>
          <template v-slot:item.date="{ item }">
            <span v-if="item.deadline">
              {{ new Date(item.deadline).toLocaleDateString() }}
            </span>
            <span v-else-if="item.interaction_date">
              {{ new Date(item.interaction_date).toLocaleDateString() }}
            </span>
            <span v-else>-</span>
          </template>
          <template v-slot:item.actions="{ item }">
            <v-icon small class="mr-2" @click="editItem(item)">
              mdi-pencil
            </v-icon>
            <v-icon small @click="deleteItem(item)">
              mdi-delete
            </v-icon>
          </template>
        </v-data-table>
      </v-card-text>
    </v-card>

    <!-- Assessment Dialog -->
    <v-dialog v-model="assessmentDialog" max-width="600px">
      <v-card>
        <v-card-title>
          {{ assessmentEditMode ? 'Edit Assessment' : 'Add Assessment' }}
        </v-card-title>
        <v-card-text>
          <v-form @submit.prevent="saveAssessment">
            <v-select
              v-model="assessmentForm.application"
              :items="applications"
              item-title="title"
              item-value="id"
              label="Job Opportunity"
              required
            ></v-select>
            <v-text-field
              v-model="assessmentForm.deadline"
              label="Deadline"
              type="date"
              required
            ></v-text-field>
            <v-text-field
              v-model="assessmentForm.website_url"
              label="Website URL"
              hint="URL for assessment platform or project submission"
            ></v-text-field>
            <v-text-field
              v-model="assessmentForm.recruiter_contact_name"
              label="Recruiter Contact Name"
            ></v-text-field>
            <v-text-field
              v-model="assessmentForm.recruiter_contact_email"
              label="Recruiter Contact Email"
              type="email"
            ></v-text-field>
            <v-text-field
              v-model="assessmentForm.recruiter_contact_phone"
              label="Recruiter Contact Phone"
            ></v-text-field>
            <v-select
              v-model="assessmentForm.status"
              :items="statusOptions"
              label="Status"
              required
            ></v-select>
            <v-textarea
              v-model="assessmentForm.notes"
              label="Notes"
            ></v-textarea>
          </v-form>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn text :disabled="assessmentSaving" @click="assessmentDialog = false">Cancel</v-btn>
          <v-btn
            color="primary"
            :loading="assessmentSaving"
            :disabled="assessmentSaving"
            @click="saveAssessment"
          >
            Save
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Interaction Dialog -->
    <v-dialog v-model="interactionDialog" max-width="600px">
      <v-card>
        <v-card-title>
          {{ interactionEditMode ? 'Edit Interaction' : 'Add Interaction' }}
        </v-card-title>
        <v-card-text>
          <v-form @submit.prevent="saveInteraction">
            <v-select
              v-model="interactionForm.application"
              :items="applications"
              item-title="title"
              item-value="id"
              label="Job Opportunity (Optional)"
            ></v-select>
            <v-select
              v-model="interactionForm.interaction_type"
              :items="interactionTypes"
              label="Interaction Type"
              required
            ></v-select>
            <v-select
              v-model="interactionForm.direction"
              :items="directionOptions"
              label="Direction"
            ></v-select>
            <v-text-field
              v-model="interactionForm.subject"
              label="Subject"
              required
            ></v-text-field>
            <v-textarea
              v-model="interactionForm.notes"
              label="Notes"
              required
            ></v-textarea>
            <v-text-field
              v-model="interactionForm.interaction_date"
              label="Interaction Date"
              type="datetime-local"
              required
            ></v-text-field>
          </v-form>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn text :disabled="interactionSaving" @click="interactionDialog = false">Cancel</v-btn>
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
  name: 'Activities',
  components: {
    Layout,
    ErrorSnackbar
  },
  data() {
    return {
      assessments: [],
      interactions: [],
      applications: [],
      loading: false,
      selectedApplication: null,
      assessmentDialog: false,
      interactionDialog: false,
      assessmentEditMode: false,
      interactionEditMode: false,
      showError: false,
      errorMessage: '',
      showSuccess: false,
      successMessage: '',
      assessmentSaving: false,
      interactionSaving: false,
      /** In-flight delete per row only — avoids double-click on same item; other rows can delete in parallel. */
      deletingActivityKeys: {},
      statusOptions: [
        { title: 'Pending', value: 'pending' },
        { title: 'In Progress', value: 'in_progress' },
        { title: 'Submitted', value: 'submitted' },
        { title: 'Completed', value: 'completed' }
      ],
      skipNextActivatedRefresh: true,
      interactionTypes: [
        { title: 'Email', value: 'email' },
        { title: 'Phone Call', value: 'phone' },
        { title: 'Meeting', value: 'meeting' },
        { title: 'Interview', value: 'interview' },
        { title: 'Follow-up', value: 'follow-up' },
        { title: 'Other', value: 'other' }
      ],
      directionOptions: [
        { title: 'Inbound', value: 'inbound' },
        { title: 'Outbound', value: 'outbound' }
      ],
      headers: [
        { title: 'Type', key: 'type', sortable: true },
        { title: 'Job Opportunity', key: 'application_info', sortable: true },
        { title: 'Subject/Title', key: 'subject', sortable: true },
        { title: 'Deadline', key: 'deadline', sortable: true },
        { title: 'Status', key: 'status', sortable: true },
        { title: 'Date', key: 'date', sortable: true },
        { title: 'Actions', key: 'actions', sortable: false }
      ],
      assessmentForm: {
        application: null,
        deadline: '',
        website_url: '',
        recruiter_contact_name: '',
        recruiter_contact_email: '',
        recruiter_contact_phone: '',
        status: 'pending',
        notes: ''
      },
      interactionForm: {
        application: null,
        interaction_type: '',
        direction: 'outbound',
        subject: '',
        notes: '',
        interaction_date: ''
      }
    }
  },
  computed: {
    applicationOptions() {
      return [
        { id: null, label: 'All Job Opportunities' },
        ...this.applications.map(app => ({
          id: app.id,
          label: `${app.company_name}${app.position ? ` - ${app.position}` : ''}`
        }))
      ]
    },
    filteredActivities() {
      let activities = []
      
      // Add assessments
      this.assessments.forEach(assessment => {
        activities.push({
          ...assessment,
          type: 'Assessment',
          subject: `Assessment: ${assessment.application_company_name || 'N/A'}`,
          id: `assessment-${assessment.id}`,
          originalId: assessment.id,
          originalType: 'assessment',
          application: assessment.application // Keep application ID for filtering
        })
      })
      
      // Add interactions
      this.interactions.forEach(interaction => {
        activities.push({
          ...interaction,
          type: 'Interaction',
          subject: interaction.subject,
          id: `interaction-${interaction.id}`,
          originalId: interaction.id,
          originalType: 'interaction',
          application: interaction.application // Keep application ID for filtering
        })
      })
      
      // Filter by application if selected
      if (this.selectedApplication) {
        activities = activities.filter(activity => {
          return activity.application === this.selectedApplication
        })
      }
      
      // Sort by date (most recent first)
      return activities.sort((a, b) => {
        const dateA = a.deadline || a.interaction_date
        const dateB = b.deadline || b.interaction_date
        
        // Handle missing dates - put them at the end
        if (!dateA && !dateB) return 0
        if (!dateA) return 1
        if (!dateB) return -1
        
        const dateAObj = new Date(dateA)
        const dateBObj = new Date(dateB)
        
        // Handle invalid dates
        if (isNaN(dateAObj.getTime()) && isNaN(dateBObj.getTime())) return 0
        if (isNaN(dateAObj.getTime())) return 1
        if (isNaN(dateBObj.getTime())) return -1
        
        return dateBObj - dateAObj
      })
    }
  },
  async mounted() {
    await Promise.all([
      this.loadAssessments(),
      this.loadInteractions(),
      this.loadApplications()
    ])
  },
  activated() {
    if (this.skipNextActivatedRefresh) {
      this.skipNextActivatedRefresh = false
      return
    }
    Promise.all([
      this.loadAssessments(),
      this.loadInteractions(),
      this.loadApplications()
    ])
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
    async loadAssessments(options = {}) {
      const force = options.force === true
      const key = 'assessments'
      const e = getEntry(key)
      if (!force && !e.dirty && e.fetched) {
        this.assessments = e.data || []
        return
      }
      if (e.fetched) {
        this.assessments = e.data || []
      }
      this.loading = !e.fetched
      try {
        const { data } = await getOrFetch(key, '/assessments/', { force })
        this.assessments = data || []
      } catch (error) {
        const message = formatErrorMessage(error) || 'Failed to load assessments. Please refresh the page.'
        this.showErrorNotification(message)
      } finally {
        this.loading = false
      }
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
    openAssessmentDialog(assessment = null) {
      if (assessment) {
        this.assessmentEditMode = true
        this.assessmentForm = { ...assessment }
        if (this.assessmentForm.deadline) {
          this.assessmentForm.deadline = this.assessmentForm.deadline.split('T')[0]
        }
      } else {
        this.assessmentEditMode = false
        this.assessmentForm = {
          application: null,
          deadline: '',
          website_url: '',
          recruiter_contact_name: '',
          recruiter_contact_email: '',
          recruiter_contact_phone: '',
          status: 'pending',
          notes: ''
        }
      }
      this.assessmentDialog = true
    },
    openInteractionDialog(interaction = null) {
      if (interaction) {
        this.interactionEditMode = true
        this.interactionForm = { ...interaction }
        if (this.interactionForm.interaction_date) {
          const date = new Date(this.interactionForm.interaction_date)
          const localDateTime = new Date(date.getTime() - date.getTimezoneOffset() * 60000)
            .toISOString()
            .slice(0, 16)
          this.interactionForm.interaction_date = localDateTime
        }
      } else {
        this.interactionEditMode = false
        const now = new Date()
        const localDateTime = new Date(now.getTime() - now.getTimezoneOffset() * 60000)
          .toISOString()
          .slice(0, 16)
        this.interactionForm = {
          application: null,
          interaction_type: '',
          direction: 'outbound',
          subject: '',
          notes: '',
          interaction_date: localDateTime
        }
      }
      this.interactionDialog = true
    },
    saveAssessment() {
      if (this.assessmentSaving) return
      this.assessmentSaving = true
      this.showError = false

      const formData = { ...this.assessmentForm }
      if (formData.website_url && formData.website_url.trim() && !formData.website_url.match(/^https?:\/\//)) {
        formData.website_url = 'https://' + formData.website_url.trim()
      }

      const assessmentErrors = []
      if (formData.application == null || formData.application === '') {
        assessmentErrors.push('Application is required.')
      }
      if (!formData.deadline) assessmentErrors.push('Deadline is required.')
      if (!formData.status) assessmentErrors.push('Status is required.')
      if (assessmentErrors.length) {
        this.showErrorNotification(assessmentErrors.join(' '))
        this.assessmentSaving = false
        return
      }

      const finish = () => {
        this.assessmentSaving = false
      }

      try {
        if (this.assessmentEditMode) {
          const idx = this.assessments.findIndex((a) => a.id === formData.id)
          if (idx === -1) {
            finish()
            return
          }
          const snapshot = { ...this.assessments[idx] }
          const app = this.applications.find((a) => a.id === formData.application)
          const updated = {
            ...this.assessments[idx],
            ...formData,
            application_company_name: app
              ? app.company_name
              : this.assessments[idx].application_company_name,
          }
          this.assessments.splice(idx, 1, updated)
          putCached('assessments', [...this.assessments])
          this.assessmentDialog = false
          this.showSuccessNotification('Assessment updated successfully!')

          api
            .put(`/assessments/${formData.id}/`, formData)
            .then(({ data }) => {
              const i = this.assessments.findIndex((x) => x.id === formData.id)
              if (i !== -1 && data && typeof data === 'object' && Object.keys(data).length > 0) {
                this.assessments.splice(i, 1, { ...this.assessments[i], ...data })
                putCached('assessments', [...this.assessments])
              }
              markDirty('assessments')
              markDirtyDashboardLists()
            })
            .catch((error) => {
              const i = this.assessments.findIndex((x) => x.id === formData.id)
              if (i !== -1) this.assessments.splice(i, 1, snapshot)
              putCached('assessments', [...this.assessments])
              markDirty('assessments')
              this.showErrorNotification(
                formatErrorMessage(error) ||
                  'Failed to save assessment. Please check the form fields and try again.'
              )
            })
            .finally(finish)
          return
        }

        const tempId = -Date.now()
        const app = this.applications.find((a) => a.id === formData.application)
        const optimistic = {
          id: tempId,
          application: formData.application,
          application_company_name: app ? app.company_name : undefined,
          deadline: formData.deadline,
          website_url: formData.website_url,
          recruiter_contact_name: formData.recruiter_contact_name,
          recruiter_contact_email: formData.recruiter_contact_email,
          recruiter_contact_phone: formData.recruiter_contact_phone,
          status: formData.status,
          notes: formData.notes,
        }
        this.assessments = [optimistic, ...this.assessments]
        putCached('assessments', [...this.assessments])
        this.assessmentDialog = false
        this.showSuccessNotification('Assessment created successfully!')

        api
          .post('/assessments/', formData)
          .then(({ data }) => {
            const idx = this.assessments.findIndex((a) => a.id === tempId)
            if (idx !== -1) {
              const merged =
                data && typeof data === 'object' ? { ...optimistic, ...data } : optimistic
              this.assessments.splice(idx, 1, merged)
              putCached('assessments', [...this.assessments])
            }
            markDirty('assessments')
            markDirtyDashboardLists()
          })
          .catch((error) => {
            const idx = this.assessments.findIndex((a) => a.id === tempId)
            if (idx !== -1) {
              this.assessments.splice(idx, 1)
              putCached('assessments', [...this.assessments])
            }
            markDirty('assessments')
            this.showErrorNotification(
              formatErrorMessage(error) ||
                'Failed to save assessment. Please check the form fields and try again.'
            )
          })
          .finally(finish)
      } catch (error) {
        finish()
        this.showErrorNotification(
          formatErrorMessage(error) ||
            'Failed to save assessment. Please check the form fields and try again.'
        )
      }
    },
    saveInteraction() {
      if (this.interactionSaving) return
      this.interactionSaving = true
      this.showError = false

      const form = { ...this.interactionForm }
      const interactionValidationError = () => {
        if (!form.interaction_type) return 'Interaction type is required.'
        if (!form.subject || !String(form.subject).trim()) return 'Subject is required.'
        if (!form.notes || !String(form.notes).trim()) return 'Notes are required.'
        if (!form.interaction_date) return 'Interaction date is required.'
        return null
      }
      const validationMsg = interactionValidationError()
      if (validationMsg) {
        this.showErrorNotification(validationMsg)
        this.interactionSaving = false
        return
      }

      const finish = () => {
        this.interactionSaving = false
      }

      try {
        if (this.interactionEditMode) {
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
          this.interactionDialog = false
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
        this.interactionDialog = false
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
    editItem(item) {
      if (item.originalType === 'assessment') {
        const assessment = this.assessments.find(a => a.id === item.originalId)
        this.openAssessmentDialog(assessment)
      } else {
        const interaction = this.interactions.find(i => i.id === item.originalId)
        this.openInteractionDialog(interaction)
      }
    },
    clearDeletingActivityKey(key) {
      if (!key || !this.deletingActivityKeys[key]) return
      const next = { ...this.deletingActivityKeys }
      delete next[key]
      this.deletingActivityKeys = next
    },
    /**
     * After optimistic DELETE, only restore the row if the server rejected a real failure.
     * 404 = resource already absent (idempotent delete); keep UI as-is.
     */
    deleteErrorRequiresRestore(error) {
      return error?.response?.status !== 404
    },
    restoreAssessmentAfterFailedDelete(snapshot) {
      if (this.assessments.some((a) => a.id === snapshot.id)) return
      this.assessments.push({ ...snapshot })
      this.assessments.sort((a, b) => {
        const da = a.deadline || ''
        const db = b.deadline || ''
        return da.localeCompare(db)
      })
      putCached('assessments', [...this.assessments])
    },
    restoreInteractionAfterFailedDelete(snapshot) {
      if (this.interactions.some((i) => i.id === snapshot.id)) return
      this.interactions.push({ ...snapshot })
      this.interactions.sort((a, b) => {
        const ta = new Date(a.interaction_date).getTime()
        const tb = new Date(b.interaction_date).getTime()
        if (Number.isNaN(ta) && Number.isNaN(tb)) return 0
        if (Number.isNaN(ta)) return 1
        if (Number.isNaN(tb)) return -1
        return tb - ta
      })
      putCached('interactions', [...this.interactions])
    },
    deleteItem(item) {
      const itemType = item.originalType === 'assessment' ? 'assessment' : 'interaction'
      const itemName = itemType === 'assessment' ? 'Assessment' : 'Interaction'
      if (!confirm(`Are you sure you want to delete this ${itemName.toLowerCase()}?`)) return
      const key = `${itemType}-${item.originalId}`
      if (this.deletingActivityKeys[key]) return
      this.deletingActivityKeys = { ...this.deletingActivityKeys, [key]: true }

      if (itemType === 'assessment') {
        const idx = this.assessments.findIndex((a) => a.id === item.originalId)
        if (idx === -1) {
          this.clearDeletingActivityKey(key)
          return
        }
        const snapshot = this.assessments[idx]
        this.assessments.splice(idx, 1)
        putCached('assessments', [...this.assessments])
        this.showSuccessNotification(`${itemName} removed`)
        api
          .delete(`/assessments/${item.originalId}/`)
          .then(() => {
            markDirty('assessments')
            markDirtyDashboardLists()
          })
          .catch((error) => {
            if (this.deleteErrorRequiresRestore(error)) {
              this.restoreAssessmentAfterFailedDelete(snapshot)
              markDirty('assessments')
              this.showErrorNotification(
                formatErrorMessage(error) ||
                  `Failed to delete ${itemName.toLowerCase()}. Please try again.`
              )
            } else {
              markDirty('assessments')
              markDirtyDashboardLists()
            }
          })
          .finally(() => {
            this.clearDeletingActivityKey(key)
          })
        return
      }

      const idx = this.interactions.findIndex((i) => i.id === item.originalId)
      if (idx === -1) {
        this.clearDeletingActivityKey(key)
        return
      }
      const snapshot = this.interactions[idx]
      this.interactions.splice(idx, 1)
      putCached('interactions', [...this.interactions])
      this.showSuccessNotification(`${itemName} removed`)
      api
        .delete(`/interactions/${item.originalId}/`)
        .then(() => {
          markDirty('interactions')
          markDirtyDashboardLists()
        })
        .catch((error) => {
          if (this.deleteErrorRequiresRestore(error)) {
            this.restoreInteractionAfterFailedDelete(snapshot)
            markDirty('interactions')
            this.showErrorNotification(
              formatErrorMessage(error) ||
                `Failed to delete ${itemName.toLowerCase()}. Please try again.`
            )
          } else {
            markDirty('interactions')
            markDirtyDashboardLists()
          }
        })
        .finally(() => {
          this.clearDeletingActivityKey(key)
        })
    },
    getTypeColor(type) {
      return type === 'Assessment' ? 'blue' : 'green'
    },
    getStatusColor(status) {
      const colors = {
        pending: 'orange',
        in_progress: 'blue',
        submitted: 'purple',
        completed: 'green'
      }
      return colors[status] || 'grey'
    },
    getStatusLabel(status) {
      const labels = {
        pending: 'Pending',
        in_progress: 'In Progress',
        submitted: 'Submitted',
        completed: 'Completed'
      }
      return labels[status] || status
    },
    isDeadlineApproaching(deadline) {
      if (!deadline) return false
      const deadlineDate = new Date(deadline)
      const today = new Date()
      const diffTime = deadlineDate - today
      const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24))
      return diffDays <= 7 && diffDays >= 0
    },
    getDeadlineColor(deadline) {
      if (!deadline) return 'grey'
      const deadlineDate = new Date(deadline)
      const today = new Date()
      const diffTime = deadlineDate - today
      const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24))
      
      if (diffDays < 0) return 'red' // Overdue
      if (diffDays <= 2) return 'red' // Due soon
      if (diffDays <= 7) return 'orange' // Approaching
      return 'green'
    },
    getDeadlineLabel(deadline) {
      if (!deadline) return ''
      const deadlineDate = new Date(deadline)
      const today = new Date()
      const diffTime = deadlineDate - today
      const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24))
      
      if (diffDays < 0) return 'Overdue'
      if (diffDays === 0) return 'Due Today'
      if (diffDays === 1) return 'Due Tomorrow'
      return `${diffDays} days left`
    }
  }
}
</script>

