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

export interface PollType {
  id?: number
  question: string
  source: string
  options: { id: number; choice: string }[]
  startDate: Date | null
  expireDate: Date | null
  userComments: string
  status: Status
  targetPopulations: number[]
}

export type updateStateType = (newState: Object) => void
