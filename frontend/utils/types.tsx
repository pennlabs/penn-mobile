export interface User {
  first_name: string
  last_name: string
  email: string
  clubs: Club[]
}

export interface Club {
  name: string
  image?: string
  club_code: string
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
  start_date: Date | null
  expire_date: Date | null
  club_comment: string
  status: Status
  target_populations: number[]
}

export interface PollType extends ContentType {
  club_code: string
  question: string
  options: { id: number; choice: string }[]
}

export interface PostType extends ContentType {
  title: string
  subtitle: string
  source: string // TODO: replace with club_code
  post_url: string
  image_url: string
}

export type updateStateType = (newState: Object) => void
