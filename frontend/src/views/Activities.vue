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
          <v-btn text @click="assessmentDialog = false">Cancel</v-btn>
          <v-btn color="primary" @click="saveAssessment">Save</v-btn>
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
          <v-btn text @click="interactionDialog = false">Cancel</v-btn>
          <v-btn color="primary" @click="saveInteraction">Save</v-btn>
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
      statusOptions: [
        { title: 'Pending', value: 'pending' },
        { title: 'In Progress', value: 'in_progress' },
        { title: 'Submitted', value: 'submitted' },
        { title: 'Completed', value: 'completed' }
      ],
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
  methods: {
    showErrorNotification(message) {
      this.errorMessage = message
      this.showError = true
    },
    showSuccessNotification(message) {
      this.successMessage = message
      this.showSuccess = true
    },
    async loadAssessments() {
      this.loading = true
      try {
        const response = await api.get('/assessments/')
        this.assessments = response.data
      } catch (error) {
        const message = formatErrorMessage(error) || 'Failed to load assessments. Please refresh the page.'
        this.showErrorNotification(message)
      } finally {
        this.loading = false
      }
    },
    async loadInteractions() {
      try {
        const response = await api.get('/interactions/')
        this.interactions = response.data
      } catch (error) {
        const message = formatErrorMessage(error) || 'Failed to load interactions. Please refresh the page.'
        this.showErrorNotification(message)
      }
    },
    async loadApplications() {
      try {
        const response = await api.get('/applications/')
        this.applications = response.data.map(app => ({
          ...app,
          title: `${app.company_name}${app.position ? ` - ${app.position}` : ''}`
        }))
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
    async saveAssessment() {
      try {
        // Normalize website_url - add https:// if missing
        const formData = { ...this.assessmentForm }
        if (formData.website_url && formData.website_url.trim() && !formData.website_url.match(/^https?:\/\//)) {
          formData.website_url = 'https://' + formData.website_url.trim()
        }
        
        if (this.assessmentEditMode) {
          await api.put(`/assessments/${formData.id}/`, formData)
          this.showSuccessNotification('Assessment updated successfully!')
        } else {
          await api.post('/assessments/', formData)
          this.showSuccessNotification('Assessment created successfully!')
        }
        this.assessmentDialog = false
        await this.loadAssessments()
      } catch (error) {
        const message = formatErrorMessage(error) || 'Failed to save assessment. Please check the form fields and try again.'
        this.showErrorNotification(message)
      }
    },
    async saveInteraction() {
      try {
        if (this.interactionEditMode) {
          await api.put(`/interactions/${this.interactionForm.id}/`, this.interactionForm)
          this.showSuccessNotification('Interaction updated successfully!')
        } else {
          await api.post('/interactions/', this.interactionForm)
          this.showSuccessNotification('Interaction created successfully!')
        }
        this.interactionDialog = false
        await this.loadInteractions()
      } catch (error) {
        const message = formatErrorMessage(error) || 'Failed to save interaction. Please try again.'
        this.showErrorNotification(message)
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
    async deleteItem(item) {
      const itemType = item.originalType === 'assessment' ? 'assessment' : 'interaction'
      const itemName = itemType === 'assessment' ? 'Assessment' : 'Interaction'
      
      if (confirm(`Are you sure you want to delete this ${itemName.toLowerCase()}?`)) {
        try {
          await api.delete(`/${itemType}s/${item.originalId}/`)
          this.showSuccessNotification(`${itemName} deleted successfully!`)
          if (itemType === 'assessment') {
            await this.loadAssessments()
          } else {
            await this.loadInteractions()
          }
        } catch (error) {
          const message = formatErrorMessage(error) || `Failed to delete ${itemName.toLowerCase()}. Please try again.`
          this.showErrorNotification(message)
        }
      }
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

