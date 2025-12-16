import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import Applications from './Applications.vue'
import Layout from '../components/Layout.vue'
import api from '../services/api'

vi.mock('../services/api')
vi.mock('../components/Layout.vue', () => ({
  default: {
    name: 'Layout',
    template: '<div><slot /></div>'
  }
}))

describe('Applications.vue', () => {
  let wrapper

  const mockStages = [
    { id: 1, name: 'Applied', order: 1 },
    { id: 2, name: 'Interview', order: 2 }
  ]

  const mockApplications = [
    { id: 1, company_name: 'Company 1', stage: 1, salary_range: '80k-120k', stack: 'Python, React' },
    { id: 2, company_name: 'Company 2', stage: 1, salary_range: '100k-150k', stack: 'JavaScript, Vue' }
  ]

  beforeEach(() => {
    api.get = vi.fn((url) => {
      if (url === '/stages/') {
        return Promise.resolve({ data: mockStages })
      }
      if (url === '/applications/') {
        return Promise.resolve({ data: mockApplications })
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
      if (url === '/applications/') return Promise.resolve({ data: [] })
      return Promise.reject(new Error('Unknown URL'))
    })

    wrapper = mount(Applications, {
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

  it('loads stages and applications on mount', async () => {
    wrapper = mount(Applications, {
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
    expect(api.get).toHaveBeenCalledWith('/applications/')
  })

  it('filters applications by stage correctly', () => {
    wrapper = mount(Applications, {
      data() {
        return {
          applications: mockApplications,
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

    const applicationsInStage1 = wrapper.vm.applicationsByStage[1]
    expect(applicationsInStage1).toHaveLength(2)
    expect(applicationsInStage1[0].company_name).toBe('Company 1')

    const applicationsInStage2 = wrapper.vm.applicationsByStage[2]
    expect(applicationsInStage2).toHaveLength(0)
  })

  it('calls API when moving application to different stage', async () => {
    wrapper = mount(Applications, {
      data() {
        return {
          applications: mockApplications,
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

    expect(api.patch).toHaveBeenCalledWith('/applications/1/', { stage: 2 })
  })

  it('shows error alert when API call fails', async () => {
    api.get = vi.fn(() => Promise.reject(new Error('Network error')))

    wrapper = mount(Applications, {
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

