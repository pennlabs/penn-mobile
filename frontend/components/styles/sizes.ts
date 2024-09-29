export const NAV_HEIGHT = '4.25rem'
export const NAV_WIDTH = '15%'
export const MAX_BODY_HEIGHT = `calc(100vh - ${NAV_HEIGHT})`

export const DESKTOP = '1248px'
export const TABLET = '992px'
export const PHONE = '584px'

export const minWidth = (w: string): string =>
  `@media screen and (min-width: ${w})`
export const maxWidth = (w: string): string =>
  `@media screen and (max-width: ${w})`
