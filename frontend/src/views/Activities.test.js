import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import Activities from './Activities.vue'
import Layout from '../components/Layout.vue'
import api from '../services/api'

vi.mock('../services/api')
vi.mock('../components/Layout.vue', () => ({
  default: {
    name: 'Layout',
    template: '<div><slot /></div>'
  }
}))

describe('Activities.vue', () => {
  let wrapper

  const mockApplications = [
    { id: 1, company_name: 'Tech Corp', position: 'Software Engineer' },
    { id: 2, company_name: 'Another Corp', position: 'Developer' }
  ]

  const mockAssessments = [
    {
      id: 1,
      application: 1,
      application_company_name: 'Tech Corp',
      deadline: '2024-12-25',
      status: 'pending',
      website_url: 'https://assessment.example.com',
      recruiter_contact_name: 'John Doe',
      recruiter_contact_email: 'john@example.com',
      recruiter_contact_phone: '555-1234',
      notes: 'Take-home project'
    },
    {
      id: 2,
      application: 2,
      application_company_name: 'Another Corp',
      deadline: '2024-12-30',
      status: 'in_progress',
      website_url: '',
      recruiter_contact_name: '',
      recruiter_contact_email: '',
      recruiter_contact_phone: '',
      notes: ''
    }
  ]

  const mockInteractions = [
    {
      id: 1,
      application: 1,
      application_company_name: 'Tech Corp',
      interaction_type: 'email',
      direction: 'outbound',
      subject: 'Follow-up email',
      notes: 'Sent follow-up',
      interaction_date: '2024-12-20T10:00:00Z'
    },
    {
      id: 2,
      application: 2,
      application_company_name: 'Another Corp',
      interaction_type: 'interview',
      direction: 'inbound',
      subject: 'Technical interview',
      notes: 'Interview scheduled',
      interaction_date: '2024-12-22T14:00:00Z'
    }
  ]

  beforeEach(() => {
    api.get = vi.fn((url) => {
      if (url === '/assessments/') {
        return Promise.resolve({ data: mockAssessments })
      }
      if (url === '/interactions/') {
        return Promise.resolve({ data: mockInteractions })
      }
      if (url === '/applications/') {
        return Promise.resolve({ data: mockApplications })
      }
      return Promise.reject(new Error('Unknown URL'))
    })

    api.post = vi.fn(() => Promise.resolve({ data: { id: 3 } }))
    api.put = vi.fn(() => Promise.resolve({ data: {} }))
    api.delete = vi.fn(() => Promise.resolve({ status: 204 }))
  })

  it('renders Activities component', () => {
    wrapper = mount(Activities, {
      global: {
        stubs: {
          Layout: true,
          'v-card': true,
          'v-card-title': true,
          'v-card-text': true,
          'v-btn': true,
          'v-icon': true,
          'v-spacer': true,
          'v-select': true,
          'v-data-table': true
        }
      }
    })

    expect(wrapper.exists()).toBe(true)
  })

  it('loads assessments, interactions, and applications on mount', async () => {
    wrapper = mount(Activities, {
      global: {
        stubs: {
          Layout: true,
          'v-card': true,
          'v-card-title': true,
          'v-card-text': true,
          'v-btn': true,
          'v-icon': true,
          'v-spacer': true,
          'v-select': true,
          'v-data-table': true
        }
      }
    })

    await wrapper.vm.$nextTick()
    await new Promise(resolve => setTimeout(resolve, 100))

    expect(api.get).toHaveBeenCalledWith('/assessments/')
    expect(api.get).toHaveBeenCalledWith('/interactions/')
    expect(api.get).toHaveBeenCalledWith('/applications/')
  })

  it('combines assessments and interactions in filteredActivities', async () => {
    wrapper = mount(Activities, {
      data() {
        return {
          assessments: mockAssessments,
          interactions: mockInteractions,
          applications: mockApplications,
          loading: false,
          selectedApplication: null
        }
      },
      global: {
        stubs: {
          Layout: true,
          'v-card': true,
          'v-card-title': true,
          'v-card-text': true,
          'v-btn': true,
          'v-icon': true,
          'v-spacer': true,
          'v-select': true,
          'v-data-table': true
        }
      }
    })

    await wrapper.vm.$nextTick()

    const activities = wrapper.vm.filteredActivities
    expect(activities).toHaveLength(4) // 2 assessments + 2 interactions
    expect(activities.some(a => a.type === 'Assessment')).toBe(true)
    expect(activities.some(a => a.type === 'Interaction')).toBe(true)
  })

  it('filters activities by selected application', async () => {
    wrapper = mount(Activities, {
      data() {
        return {
          assessments: mockAssessments,
          interactions: mockInteractions,
          applications: mockApplications,
          loading: false,
          selectedApplication: 1
        }
      },
      global: {
        stubs: {
          Layout: true,
          'v-card': true,
          'v-card-title': true,
          'v-card-text': true,
          'v-btn': true,
          'v-icon': true,
          'v-spacer': true,
          'v-select': true,
          'v-data-table': true
        }
      }
    })

    await wrapper.vm.$nextTick()

    const activities = wrapper.vm.filteredActivities
    expect(activities).toHaveLength(2) // Only activities for application 1
    expect(activities.every(a => a.application === 1)).toBe(true)
  })

  it('opens assessment dialog when Add Assessment button is clicked', async () => {
    wrapper = mount(Activities, {
      data() {
        return {
          assessments: [],
          interactions: [],
          applications: mockApplications,
          loading: false,
          selectedApplication: null,
          assessmentDialog: false
        }
      },
      global: {
        stubs: {
          Layout: true,
          'v-card': true,
          'v-card-title': true,
          'v-card-text': true,
          'v-btn': true,
          'v-icon': true,
          'v-spacer': true,
          'v-select': true,
          'v-data-table': true
        }
      }
    })

    await wrapper.vm.openAssessmentDialog()
    expect(wrapper.vm.assessmentDialog).toBe(true)
    expect(wrapper.vm.assessmentEditMode).toBe(false)
  })

  it('opens interaction dialog when Add Interaction button is clicked', async () => {
    wrapper = mount(Activities, {
      data() {
        return {
          assessments: [],
          interactions: [],
          applications: mockApplications,
          loading: false,
          selectedApplication: null,
          interactionDialog: false
        }
      },
      global: {
        stubs: {
          Layout: true,
          'v-card': true,
          'v-card-title': true,
          'v-card-text': true,
          'v-btn': true,
          'v-icon': true,
          'v-spacer': true,
          'v-select': true,
          'v-data-table': true
        }
      }
    })

    await wrapper.vm.openInteractionDialog()
    expect(wrapper.vm.interactionDialog).toBe(true)
    expect(wrapper.vm.interactionEditMode).toBe(false)
  })

  it('saves new assessment via API', async () => {
    wrapper = mount(Activities, {
      data() {
        return {
          assessments: [],
          interactions: [],
          applications: mockApplications,
          loading: false,
          selectedApplication: null,
          assessmentDialog: true,
          assessmentEditMode: false,
          assessmentForm: {
            application: 1,
            deadline: '2024-12-25',
            website_url: 'https://test.com',
            recruiter_contact_name: 'Jane Doe',
            recruiter_contact_email: 'jane@example.com',
            recruiter_contact_phone: '555-5678',
            status: 'pending',
            notes: 'Test assessment'
          }
        }
      },
      global: {
        stubs: {
          Layout: true,
          'v-card': true,
          'v-card-title': true,
          'v-card-text': true,
          'v-btn': true,
          'v-icon': true,
          'v-spacer': true,
          'v-select': true,
          'v-data-table': true
        }
      }
    })

    await wrapper.vm.saveAssessment()

    expect(api.post).toHaveBeenCalledWith('/assessments/', wrapper.vm.assessmentForm)
    expect(api.get).toHaveBeenCalledWith('/assessments/')
  })

  it('saves new interaction via API', async () => {
    wrapper = mount(Activities, {
      data() {
        return {
          assessments: [],
          interactions: [],
          applications: mockApplications,
          loading: false,
          selectedApplication: null,
          interactionDialog: true,
          interactionEditMode: false,
          interactionForm: {
            application: 1,
            interaction_type: 'email',
            direction: 'outbound',
            subject: 'Test email',
            notes: 'Test notes',
            interaction_date: '2024-12-20T10:00:00'
          }
        }
      },
      global: {
        stubs: {
          Layout: true,
          'v-card': true,
          'v-card-title': true,
          'v-card-text': true,
          'v-btn': true,
          'v-icon': true,
          'v-spacer': true,
          'v-select': true,
          'v-data-table': true
        }
      }
    })

    await wrapper.vm.saveInteraction()

    expect(api.post).toHaveBeenCalledWith('/interactions/', wrapper.vm.interactionForm)
    expect(api.get).toHaveBeenCalledWith('/interactions/')
  })

  it('deletes assessment when deleteItem is called', async () => {
    wrapper = mount(Activities, {
      data() {
        return {
          assessments: mockAssessments,
          interactions: [],
          applications: mockApplications,
          loading: false,
          selectedApplication: null
        }
      },
      global: {
        stubs: {
          Layout: true,
          'v-card': true,
          'v-card-title': true,
          'v-card-text': true,
          'v-btn': true,
          'v-icon': true,
          'v-spacer': true,
          'v-select': true,
          'v-data-table': true
        }
      }
    })

    const activity = {
      originalType: 'assessment',
      originalId: 1
    }

    await wrapper.vm.deleteItem(activity)

    expect(api.delete).toHaveBeenCalledWith('/assessments/1/')
    expect(api.get).toHaveBeenCalledWith('/assessments/')
  })

  it('deletes interaction when deleteItem is called', async () => {
    wrapper = mount(Activities, {
      data() {
        return {
          assessments: [],
          interactions: mockInteractions,
          applications: mockApplications,
          loading: false,
          selectedApplication: null
        }
      },
      global: {
        stubs: {
          Layout: true,
          'v-card': true,
          'v-card-title': true,
          'v-card-text': true,
          'v-btn': true,
          'v-icon': true,
          'v-spacer': true,
          'v-select': true,
          'v-data-table': true
        }
      }
    })

    const activity = {
      originalType: 'interaction',
      originalId: 1
    }

    await wrapper.vm.deleteItem(activity)

    expect(api.delete).toHaveBeenCalledWith('/interactions/1/')
    expect(api.get).toHaveBeenCalledWith('/interactions/')
  })

  it('returns correct type color for Assessment and Interaction', () => {
    wrapper = mount(Activities, {
      global: {
        stubs: {
          Layout: true,
          'v-card': true,
          'v-card-title': true,
          'v-card-text': true,
          'v-btn': true,
          'v-icon': true,
          'v-spacer': true,
          'v-select': true,
          'v-data-table': true
        }
      }
    })

    expect(wrapper.vm.getTypeColor('Assessment')).toBe('blue')
    expect(wrapper.vm.getTypeColor('Interaction')).toBe('green')
  })

  it('returns correct status color for assessment statuses', () => {
    wrapper = mount(Activities, {
      global: {
        stubs: {
          Layout: true,
          'v-card': true,
          'v-card-title': true,
          'v-card-text': true,
          'v-btn': true,
          'v-icon': true,
          'v-spacer': true,
          'v-select': true,
          'v-data-table': true
        }
      }
    })

    expect(wrapper.vm.getStatusColor('pending')).toBe('orange')
    expect(wrapper.vm.getStatusColor('in_progress')).toBe('blue')
    expect(wrapper.vm.getStatusColor('submitted')).toBe('purple')
    expect(wrapper.vm.getStatusColor('completed')).toBe('green')
  })

  it('detects approaching deadlines correctly', () => {
    wrapper = mount(Activities, {
      global: {
        stubs: {
          Layout: true,
          'v-card': true,
          'v-card-title': true,
          'v-card-text': true,
          'v-btn': true,
          'v-icon': true,
          'v-spacer': true,
          'v-select': true,
          'v-data-table': true
        }
      }
    })

    const today = new Date()
    const tomorrow = new Date(today)
    tomorrow.setDate(tomorrow.getDate() + 1)
    const nextWeek = new Date(today)
    nextWeek.setDate(nextWeek.getDate() + 7)
    const twoWeeks = new Date(today)
    twoWeeks.setDate(twoWeeks.getDate() + 14)

    expect(wrapper.vm.isDeadlineApproaching(tomorrow.toISOString().split('T')[0])).toBe(true)
    expect(wrapper.vm.isDeadlineApproaching(nextWeek.toISOString().split('T')[0])).toBe(true)
    expect(wrapper.vm.isDeadlineApproaching(twoWeeks.toISOString().split('T')[0])).toBe(false)
  })

  it('sorts activities by date (most recent first)', async () => {
    wrapper = mount(Activities, {
      data() {
        return {
          assessments: [
            {
              id: 1,
              application: 1,
              application_company_name: 'Tech Corp',
              deadline: '2024-12-25'
            }
          ],
          interactions: [
            {
              id: 1,
              application: 1,
              application_company_name: 'Tech Corp',
              interaction_date: '2024-12-20T10:00:00Z'
            }
          ],
          applications: mockApplications,
          loading: false,
          selectedApplication: null
        }
      },
      global: {
        stubs: {
          Layout: true,
          'v-card': true,
          'v-card-title': true,
          'v-card-text': true,
          'v-btn': true,
          'v-icon': true,
          'v-spacer': true,
          'v-select': true,
          'v-data-table': true
        }
      }
    })

    await wrapper.vm.$nextTick()

    const activities = wrapper.vm.filteredActivities
    // Assessment with deadline 2024-12-25 should come before interaction with date 2024-12-20 (most recent first)
    expect(activities).toHaveLength(2)
    
    // Verify dates are being compared correctly
    const dateA = new Date(activities[0].deadline || activities[0].interaction_date)
    const dateB = new Date(activities[1].deadline || activities[1].interaction_date)
    
    // Most recent date should be first
    expect(dateA.getTime()).toBeGreaterThanOrEqual(dateB.getTime())
    
    // Verify the actual items
    const assessment = activities.find(a => a.type === 'Assessment')
    const interaction = activities.find(a => a.type === 'Interaction')
    
    expect(assessment).toBeDefined()
    expect(interaction).toBeDefined()
    expect(assessment.deadline).toBe('2024-12-25')
    expect(interaction.interaction_date).toBe('2024-12-20T10:00:00Z')
    
    // Most recent (2024-12-25) should be first
    expect(activities[0].deadline || activities[0].interaction_date).toBeTruthy()
  })
})

