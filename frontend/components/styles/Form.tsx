import s from 'styled-components'
import { Text } from './Text'
import { updateStateType } from '../../pages/polls/create'

const FormInputStyle = s.input<{ marginBottom?: boolean }>`
  width: 100%;
  border-radius: 5px;
  padding: 0.75rem;
  background-color: #f7f7f7;
  font-family: inherit;
  border: 1px solid #e6e6e6;
  marginBottom: ${(props) => (props.marginBottom ? '1rem' : '0')};
  &:focus {
    outline: none;
    border: 2px solid rgb(50 115 220 / 25%);
  }
`

const FormTextAreaStyle = s.textarea`
  width: 100%;
  border-radius: 5px;
  padding: 0.75rem;
  background-color: #f7f7f7;
  font-family: inherit;
  border: 1px solid #e6e6e6;
  &:focus {
    outline: none;
    border: 2px solid rgb(50 115 220 / 25%);
  }
`

interface iFormFieldProps {
  label?: string
  name: string
  value: string
  updateState: updateStateType
  placeholder?: string
  marginBottom?: boolean
  textArea?: boolean
}

export const FormField = ({
  label,
  name,
  value,
  updateState,
  placeholder,
  marginBottom,
  textArea,
}: iFormFieldProps) => {
  return (
    <>
      {label && <Text bold>{label}</Text>}
      {textArea ? (
        <FormTextAreaStyle
          rows={3}
          name={name}
          value={value || ''}
          placeholder={placeholder}
          onChange={(e) => updateState({ [name]: e.target.value })}
        />
      ) : (
        <FormInputStyle
          type="text"
          name={name}
          value={value || ''}
          placeholder={placeholder}
          onChange={(e) => updateState({ [name]: e.target.value })}
          marginBottom={marginBottom}
        />
      )}
    </>
  )
}
