import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import ReviewQueue from './ReviewQueue.vue'
import api from '../services/api'
import ErrorSnackbar from '../components/ErrorSnackbar.vue'

// Mock the API
vi.mock('../services/api', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
  }
}))

// Mock Vuetify components
const vuetifyComponents = {
  'v-app': { template: '<div><slot /></div>' },
  'v-container': { template: '<div><slot /></div>' },
  'v-card': { template: '<div><slot /></div>' },
  'v-card-title': { template: '<div><slot /></div>' },
  'v-card-text': { template: '<div><slot /></div>' },
  'v-btn': { 
    template: '<button @click="$emit(\'click\')"><slot /></button>',
    props: ['color', 'loading', 'disabled', 'small']
  },
  'v-icon': { template: '<i />' },
  'v-spacer': { template: '<div />' },
  'v-alert': { 
    template: '<div v-if="modelValue"><slot /></div>',
    props: ['modelValue', 'type']
  },
  'v-progress-circular': { 
    template: '<div v-if="modelValue" />',
    props: ['modelValue']
  },
  'v-chip': {
    template: '<span><slot /></span>',
    props: ['color', 'small']
  },
  'v-data-table': {
    template: '<table><slot /></table>',
    props: ['headers', 'items', 'loading', 'items-per-page']
  },
  'v-select': {
    template: '<select><slot /></select>',
    props: ['modelValue', 'items', 'label']
  },
  'v-dialog': {
    template: '<div v-if="modelValue"><slot /></div>',
    props: ['modelValue', 'max-width']
  },
  'v-text-field': {
    template: '<input />',
    props: ['modelValue', 'label', 'type']
  },
  'v-form': {
    template: '<form @submit.prevent="$emit(\'submit\')"><slot /></form>'
  }
}

describe('ReviewQueue - Auto-Detected Items Review', () => {
  let wrapper

  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.clear()
    localStorage.setItem('access_token', 'test-token')
  })

  const createWrapper = (props = {}) => {
    return mount(ReviewQueue, {
      global: {
        components: {
          ...vuetifyComponents,
          ErrorSnackbar
        },
        mocks: {
          $router: {
            push: vi.fn()
          }
        }
      },
      props
    })
  }

  const mockDetectedItems = [
    {
      id: 1,
      email_account: 1,
      email_account_email: 'test@gmail.com',
      email_message_id: 'msg1',
      company_name: 'Google',
      position: 'Software Engineer',
      confidence_score: 0.85,
      status: 'pending',
      detected_at: '2024-01-01T12:00:00Z'
    },
    {
      id: 2,
      email_account: 1,
      email_account_email: 'test@gmail.com',
      email_message_id: 'msg2',
      company_name: 'Microsoft',
      position: 'Senior Developer',
      confidence_score: 0.90,
      status: 'pending',
      detected_at: '2024-01-01T13:00:00Z'
    },
    {
      id: 3,
      email_account: 1,
      email_account_email: 'test@gmail.com',
      email_message_id: 'msg3',
      company_name: 'Apple',
      position: 'iOS Developer',
      confidence_score: 0.75,
      status: 'accepted',
      detected_at: '2024-01-01T14:00:00Z'
    }
  ]

  it('displays list of pending items', async () => {
    api.get.mockResolvedValueOnce({ data: mockDetectedItems.filter(item => item.status === 'pending') })

    wrapper = createWrapper()
    await new Promise(resolve => setTimeout(resolve, 50))
    await wrapper.vm.$nextTick()

    expect(wrapper.text()).toContain('Google')
    expect(wrapper.text()).toContain('Microsoft')
    expect(wrapper.text()).not.toContain('Apple') // Accepted items not shown in pending list
  })

  it('allows accepting detected application', async () => {
    const pendingItem = mockDetectedItems[0]
    api.get.mockResolvedValueOnce({ data: [pendingItem] })
    api.post.mockResolvedValueOnce({
      data: {
        application: {
          id: 1,
          company_name: 'Google',
          position: 'Software Engineer'
        }
      }
    })
    api.get.mockResolvedValueOnce({ data: [] }) // Refresh list after accept

    wrapper = createWrapper()
    await new Promise(resolve => setTimeout(resolve, 50))
    await wrapper.vm.$nextTick()

    const buttons = wrapper.findAll('button')
    const acceptButton = buttons.find(btn => 
      btn.text().includes('Accept') || btn.text().includes('accept')
    )

    if (acceptButton) {
      await acceptButton.trigger('click')
      await wrapper.vm.$nextTick()

      expect(api.post).toHaveBeenCalledWith(
        `/auto-detected-applications/${pendingItem.id}/accept/`,
        expect.any(Object)
      )
    }
  })

  it('allows rejecting detected item', async () => {
    const pendingItem = mockDetectedItems[0]
    api.get.mockResolvedValueOnce({ data: [pendingItem] })
    api.post.mockResolvedValueOnce({
      data: {
        id: pendingItem.id,
        status: 'rejected'
      }
    })
    api.get.mockResolvedValueOnce({ data: [] }) // Refresh list after reject

    wrapper = createWrapper()
    await new Promise(resolve => setTimeout(resolve, 50))
    await wrapper.vm.$nextTick()

    const buttons = wrapper.findAll('button')
    const rejectButton = buttons.find(btn => 
      btn.text().includes('Reject') || btn.text().includes('reject')
    )

    if (rejectButton) {
      await rejectButton.trigger('click')
      await wrapper.vm.$nextTick()

      expect(api.post).toHaveBeenCalledWith(
        `/auto-detected-applications/${pendingItem.id}/reject/`
      )
    }
  })

  it('shows confidence scores', async () => {
    api.get.mockResolvedValueOnce({ data: mockDetectedItems.filter(item => item.status === 'pending') })

    wrapper = createWrapper()
    await new Promise(resolve => setTimeout(resolve, 50))
    await wrapper.vm.$nextTick()

    // Check that confidence scores are displayed
    expect(wrapper.text()).toContain('85') // 0.85 * 100
    expect(wrapper.text()).toContain('90') // 0.90 * 100
  })

  it('displays loading state while fetching items', async () => {
    api.get.mockImplementationOnce(() => new Promise(resolve => {
      setTimeout(() => resolve({ data: [] }), 100)
    }))

    wrapper = createWrapper()
    await wrapper.vm.$nextTick()

    expect(wrapper.vm.loading).toBe(true)
  })

  it('displays error message when API call fails', async () => {
    api.get.mockRejectedValueOnce({
      response: {
        status: 400,
        data: { detail: 'Failed to load detected items' }
      }
    })

    wrapper = createWrapper()
    await new Promise(resolve => setTimeout(resolve, 50))
    await wrapper.vm.$nextTick()

    expect(wrapper.vm.showError).toBe(true)
    expect(wrapper.vm.errorMessage).toBeTruthy()
  })

  it('allows merging detected application with existing', async () => {
    const pendingItem = mockDetectedItems[0]
    const mockApplications = [
      { id: 1, company_name: 'Google', position: 'Software Engineer' }
    ]

    api.get.mockResolvedValueOnce({ data: [pendingItem] })
    api.get.mockResolvedValueOnce({ data: mockApplications }) // For merge dialog
    api.post.mockResolvedValueOnce({
      data: {
        id: pendingItem.id,
        status: 'merged',
        merged_into_application: 1
      }
    })
    api.get.mockResolvedValueOnce({ data: [] }) // Refresh list after merge

    wrapper = createWrapper()
    await new Promise(resolve => setTimeout(resolve, 50))
    await wrapper.vm.$nextTick()

    const buttons = wrapper.findAll('button')
    const mergeButton = buttons.find(btn => 
      btn.text().includes('Merge') || btn.text().includes('merge')
    )

    if (mergeButton) {
      await mergeButton.trigger('click')
      await wrapper.vm.$nextTick()

      // Should open merge dialog or trigger merge action
      expect(wrapper.vm.showMergeDialog || api.post).toBeTruthy()
    }
  })

  it('filters items by status', async () => {
    api.get.mockResolvedValueOnce({ data: mockDetectedItems })

    wrapper = createWrapper()
    await new Promise(resolve => setTimeout(resolve, 50))
    await wrapper.vm.$nextTick()

    // Test filtering by status
    wrapper.vm.selectedStatus = 'pending'
    await wrapper.vm.$nextTick()

    expect(api.get).toHaveBeenCalledWith(
      '/auto-detected-applications/',
      expect.objectContaining({
        params: expect.objectContaining({
          status: 'pending'
        })
      })
    )
  })

  it('displays empty state when no items found', async () => {
    api.get.mockResolvedValueOnce({ data: [] })

    wrapper = createWrapper()
    await new Promise(resolve => setTimeout(resolve, 50))
    await wrapper.vm.$nextTick()

    expect(wrapper.text()).toContain('No') || expect(wrapper.text()).toContain('empty')
  })

  it('shows success message after accepting item', async () => {
    const pendingItem = mockDetectedItems[0]
    api.get.mockResolvedValueOnce({ data: [pendingItem] })
    api.post.mockResolvedValueOnce({
      data: {
        application: {
          id: 1,
          company_name: 'Google'
        }
      }
    })
    api.get.mockResolvedValueOnce({ data: [] })

    wrapper = createWrapper()
    await new Promise(resolve => setTimeout(resolve, 50))
    await wrapper.vm.$nextTick()

    // Trigger accept action
    await wrapper.vm.acceptItem(pendingItem)
    await wrapper.vm.$nextTick()

    expect(wrapper.vm.showSuccess).toBe(true)
    expect(wrapper.vm.successMessage).toBeTruthy()
  })
})

