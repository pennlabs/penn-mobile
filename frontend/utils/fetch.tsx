import getCsrf from './csrf'

export const SITE_ORIGIN =
  process.env.NODE_ENV === 'production'
    ? `https://${process.env.DOMAIN || 'portal.pennmobile.org'}`
    : `http://localhost:${process.env.PORT || 3000}`

export const API_BASE_URL = `${SITE_ORIGIN}`

export function getApiUrl(path: string): string {
  if (/^https?:\/\//.test(path)) {
    const url = new URL(path)
    return url.pathname + url.search
  }
  return API_BASE_URL + path
}

/**
 * perform a fetch request to the API
 * @param path e.g. /api/portal/polls/
 * @param data
 * @returns
 */
export function doApiRequest(path: string, data?: any): Promise<Response> {
  let formattedData = data
  if (!formattedData) {
    formattedData = {}
  }
  formattedData.credentials = 'include'
  formattedData.mode = 'same-origin'
  if (typeof document !== 'undefined') {
    formattedData.headers = formattedData.headers || {}
    if (!(formattedData.body instanceof FormData)) {
      formattedData.headers.Accept = 'application/json'
      formattedData.headers['Content-Type'] = 'application/json'
    }
    formattedData.headers['X-CSRFToken'] = getCsrf()
  }
  if (formattedData.body && !(formattedData.body instanceof FormData)) {
    formattedData.body = JSON.stringify(formattedData.body)
  }
  return fetch(getApiUrl(path), formattedData)
}
