import React from 'react'
import _, { startCase, camelCase } from 'lodash'
import Select, { MultiValue } from 'react-select'

import { Heading3, Text } from '@/components/styles/Text'
import { Card } from '@/components/styles/Card'
import { updateStateType } from '@/utils/types'
import { InfoSpan } from '@/components/styles/Icons'

export interface FilterType {
  id: number
  population: string
  kind: string
}

interface OptionType {
  value: number
  label: string
  kind: string
}

interface SelectedFilters {
  [key: string]: any
}

const FiltersCard = ({
  targetPopulations,
  updateState,
  filters,
}: {
  targetPopulations: number[]
  updateState: updateStateType
  filters: FilterType[]
}) => {
  // format all filters for select dropdown, grouped by kind (e.g. major, year, degree)
  const populations = _.groupBy(
    filters.map((filter: any) => ({
      value: filter.id,
      label: filter.population,
      kind: filter.kind,
    })),
    'kind'
  )

  // format previously selected filters with value and label
  const selectedFilters: SelectedFilters = Object.fromEntries(
    Object.entries(populations).map(([kind, value]) => [
      kind,
      value.filter((filter: OptionType) =>
        targetPopulations.includes(filter.value)
      ),
    ])
  )
  const onChange = (kind: string, newValue: MultiValue<OptionType>) => {
    const kindIds = populations[kind].map((filter: OptionType) => filter.value)
    const newFilters: number[] = targetPopulations.filter(
      (id: number) => !kindIds.includes(id)
    )
    newFilters.push(...newValue.map((filter: OptionType) => filter.value))

    updateState({ target_populations: newFilters })
  }

  return (
    <>
      <Heading3>
        Filters
        <InfoSpan infoText="If no filters are applied, the post will be shared with all Penn Mobile users." />
      </Heading3>
      <Card>
        {Object.entries(populations).map(([kind, populationArr], i) => (
          <div key={`div-${kind}`}>
            <Text bold heading id={`text-${kind}`}>
              {startCase(camelCase(kind))}
            </Text>
            <Select
              isMulti
              options={populationArr}
              defaultValue={selectedFilters[kind]}
              onChange={(selectedVals) => onChange(kind, selectedVals)}
              styles={{
                control: (base, selectState) => ({
                  ...base,
                  boxShadow: 'none',
                  borderColor: selectState.isFocused
                    ? 'rgb(50 115 220 / 25%)'
                    : base.borderColor,
                  '&:hover': { borderColor: 'rgb(50 115 220 / 25%)' },
                }),
              }}
              instanceId={`filter-select-${kind}`}
              id={`filter-select-${kind}`}
            />
          </div>
        ))}
      </Card>
    </>
  )
}

export default FiltersCard
