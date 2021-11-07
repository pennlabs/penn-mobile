import { PollType } from '../types'

/**
 * converts objects with snake_case keys to camelCase key
 * @param obj object with snake_case keys
 * @returns copy of object with camelCase keys
 */
export const camelizeSnakeKeys = (obj: { [key: string]: string }) => {
  const newObj: { [key: string]: string } = {}
  Object.keys(obj).forEach((key) => {
    const newKey = key.replace(/(_\w)/g, (m) => m[1].toUpperCase())
    newObj[newKey] = obj[key]
  })
  return newObj as unknown as PollType
}
