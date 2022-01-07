/**
 * converts objects with snake_case keys to camelCase key
 * @param obj object with snake_case keys
 * @returns copy of object with camelCase keys
 */
export const convertSnakeCase = (obj: { [key: string]: string }) => {
  const newObj: { [key: string]: string } = {}
  Object.keys(obj).forEach((key) => {
    const newKey = key.replace(/(_\w)/g, (m) => m[1].toUpperCase())
    newObj[newKey] = obj[key]
  })
  return newObj
}

/**
 * converts objects with camelCase keys to snake_case key
 * @param obj object with camelCase keys
 * @returns copy of object with snake_case keys
 */
export const convertCamelCase = (obj: any) => {
  const newObj: { [key: string]: string } = {}
  Object.keys(obj).forEach((key) => {
    const newKey = key.replace(/[A-Z]/g, (m) => `_${m.toLowerCase()}`)
    newObj[newKey] = obj[key]
  })
  return newObj
}
