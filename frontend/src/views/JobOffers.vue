<template>
  <Layout title="Job Offers">
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
              item-title="company_name"
              item-value="id"
              label="Application"
              required
            ></v-select>
            <v-text-field
              v-model="form.offer_date"
              label="Offer Date"
              type="date"
            ></v-text-field>
            <v-text-field
              v-model="form.salary_range"
              label="Salary Range"
              required
              hint="e.g., '120k', '100k-130k'"
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
          <v-btn text @click="dialog = false">Cancel</v-btn>
          <v-btn color="primary" @click="saveJobOffer">Save</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </Layout>
</template>

<script>
import Layout from '../components/Layout.vue'
import api from '../services/api'

export default {
  name: 'JobOffers',
  components: {
    Layout
  },
  data() {
    return {
      jobOffers: [],
      loading: false,
      dialog: false,
      editMode: false,
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
        application: null,
        offer_date: '',
        start_date: '',
        response_deadline: '',
        status: 'pending',
        notes: ''
      }
    }
  },
  async mounted() {
    await Promise.all([
      this.loadJobOffers(),
      this.loadApplications()
    ])
  },
  methods: {
    async loadJobOffers() {
      this.loading = true
      try {
        const response = await api.get('/job-offers/')
        this.jobOffers = response.data
      } catch (error) {
        console.error('Error loading job offers:', error)
      } finally {
        this.loading = false
      }
    },
    async loadApplications() {
      try {
        const response = await api.get('/applications/')
        this.applications = response.data
      } catch (error) {
        console.error('Error loading applications:', error)
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
    async saveJobOffer() {
      try {
        if (this.editMode) {
          await api.put(`/job-offers/${this.form.id}/`, this.form)
        } else {
          await api.post('/job-offers/', this.form)
        }
        this.dialog = false
        await this.loadJobOffers()
      } catch (error) {
        console.error('Error saving job offer:', error)
      }
    },
    async deleteJobOffer(id) {
      if (confirm('Are you sure you want to delete this job offer?')) {
        try {
          await api.delete(`/job-offers/${id}/`)
          await this.loadJobOffers()
        } catch (error) {
          console.error('Error deleting job offer:', error)
        }
      }
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

