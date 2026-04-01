import { vi } from 'vitest'

const confirmMock = vi.fn(() => true)
globalThis.alert = vi.fn()
globalThis.confirm = confirmMock
if (typeof globalThis.window !== 'undefined') {
  globalThis.window.confirm = confirmMock
}

