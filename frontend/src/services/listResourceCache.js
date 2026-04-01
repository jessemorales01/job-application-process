import { reactive, ref } from 'vue'

/** Bumped on logout/login with clearAllCaches so keep-alive drops in-memory view state. */
export const listCacheSessionId = ref(0)

const entries = reactive({})

export function getEntry(key) {
  if (!entries[key]) {
    entries[key] = { data: null, dirty: true, fetched: false }
  }
  return entries[key]
}

export function markDirty(key) {
  getEntry(key).dirty = true
}

export function markDirtyAutoDetected() {
  Object.keys(entries).forEach((k) => {
    if (k.startsWith('autoDetected:')) {
      entries[k].dirty = true
    }
  })
}

export function markDirtyDashboardLists() {
  ;['jobOffers', 'assessments', 'interactions', 'applications'].forEach(markDirty)
}

export function clearAllCaches() {
  Object.keys(entries).forEach((k) => {
    entries[k].data = null
    entries[k].dirty = true
    entries[k].fetched = false
  })
  listCacheSessionId.value += 1
}

/** Cache key for auto-detected list (must match status query param). */
export function autoDetectedKey(status) {
  const s =
    status === null || status === undefined || status === '' ? 'all' : status
  return `autoDetected:${s}`
}

/**
 * Return cached list if fresh; otherwise GET and store.
 * @returns {{ data: *, fromCache: boolean }}
 */
export async function getOrFetch(
  key,
  url,
  { params, transform, force = false } = {}
) {
  const e = getEntry(key)
  if (force) e.dirty = true
  if (!e.dirty && e.fetched && !force) {
    return { data: e.data, fromCache: true }
  }
  const api = (await import('./api')).default
  const response = await api.get(url, { params })
  let data = response.data
  if (transform) data = transform(data)
  e.data = data
  e.dirty = false
  e.fetched = true
  return { data, fromCache: false }
}

/** After an in-place mutation, keep cache aligned without a round trip. */
export function putCached(key, data) {
  const e = getEntry(key)
  e.data = data
  e.dirty = false
  e.fetched = true
}
