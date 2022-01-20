import React, { useRef } from 'react'

import { PostType, updateStateType } from '@/utils/types'
import { Button } from '@/components/styles/Buttons'
import { Heading3, Text } from '@/components/styles/Text'
import { colors } from '@/components/styles/colors'
import { Card } from '@/components/styles/Card'
import { FormField } from '@/components/styles/Form'
import { Group } from '@/components/styles/Layout'
import { DatesCard, NotesCard } from '@/components/form/SharedCards'
import FiltersCard, { FilterType } from '@/components/form/Filters'
import ClubSelect from '@/components/form/ClubSelect'

interface PostFormProps {
  state: PostType
  updateState: updateStateType
  filters: FilterType[]
}

const PostForm = ({ state, updateState, filters }: PostFormProps) => {
  const imageFile = useRef<HTMLInputElement | null>(null)

  const uploadImage = (e: React.ChangeEvent<HTMLInputElement>) => {
    // const file = e.target.files?.[0]
  }

  return (
    <>
      <Heading3>Content</Heading3>
      <Card>
        <FormField
          label="Title"
          name="title"
          value={state.title}
          placeholder="e.g. Apply to Penn Labs!"
          updateState={updateState}
        />
        <FormField
          label="Description"
          name="subtitle"
          value={state.subtitle}
          placeholder="e.g. Interested in developing new features for Penn Mobile? Come out and meet the team!"
          updateState={updateState}
          textArea={true}
        />

        <Text bold>Club</Text>
        <ClubSelect updateState={updateState} clubCode={state.club_code} />

        <FormField
          label="Link"
          name="post_url"
          value={state.post_url}
          placeholder="e.g. https://pennlabs.org"
          updateState={updateState}
        />
        <Text bold heading>
          Add Cover Image
        </Text>
        <input
          accept="image/*"
          type="file"
          ref={imageFile}
          onChange={uploadImage}
          hidden
        />
        <Group horizontal>
          <Button
            color={colors.IMAGE_BLUE}
            onClick={() => {
              imageFile.current?.click()
            }}
          >
            Browse
          </Button>
          {state.image_url && <Button color={colors.IMAGE_BLUE}>Crop</Button>}
        </Group>
      </Card>

      <DatesCard updateState={updateState} state={state} />

      <FiltersCard
        updateState={updateState}
        targetPopulations={state.target_populations}
        filters={filters}
      />

      <NotesCard updateState={updateState} state={state} />
    </>
  )
}

export default PostForm
