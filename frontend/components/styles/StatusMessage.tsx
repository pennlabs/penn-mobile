import s, { keyframes } from 'styled-components'
import { colors } from '@/components/styles/colors'
import { Icon } from '@/components/styles/Icons'
import { InlineText } from '@/components/styles/Text'

interface iStatusMessageProps {
  backgroundColor: string
  color: string
}

const SlideInAnimation = keyframes`
  0% {
    -webkit-transform: translateY(-1000px);
            transform: translateY(-1000px);
    opacity: 0;
  }
  100% {
    -webkit-transform: translateY(0);
            transform: translateY(0);
    opacity: 1;
  }
`

const SlideOutAnimation = keyframes`
  0% {
    -webkit-transform: translateY(0);
            transform: translateY(0);
    opacity: 1;
  }
  100% {
    -webkit-transform: translateY(-1000px);
            transform: translateY(-1000px);
    opacity: 0;
  }
`

const StatusMessage = s.div<iStatusMessageProps>`
  border-radius: 10px;
  background-color: ${(props) => props.backgroundColor};
  color: ${(props) => props.color};
  border: solid 1px ${(props) => props.color};
  line-height: 1.5rem;
  padding: 0.75rem;
  margin: 0 auto;
  z-index: 1;
 `

const StatusMessageEnter = s.div`
  animation-name: ${SlideInAnimation};
  animation-duration: 1s;
`

const StatusMessageExit = s.div`
  animation-name: ${SlideOutAnimation};
  animation-duration: 1s;
  animation-delay: 5s;
  animation-fill-mode: forwards;
`

export const SuccessMessage = ({ msg }: { msg: string }) => (
  <StatusMessageEnter>
    <StatusMessageExit>
      <StatusMessage
        backgroundColor={colors.LIGHT_GREEN}
        color={colors.GREEN}
        style={{ position: 'absolute', left: 0, right: 0, width: '50%' }}
      >
        <Icon name="check-circle" color={colors.GREEN} />
        <InlineText heading color={colors.GREEN} style={{ marginLeft: '1rem' }}>
          {msg}
        </InlineText>
      </StatusMessage>
    </StatusMessageExit>
  </StatusMessageEnter>
)

export const ErrorMessage = ({ msg }: { msg: string }) => (
  <StatusMessage
    backgroundColor={colors.LIGHT_RED}
    color={colors.RED}
    style={{ marginBottom: '1rem' }}
  >
    <Icon name="error" color={colors.DARK_RED} />
    <InlineText heading color={colors.DARK_RED} style={{ marginLeft: '1rem' }}>
      {msg}
    </InlineText>
  </StatusMessage>
)
