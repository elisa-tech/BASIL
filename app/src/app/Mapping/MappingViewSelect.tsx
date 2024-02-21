import React from 'react'
import { FormSelect, FormSelectOption } from '@patternfly/react-core'

export interface MappingViewSelectProps {
  mappingViewSelectValue
  setMappingViewSelectValue
}

export const MappingViewSelect: React.FunctionComponent<MappingViewSelectProps> = ({
  mappingViewSelectValue,
  setMappingViewSelectValue
}: MappingViewSelectProps) => {
  const onChange = (_event: React.FormEvent<HTMLSelectElement>, value: string) => {
    setMappingViewSelectValue(value)
  }

  const options = [
    { value: 'sw-requirements', label: 'Sw Requirements', disabled: false },
    { value: 'test-specifications', label: 'Test Specifications', disabled: false },
    { value: 'test-cases', label: 'Test Cases', disabled: false },
    { value: 'justifications', label: 'Justifications Only', disabled: false },
    { value: 'specifications', label: 'Raw Specification', disabled: false }
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
