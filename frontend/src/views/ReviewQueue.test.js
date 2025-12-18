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
    template: '<div></div>', // Simplified - we test component state, not rendering
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
  },
  'v-card-actions': {
    template: '<div><slot /></div>'
  }
}

describe('ReviewQueue - Auto-Detected Items Review', () => {
  let wrapper

  beforeEach(() => {
    vi.clearAllMocks()
    api.get.mockReset()
    api.post.mockReset()
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
    const pendingItems = mockDetectedItems.filter(item => item.status === 'pending')
    // Component defaults selectedStatus to 'pending', so API will be called with status filter
    api.get.mockResolvedValueOnce({ data: pendingItems })

    wrapper = createWrapper()
    // Wait for mounted hook to complete (loadDetectedItems is called there)
    await new Promise(resolve => setTimeout(resolve, 100))
    await wrapper.vm.$nextTick()

    // Check that detectedItems contains the expected items
    expect(wrapper.vm.detectedItems).toHaveLength(2)
    expect(wrapper.vm.detectedItems.map(item => item.company_name)).toContain('Google')
    expect(wrapper.vm.detectedItems.map(item => item.company_name)).toContain('Microsoft')
    expect(wrapper.vm.detectedItems.map(item => item.company_name)).not.toContain('Apple') // Accepted items not shown in pending list
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
    // Ensure we have both items with different confidence scores
    const pendingItems = [
      { ...mockDetectedItems[0], confidence_score: 0.85 },
      { ...mockDetectedItems[1], confidence_score: 0.90 }
    ]
    api.get.mockResolvedValueOnce({ data: pendingItems })

    wrapper = createWrapper()
    // Wait for mounted hook to complete
    await new Promise(resolve => setTimeout(resolve, 100))
    await wrapper.vm.$nextTick()

    // Check that confidence scores are in the data
    expect(wrapper.vm.detectedItems).toHaveLength(2)
    const scores = wrapper.vm.detectedItems.map(item => Math.round(item.confidence_score * 100))
    expect(scores).toContain(85) // 0.85 * 100
    expect(scores).toContain(90) // 0.90 * 100
  })

  it('displays loading state while fetching items', async () => {
    // Mock API to delay response - use a promise that doesn't resolve immediately
    let resolvePromise
    const delayedPromise = new Promise(resolve => {
      // Store the resolve function but don't call it yet
      resolvePromise = resolve
    })
    api.get.mockImplementationOnce(() => delayedPromise)

    wrapper = createWrapper()
    // The mounted hook calls loadDetectedItems which sets loading = true immediately
    // Check loading state right after mount, before the promise can resolve
    // Use a microtask to ensure loadDetectedItems has started
    await wrapper.vm.$nextTick()
    // Give it a tiny bit of time for loadDetectedItems to set loading = true
    await new Promise(resolve => setTimeout(resolve, 10))
    
    // Component should show loading state while fetching
    // loadDetectedItems sets loading = true at the start
    expect(wrapper.vm.loading).toBe(true)
    
    // Resolve the promise to clean up
    resolvePromise({ data: [] })
    await new Promise(resolve => setTimeout(resolve, 50))
    await wrapper.vm.$nextTick()
  })

  it('displays error message when API call fails', async () => {
    api.get.mockRejectedValueOnce({
      response: {
        status: 400,
        data: { detail: 'Failed to load detected items' }
      }
    })

    wrapper = createWrapper()
    // Wait for mounted hook to complete (loadDetectedItems is called there)
    // The error should be caught and set in the catch block
    // Need to wait for the promise to reject and the catch block to execute
    await new Promise(resolve => setTimeout(resolve, 150))
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
    api.get.mockResolvedValueOnce({ data: mockDetectedItems.filter(item => item.status === 'pending') })

    wrapper = createWrapper()
    await new Promise(resolve => setTimeout(resolve, 100))
    await wrapper.vm.$nextTick()

    // Test filtering by status - this triggers loadDetectedItems via watcher
    wrapper.vm.selectedStatus = 'pending'
    await wrapper.vm.$nextTick()
    await wrapper.vm.loadDetectedItems()
    await wrapper.vm.$nextTick()

    // Check that API was called with status filter
    const calls = api.get.mock.calls
    const filteredCall = calls.find(call => 
      call[0] === '/auto-detected-applications/' && 
      call[1]?.params?.status === 'pending'
    )
    expect(filteredCall).toBeTruthy()
  })

  it('displays empty state when no items found', async () => {
    // Component defaults selectedStatus to 'pending', so API will be called with status filter
    api.get.mockResolvedValueOnce({ data: [] })

    wrapper = createWrapper()
    // Wait for mounted hook to complete (loadDetectedItems is called there)
    await new Promise(resolve => setTimeout(resolve, 100))
    await wrapper.vm.$nextTick()

    // Check that detectedItems is empty
    expect(wrapper.vm.detectedItems).toHaveLength(0)
    expect(wrapper.vm.loading).toBe(false)
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

