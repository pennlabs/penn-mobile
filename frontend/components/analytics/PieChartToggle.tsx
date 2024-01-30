import { Toggle, ToggleOption } from '../styles/Buttons'
import { InlineText } from '../styles/Text'

export const PieChartToggle = ({
  activeOption,
  setActiveOption,
}: {
  activeOption: 'school' | 'year'
  setActiveOption: React.Dispatch<React.SetStateAction<'school' | 'year'>>
}) => (
  <Toggle style={{ verticalAlign: 'middle' }}>
    <ToggleOption
      active={activeOption === 'year'}
      onClick={() => setActiveOption('year')}
    >
      <InlineText heading color="inherit">
        Year
      </InlineText>
    </ToggleOption>
    <ToggleOption
      active={activeOption === 'school'}
      onClick={() => setActiveOption('school')}
    >
      <InlineText heading color="inherit">
        School
      </InlineText>
    </ToggleOption>
  </Toggle>
)
