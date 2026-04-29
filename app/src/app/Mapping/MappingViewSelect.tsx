import React from 'react'
import { FormSelect, FormSelectOption } from '@patternfly/react-core'
import * as Constants from '../Constants/constants'

export interface MappingViewSelectProps {
  mappingViewSelectValue
  setMappingViewSelectValue
  setMappingViewSelectValueOld
}

export const MappingViewSelect: React.FunctionComponent<MappingViewSelectProps> = ({
  mappingViewSelectValue,
  setMappingViewSelectValue,
  setMappingViewSelectValueOld
}: MappingViewSelectProps) => {
  const onChange = (_event: React.FormEvent<HTMLSelectElement>, value: string) => {
    setMappingViewSelectValueOld(mappingViewSelectValue)
    setMappingViewSelectValue(value)
  }

  const options = [
    { value: Constants._SRs, label: 'Sw Requirements', disabled: false },
    { value: Constants._TSs, label: 'Test Specifications', disabled: false },
    { value: Constants._TCs, label: 'Test Cases', disabled: false },
    { value: Constants._Js, label: 'Justifications Only', disabled: false },
    { value: Constants._DV, label: 'Dynamic View', disabled: false },
    { value: Constants._RS, label: 'Raw Specification', disabled: false }
  ]

  return (
    <FormSelect
      id='select-mapping-view'
      width={50}
      value={mappingViewSelectValue}
      onChange={onChange}
      aria-label='FormSelect Input'
      ouiaId='BasicFormSelect'
    >
      {options.map((option, index) => (
        <FormSelectOption isDisabled={option.disabled} key={index} value={option.value} label={option.label} />
      ))}
    </FormSelect>
  )
}
