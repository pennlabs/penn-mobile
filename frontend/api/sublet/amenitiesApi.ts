// /api/amenitiesApi.ts

import { doApiRequest } from '@/utils/fetch'

const BASE_URL = 'api/sublet'

export const getAmenities = async (): Promise<string[]> => {
  const response = await doApiRequest(`${BASE_URL}/listAmenities`)
  if (!response.ok) {
    throw new Error('Failed to fetch amenities')
  }
  return response.json()
}
