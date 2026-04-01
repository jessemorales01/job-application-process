<template>
  <Layout title="Leads">
    <ErrorSnackbar
      v-model="showError"
      :message="errorMessage"
      type="error"
      :multiline="true"
    />
    <v-card>
      <v-card-title>
        Leads Management
        <v-spacer></v-spacer>
        <v-btn color="primary" @click="openDialog()">
          <v-icon left>mdi-plus</v-icon>
          Register Lead
        </v-btn>
      </v-card-title>
      <v-card-text>
        <!-- Kanban Board Container -->
        <div class="kanban-board">
          <!-- Empty State Message (when no stages exist) -->
          <div v-if="stages.length === 0" class="empty-board-message">
            <v-icon size="48" color="grey">mdi-view-column-outline</v-icon>
            <p>No stages exist. Click "+" to create your first stage.</p>
          </div>
          <!-- Loop through each stage to create a column -->
          <div 
            v-for="stage in stages" 
            :key="stage.id" 
            class="kanban-column"
          >
            <!-- Column Header -->
            <div class="kanban-column-header">
              <template v-if="editingStageId === stage.id">
                <v-text-field
                  v-model="editingStageName"
                  dense
                  hide-details
                  autofocus
                  maxlength="30"
                  @blur="saveStageEdit(stage.id)"
                  @keyup.enter="saveStageEdit(stage.id)"
                  @keyup.escape="cancelStageEdit"
                ></v-text-field>
              </template>
              
              <template v-else>
                <span class="stage-name">{{ stage.name }}</span>
                <v-menu offset-y>
                  <template v-slot:activator="{ props }">
                    <v-icon 
                      v-bind="props"
                      small 
                      class="ml-2" 
                      style="cursor: pointer;"
                    >
                      mdi-dots-horizontal
                    </v-icon>
                  </template>
                  
                  <v-list density="compact">
                    <v-list-item @click="startStageEdit(stage)">
                      <template v-slot:prepend>
                        <v-icon size="small">mdi-pencil</v-icon>
                      </template>
                      <v-list-item-title>Edit Name</v-list-item-title>
                    </v-list-item>
                    
                    <v-list-item @click="deleteStage(stage.id)">
                      <template v-slot:prepend>
                        <v-icon size="small" color="red">mdi-delete</v-icon>
                      </template>
                      <v-list-item-title class="text-red">Delete Stage</v-list-item-title>
                    </v-list-item>
                  </v-list>
                </v-menu>
              </template>
            </div>
            <!-- Lead Cards - draggable container -->
            <draggable
              :list="leadsByStage[stage.id] || []"
              group="leads"
              item-key="id"
              class="kanban-cards"
              @change="onDragChange($event, stage.id)"
            >
              <template #item="{ element }">
                <v-card class="kanban-card" @click="openDialog(element)">
                  <v-card-title class="d-flex align-center">
                    <span class="lead-name">{{ element.name }}</span>
                    <v-spacer></v-spacer>
                    <v-menu offset-y>
                      <template v-slot:activator="{ props }">
                        <v-icon v-bind="props" size="small" @click.stop>mdi-dots-horizontal</v-icon>
                      </template>
                      <v-list density="compact">
                        <v-list-item @click="openDialog(element)">
                          <template v-slot:prepend>
                            <v-icon size="small">mdi-pencil</v-icon>
                          </template>
                          <v-list-item-title>Edit Lead</v-list-item-title>
                        </v-list-item>
                        <v-list-item @click="deleteLead(element.id)">
                          <template v-slot:prepend>
                            <v-icon size="small" color="red">mdi-delete</v-icon>
                          </template>
                          <v-list-item-title class="text-red">Delete Lead</v-list-item-title>
                        </v-list-item>
                      </v-list>
                    </v-menu>
                  </v-card-title>
                  <v-card-text>
                    <div>{{ element.company }}</div>
                    <div>${{ element.estimated_value }}</div>
                    <div>Win: {{ Math.round((element.win_score || 0) * 100) }}%</div>
                  </v-card-text>
                </v-card>
              </template>
            </draggable>
          </div>
          <div class="kanban-column add-stage-column" @click="addStage">
          <div class="add-stage-content">
            <v-icon large>mdi-plus</v-icon>
            <div>Add Stage</div>
          </div>
        </div>
        </div>
      </v-card-text>
    </v-card>

    <!-- Dialog for Add/Edit -->
    <v-dialog v-model="dialog" max-width="600px">
      <v-card>
        <v-card-title>
          {{ editMode ? 'Edit Lead' : 'Register Lead' }}
        </v-card-title>
        <v-card-text>
          <v-form @submit.prevent="saveLead">
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
            <v-select
              v-model="form.status"
              :items="statusOptions"
              label="Status"
              required
            ></v-select>
            <v-text-field
              v-model="form.source"
              label="Source"
            ></v-text-field>
            <v-text-field
              v-model="form.estimated_value"
              label="Estimated Value"
              type="number"
              step="0.01"
            ></v-text-field>
            <v-textarea
              v-model="form.notes"
              label="Notes"
            ></v-textarea>
          </v-form>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn text :disabled="leadSaving" @click="dialog = false">Cancel</v-btn>
          <v-btn
            color="primary"
            :loading="leadSaving"
            :disabled="leadSaving"
            @click="saveLead"
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
import draggable from 'vuedraggable'
import { formatErrorMessage } from '../utils/errorHandler'

export default {
  name: 'Leads',
  components: {
    Layout,
    ErrorSnackbar,
    draggable
  },
  data() {
    return {
      leads: [],
      stages: [],
      editingStageId: null,
      editingStageName: '',
      loading: false,
      dialog: false,
      editMode: false,
      leadSaving: false,
      deletingLeadId: null,
      stageAdding: false,
      deletingStageId: null,
      showError: false,
      errorMessage: '',
      statusOptions: [
        { title: 'New', value: 'new' },
        { title: 'Contacted', value: 'contacted' },
        { title: 'Qualified', value: 'qualified' },
        { title: 'Converted', value: 'converted' },
        { title: 'Lost', value: 'lost' }
      ],
      headers: [
        { title: 'Name', key: 'name' },
        { title: 'Email', key: 'email' },
        { title: 'Company', key: 'company' },
        { title: 'Status', key: 'status' },
        { title: 'Estimated Value', key: 'estimated_value' },
        { title: 'Actions', key: 'actions', sortable: false }
      ],
      form: {
        name: '',
        email: '',
        phone: '',
        company: '',
        status: 'new',
        source: '',
        estimated_value: null,
        notes: ''
      }
    }
  },
  computed: {
    leadsByStage() {
      const grouped = {}
      this.leads.forEach(lead => {
        const stageId = lead.stage
        if (!grouped[stageId]) {
          grouped[stageId] = []
        }
        grouped[stageId].push(lead)
      })
      return grouped
    }
  },
  async mounted() {
    await Promise.all([
      this.loadLeads(),
      this.loadStages() // load stages and leads simultaneously, could use Promise.allSettled but need both for board to correctly display
    ])
  },
  methods: {
    showErrorNotification(message) {
      this.errorMessage = message
      this.showError = true
    },
    async loadStages() {
      try {
        const response = await api.get('/stages/')
        this.stages = response.data
      } catch (error) {
        this.showErrorNotification(
          formatErrorMessage(error) || 'Failed to load stages. Please refresh the page.'
        )
      }
    },
    async loadLeads() {
      this.loading = true
      try {
        const response = await api.get('/leads/')
        this.leads = response.data
      } catch (error) {
        this.showErrorNotification(
          formatErrorMessage(error) || 'Failed to load leads. Please refresh the page.'
        )
      } finally {
        this.loading = false
      }
    },
    getStatusColor(status) {
      const colors = {
        new: 'blue',
        contacted: 'orange',
        qualified: 'purple',
        converted: 'green',
        lost: 'red'
      }
      return colors[status] || 'grey'
    },
    openDialog(lead = null) {
      if (lead) {
        this.editMode = true
        this.form = { ...lead }
      } else {
        this.editMode = false
        this.form = {
          name: '',
          email: '',
          phone: '',
          company: '',
          status: 'new',
          source: '',
          estimated_value: null,
          notes: ''
        }
      }
      this.dialog = true
    },
    startStageEdit(stage) {
      this.editingStageId = stage.id
      this.editingStageName = stage.name
    },
    cancelStageEdit() {
      this.editingStageId = null
      this.editingStageName = ''
    },
    saveLead() {
      if (this.leadSaving) return
      this.leadSaving = true
      this.showError = false

      const form = { ...this.form }
      const errs = []
      if (!form.name || !String(form.name).trim()) errs.push('Name is required.')
      if (!form.email || !String(form.email).trim()) errs.push('Email is required.')
      if (!form.status) errs.push('Status is required.')
      if (errs.length) {
        this.showErrorNotification(errs.join(' '))
        this.leadSaving = false
        return
      }

      const finish = () => {
        this.leadSaving = false
      }

      try {
        if (this.editMode) {
          const idx = this.leads.findIndex((l) => l.id === form.id)
          if (idx === -1) {
            finish()
            return
          }
          const snapshot = { ...this.leads[idx] }
          Object.assign(this.leads[idx], form)
          this.dialog = false

          api
            .put(`/leads/${form.id}/`, form)
            .then(({ data }) => {
              const i = this.leads.findIndex((l) => l.id === form.id)
              if (i !== -1 && data && typeof data === 'object' && Object.keys(data).length > 0) {
                Object.assign(this.leads[i], data)
              }
            })
            .catch((error) => {
              Object.assign(this.leads[idx], snapshot)
              this.showErrorNotification(
                formatErrorMessage(error) || 'Failed to save lead. Please try again.'
              )
            })
            .finally(finish)
          return
        }

        const ordered = [...this.stages].sort((a, b) => a.order - b.order)
        const firstStage = ordered[0]
        if (!firstStage) {
          this.showErrorNotification('Create a pipeline stage before adding leads.')
          finish()
          return
        }

        const payload = { ...form, stage: firstStage.id }
        const tempId = `__tmp_lead_${Date.now()}`
        const optimistic = { ...payload, id: tempId }
        this.leads.push(optimistic)
        this.dialog = false

        api
          .post('/leads/', payload)
          .then(({ data }) => {
            const i = this.leads.findIndex((l) => l.id === tempId)
            if (i !== -1) {
              this.leads.splice(i, 1, data)
            } else {
              this.leads.push(data)
            }
          })
          .catch((error) => {
            const i = this.leads.findIndex((l) => l.id === tempId)
            if (i !== -1) this.leads.splice(i, 1)
            this.showErrorNotification(
              formatErrorMessage(error) || 'Failed to save lead. Please try again.'
            )
          })
          .finally(finish)
      } catch (error) {
        finish()
        this.showErrorNotification(
          formatErrorMessage(error) || 'Failed to save lead. Please try again.'
        )
      }
    },
    deleteLead(id) {
      if (!confirm('Are you sure you want to delete this lead?')) return
      if (this.deletingLeadId != null) return
      if (String(id).startsWith('__tmp_')) return

      const idx = this.leads.findIndex((l) => l.id === id)
      if (idx === -1) return
      const snapshot = this.leads[idx]
      this.deletingLeadId = id
      this.leads.splice(idx, 1)

      api
        .delete(`/leads/${id}/`)
        .catch((error) => {
          const at = Math.min(idx, this.leads.length)
          this.leads.splice(at, 0, snapshot)
          this.showErrorNotification(
            formatErrorMessage(error) || 'Failed to delete lead. Please try again.'
          )
        })
        .finally(() => {
          this.deletingLeadId = null
        })
    },
    addStage() {
      if (this.stageAdding) return
      this.stageAdding = true
      const maxOrder = Math.max(...this.stages.map((s) => s.order), 0)
      const nextOrder = maxOrder + 1
      const tempId = `__tmp_stage_${Date.now()}`
      const optimistic = { id: tempId, name: 'New Stage', order: nextOrder }
      this.stages = [...this.stages, optimistic].sort((a, b) => a.order - b.order)

      this.$nextTick(() => {
        api
          .post('/stages/', { name: 'New Stage', order: nextOrder })
          .then(({ data }) => {
            const i = this.stages.findIndex((s) => s.id === tempId)
            if (i !== -1) {
              this.stages.splice(i, 1, data)
            } else {
              this.stages.push(data)
            }
            this.stages.sort((a, b) => a.order - b.order)
          })
          .catch((error) => {
            this.stages = this.stages.filter((s) => s.id !== tempId)
            this.showErrorNotification(
              formatErrorMessage(error) || 'Failed to add stage. Please try again.'
            )
          })
          .finally(() => {
            this.stageAdding = false
          })
      })
    },
    deleteStage(id) {
      if (!confirm('Are you sure you want to delete this stage?')) return
      if (this.deletingStageId != null) return
      if (String(id).startsWith('__tmp_')) return

      const inStage = this.leads.filter((l) => l.stage === id)
      if (inStage.length > 0) {
        this.showErrorNotification(
          `Move all leads out of this stage before deleting it (${inStage.length} still here).`
        )
        return
      }

      const sIdx = this.stages.findIndex((s) => s.id === id)
      if (sIdx === -1) return
      const snapshot = this.stages[sIdx]
      this.deletingStageId = id
      this.stages.splice(sIdx, 1)

      api
        .delete(`/stages/${id}/`)
        .catch((error) => {
          const at = Math.min(sIdx, this.stages.length)
          this.stages.splice(at, 0, snapshot)
          this.stages.sort((a, b) => a.order - b.order)
          this.showErrorNotification(
            formatErrorMessage(error) || 'Failed to delete stage. Please try again.'
          )
        })
        .finally(() => {
          this.deletingStageId = null
        })
    },
    onDragChange(event, newStageId) {
      if (!event.added) return
      const lead = event.added.element
      const leadId = lead.id
      if (String(leadId).startsWith('__tmp_')) return

      const previousStage = lead.stage
      lead.stage = newStageId

      api
        .patch(`/leads/${leadId}/`, { stage: newStageId })
        .catch((error) => {
          lead.stage = previousStage
          this.showErrorNotification(
            formatErrorMessage(error) || 'Failed to move lead. Please try again.'
          )
        })
    },
    saveStageEdit(stageId) {
      if (!this.editingStageName.trim()) {
        this.cancelStageEdit()
        return
      }
      const stage = this.stages.find((s) => s.id === stageId)
      if (!stage) {
        this.cancelStageEdit()
        return
      }
      const previousName = stage.name
      const nextName = this.editingStageName.trim()
      stage.name = nextName
      this.editingStageId = null
      this.editingStageName = ''

      if (String(stageId).startsWith('__tmp_')) {
        return
      }

      api
        .patch(`/stages/${stageId}/`, { name: nextName })
        .catch((error) => {
          stage.name = previousName
          this.showErrorNotification(
            formatErrorMessage(error) || 'Failed to update stage name. Please try again.'
          )
        })
    },
  }
}
</script>

<style scoped>
.kanban-board {
  display: flex;
  gap: 16px;
  overflow-x: auto;
  padding: 16px 0;
}

.kanban-column {
  min-width: 280px;
  max-width: 280px;
  background-color: #f5f5f5;
  border-radius: 8px;
  padding: 12px;
  display: flex;
  flex-direction: column;
}

.kanban-column-header {
  font-weight: bold;
  font-size: 16px;
  padding: 8px;
  margin-bottom: 12px;
  background-color: #e0e0e0;
  border-radius: 4px;
  text-align: center;
  display: flex;
  align-items: center;
  justify-content: center;
}

.kanban-cards {
  min-height: 200px;
  flex-grow: 1;
}

.kanban-card {
  margin-bottom: 12px;
  cursor: pointer;
}

.kanban-card:hover {
  box-shadow: 0 4px 8px rgba(0,0,0,0.15);
}

.add-stage-column {
  min-width: 200px;
  max-width: 200px;
  background-color: rgba(0,0,0,0.05);
  border: 2px dashed #ccc;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
}

.add-stage-column:hover {
  background-color: rgba(0,0,0,0.1);
  border-color: #999;
}

.add-stage-content {
  text-align: center;
  color: #666;
}

.stage-name {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 180px;
}

.empty-board-message {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px;
  color: #757575;
  text-align: center;
}

.empty-board-message p {
  margin-top: 12px;
  font-size: 14px;
}

.kanban-card .v-card-title {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.lead-name {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 180px;
}
</style>