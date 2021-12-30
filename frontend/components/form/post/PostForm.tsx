import React, { useRef } from 'react'

import { PostType, updateStateType } from '@/utils/types'
import { Button } from '@/components/styles/Buttons'
import { Heading3, InlineText, Text } from '@/components/styles/Text'
import { colors } from '@/components/styles/colors'
import { Card } from '@/components/styles/Card'
import { FormField } from '@/components/styles/Form'
import { InfoSpan } from '@/components/styles/Icons'
import { Group } from '@/components/styles/Layout'
import DatePickerForm from '@/components/styles/DatePicker'
import { Badge } from '@/components/styles/Badge'

interface PostFormProps {
  state: PostType
  updateState: updateStateType
}

const PostForm = ({ state, updateState }: PostFormProps) => {
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
        <FormField
          label="Organization"
          name="source"
          value={state.source}
          placeholder="e.g. Penn Labs"
          updateState={updateState}
        />
        <FormField
          label="Link"
          name="postUrl"
          value={state.postUrl}
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
          {state.imageUrl && <Button color={colors.IMAGE_BLUE}>Crop</Button>}
        </Group>
      </Card>

      <Heading3>Dates</Heading3>
      <Card>
        <DatePickerForm
          updateState={updateState}
          startDate={state.startDate}
          expireDate={state.expireDate}
        />
      </Card>

      <Heading3>Filters</Heading3>
      <Card>
        <Group horizontal justifyContent="space-between">
          <InlineText
            bold
            heading
            style={{ lineHeight: '1.75rem', width: '5.5rem' }}
          >
            Class Year
          </InlineText>
          <Badge>2021</Badge>
          <Badge>2022</Badge>
          <Badge>2023</Badge>
          <Badge>2024</Badge>
        </Group>
        <Group horizontal justifyContent="space-between">
          <InlineText
            bold
            heading
            style={{ lineHeight: '1.75rem', width: '5.5rem' }}
          >
            School
          </InlineText>
          <Badge>College</Badge>
          <Badge>Wharton</Badge>
          <Badge>SEAS</Badge>
          <Badge>Nursing</Badge>
        </Group>
      </Card>

      <Heading3>
        Notes
        <InfoSpan infoText="Portal admin will see this message during the review process." />
      </Heading3>
      <Card>
        <FormField
          name="userComments"
          value={state.userComments}
          placeholder="Enter any comments here."
          updateState={updateState}
          textArea={true}
        />
      </Card>
    </>
  )
}

export default PostForm
