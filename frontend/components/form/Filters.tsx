import React, { useState, useEffect } from 'react'
import _, { startCase, camelCase } from 'lodash'
import Select, { MultiValue } from 'react-select'

import { Heading3, Text } from '@/components/styles/Text'
import { Card } from '@/components/styles/Card'
import { ContentType, updateStateType } from '@/utils/types'
import { InfoSpan } from '@/components/styles/Icons'
import { doApiRequest } from '@/utils/fetch'

interface OptionType {
  value: number
  label: string
}

interface SelectedFilters {
  [key: string]: any
}

const FiltersCard = ({
  state,
  updateState,
}: {
  state: ContentType
  updateState: updateStateType
}) => {
  // info for all target populations
  const [populations, setPopulations] = useState<{
    [key: string]: OptionType[]
  }>({})

  // selected target population IDs and labels grouped by kind of target population
  const [selectedFilters, setSelectedFilters] = useState<SelectedFilters>({})

  useEffect(() => {
    // get all population IDs and labels
    doApiRequest('/api/portal/populations/')
      .then((res) => res.json())
      .then((res) => {
        let formattedSelectedFilters: SelectedFilters = {}
        const formattedFilters = res.map((filter: any) => {
          const { id: value, population: label, kind } = filter

          // if target population is previously selected, add to selectedFilters
          // selectedFilters stays empty if all populations are selected
          if (
            state.target_populations.includes(value) &&
            state.target_populations.length !== res.length
          ) {
            if (kind in formattedSelectedFilters) {
              formattedSelectedFilters = {
                ...formattedSelectedFilters,
                [kind]: [...formattedSelectedFilters[kind], { value, label }],
              }
            } else {
              formattedSelectedFilters = {
                ...formattedSelectedFilters,
                [kind]: [{ value, label }],
              }
            }
          }

          return { value, label, kind }
        })

        setSelectedFilters(formattedSelectedFilters)

        // group filters by kind (e.g. major, year)
        setPopulations(_.groupBy(formattedFilters, 'kind'))
      })
  }, [])

  const onChange = (kind: string, newValue: MultiValue<OptionType>) => {
    const newSelectedFilters = {
      ...selectedFilters,
      [kind]: newValue,
    }

    const newFilters: number[] = []
    Object.entries(newSelectedFilters).forEach(([_, populationArr]) =>
      newFilters.push(...populationArr.map((filter: any) => filter.value))
    )

    updateState({ target_populations: newFilters })
    setSelectedFilters(newSelectedFilters)
  }

  return (
    <>
      <Heading3>
        Filters
        <InfoSpan infoText="If no filters are applied, the post will be shared with all Penn Mobile users." />
      </Heading3>
      <Card>
        {Object.entries(populations).map(([kind, populationArr], i) => (
          <div key={`div-${i}`}>
            <Text bold heading id={`text-${kind}-${i}`}>
              {startCase(camelCase(kind))}
            </Text>
            <Select
              isMulti
              options={populationArr}
              defaultValue={selectedFilters[kind]}
              onChange={(selectedVals) => onChange(kind, selectedVals)}
              styles={{
                control: (base, state) => ({
                  ...base,
                  boxShadow: 'none',
                  borderColor: state.isFocused
                    ? 'rgb(50 115 220 / 25%)'
                    : base.borderColor,
                  '&:hover': { borderColor: 'rgb(50 115 220 / 25%)' },
                }),
              }}
              instanceId={`filter-select-${kind}-${i}`}
              id={`filter-select-${kind}-${i}`}
            />
          </div>
        ))}
      </Card>
    </>
  )
}

export default FiltersCard
