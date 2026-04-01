import { describe, it, expect } from 'vitest'
import { formatSyncNotification } from './emailSyncNotification'

describe('formatSyncNotification', () => {
  it('returns success when no errors', () => {
    const r = formatSyncNotification({
      total_detected_created: 2,
      errors: [],
      processing_errors: 0,
    })
    expect(r.type).toBe('success')
    expect(r.message).toContain('Sync complete')
    expect(r.message).toContain('2')
  })

  it('returns warning with first account error', () => {
    const r = formatSyncNotification({
      total_detected_created: 0,
      errors: [{ email: 'a@b.com', error: 'Token expired' }],
      processing_errors: 0,
    })
    expect(r.type).toBe('warning')
    expect(r.message).toContain('Token expired')
    expect(r.message).toContain('New items: 0')
  })

  it('includes processing_errors', () => {
    const r = formatSyncNotification({
      total_detected_created: 1,
      errors: [],
      processing_errors: 3,
    })
    expect(r.type).toBe('warning')
    expect(r.message).toContain('3 message(s) failed')
    expect(r.message).toContain('New items: 1')
  })
})
