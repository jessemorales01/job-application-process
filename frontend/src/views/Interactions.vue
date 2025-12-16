<template>
  <Layout title="Interactions">
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

    <!-- Dialog for Add/Edit -->
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
              v-model="form.customer"
              :items="customers"
              item-title="name"
              item-value="id"
              label="Customer (Optional)"
            ></v-select>
            <v-select
              v-model="form.contact"
              :items="contacts"
              item-title="full_name"
              item-value="id"
              label="Contact (Optional)"
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
              required
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
          <v-btn text @click="dialog = false">Cancel</v-btn>
          <v-btn color="primary" @click="saveInteraction">Save</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </Layout>
</template>

<script>
import Layout from '../components/Layout.vue'
import api from '../services/api'

export default {
  name: 'Interactions',
  components: {
    Layout
  },
  data() {
    return {
      interactions: [],
      customers: [],
      contacts: [],
      loading: false,
      dialog: false,
      editMode: false,
      applications: [],
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
        { title: 'Application', key: 'application_company_name' },
        { title: 'Customer', key: 'customer_name' },
        { title: 'Contact', key: 'contact_name' },
        { title: 'Type', key: 'interaction_type' },
        { title: 'Direction', key: 'direction' },
        { title: 'Subject', key: 'subject' },
        { title: 'Date', key: 'interaction_date' },
        { title: 'Actions', key: 'actions', sortable: false }
      ],
      form: {
        application: null,
        customer: null,
        contact: null,
        interaction_type: '',
        direction: 'outbound',
        subject: '',
        notes: '',
        interaction_date: ''
      }
    }
  },
  async mounted() {
    await this.loadInteractions()
    await this.loadApplications()
    await this.loadCustomers()
    await this.loadContacts()
  },
  methods: {
    async loadInteractions() {
      this.loading = true
      try {
        const response = await api.get('/interactions/')
        this.interactions = response.data
      } catch (error) {
        console.error('Error loading interactions:', error)
      } finally {
        this.loading = false
      }
    },
    async loadCustomers() {
      try {
        const response = await api.get('/customers/')
        this.customers = response.data
      } catch (error) {
        console.error('Error loading customers:', error)
      }
    },
    async loadContacts() {
      try {
        const response = await api.get('/contacts/')
        this.contacts = response.data.map(contact => ({
          ...contact,
          full_name: `${contact.first_name} ${contact.last_name}`
        }))
      } catch (error) {
        console.error('Error loading contacts:', error)
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
    openDialog(interaction = null) {
      if (interaction) {
        this.editMode = true
        this.form = { ...interaction }
      } else {
        this.editMode = false
        const now = new Date()
        const localDateTime = new Date(now.getTime() - now.getTimezoneOffset() * 60000)
          .toISOString()
          .slice(0, 16)
        this.form = {
          application: null,
          customer: null,
          contact: null,
          interaction_type: '',
          direction: 'outbound',
          subject: '',
          notes: '',
          interaction_date: localDateTime
        }
      }
      this.dialog = true
    },
    async saveInteraction() {
      try {
        if (this.editMode) {
          await api.put(`/interactions/${this.form.id}/`, this.form)
        } else {
          await api.post('/interactions/', this.form)
        }
        this.dialog = false
        await this.loadInteractions()
      } catch (error) {
        console.error('Error saving interaction:', error)
      }
    },
    async deleteInteraction(id) {
      if (confirm('Are you sure you want to delete this interaction?')) {
        try {
          await api.delete(`/interactions/${id}/`)
          await this.loadInteractions()
        } catch (error) {
          console.error('Error deleting interaction:', error)
        }
      }
    }
  }
}
</script>
