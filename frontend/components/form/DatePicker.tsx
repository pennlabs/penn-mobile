import React from 'react'
import moment from 'moment'

import DatePicker from 'antd/lib/date-picker'
import { updateStateType } from '../../pages/polls/create'

const disabledDate = (current: moment.Moment) =>
  // disable days before today
  current && current < moment().startOf('day')

interface IDatePickerProps {
  updateState: updateStateType
  startDate: Date | null
  endDate: Date | null
}

const DatePickerForm = ({
  updateState,
  startDate,
  endDate,
}: IDatePickerProps) => {
  const { RangePicker } = DatePicker
  return (
    <RangePicker
      inputReadOnly
      disabledDate={disabledDate}
      showTime={{
        defaultValue: [
          moment('00:00:00', 'HH:mm:ss'),
          moment('23:59:59', 'HH:mm:ss'),
        ],
        format: 'hh:mm A',
        use12Hours: true,
      }}
      format="MM-DD-YYYY hh:mm A"
      defaultValue={
        startDate && endDate ? [moment(startDate), moment(endDate)] : undefined
      }
      onChange={(dates) =>
        dates &&
        updateState({
          startDate: dates[0]?.toDate(),
          endDate: dates[1]?.toDate(),
        })
      }
      style={{
        fontFamily: 'inherit',
        padding: '0.5rem',
        borderRadius: '5px',
        width: '100%',
      }}
    />
  )
}

export default DatePickerForm
