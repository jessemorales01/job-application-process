import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import Settings from './Settings.vue'
import api from '../services/api'
import ErrorSnackbar from '../components/ErrorSnackbar.vue'

// Mock the API
vi.mock('../services/api', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    delete: vi.fn(),
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
    props: ['color', 'loading', 'disabled']
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
  'v-divider': { template: '<hr />' },
}

describe('Settings - Email Connection', () => {
  let wrapper

  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.clear()
    localStorage.setItem('access_token', 'test-token')
  })

  const createWrapper = (props = {}) => {
    return mount(Settings, {
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

  it('displays connect email button when no account connected', async () => {
    // Mock API to return no email account (called in mounted)
    api.get.mockResolvedValueOnce({ data: null })

    wrapper = createWrapper()
    // Wait for mounted hook to complete (loadEmailAccount is called there)
    await new Promise(resolve => setTimeout(resolve, 50))
    await wrapper.vm.$nextTick()

    const buttons = wrapper.findAll('button')
    const connectButton = buttons.find(btn => {
      const text = btn.text()
      return text.includes('Connect Email') || text.includes('Connect')
    })
    expect(connectButton).toBeTruthy()
    if (connectButton) {
      expect(connectButton.text()).toContain('Connect')
    }
  })

  it('opens OAuth flow when connect button clicked', async () => {
    // Mock API responses
    api.get.mockResolvedValueOnce({ data: null }) // No account (for loadEmailAccount in mounted)
    api.get.mockResolvedValueOnce({
      data: {
        authorization_url: 'https://accounts.google.com/o/oauth2/auth?state=test',
        state: 'test'
      }
    })

    wrapper = createWrapper()
    // Wait for mounted hook to complete
    await new Promise(resolve => setTimeout(resolve, 50))
    await wrapper.vm.$nextTick()

    const buttons = wrapper.findAll('button')
    const connectButton = buttons.find(btn => {
      const text = btn.text()
      return text.includes('Connect Email') || text.includes('Connect')
    })
    
    // Mock window.location.href to prevent actual redirect
    const originalLocation = window.location
    delete window.location
    window.location = { href: '' }

    if (connectButton) {
      await connectButton.trigger('click')
      await wrapper.vm.$nextTick()
    }

    // Check that OAuth initiate was called (after the initial loadEmailAccount call)
    expect(api.get).toHaveBeenCalledWith(
      '/email-accounts/oauth/initiate/',
      expect.objectContaining({
        params: expect.any(Object)
      })
    )

    // Restore window.location
    window.location = originalLocation
  })

  it('displays connected email account', async () => {
    // Mock API to return connected email account
    const mockAccount = {
      id: 1,
      email: 'test@gmail.com',
      provider: 'gmail',
      is_active: true,
      last_sync_at: '2024-01-01T12:00:00Z'
    }

    api.get.mockResolvedValueOnce({ data: mockAccount })

    wrapper = createWrapper()
    await wrapper.vm.$nextTick()
    await wrapper.vm.loadEmailAccount()
    await wrapper.vm.$nextTick()

    expect(wrapper.text()).toContain('test@gmail.com')
    expect(wrapper.text()).toContain('gmail')
  })

  it('allows disconnecting email account', async () => {
    // Mock API responses
    const mockAccount = {
      id: 1,
      email: 'test@gmail.com',
      provider: 'gmail',
      is_active: true
    }

    api.get.mockResolvedValueOnce({ data: mockAccount })
    api.delete.mockResolvedValueOnce({ status: 204 })

    wrapper = createWrapper()
    await wrapper.vm.$nextTick()
    await wrapper.vm.loadEmailAccount()
    await wrapper.vm.$nextTick()

    const disconnectButton = wrapper.findAll('button').find(btn => 
      btn.text().includes('Disconnect')
    )

    if (disconnectButton) {
      await disconnectButton.trigger('click')
      await wrapper.vm.$nextTick()

      expect(api.delete).toHaveBeenCalledWith(`/email-accounts/${mockAccount.id}/`)
    }
  })

  it('handles OAuth callback when code is present in URL', async () => {
    // Mock window.location.search
    const originalSearch = window.location.search
    Object.defineProperty(window, 'location', {
      value: {
        search: '?code=test_code&state=test_state'
      },
      writable: true
    })

    // Mock API responses
    api.get.mockResolvedValueOnce({ data: null })
    api.get.mockResolvedValueOnce({
      data: {
        authorization_url: 'https://accounts.google.com/o/oauth2/auth',
        state: 'test_state'
      }
    })
    api.get.mockResolvedValueOnce({
      data: {
        id: 1,
        email: 'test@gmail.com',
        provider: 'gmail',
        is_active: true,
        created: true
      }
    })

    wrapper = createWrapper()
    await wrapper.vm.$nextTick()
    await wrapper.vm.handleOAuthCallback()
    await wrapper.vm.$nextTick()

    expect(api.get).toHaveBeenCalledWith(
      '/email-accounts/oauth/callback/',
      expect.objectContaining({
        params: expect.objectContaining({
          code: 'test_code',
          state: 'test_state'
        })
      })
    )

    // Restore
    Object.defineProperty(window, 'location', {
      value: { search: originalSearch },
      writable: true
    })
  })

  it('displays loading state while fetching email account', async () => {
    // Mock API to delay response
    api.get.mockImplementationOnce(() => new Promise(resolve => {
      setTimeout(() => resolve({ data: null }), 100)
    }))

    wrapper = createWrapper()
    await wrapper.vm.$nextTick()

    // Component should show loading state
    expect(wrapper.vm.loading).toBe(true)
  })

  it('displays error message when API call fails', async () => {
    const errorMessage = 'Failed to load email account'
    api.get.mockRejectedValueOnce({
      response: {
        status: 400,
        data: { detail: errorMessage }
      }
    })

    wrapper = createWrapper()
    // Wait for mounted hook to complete (loadEmailAccount is called there)
    await new Promise(resolve => setTimeout(resolve, 50))
    await wrapper.vm.$nextTick()

    expect(wrapper.vm.showError).toBe(true)
    // The error handler formats the message, so check if error message exists
    expect(wrapper.vm.errorMessage).toBeTruthy()
    expect(wrapper.vm.errorMessage.length).toBeGreaterThan(0)
  })

  it('displays last sync time when email account is connected', async () => {
    const mockAccount = {
      id: 1,
      email: 'test@gmail.com',
      provider: 'gmail',
      is_active: true,
      last_sync_at: '2024-01-01T12:00:00Z'
    }

    api.get.mockResolvedValueOnce({ data: mockAccount })

    wrapper = createWrapper()
    await wrapper.vm.$nextTick()
    await wrapper.vm.loadEmailAccount()
    await wrapper.vm.$nextTick()

    expect(wrapper.text()).toContain('Last synced')
  })

  it('shows sync status indicator when account is active', async () => {
    const mockAccount = {
      id: 1,
      email: 'test@gmail.com',
      provider: 'gmail',
      is_active: true
    }

    api.get.mockResolvedValueOnce({ data: mockAccount })

    wrapper = createWrapper()
    await wrapper.vm.$nextTick()
    await wrapper.vm.loadEmailAccount()
    await wrapper.vm.$nextTick()

    expect(wrapper.text()).toContain('Active')
  })
})

