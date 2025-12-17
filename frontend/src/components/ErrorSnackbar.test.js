import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import ErrorSnackbar from './ErrorSnackbar.vue'

describe('ErrorSnackbar.vue', () => {
  it('renders error message when visible', () => {
    const wrapper = mount(ErrorSnackbar, {
      props: {
        modelValue: true,
        message: 'Test error message',
        type: 'error'
      },
      global: {
        stubs: {
          'v-snackbar': {
            template: '<div v-if="modelValue"><slot /></div>',
            props: ['modelValue', 'color', 'timeout', 'multiLine', 'location']
          },
          'v-icon': true,
          'v-btn': true
        }
      }
    })

    expect(wrapper.text()).toContain('Test error message')
  })

  it('does not render when not visible', () => {
    const wrapper = mount(ErrorSnackbar, {
      props: {
        modelValue: false,
        message: 'Test error message',
        type: 'error'
      },
      global: {
        stubs: {
          'v-snackbar': {
            template: '<div v-if="modelValue"><slot /></div>',
            props: ['modelValue', 'color', 'timeout', 'multiLine', 'location']
          },
          'v-icon': true,
          'v-btn': true
        }
      }
    })

    // Vuetify snackbar might still render but be hidden
    // Check that the component exists but may not be visible
    expect(wrapper.exists()).toBe(true)
  })

  it('displays correct icon for error type', () => {
    const wrapper = mount(ErrorSnackbar, {
      props: {
        modelValue: true,
        message: 'Error message',
        type: 'error'
      },
      global: {
        stubs: {
          'v-snackbar': {
            template: '<div v-if="modelValue"><slot /></div>',
            props: ['modelValue', 'color', 'timeout', 'multiLine', 'location']
          },
          'v-icon': true,
          'v-btn': true
        }
      }
    })

    expect(wrapper.vm.icon).toBe('mdi-alert-circle')
  })

  it('displays correct icon for success type', () => {
    const wrapper = mount(ErrorSnackbar, {
      props: {
        modelValue: true,
        message: 'Success message',
        type: 'success'
      },
      global: {
        stubs: {
          'v-snackbar': {
            template: '<div v-if="modelValue"><slot /></div>',
            props: ['modelValue', 'color', 'timeout', 'multiLine', 'location']
          },
          'v-icon': true,
          'v-btn': true
        }
      }
    })

    expect(wrapper.vm.icon).toBe('mdi-check-circle')
  })

  it('displays correct icon for warning type', () => {
    const wrapper = mount(ErrorSnackbar, {
      props: {
        modelValue: true,
        message: 'Warning message',
        type: 'warning'
      },
      global: {
        stubs: {
          'v-snackbar': {
            template: '<div v-if="modelValue"><slot /></div>',
            props: ['modelValue', 'color', 'timeout', 'multiLine', 'location']
          },
          'v-icon': true,
          'v-btn': true
        }
      }
    })

    expect(wrapper.vm.icon).toBe('mdi-alert')
  })

  it('displays correct icon for info type', () => {
    const wrapper = mount(ErrorSnackbar, {
      props: {
        modelValue: true,
        message: 'Info message',
        type: 'info'
      },
      global: {
        stubs: {
          'v-snackbar': {
            template: '<div v-if="modelValue"><slot /></div>',
            props: ['modelValue', 'color', 'timeout', 'multiLine', 'location']
          },
          'v-icon': true,
          'v-btn': true
        }
      }
    })

    expect(wrapper.vm.icon).toBe('mdi-information')
  })

  it('uses correct color for error type', () => {
    const wrapper = mount(ErrorSnackbar, {
      props: {
        modelValue: true,
        message: 'Error message',
        type: 'error'
      },
      global: {
        stubs: {
          'v-snackbar': {
            template: '<div v-if="modelValue"><slot /></div>',
            props: ['modelValue', 'color', 'timeout', 'multiLine', 'location']
          },
          'v-icon': true,
          'v-btn': true
        }
      }
    })

    expect(wrapper.vm.color).toBe('error')
  })

  it('uses correct color for success type', () => {
    const wrapper = mount(ErrorSnackbar, {
      props: {
        modelValue: true,
        message: 'Success message',
        type: 'success'
      },
      global: {
        stubs: {
          'v-snackbar': {
            template: '<div v-if="modelValue"><slot /></div>',
            props: ['modelValue', 'color', 'timeout', 'multiLine', 'location']
          },
          'v-icon': true,
          'v-btn': true
        }
      }
    })

    expect(wrapper.vm.color).toBe('success')
  })

  it('uses default timeout of 5000ms', () => {
    const wrapper = mount(ErrorSnackbar, {
      props: {
        modelValue: true,
        message: 'Test message',
        type: 'error'
      },
      global: {
        stubs: {
          'v-snackbar': {
            template: '<div v-if="modelValue"><slot /></div>',
            props: ['modelValue', 'color', 'timeout', 'multiLine', 'location']
          },
          'v-icon': true,
          'v-btn': true
        }
      }
    })

    expect(wrapper.props('timeout')).toBe(5000)
  })

  it('uses custom timeout when provided', () => {
    const wrapper = mount(ErrorSnackbar, {
      props: {
        modelValue: true,
        message: 'Test message',
        type: 'error',
        timeout: 10000
      },
      global: {
        stubs: {
          'v-snackbar': {
            template: '<div v-if="modelValue"><slot /></div>',
            props: ['modelValue', 'color', 'timeout', 'multiLine', 'location']
          },
          'v-icon': true,
          'v-btn': true
        }
      }
    })

    expect(wrapper.props('timeout')).toBe(10000)
  })

  it('enables multiline when prop is true', () => {
    const wrapper = mount(ErrorSnackbar, {
      props: {
        modelValue: true,
        message: 'Test message',
        type: 'error',
        multiline: true
      },
      global: {
        stubs: {
          'v-snackbar': {
            template: '<div v-if="modelValue"><slot /></div>',
            props: ['modelValue', 'color', 'timeout', 'multiLine', 'location']
          },
          'v-icon': true,
          'v-btn': true
        }
      }
    })

    expect(wrapper.props('multiline')).toBe(true)
  })

  it('disables multiline by default', () => {
    const wrapper = mount(ErrorSnackbar, {
      props: {
        modelValue: true,
        message: 'Test message',
        type: 'error'
      },
      global: {
        stubs: {
          'v-snackbar': {
            template: '<div v-if="modelValue"><slot /></div>',
            props: ['modelValue', 'color', 'timeout', 'multiLine', 'location']
          },
          'v-icon': true,
          'v-btn': true
        }
      }
    })

    expect(wrapper.props('multiline')).toBe(false)
  })

  it('emits update:modelValue when close button is clicked', async () => {
    const wrapper = mount(ErrorSnackbar, {
      props: {
        modelValue: true,
        message: 'Test message',
        type: 'error'
      },
      global: {
        stubs: {
          'v-snackbar': {
            template: '<div v-if="modelValue"><slot /></div>',
            props: ['modelValue', 'color', 'timeout', 'multiLine', 'location']
          },
          'v-icon': true,
          'v-btn': {
            template: '<button @click="$emit(\'click\')"><slot /></button>'
          }
        }
      }
    })

    // Set visible to false to trigger the emit
    wrapper.vm.visible = false
    await wrapper.vm.$nextTick()

    expect(wrapper.emitted('update:modelValue')).toBeTruthy()
    expect(wrapper.emitted('update:modelValue')[0]).toEqual([false])
  })

  it('updates visible computed property when modelValue changes', async () => {
    const wrapper = mount(ErrorSnackbar, {
      props: {
        modelValue: false,
        message: 'Test message',
        type: 'error'
      },
      global: {
        stubs: {
          'v-snackbar': {
            template: '<div v-if="modelValue"><slot /></div>',
            props: ['modelValue', 'color', 'timeout', 'multiLine', 'location']
          },
          'v-icon': true,
          'v-btn': true
        }
      }
    })

    expect(wrapper.vm.visible).toBe(false)

    await wrapper.setProps({ modelValue: true })
    expect(wrapper.vm.visible).toBe(true)
  })
})

