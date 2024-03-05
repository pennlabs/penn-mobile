import React from 'react'
import moment from 'moment'

import DatePicker from 'antd/lib/date-picker'
import { updateStateType } from '../../utils/types'

const disabledDate = (current: moment.Moment) =>
  // disable days before today
  current && current < moment().startOf('day')

interface IDatePickerProps {
  updateState: updateStateType
  startDate: Date | null
  expireDate: Date | null
}

const DatePickerForm = ({
  updateState,
  startDate,
  expireDate,
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
        startDate && expireDate
          ? [moment(startDate), moment(expireDate)]
          : undefined
      }
      onChange={(dates) => {
        dates &&
          updateState({
            start_date: dates[0]?.toDate(),
            expire_date: dates[1]?.toDate(),
          })
      }}
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
