<template>
  <Layout title="Contacts">
    <v-card>
      <v-card-title>
        Contacts Management
        <v-spacer></v-spacer>
        <v-btn color="primary" @click="openDialog()">
          <v-icon left>mdi-plus</v-icon>
          Add Contact
        </v-btn>
      </v-card-title>
      <v-card-text>
        <v-data-table
          :headers="headers"
          :items="contacts"
          :loading="loading"
        >
          <template v-slot:item.actions="{ item }">
            <v-icon small class="mr-2" @click="openDialog(item)">
              mdi-pencil
            </v-icon>
            <v-icon small @click="deleteContact(item.id)">
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
          {{ editMode ? 'Edit Contact' : 'Add Contact' }}
        </v-card-title>
        <v-card-text>
          <v-form @submit.prevent="saveContact">
            <v-text-field
              v-model="form.first_name"
              label="First Name"
              required
            ></v-text-field>
            <v-text-field
              v-model="form.last_name"
              label="Last Name"
              required
            ></v-text-field>
            <v-text-field
              v-model="form.email"
              label="Email"
              type="email"
              required
            ></v-text-field>
            <v-text-field
              v-model="form.phone"
              label="Phone"
            ></v-text-field>
            <v-text-field
              v-model="form.position"
              label="Position"
            ></v-text-field>
          </v-form>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn text @click="dialog = false">Cancel</v-btn>
          <v-btn color="primary" @click="saveContact">Save</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </Layout>
</template>

<script>
import Layout from '../components/Layout.vue'
import api from '../services/api'

export default {
  name: 'Contacts',
  components: {
    Layout
  },
  data() {
    return {
      contacts: [],
      loading: false,
      dialog: false,
      editMode: false,
      headers: [
        { title: 'First Name', key: 'first_name' },
        { title: 'Last Name', key: 'last_name' },
        { title: 'Email', key: 'email' },
        { title: 'Phone', key: 'phone' },
        { title: 'Position', key: 'position' },
        { title: 'Actions', key: 'actions', sortable: false }
      ],
      form: {
        first_name: '',
        last_name: '',
        email: '',
        phone: '',
        position: ''
      }
    }
  },
  async mounted() {
    await this.loadContacts()
  },
  methods: {
    async loadContacts() {
      this.loading = true
      try {
        const response = await api.get('/contacts/')
        this.contacts = response.data
      } catch (error) {
        console.error('Error loading contacts:', error)
      } finally {
        this.loading = false
      }
    },
    openDialog(contact = null) {
      if (contact) {
        this.editMode = true
        this.form = { ...contact }
      } else {
        this.editMode = false
        this.form = {
          first_name: '',
          last_name: '',
          email: '',
          phone: '',
          position: ''
        }
      }
      this.dialog = true
    },
    async saveContact() {
      try {
        if (this.editMode) {
          await api.put(`/contacts/${this.form.id}/`, this.form)
        } else {
          await api.post('/contacts/', this.form)
        }
        this.dialog = false
        await this.loadContacts()
      } catch (error) {
        console.error('Error saving contact:', error)
      }
    },
    async deleteContact(id) {
      if (confirm('Are you sure you want to delete this contact?')) {
        try {
          await api.delete(`/contacts/${id}/`)
          await this.loadContacts()
        } catch (error) {
          console.error('Error deleting contact:', error)
        }
      }
    }
  }
}
</script>
