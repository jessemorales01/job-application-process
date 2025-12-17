import { describe, it, expect } from 'vitest'
import { formatErrorMessage, getFieldErrors } from './errorHandler'

describe('errorHandler', () => {
  describe('formatErrorMessage', () => {
    it('handles network errors', () => {
      const error = {
        message: 'Network Error'
      }
      const result = formatErrorMessage(error)
      expect(result).toContain('connect to the server')
      expect(result).toContain('internet connection')
    })

    it('handles 400 Bad Request with field errors', () => {
      const error = {
        response: {
          status: 400,
          data: {
            company_name: ['This field is required.'],
            email: ['Enter a valid email address.']
          }
        }
      }
      const result = formatErrorMessage(error)
      expect(result).toContain('Company Name')
      expect(result).toContain('This field is required')
      expect(result).toContain('Email')
      expect(result).toContain('Enter a valid email address')
    })

    it('handles 400 with non_field_errors', () => {
      const error = {
        response: {
          status: 400,
          data: {
            non_field_errors: ['Invalid credentials provided.']
          }
        }
      }
      const result = formatErrorMessage(error)
      expect(result).toBe('Invalid credentials provided.')
    })

    it('handles 400 with detail field', () => {
      const error = {
        response: {
          status: 400,
          data: {
            detail: 'Invalid input data.'
          }
        }
      }
      const result = formatErrorMessage(error)
      expect(result).toBe('Invalid input data.')
    })

    it('handles 401 Unauthorized', () => {
      const error = {
        response: {
          status: 401
        }
      }
      const result = formatErrorMessage(error)
      expect(result).toContain('session has expired')
      expect(result).toContain('log in again')
    })

    it('handles 403 Forbidden', () => {
      const error = {
        response: {
          status: 403
        }
      }
      const result = formatErrorMessage(error)
      expect(result).toContain('permission')
    })

    it('handles 404 Not Found', () => {
      const error = {
        response: {
          status: 404
        }
      }
      const result = formatErrorMessage(error)
      expect(result).toContain('not found')
    })

    it('handles 422 Unprocessable Entity', () => {
      const error = {
        response: {
          status: 422,
          data: {
            deadline: ['This date is in the past.']
          }
        }
      }
      const result = formatErrorMessage(error)
      expect(result).toContain('Deadline')
      expect(result).toContain('This date is in the past')
    })

    it('handles 500 Internal Server Error', () => {
      const error = {
        response: {
          status: 500
        }
      }
      const result = formatErrorMessage(error)
      expect(result).toContain('server error')
    })

    it('handles 502/503/504 server errors', () => {
      const error502 = {
        response: { status: 502 }
      }
      const error503 = {
        response: { status: 503 }
      }
      const error504 = {
        response: { status: 504 }
      }
      
      expect(formatErrorMessage(error502)).toContain('temporarily unavailable')
      expect(formatErrorMessage(error503)).toContain('temporarily unavailable')
      expect(formatErrorMessage(error504)).toContain('temporarily unavailable')
    })

    it('handles HTML error responses', () => {
      const error = {
        response: {
          status: 400, // Use 400 so it goes through formatValidationErrors
          data: '<!DOCTYPE html><html>Error page</html>'
        }
      }
      const result = formatErrorMessage(error)
      expect(result).toContain('error page')
      expect(result).toContain('check the form fields')
    })

    it('handles string error responses', () => {
      const error = {
        response: {
          status: 400,
          data: 'Simple error message'
        }
      }
      const result = formatErrorMessage(error)
      expect(result).toBe('Simple error message')
    })

    it('handles array field errors', () => {
      const error = {
        response: {
          status: 400,
          data: {
            password: ['This field is required.', 'Password must be at least 8 characters.']
          }
        }
      }
      const result = formatErrorMessage(error)
      expect(result).toContain('Password')
      expect(result).toContain('This field is required')
      expect(result).toContain('Password must be at least 8 characters')
    })

    it('handles single string field errors', () => {
      const error = {
        response: {
          status: 400,
          data: {
            email: 'Invalid email format.'
          }
        }
      }
      const result = formatErrorMessage(error)
      expect(result).toContain('Email')
      expect(result).toContain('Invalid email format')
    })

    it('handles errors without response', () => {
      const error = {
        message: 'Custom error message'
      }
      const result = formatErrorMessage(error)
      expect(result).toBe('Custom error message')
    })

    it('handles errors without message or response', () => {
      const error = {}
      const result = formatErrorMessage(error)
      expect(result).toContain('unexpected error')
    })

    it('handles unknown status codes', () => {
      const error = {
        response: {
          status: 418,
          data: {
            detail: 'I\'m a teapot'
          }
        }
      }
      const result = formatErrorMessage(error)
      expect(result).toBe('I\'m a teapot')
    })

    it('formats field names correctly', () => {
      const error = {
        response: {
          status: 400,
          data: {
            applied_date: ['Invalid date format.'],
            phone_number: ['Invalid phone number.'],
            salary_range: ['This field is required.']
          }
        }
      }
      const result = formatErrorMessage(error)
      expect(result).toContain('Applied Date')
      expect(result).toContain('Phone Number')
      expect(result).toContain('Salary Range')
    })
  })

  describe('getFieldErrors', () => {
    it('extracts field errors from error response', () => {
      const error = {
        response: {
          data: {
            company_name: ['This field is required.'],
            email: ['Enter a valid email address.']
          }
        }
      }
      const result = getFieldErrors(error)
      expect(result.company_name).toBe('This field is required.')
      expect(result.email).toBe('Enter a valid email address.')
    })

    it('handles array field errors', () => {
      const error = {
        response: {
          data: {
            password: ['Too short.', 'Needs uppercase.']
          }
        }
      }
      const result = getFieldErrors(error)
      expect(result.password).toBe('Too short., Needs uppercase.')
    })

    it('ignores non_field_errors and detail', () => {
      const error = {
        response: {
          data: {
            company_name: ['Required'],
            non_field_errors: ['Global error'],
            detail: 'Detail error'
          }
        }
      }
      const result = getFieldErrors(error)
      expect(result.company_name).toBe('Required')
      expect(result.non_field_errors).toBeUndefined()
      expect(result.detail).toBeUndefined()
    })

    it('returns empty object for errors without response', () => {
      const error = {}
      const result = getFieldErrors(error)
      expect(result).toEqual({})
    })

    it('returns empty object for non-object data', () => {
      const error = {
        response: {
          data: 'String error'
        }
      }
      const result = getFieldErrors(error)
      expect(result).toEqual({})
    })

    it('handles null data', () => {
      const error = {
        response: {
          data: null
        }
      }
      const result = getFieldErrors(error)
      expect(result).toEqual({})
    })
  })
})

