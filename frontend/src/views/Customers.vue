<template>
  <Layout title="Customers">
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
          <v-btn text :disabled="customerSaving" @click="dialog = false">Cancel</v-btn>
          <v-btn
            color="primary"
            :loading="customerSaving"
            :disabled="customerSaving"
            @click="saveCustomer"
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

export default {
  name: 'Customers',
  components: {
    Layout,
    ErrorSnackbar
  },
  data() {
    return {
      customers: [],
      loading: false,
      dialog: false,
      editMode: false,
      customerSaving: false,
      deletingCustomerId: null,
      showError: false,
      errorMessage: '',
      showSuccess: false,
      successMessage: '',
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
    showErrorNotification(message) {
      this.errorMessage = message
      this.showError = true
    },
    showSuccessNotification(message) {
      this.successMessage = message
      this.showSuccess = true
    },
    async loadCustomers() {
      this.loading = true
      try {
        const response = await api.get('/customers/')
        this.customers = response.data
      } catch (error) {
        this.showErrorNotification(
          formatErrorMessage(error) || 'Failed to load customers. Please refresh the page.'
        )
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
    saveCustomer() {
      if (this.customerSaving) return
      this.customerSaving = true
      this.showError = false

      const form = { ...this.form }
      const errs = []
      if (!form.name || !String(form.name).trim()) errs.push('Name is required.')
      if (!form.email || !String(form.email).trim()) errs.push('Email is required.')
      if (errs.length) {
        this.showErrorNotification(errs.join(' '))
        this.customerSaving = false
        return
      }

      const finish = () => {
        this.customerSaving = false
      }

      try {
        if (this.editMode) {
          const idx = this.customers.findIndex((c) => c.id === form.id)
          if (idx === -1) {
            finish()
            return
          }
          const snapshot = { ...this.customers[idx] }
          this.customers.splice(idx, 1, { ...this.customers[idx], ...form })
          this.dialog = false
          this.showSuccessNotification('Customer updated')

          api
            .put(`/customers/${form.id}/`, form)
            .then(({ data }) => {
              const i = this.customers.findIndex((x) => x.id === form.id)
              if (i !== -1 && data && typeof data === 'object' && Object.keys(data).length > 0) {
                this.customers.splice(i, 1, { ...this.customers[i], ...data })
              }
            })
            .catch((error) => {
              const i = this.customers.findIndex((x) => x.id === form.id)
              if (i !== -1) this.customers.splice(i, 1, snapshot)
              this.showErrorNotification(
                formatErrorMessage(error) || 'Failed to save customer. Please try again.'
              )
            })
            .finally(finish)
          return
        }

        const tempId = -Date.now()
        const optimistic = { ...form, id: tempId }
        this.customers = [optimistic, ...this.customers]
        this.dialog = false
        this.showSuccessNotification('Customer added')

        api
          .post('/customers/', form)
          .then(({ data }) => {
            const idx = this.customers.findIndex((c) => c.id === tempId)
            if (idx !== -1) {
              const merged =
                data && typeof data === 'object' ? { ...optimistic, ...data } : optimistic
              this.customers.splice(idx, 1, merged)
            }
          })
          .catch((error) => {
            const idx = this.customers.findIndex((c) => c.id === tempId)
            if (idx !== -1) this.customers.splice(idx, 1)
            this.showErrorNotification(
              formatErrorMessage(error) || 'Failed to save customer. Please try again.'
            )
          })
          .finally(finish)
      } catch (error) {
        finish()
        this.showErrorNotification(
          formatErrorMessage(error) || 'Failed to save customer. Please try again.'
        )
      }
    },
    deleteCustomer(id) {
      if (!confirm('Are you sure you want to delete this customer?')) return
      if (this.deletingCustomerId != null) return
      const idx = this.customers.findIndex((c) => c.id === id)
      if (idx === -1) return
      const snapshot = this.customers[idx]
      this.deletingCustomerId = id
      this.customers.splice(idx, 1)
      this.showSuccessNotification('Customer removed')

      api
        .delete(`/customers/${id}/`)
        .catch((error) => {
          const at = Math.min(idx, this.customers.length)
          this.customers.splice(at, 0, snapshot)
          this.showErrorNotification(
            formatErrorMessage(error) || 'Failed to delete customer. Please try again.'
          )
        })
        .finally(() => {
          this.deletingCustomerId = null
        })
    }
  }
}
</script>
