import '../stylesheets/devices.min.css'
import type { AppProps } from 'next/app'
import { SWRConfig } from 'swr'
import { config } from '@fortawesome/fontawesome-svg-core'
import { doApiRequest } from '../utils/fetch'
import '@fortawesome/fontawesome-svg-core/styles.css'
import '../stylesheets/globals.css'

config.autoAddCss = false

function MyApp({ Component, pageProps }: AppProps) {
  return (
    <SWRConfig
      value={{
        fetcher: (path, ...args) =>
          doApiRequest(path, ...args).then((res) => res.json()),
        refreshWhenHidden: true,
      }}
    >
      <Component {...pageProps} />
    </SWRConfig>
  )
}
export default MyApp
