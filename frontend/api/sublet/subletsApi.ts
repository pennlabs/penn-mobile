// /api/subletsApi.ts
import {
  CreateSubletImageRequest,
  CreateSubletRequest,
  Sublet,
  SubletResponse,
  UpdateSubletRequest,
} from '@/interfaces/sublet/Sublet'
import { doApiRequest } from '@/utils/fetch'

const BASE_URL = 'api/sublet'

export const getSublets = async (): Promise<SubletResponse[]> => {
  const response = await doApiRequest(`${BASE_URL}/listSublets`)
  if (!response.ok) {
    throw new Error('Failed to fetch sublets')
  }
  return response.json()
}

export const getSubletById = async (id: number): Promise<Sublet> => {
  const response = await doApiRequest(
    `${BASE_URL}/retrieveSubletSerializerRead/${id}`
  )
  if (!response.ok) {
    throw new Error('Failed to fetch sublet')
  }
  return response.json()
}

export const createSublet = async (
  data: CreateSubletRequest
): Promise<SubletResponse> => {
  const response = await doApiRequest(`${BASE_URL}/createSublet`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  })
  if (!response.ok) {
    throw new Error('Failed to create sublet')
  }
  return response.json()
}

export const updateSublet = async (
  id: string,
  data: UpdateSubletRequest
): Promise<SubletResponse> => {
  const response = await doApiRequest(`${BASE_URL}/updateSublet/${id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  })
  if (!response.ok) {
    throw new Error('Failed to update sublet')
  }
  return response.json()
}

export const deleteSublet = async (id: number): Promise<void> => {
  const response = await doApiRequest(`${BASE_URL}/destroySublet/${id}`, {
    method: 'DELETE',
  })
  if (!response.ok) {
    throw new Error('Failed to delete sublet')
  }
}

export const uploadSubletImage = async (
  subletId: string,
  data: CreateSubletImageRequest
): Promise<void> => {
  const formData = new FormData()
  formData.append('sublet', data.sublet.toString())
  if (data.image) formData.append('image', data.image)

  const response = await doApiRequest(
    `${BASE_URL}/createSubletImage/${subletId}`,
    {
      method: 'POST',
      body: formData,
    }
  )
  if (!response.ok) {
    throw new Error('Failed to upload sublet image')
  }
}

export const deleteSubletImage = async (imageId: number): Promise<void> => {
  const response = await doApiRequest(
    `${BASE_URL}/destroySubletImage/${imageId}`,
    {
      method: 'DELETE',
    }
  )
  if (!response.ok) {
    throw new Error('Failed to delete sublet image')
  }
}
