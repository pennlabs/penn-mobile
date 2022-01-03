export interface User {
  username: string
  firstName: string
  lastName: string
  email: string
}

export enum PageType {
  POST,
  POLL,
}

export enum Status {
  DRAFT,
  PENDING, // pending review
  REVISION, // under revision
  APPROVED,
  LIVE,
  EXPIRED,
  REJECTED,
}

export interface ContentType {
  id?: number
  source: string
  startDate: Date | null
  expireDate: Date | null
  userComments: string
  status: Status
  targetPopulations: number[]
}

export interface PollType extends ContentType {
  question: string
  options: { id: number; choice: string }[]
}

export interface PostType extends ContentType {
  title: string
  subtitle: string
  postUrl: string
  imageUrl: string
}

export type updateStateType = (newState: Object) => void
