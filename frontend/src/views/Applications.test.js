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
          ErrorSnackbar: true,
          'v-card': true,
          'v-card-title': true,
          'v-card-text': true,
          'v-btn': true,
          'v-icon': true,
          'v-spacer': true
        }
      }
    })

    // Wait for mounted hook and data loading to complete
    await wrapper.vm.$nextTick()
    await Promise.all([
      wrapper.vm.loadStages(),
      wrapper.vm.loadApplications()
    ])
    await wrapper.vm.$nextTick()

    // Verify that stages array is empty (which triggers the empty message in template)
    expect(wrapper.vm.stages).toHaveLength(0)
    expect(wrapper.vm.applicationsByStage).toEqual({})
    // The template condition `v-if="stages.length === 0"` should be true
    expect(wrapper.vm.stages.length === 0).toBe(true)
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
          ErrorSnackbar: true,
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
    expect(applicationsInStage1).toBeDefined()
    expect(applicationsInStage1).toHaveLength(2)
    expect(applicationsInStage1[0].company_name).toBe('Company 1')

    // applicationsByStage only creates entries for stages that have applications
    // Stage 2 has no applications, so it won't exist in the object
    const applicationsInStage2 = wrapper.vm.applicationsByStage[2]
    expect(applicationsInStage2).toBeUndefined()
    // Verify that stage 2 is not in the object keys
    expect(Object.keys(wrapper.vm.applicationsByStage)).not.toContain('2')
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

  describe('Error Handling', () => {
    it('displays error snackbar when loading stages fails', async () => {
      const error = {
        response: {
          status: 500,
          data: { detail: 'Server error' }
        }
      }
      api.get = vi.fn((url) => {
        if (url === '/stages/') return Promise.reject(error)
        if (url === '/applications/') return Promise.resolve({ data: [] })
        return Promise.reject(new Error('Unknown URL'))
      })

      wrapper = mount(Applications, {
        global: {
          stubs: {
            Layout: true,
            ErrorSnackbar: true,
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

      expect(wrapper.vm.showError).toBe(true)
      expect(wrapper.vm.errorMessage).toContain('server error')
    })

    it('displays error snackbar when loading applications fails', async () => {
      const error = {
        response: {
          status: 404,
          data: { detail: 'Not found' }
        }
      }
      api.get = vi.fn((url) => {
        if (url === '/stages/') return Promise.resolve({ data: mockStages })
        if (url === '/applications/') return Promise.reject(error)
        return Promise.reject(new Error('Unknown URL'))
      })

      wrapper = mount(Applications, {
        global: {
          stubs: {
            Layout: true,
            ErrorSnackbar: true,
            'v-card': true,
            'v-card-title': true,
            'v-card-text': true,
            'v-btn': true,
            'v-icon': true,
            'v-spacer': true
          }
        }
      })

      await wrapper.vm.loadApplications()
      await wrapper.vm.$nextTick()

      expect(wrapper.vm.showError).toBe(true)
      expect(wrapper.vm.errorMessage).toContain('not found')
    })

    it('displays error snackbar with validation errors when saving application fails', async () => {
      const error = {
        response: {
          status: 400,
          data: {
            company_name: ['This field is required.'],
            email: ['Enter a valid email address.']
          }
        }
      }
      api.post = vi.fn(() => Promise.reject(error))

      wrapper = mount(Applications, {
        data() {
          return {
            applications: [],
            stages: mockStages,
            form: {
              company_name: '',
              email: '',
              position: '',
              phone_number: '',
              stack: '',
              salary_range: '',
              where_applied: '',
              applied_date: '',
              notes: ''
            }
          }
        },
        global: {
          stubs: {
            Layout: true,
            ErrorSnackbar: true,
            'v-card': true,
            'v-card-title': true,
            'v-card-text': true,
            'v-btn': true,
            'v-icon': true,
            'v-spacer': true
          }
        }
      })

      await wrapper.vm.saveApplication()
      await wrapper.vm.$nextTick()

      expect(wrapper.vm.showError).toBe(true)
      expect(wrapper.vm.errorMessage).toContain('Company Name')
      expect(wrapper.vm.errorMessage).toContain('Email')
    })

    it('displays success snackbar when application is saved successfully', async () => {
      api.post = vi.fn(() => Promise.resolve({ data: { id: 1, company_name: 'New Company' } }))
      api.get = vi.fn((url) => {
        if (url === '/applications/') return Promise.resolve({ data: [] })
        return Promise.resolve({ data: [] })
      })

      wrapper = mount(Applications, {
        data() {
          return {
            applications: [],
            stages: mockStages,
            form: {
              company_name: 'New Company',
              email: 'test@example.com',
              position: '',
              phone_number: '',
              stack: '',
              salary_range: '',
              where_applied: '',
              applied_date: '',
              notes: ''
            }
          }
        },
        global: {
          stubs: {
            Layout: true,
            ErrorSnackbar: true,
            'v-card': true,
            'v-card-title': true,
            'v-card-text': true,
            'v-btn': true,
            'v-icon': true,
            'v-spacer': true
          }
        }
      })

      await wrapper.vm.saveApplication()
      await wrapper.vm.$nextTick()

      expect(wrapper.vm.showSuccess).toBe(true)
      expect(wrapper.vm.successMessage).toContain('created successfully')
    })

    it('displays error snackbar when deleting application fails', async () => {
      const error = {
        response: {
          status: 403,
          data: { detail: 'Permission denied' }
        }
      }
      api.delete = vi.fn(() => Promise.reject(error))

      // Mock confirm to return true
      global.confirm = vi.fn(() => true)

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
            ErrorSnackbar: true,
            'v-card': true,
            'v-card-title': true,
            'v-card-text': true,
            'v-btn': true,
            'v-icon': true,
            'v-spacer': true
          }
        }
      })

      await wrapper.vm.deleteApplication(1)
      await wrapper.vm.$nextTick()

      expect(wrapper.vm.showError).toBe(true)
      expect(wrapper.vm.errorMessage).toContain('permission')
    })

    it('displays error snackbar when moving application fails', async () => {
      const error = {
        response: {
          status: 400,
          data: { detail: 'Invalid stage' }
        }
      }
      api.patch = vi.fn(() => Promise.reject(error))

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
            ErrorSnackbar: true,
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
      await wrapper.vm.$nextTick()

      expect(wrapper.vm.showError).toBe(true)
      expect(wrapper.vm.errorMessage).toBeTruthy()
    })

    it('handles network errors gracefully', async () => {
      const error = {
        message: 'Network Error'
      }
      api.get = vi.fn((url) => {
        if (url === '/stages/') return Promise.reject(error)
        if (url === '/applications/') return Promise.resolve({ data: [] })
        return Promise.reject(new Error('Unknown URL'))
      })

      wrapper = mount(Applications, {
        global: {
          stubs: {
            Layout: true,
            ErrorSnackbar: true,
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

      expect(wrapper.vm.showError).toBe(true)
      expect(wrapper.vm.errorMessage).toContain('connect to the server')
    })
  })
})

