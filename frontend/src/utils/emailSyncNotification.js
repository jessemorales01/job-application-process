/**
 * Build user-facing copy for POST /email-accounts/sync/ responses.
 * @param {object} data - Response body from sync endpoint
 * @returns {{ type: 'success' | 'warning', message: string }}
 */
export function formatSyncNotification(data) {
  const created = data?.total_detected_created ?? 0
  const accountErrs = Array.isArray(data?.errors) ? data.errors : []
  const procErrs = Number(data?.processing_errors ?? 0)

  const hasAccountErrors = accountErrs.length > 0
  const hasProcessingErrors = procErrs > 0

  if (!hasAccountErrors && !hasProcessingErrors) {
    return {
      type: 'success',
      message: `Sync complete. New detected items: ${created}.`,
    }
  }

  const parts = []
  if (hasAccountErrors) {
    const first = accountErrs[0]?.error || 'Unknown error'
    parts.push(`Sync problem: ${first}`)
    if (accountErrs.length > 1) {
      parts.push(`${accountErrs.length - 1} other account(s) also failed.`)
    }
  }
  if (hasProcessingErrors) {
    parts.push(
      `${procErrs} message(s) failed while processing (other messages may still have been imported).`
    )
  }
  parts.push(`New items: ${created}.`)
  return { type: 'warning', message: parts.join(' ') }
}
