<template>
  <Layout title="Applications">
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
                    <div>
                      <div class="font-weight-bold">{{ element.company_name }}</div>
                      <div v-if="element.position" class="text-caption text-grey">{{ element.position }}</div>
                    </div>
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
              v-model="form.position"
              label="Position"
              hint="e.g., Software Engineer, Senior Developer"
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
          <v-btn text :disabled="applicationSaving" @click="dialog = false">Cancel</v-btn>
          <v-btn
            color="primary"
            :loading="applicationSaving"
            :disabled="applicationSaving"
            @click="saveApplication"
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
import {
  getEntry,
  getOrFetch,
  markDirty,
  markDirtyAutoDetected,
  markDirtyDashboardLists,
  putCached,
} from '../services/listResourceCache'

export default {
  name: 'Applications',
  components: {
    Layout,
    ErrorSnackbar,
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
      showError: false,
      errorMessage: '',
      showSuccess: false,
      successMessage: '',
      form: {
        company_name: '',
        position: '',
        email: '',
        phone_number: '',
        stack: '',
        salary_range: '',
        where_applied: '',
        applied_date: '',
        notes: ''
      },
      skipNextActivatedRefresh: true,
      applicationSaving: false,
      deletingApplicationId: null,
      deletingStageId: null
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
  activated() {
    if (this.skipNextActivatedRefresh) {
      this.skipNextActivatedRefresh = false
      return
    }
    Promise.all([this.loadApplications(), this.loadStages()])
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
    async loadStages(options = {}) {
      const force = options.force === true
      const key = 'stages'
      const e = getEntry(key)
      try {
        if (!force && !e.dirty && e.fetched) {
          this.stages = e.data || []
          return
        }
        const { data } = await getOrFetch(key, '/stages/', { force })
        this.stages = data || []
      } catch (error) {
        const message = formatErrorMessage(error) || 'Failed to load stages. Please refresh the page.'
        this.showErrorNotification(message)
      }
    },
    async loadApplications(options = {}) {
      const force = options.force === true
      const key = 'applications'
      const e = getEntry(key)
      if (!force && !e.dirty && e.fetched) {
        this.applications = e.data || []
        return
      }
      if (e.fetched) {
        this.applications = e.data || []
      }
      this.loading = !e.fetched
      try {
        const { data } = await getOrFetch(key, '/applications/', { force })
        this.applications = data || []
      } catch (error) {
        const message = formatErrorMessage(error) || 'Failed to load applications. Please refresh the page.'
        this.showErrorNotification(message)
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
    resetCreateForm() {
      this.form = {
        company_name: '',
        position: '',
        email: '',
        phone_number: '',
        stack: '',
        salary_range: '',
        where_applied: '',
        applied_date: '',
        notes: ''
      }
    },
    saveApplication() {
      if (this.applicationSaving) return
      const finish = () => {
        this.applicationSaving = false
      }

      if (this.editMode) {
        const id = this.form.id
        const app = this.applications.find((a) => a.id === id)
        if (!app) {
          this.persistApplicationEditFallback()
          return
        }
        this.applicationSaving = true
        const snapshot = { ...app }
        Object.assign(app, this.form)
        if (this.form.applied_date) {
          app.applied_date = this.form.applied_date
        }
        putCached('applications', this.applications)
        this.dialog = false
        api
          .put(`/applications/${id}/`, this.form)
          .then(({ data }) => {
            Object.assign(app, data)
            putCached('applications', this.applications)
            markDirtyAutoDetected()
            markDirtyDashboardLists()
            this.showSuccessNotification('Application updated successfully!')
          })
          .catch((error) => {
            Object.assign(app, snapshot)
            putCached('applications', this.applications)
            this.showErrorNotification(
              formatErrorMessage(error) || 'Failed to save application. Please try again.'
            )
          })
          .finally(finish)
        return
      }

      const ordered = [...this.stages].sort((a, b) => a.order - b.order)
      const firstStage = ordered[0]
      if (!firstStage) {
        this.showErrorNotification('Create a pipeline stage before adding applications.')
        return
      }

      this.applicationSaving = true
      const tempId = `__tmp_app_${Date.now()}`
      const payload = { ...this.form }
      const optimistic = {
        ...payload,
        id: tempId,
        stage: firstStage.id
      }
      this.applications.push(optimistic)
      putCached('applications', this.applications)
      this.dialog = false
      this.resetCreateForm()
      this.showSuccessNotification('Application added.')

      api
        .post('/applications/', payload)
        .then(({ data }) => {
          const i = this.applications.findIndex((a) => a.id === tempId)
          if (i !== -1) {
            this.applications.splice(i, 1, data)
          } else {
            this.applications.push(data)
          }
          putCached('applications', this.applications)
          markDirtyAutoDetected()
          markDirtyDashboardLists()
        })
        .catch((error) => {
          const i = this.applications.findIndex((a) => a.id === tempId)
          if (i !== -1) {
            this.applications.splice(i, 1)
          }
          putCached('applications', this.applications)
          this.showErrorNotification(
            formatErrorMessage(error) || 'Failed to create application. Please try again.'
          )
        })
        .finally(finish)
    },
    async persistApplicationEditFallback() {
      if (this.applicationSaving) return
      this.applicationSaving = true
      try {
        if (this.editMode) {
          await api.put(`/applications/${this.form.id}/`, this.form)
          this.showSuccessNotification('Application updated successfully!')
        } else {
          await api.post('/applications/', this.form)
          this.showSuccessNotification('Application created successfully!')
        }
        this.dialog = false
        markDirty('applications')
        markDirtyAutoDetected()
        markDirtyDashboardLists()
        await this.loadApplications({ force: true })
      } catch (error) {
        const message = formatErrorMessage(error) || 'Failed to save application. Please try again.'
        this.showErrorNotification(message)
      } finally {
        this.applicationSaving = false
      }
    },
    deleteApplication(id) {
      if (!confirm('Are you sure you want to delete this application?')) return
      if (this.deletingApplicationId != null) return
      if (String(id).startsWith('__tmp_')) return

      const idx = this.applications.findIndex((a) => a.id === id)
      if (idx === -1) return
      const snapshot = this.applications[idx]
      this.deletingApplicationId = id
      this.applications.splice(idx, 1)
      putCached('applications', this.applications)
      this.showSuccessNotification('Application removed')

      api
        .delete(`/applications/${id}/`)
        .then(() => {
          markDirty('applications')
          markDirtyAutoDetected()
          markDirtyDashboardLists()
        })
        .catch((error) => {
          const at = Math.min(idx, this.applications.length)
          this.applications.splice(at, 0, snapshot)
          putCached('applications', this.applications)
          markDirty('applications')
          this.showErrorNotification(
            formatErrorMessage(error) || 'Failed to delete application. Please try again.'
          )
        })
        .finally(() => {
          this.deletingApplicationId = null
        })
    },
    addStage() {
      const maxOrder = Math.max(...this.stages.map((s) => s.order), 0)
      const nextOrder = maxOrder + 1
      const tempId = `__tmp_stage_${Date.now()}`
      const optimistic = { id: tempId, name: 'New Stage', order: nextOrder }
      this.stages = [...this.stages, optimistic].sort((a, b) => a.order - b.order)
      putCached('stages', this.stages)
      this.showSuccessNotification('Stage added.')

      this.$nextTick(() => {
        const s = this.stages.find((x) => x.id === tempId)
        const body = { name: (s && s.name) || 'New Stage', order: nextOrder }
        api
          .post('/stages/', body)
          .then(({ data }) => {
            const i = this.stages.findIndex((s) => s.id === tempId)
            if (i !== -1) {
              this.stages.splice(i, 1, data)
            } else {
              this.stages.push(data)
            }
            this.stages.sort((a, b) => a.order - b.order)
            putCached('stages', this.stages)
          })
          .catch((error) => {
            this.stages = this.stages.filter((s) => s.id !== tempId)
            putCached('stages', this.stages)
            this.showErrorNotification(
              formatErrorMessage(error) || 'Failed to add stage. Please try again.'
            )
          })
      })
    },
    deleteStage(id) {
      if (!confirm('Are you sure you want to delete this stage?')) return
      if (this.deletingStageId != null) return
      if (String(id).startsWith('__tmp_')) return

      const appsInStage = this.applications.filter((a) => a.stage === id)
      if (appsInStage.length > 0) {
        this.showErrorNotification(
          `Move all applications out of this stage before deleting it (${appsInStage.length} still here).`
        )
        return
      }

      const sIdx = this.stages.findIndex((s) => s.id === id)
      if (sIdx === -1) return
      const snapshot = this.stages[sIdx]
      this.deletingStageId = id
      this.stages.splice(sIdx, 1)
      putCached('stages', [...this.stages])
      this.showSuccessNotification('Stage removed')

      api
        .delete(`/stages/${id}/`)
        .then(() => {
          markDirty('stages')
        })
        .catch((error) => {
          const at = Math.min(sIdx, this.stages.length)
          this.stages.splice(at, 0, snapshot)
          this.stages.sort((a, b) => a.order - b.order)
          putCached('stages', [...this.stages])
          markDirty('stages')
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
      const applicationId = event.added.element.id
      const application = this.applications.find((a) => a.id === applicationId)
      if (!application) return

      const previousStage = application.stage
      application.stage = newStageId
      putCached('applications', this.applications)
      this.showSuccessNotification('Application moved successfully.')

      if (String(applicationId).startsWith('__tmp_')) {
        return
      }

      api
        .patch(`/applications/${applicationId}/`, { stage: newStageId })
        .then(() => {
          putCached('applications', this.applications)
        })
        .catch((error) => {
          application.stage = previousStage
          putCached('applications', this.applications)
          this.showErrorNotification(
            formatErrorMessage(error) || 'Failed to move application. Please try again.'
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
      putCached('stages', this.stages)

      if (String(stageId).startsWith('__tmp_')) {
        return
      }

      api
        .patch(`/stages/${stageId}/`, { name: nextName })
        .then(() => {
          this.showSuccessNotification('Stage name updated successfully!')
        })
        .catch((error) => {
          stage.name = previousName
          putCached('stages', this.stages)
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

.application-name {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 180px;
}
</style>

