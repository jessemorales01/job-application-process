import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import Leads from './Leads.vue'
import Layout from '../components/Layout.vue'
import api from '../services/api'

vi.mock('../services/api')
vi.mock('../components/Layout.vue', () => ({
  default: {
    name: 'Layout',
    template: '<div><slot /></div>'
  }
}))

describe('Leads.vue', () => {
  let wrapper

  const mockStages = [
    { id: 1, name: 'Qualified', order: 1 },
    { id: 2, name: 'Contacted', order: 2 }
  ]

  const mockLeads = [
    { id: 1, name: 'Lead 1', email: 'lead1@test.com', stage: 1, estimated_value: 5000, win_score: 0.75 },
    { id: 2, name: 'Lead 2', email: 'lead2@test.com', stage: 1, estimated_value: 10000, win_score: 0.85 }
  ]

  beforeEach(() => {
    api.get = vi.fn((url) => {
      if (url === '/stages/') {
        return Promise.resolve({ data: mockStages })
      }
      if (url === '/leads/') {
        return Promise.resolve({ data: mockLeads })
      }
      return Promise.reject(new Error('Unknown URL'))
    })

    api.post = vi.fn(() => Promise.resolve({ data: {} }))
    api.patch = vi.fn(() => Promise.resolve({ data: {} }))
    api.delete = vi.fn(() => Promise.resolve({ status: 204 }))
  })

  it('renders empty board message when no stages exist', async () => {
    api.get = vi.fn((url) => {
      if (url === '/stages/') return Promise.resolve({ data: [] })
      if (url === '/leads/') return Promise.resolve({ data: [] })
      return Promise.reject(new Error('Unknown URL'))
    })

    wrapper = mount(Leads, {
      global: {
        stubs: {
          Layout: true,
          'v-card': true,
          'v-card-title': true,
          'v-card-text': true,
          'v-btn': true,
          'v-icon': true,
          'v-spacer': true
        }
      }
    })

    await wrapper.vm.$nextTick()
    await new Promise(resolve => setTimeout(resolve, 100))

    expect(wrapper.text()).toContain('No stages exist')
  })

  it('loads stages and leads on mount', async () => {
    wrapper = mount(Leads, {
      global: {
        stubs: {
          Layout: true,
          'v-card': true,
          'v-card-title': true,
          'v-card-text': true,
          'v-btn': true,
          'v-icon': true,
          'v-spacer': true,
          draggable: true
        }
      }
    })

    await wrapper.vm.$nextTick()
    await new Promise(resolve => setTimeout(resolve, 100))

    expect(api.get).toHaveBeenCalledWith('/stages/')
    expect(api.get).toHaveBeenCalledWith('/leads/')
  })

  it('filters leads by stage correctly', () => {
    wrapper = mount(Leads, {
      data() {
        return {
          leads: mockLeads,
          stages: mockStages
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
          'v-spacer': true
        }
      }
    })

    const leadsInStage1 = wrapper.vm.getLeadsByStage(1)
    expect(leadsInStage1).toHaveLength(2)
    expect(leadsInStage1[0].name).toBe('Lead 1')

    const leadsInStage2 = wrapper.vm.getLeadsByStage(2)
    expect(leadsInStage2).toHaveLength(0)
  })

  it('calls API when moving lead to different stage', async () => {
    wrapper = mount(Leads, {
      data() {
        return {
          leads: mockLeads,
          stages: mockStages
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
          'v-spacer': true
        }
      }
    })

    const dragEvent = {
      added: {
        element: { id: 1 },
        newIndex: 0
      }
    }

    await wrapper.vm.onDragChange(dragEvent, 2)

    expect(api.patch).toHaveBeenCalledWith('/leads/1/', { stage: 2 })
  })

  it('shows error alert when API call fails', async () => {
    api.get = vi.fn(() => Promise.reject(new Error('Network error')))

    wrapper = mount(Leads, {
      global: {
        stubs: {
          Layout: true,
          'v-card': true,
          'v-card-title': true,
          'v-card-text': true,
          'v-btn': true,
          'v-icon': true,
          'v-spacer': true
        }
      }
    })

    await wrapper.vm.loadStages()
    await wrapper.vm.$nextTick()

    expect(global.alert).toHaveBeenCalledWith('Failed to load stages. Please refresh the page.')
  })
})

