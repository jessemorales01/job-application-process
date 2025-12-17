/**
 * Error handling utility for consistent error formatting across the application
 */

/**
 * Formats API error responses into user-friendly messages
 * @param {Error} error - The error object from axios/API call
 * @returns {string} - User-friendly error message
 */
export function formatErrorMessage(error) {
  // Handle network errors
  if (!error.response) {
    if (error.message === 'Network Error') {
      return 'Unable to connect to the server. Please check your internet connection and try again.'
    }
    return error.message || 'An unexpected error occurred. Please try again.'
  }

  const status = error.response.status
  const data = error.response.data

  // Handle different HTTP status codes
  switch (status) {
    case 400:
      return formatValidationErrors(data)
    case 401:
      return 'Your session has expired. Please log in again.'
    case 403:
      return 'You do not have permission to perform this action.'
    case 404:
      return 'The requested resource was not found.'
    case 422:
      return formatValidationErrors(data)
    case 500:
      return 'A server error occurred. Please try again later or contact support if the problem persists.'
    case 502:
    case 503:
    case 504:
      return 'The server is temporarily unavailable. Please try again in a few moments.'
    default:
      return formatValidationErrors(data) || `An error occurred (${status}). Please try again.`
  }
}

/**
 * Formats validation errors from Django REST Framework
 * @param {Object|string} data - Error response data
 * @returns {string} - Formatted error message
 */
function formatValidationErrors(data) {
  // Handle string responses (HTML error pages)
  if (typeof data === 'string') {
    if (data.trim().startsWith('<!')) {
      return 'Server returned an error page. Please check the form fields and try again.'
    }
    return data
  }

  // Handle object responses
  if (typeof data !== 'object' || data === null) {
    return 'Invalid data provided. Please check your input and try again.'
  }

  // Check for detail field (common in DRF)
  if (data.detail) {
    return Array.isArray(data.detail) ? data.detail.join(' ') : data.detail
  }

  // Check for non_field_errors
  if (data.non_field_errors) {
    return Array.isArray(data.non_field_errors)
      ? data.non_field_errors.join(' ')
      : data.non_field_errors
  }

  // Format field-specific errors
  const fieldErrors = []
  for (const [field, messages] of Object.entries(data)) {
    if (field === 'detail' || field === 'non_field_errors') continue
    
    const fieldName = formatFieldName(field)
    const errorList = Array.isArray(messages) ? messages : [messages]
    const formattedErrors = errorList
      .filter(msg => msg) // Remove empty messages
      .map(msg => typeof msg === 'string' ? msg : JSON.stringify(msg))
      .join(', ')
    
    if (formattedErrors) {
      fieldErrors.push(`${fieldName}: ${formattedErrors}`)
    }
  }

  if (fieldErrors.length > 0) {
    return fieldErrors.join('\n')
  }

  return 'Please check the form fields and try again.'
}

/**
 * Formats field names to be more user-friendly
 * @param {string} field - Field name (e.g., 'company_name', 'applied_date')
 * @returns {string} - Formatted field name (e.g., 'Company Name', 'Applied Date')
 */
function formatFieldName(field) {
  return field
    .replace(/_/g, ' ')
    .replace(/\b\w/g, letter => letter.toUpperCase())
}

/**
 * Extracts field-specific errors for inline form validation
 * @param {Error} error - The error object from axios/API call
 * @returns {Object} - Object with field names as keys and error messages as values
 */
export function getFieldErrors(error) {
  if (!error.response || !error.response.data || typeof error.response.data !== 'object') {
    return {}
  }

  const data = error.response.data
  const fieldErrors = {}

  // Extract field errors, skipping non-field errors
  for (const [field, messages] of Object.entries(data)) {
    // Skip non-field error fields
    if (field === 'detail' || field === 'non_field_errors') continue
    
    const errorList = Array.isArray(messages) ? messages : [messages]
    const formattedErrors = errorList
      .filter(msg => msg)
      .map(msg => typeof msg === 'string' ? msg : JSON.stringify(msg))
      .join(', ')
    
    if (formattedErrors) {
      fieldErrors[field] = formattedErrors
    }
  }

  return fieldErrors
}

