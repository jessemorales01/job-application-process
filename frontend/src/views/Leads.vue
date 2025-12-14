<template>
  <Layout title="Leads">
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
          <v-btn text @click="dialog = false">Cancel</v-btn>
          <v-btn color="primary" @click="saveLead">Save</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </Layout>
</template>

<script>
import Layout from '../components/Layout.vue'
import api from '../services/api'
import draggable from 'vuedraggable'

export default {
  name: 'Leads',
  components: {
    Layout,
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
    getErrorMessage(error) {
      if (error.response?.data) {
        const data = error.response.data
        
        if (data.error) {
          return data.error
        }
        
        if (data.non_field_errors) {
          return Array.isArray(data.non_field_errors) 
            ? data.non_field_errors.join('\n')
            : data.non_field_errors
        }
        
        const fieldErrors = Object.entries(data)
          .map(([field, messages]) => {
            const fieldName = field.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())
            const errorList = Array.isArray(messages) ? messages : [messages]
            return `${fieldName}: ${errorList.join(', ')}`
          })
          .join('\n')
        
        if (fieldErrors) {
          return fieldErrors
        }
      }
      return null
    },
    async loadStages() {
      try {
        const response = await api.get('/stages/')
        this.stages = response.data
      } catch (error) {
        const message = this.getErrorMessage(error) || 'Failed to load stages. Please refresh the page.'
        alert(message)
      }
    },
    async loadLeads() {
      this.loading = true
      try {
        const response = await api.get('/leads/')
        this.leads = response.data
      } catch (error) {
        const message = this.getErrorMessage(error) || 'Failed to load leads. Please refresh the page.'
        alert(message)
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
    async saveLead() {
      try {
        if (this.editMode) {
          await api.put(`/leads/${this.form.id}/`, this.form)
        } else {
          await api.post('/leads/', this.form)
        }
        this.dialog = false
        await this.loadLeads()
      } catch (error) {
        const message = this.getErrorMessage(error) || 'Failed to save lead. Please try again.'
        alert(message)
      }
    },
    async deleteLead(id) {
      if (confirm('Are you sure you want to delete this lead?')) {
        try {
          await api.delete(`/leads/${id}/`)
          await this.loadLeads()
        } catch (error) {
          const message = this.getErrorMessage(error) || 'Failed to delete lead. Please try again.'
          alert(message)
        }
      }
    },
    async addStage() {
      const maxOrder = Math.max(...this.stages.map(s => s.order), 0)
      try {
        await api.post('/stages/', {
          name: 'New Stage',
          order: maxOrder + 1
        })
        await this.loadStages()
      } catch (error) {
        const message = this.getErrorMessage(error) || 'Failed to add stage. Please try again.'
        alert(message)
      }
    },
    async deleteStage(id) {
      if (confirm('Are you sure you want to delete this stage?')) {
        try {
          await api.delete(`/stages/${id}/`)
          await this.loadStages()
        } catch (error) {
          const message = this.getErrorMessage(error) || 'Failed to delete stage. Please try again.'
          alert(message)
        }
      }
    },
    async onDragChange(event, newStageId) {
      if (event.added) {
        const leadId = event.added.element.id
        
        try {
          await api.patch(`/leads/${leadId}/`, { stage: newStageId })
          
          // Update local state to avoid reload flash
          const lead = this.leads.find(l => l.id === leadId)
          if (lead) {
            lead.stage = newStageId
          }
        } catch (error) {
          const message = this.getErrorMessage(error) || 'Failed to move lead. Please try again.'
          alert(message)
          await this.loadLeads()
        }
      }
    },
    async saveStageEdit(stageId) {
      if (!this.editingStageName.trim()) {
        this.cancelStageEdit()
        return
      }
      try {
        await api.patch(`/stages/${stageId}/`, { name: this.editingStageName })
        await this.loadStages()
      } catch (error) {
        const message = this.getErrorMessage(error) || 'Failed to update stage name. Please try again.'
        alert(message)
      } finally {
        this.editingStageId = null
        this.editingStageName = ''
      }
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