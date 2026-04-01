/** Max time to wait for POST /email-accounts/sync/ (Gmail + per-message processing on the server). */
export const EMAIL_SYNC_TIMEOUT_MS = 300000

/** Default batch size; large values greatly increase sync duration (AI per message). */
export const EMAIL_SYNC_MAX_RESULTS = 50
