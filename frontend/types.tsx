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

/**
 * the lifecycle of a post/poll :)
 */
export enum Status {
  DRAFT,
  SUBMITTED,
  PENDING,
  APPROVED,
  LIVE,
  EXPIRED,
  REJECTED,
}

export interface PollType {
  id?: number
  question: string
  source: string
  options: { [key: number]: string }
  startDate: Date | null
  expireDate: Date | null
  userComments: string
  status: Status
  targetPopulations: number[]
}

export type updateStateType = (newState: Object) => void
