<template>
  <Layout title="Applications">
    <v-card>
      <v-card-title>
        Applications Management
        <v-spacer></v-spacer>
        <v-btn color="primary" @click="openDialog()">
          <v-icon left>mdi-plus</v-icon>
          Add Application
        </v-btn>
      </v-card-title>
      <v-card-text>
        <div class="kanban-board">
          <div v-if="stages.length === 0" class="empty-board-message">
            <v-icon size="48" color="grey">mdi-view-column-outline</v-icon>
            <p>No stages exist. Click "+" to create your first stage.</p>
          </div>
          <div 
            v-for="stage in stages" 
            :key="stage.id" 
            class="kanban-column"
          >
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
            <draggable
              :list="applicationsByStage[stage.id] || []"
              group="applications"
              item-key="id"
              class="kanban-cards"
              @change="onDragChange($event, stage.id)"
            >
              <template #item="{ element }">
                <v-card class="kanban-card" @click="openDialog(element)">
                  <v-card-title class="d-flex align-center">
                    <span class="application-name">{{ element.company_name }}</span>
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
                          <v-list-item-title>Edit Application</v-list-item-title>
                        </v-list-item>
                        <v-list-item @click="deleteApplication(element.id)">
                          <template v-slot:prepend>
                            <v-icon size="small" color="red">mdi-delete</v-icon>
                          </template>
                          <v-list-item-title class="text-red">Delete Application</v-list-item-title>
                        </v-list-item>
                      </v-list>
                    </v-menu>
                  </v-card-title>
                  <v-card-text>
                    <div v-if="element.where_applied">{{ element.where_applied }}</div>
                    <div v-if="element.salary_range">{{ element.salary_range }}</div>
                    <div v-if="element.stack" class="text-truncate" style="max-width: 200px;">{{ element.stack }}</div>
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

    <v-dialog v-model="dialog" max-width="600px">
      <v-card>
        <v-card-title>
          {{ editMode ? 'Edit Application' : 'Add Application' }}
        </v-card-title>
        <v-card-text>
          <v-form @submit.prevent="saveApplication">
            <v-text-field
              v-model="form.company_name"
              label="Company Name"
              required
            ></v-text-field>
            <v-text-field
              v-model="form.email"
              label="Email"
              type="email"
            ></v-text-field>
            <v-text-field
              v-model="form.phone_number"
              label="Phone Number"
            ></v-text-field>
            <v-text-field
              v-model="form.stack"
              label="Stack (Technologies)"
              hint="e.g., Python, React, Django, PostgreSQL"
            ></v-text-field>
            <v-text-field
              v-model="form.salary_range"
              label="Salary Range"
              hint="e.g., 80k-120k or 100k+"
            ></v-text-field>
            <v-text-field
              v-model="form.where_applied"
              label="Where Applied"
              hint="e.g., LinkedIn, Indeed, Referral, Company site"
            ></v-text-field>
            <v-text-field
              v-model="form.applied_date"
              label="Applied Date"
              type="date"
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
          <v-btn color="primary" @click="saveApplication">Save</v-btn>
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
  name: 'Applications',
  components: {
    Layout,
    draggable
  },
  data() {
    return {
      applications: [],
      stages: [],
      editingStageId: null,
      editingStageName: '',
      loading: false,
      dialog: false,
      editMode: false,
      form: {
        company_name: '',
        email: '',
        phone_number: '',
        stack: '',
        salary_range: '',
        where_applied: '',
        applied_date: '',
        notes: ''
      }
    }
  },
  computed: {
    applicationsByStage() {
      const grouped = {}
      this.applications.forEach(application => {
        const stageId = application.stage
        if (!grouped[stageId]) {
          grouped[stageId] = []
        }
        grouped[stageId].push(application)
      })
      return grouped
    }
  },
  async mounted() {
    await Promise.all([
      this.loadApplications(),
      this.loadStages()
    ])
  },
  methods: {
    getErrorMessage(error) {
      if (error.response?.data) {
        const data = error.response.data
        
        // Check if response is HTML (error page) instead of JSON
        if (typeof data === 'string' && data.trim().startsWith('<!')) {
          return 'Server returned an error page. Please check the backend logs or try refreshing the page.'
        }
        
        // Handle JSON error responses
        if (typeof data === 'object') {
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
      }
      
      // Handle network errors or other issues
      if (error.message) {
        return error.message
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
    async loadApplications() {
      this.loading = true
      try {
        const response = await api.get('/applications/')
        this.applications = response.data
      } catch (error) {
        const message = this.getErrorMessage(error) || 'Failed to load applications. Please refresh the page.'
        alert(message)
      } finally {
        this.loading = false
      }
    },
    openDialog(application = null) {
      if (application) {
        this.editMode = true
        this.form = { ...application }
        if (this.form.applied_date) {
          this.form.applied_date = this.form.applied_date.split('T')[0]
        }
      } else {
        this.editMode = false
        this.form = {
          company_name: '',
          email: '',
          phone_number: '',
          stack: '',
          salary_range: '',
          where_applied: '',
          applied_date: '',
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
    async saveApplication() {
      try {
        if (this.editMode) {
          await api.put(`/applications/${this.form.id}/`, this.form)
        } else {
          await api.post('/applications/', this.form)
        }
        this.dialog = false
        await this.loadApplications()
      } catch (error) {
        const message = this.getErrorMessage(error) || 'Failed to save application. Please try again.'
        alert(message)
      }
    },
    async deleteApplication(id) {
      if (confirm('Are you sure you want to delete this application?')) {
        try {
          await api.delete(`/applications/${id}/`)
          await this.loadApplications()
        } catch (error) {
          const message = this.getErrorMessage(error) || 'Failed to delete application. Please try again.'
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
        const applicationId = event.added.element.id
        
        try {
          await api.patch(`/applications/${applicationId}/`, { stage: newStageId })
          
          const application = this.applications.find(a => a.id === applicationId)
          if (application) {
            application.stage = newStageId
          }
        } catch (error) {
          const message = this.getErrorMessage(error) || 'Failed to move application. Please try again.'
          alert(message)
          await this.loadApplications()
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

.application-name {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 180px;
}
</style>

