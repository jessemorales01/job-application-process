<template>
  <Layout title="Customers">
    <v-card>
      <v-card-title>
        Customers Management
        <v-spacer></v-spacer>
        <v-btn color="primary" @click="openDialog()">
          <v-icon left>mdi-plus</v-icon>
          Add Customer
        </v-btn>
      </v-card-title>
      <v-card-text>
        <v-data-table
          :headers="headers"
          :items="customers"
          :loading="loading"
        >
          <template v-slot:item.actions="{ item }">
            <v-icon small class="mr-2" @click="openDialog(item)">
              mdi-pencil
            </v-icon>
            <v-icon small @click="deleteCustomer(item.id)">
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
          {{ editMode ? 'Edit Customer' : 'Add Customer' }}
        </v-card-title>
        <v-card-text>
          <v-form @submit.prevent="saveCustomer">
            <v-text-field
              v-model="form.name"
              label="Name"
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
              v-model="form.company"
              label="Company"
            ></v-text-field>
            <v-textarea
              v-model="form.address"
              label="Address"
            ></v-textarea>
          </v-form>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn text @click="dialog = false">Cancel</v-btn>
          <v-btn color="primary" @click="saveCustomer">Save</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </Layout>
</template>

<script>
import Layout from '../components/Layout.vue'
import api from '../services/api'

export default {
  name: 'Customers',
  components: {
    Layout
  },
  data() {
    return {
      customers: [],
      loading: false,
      dialog: false,
      editMode: false,
      headers: [
        { title: 'Name', key: 'name' },
        { title: 'Email', key: 'email' },
        { title: 'Phone', key: 'phone' },
        { title: 'Company', key: 'company' },
        { title: 'Actions', key: 'actions', sortable: false }
      ],
      form: {
        name: '',
        email: '',
        phone: '',
        company: '',
        address: ''
      }
    }
  },
  async mounted() {
    await this.loadCustomers()
  },
  methods: {
    async loadCustomers() {
      this.loading = true
      try {
        const response = await api.get('/customers/')
        this.customers = response.data
      } catch (error) {
        console.error('Error loading customers:', error)
      } finally {
        this.loading = false
      }
    },
    openDialog(customer = null) {
      if (customer) {
        this.editMode = true
        this.form = { ...customer }
      } else {
        this.editMode = false
        this.form = {
          name: '',
          email: '',
          phone: '',
          company: '',
          address: ''
        }
      }
      this.dialog = true
    },
    async saveCustomer() {
      try {
        if (this.editMode) {
          await api.put(`/customers/${this.form.id}/`, this.form)
        } else {
          await api.post('/customers/', this.form)
        }
        this.dialog = false
        await this.loadCustomers()
      } catch (error) {
        console.error('Error saving customer:', error)
      }
    },
    async deleteCustomer(id) {
      if (confirm('Are you sure you want to delete this customer?')) {
        try {
          await api.delete(`/customers/${id}/`)
          await this.loadCustomers()
        } catch (error) {
          console.error('Error deleting customer:', error)
        }
      }
    }
  }
}
</script>
