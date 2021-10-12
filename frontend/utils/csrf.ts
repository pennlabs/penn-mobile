/**
 * @returns {string} The CSRF token used by the Django REST Framework
 */
const getCsrf = (): string => {
  const cookiesArray = document.cookie.split('; ')
  cookiesArray.filter((cookie) => cookie.startsWith('csrftoken='))

  return cookiesArray[0]
    ? decodeURIComponent(cookiesArray[0].substring('csrftoken='.length))
    : ''
}

export default getCsrf
