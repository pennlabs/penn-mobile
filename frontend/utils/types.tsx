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
  POST = 'POST',
  POLL = 'POLL',
}

export enum Status {
  DRAFT = 'DRAFT',
  REVISION = 'REVISION',
  APPROVED = 'APPROVED',
  LIVE = 'LIVE',
  EXPIRED = 'EXPIRED',
  REJECTED = 'REJECTED',
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

export const initialPoll: PollType = {
  question: '',
  club_code: '',
  start_date: null,
  expire_date: null,
  options: [
    { id: 0, choice: '' },
    { id: 1, choice: '' },
  ],
  club_comment: '',
  status: Status.DRAFT,
  target_populations: [],
}

export const initialPost: PostType = {
  title: '',
  subtitle: '',
  source: '', // TODO: replace with club_code
  post_url: '',
  image_url:
    'https://www.akc.org/wp-content/uploads/2017/11/Pembroke-Welsh-Corgi-standing-outdoors-in-the-fall.jpg', // TODO: remove corgi :(
  start_date: null,
  expire_date: null,
  club_comment: '',
  status: Status.DRAFT,
  target_populations: [],
}

// typeguard to determine if content is PostType
export function isPost(content: PostType | PollType): content is PostType {
  return (content as PostType).title !== undefined
}

export type updateStateType = (newState: Object) => void
