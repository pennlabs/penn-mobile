/**
 * @returns {string} The CSRF token used by the Django REST Framework
 */
const getCsrf = (): string => {
  const cookiesArray = document.cookie.split('; ')
  const filteredArray = cookiesArray.filter((cookie) =>
    cookie.startsWith('csrftoken=')
  )

  return cookiesArray[0]
    ? decodeURIComponent(filteredArray[0].substring('csrftoken='.length))
    : ''
}

export default getCsrf
