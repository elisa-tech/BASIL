import React from 'react'
import * as Constants from '../../Constants/constants'
import {
  Form,
  FormGroup,
  FormHelperText,
  FormSelect,
  FormSelectOption,
  HelperText,
  HelperTextItem,
  TextInput
} from '@patternfly/react-core'

export interface TestRunConfigFormProps {
  loadSSHKeys
  sshKeys
  testRunConfig
  handleSelectExistingTestConfig
}

export const TestRunConfigForm: React.FunctionComponent<TestRunConfigFormProps> = ({
  loadSSHKeys,
  sshKeys,
  testRunConfig,
  handleSelectExistingTestConfig
}: TestRunConfigFormProps) => {
  const [titleValue, setTitleValue] = React.useState(testRunConfig.title || '')
  const [validatedTitleValue, setValidatedTitleValue] = React.useState<Constants.validate>('error')

  const [provisionTypeValue, setProvisionTypeValue] = React.useState(testRunConfig.provision_type || '')

  const [guestValue, setGuestValue] = React.useState(testRunConfig.provision_guest || '')
  const [validatedGuestValue, setValidatedGuestValue] = React.useState<Constants.validate>('error')

  const [guestPortValue, setGuestPortValue] = React.useState(testRunConfig.provision_guest_port || '')
  const [validatedGuestPortValue, setValidatedGuestPortValue] = React.useState<Constants.validate>('error')

  const [sshKeyValue, setSshKeyValue] = React.useState(testRunConfig.ssh_key || '')

  const [refValue, setRefValue] = React.useState(testRunConfig.git_repo_ref || '')
  const [envVarsValue, setEnvVarsValue] = React.useState(testRunConfig.environment_vars || '')
  const [contextVarsValue, setContextVarsValue] = React.useState(testRunConfig.context_vars || '')

  React.useEffect(() => {
    if (testRunConfig.from_db != null) {
      if (testRunConfig.from_db == 0) {
        return
      }
    }
    if (testRunConfig?.title != null) {
      setTitleValue(testRunConfig.title)
    }
    if (testRunConfig?.provision_type != null) {
      setProvisionTypeValue(testRunConfig.provision_type)
    }
    if (testRunConfig?.provision_guest != null) {
      setGuestValue(testRunConfig.provision_guest)
    }
    if (testRunConfig?.provision_guest_port != null) {
      setGuestPortValue(testRunConfig.provision_guest_port)
    }
    if (testRunConfig?.ssh_key != null) {
      setSshKeyValue(testRunConfig.ssh_key)
    }
    if (testRunConfig?.environment_vars != null) {
      setEnvVarsValue(testRunConfig.environment_vars)
    }
    if (testRunConfig?.context_vars != null) {
      setContextVarsValue(testRunConfig.context_vars)
    }
    if (testRunConfig?.git_repo_ref != null) {
      setRefValue(testRunConfig.git_repo_ref)
    }
  }, [testRunConfig])

  React.useEffect(() => {
    if (titleValue.trim() === '') {
      setValidatedTitleValue('error')
    } else {
      setValidatedTitleValue('success')
    }
    updateTestRunConfig()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [titleValue])

  React.useEffect(() => {
    if (guestValue.trim() === '') {
      setValidatedGuestValue('error')
    } else {
      setValidatedGuestValue('success')
    }
    updateTestRunConfig()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [guestValue])

  React.useEffect(() => {
    if (guestPortValue.trim() === '') {
      setValidatedGuestPortValue('error')
    } else {
      setValidatedGuestPortValue('success')
    }
    updateTestRunConfig()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [guestPortValue])

  React.useEffect(() => {
    if (provisionTypeValue == 'connect') {
      loadSSHKeys()
    }
    updateTestRunConfig()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [provisionTypeValue])

  React.useEffect(() => {
    updateTestRunConfig()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [refValue, envVarsValue, contextVarsValue, sshKeyValue])

  const handleTitleValueChange = (_event, value: string) => {
    setTitleValue(value)
  }

  const handleProvisionTypeChange = (_event, value: string) => {
    setProvisionTypeValue(value)
  }

  const handleGuestValueChange = (_event, value: string) => {
    setGuestValue(value)
  }

  const handleGuestPortValueChange = (_event, value: string) => {
    setGuestPortValue(value)
  }

  const handleSshKeyChange = (_event, value: string) => {
    setSshKeyValue(value)
  }

  const handleRefValueChange = (_event, value: string) => {
    setRefValue(value)
  }

  const handleEnvVarsValueChange = (_event, value: string) => {
    setEnvVarsValue(value)
  }

  const handleContextVarsValueChange = (_event, value: string) => {
    setContextVarsValue(value)
  }

  const updateTestRunConfig = () => {
    const tmpConfig = testRunConfig
    let changed = false
    if (tmpConfig['title'] != titleValue) {
      changed = true
    }
    if (tmpConfig['git_repo_ref'] != refValue) {
      changed = true
    }
    if (tmpConfig['provision_type'] != provisionTypeValue) {
      changed = true
    }
    if (tmpConfig['provision_guest'] != guestValue) {
      changed = true
    }
    if (tmpConfig['provision_guest_port'] != guestPortValue) {
      changed = true
    }
    if (tmpConfig['ssh_key'] != sshKeyValue) {
      changed = true
    }
    if (tmpConfig['environment_vars'] != envVarsValue) {
      changed = true
    }
    if (tmpConfig['context_vars'] != contextVarsValue) {
      changed = true
    }

    tmpConfig['title'] = titleValue
    tmpConfig['git_repo_ref'] = refValue
    tmpConfig['provision_type'] = provisionTypeValue
    tmpConfig['provision_guest'] = guestValue
    tmpConfig['provision_guest_port'] = guestPortValue
    tmpConfig['ssh_key'] = sshKeyValue
    tmpConfig['environment_vars'] = envVarsValue
    tmpConfig['context_vars'] = contextVarsValue

    if (changed == true) {
      tmpConfig['from_db'] = 0
      tmpConfig['id'] = 0
    }

    handleSelectExistingTestConfig(tmpConfig)
  }

  return (
    <Form>
      <FormGroup label='Title' isRequired fieldId={`input-test-run-config-title-${testRunConfig.id || `0`}`}>
        <TextInput
          isRequired
          id={`input-test-run-config-title-${testRunConfig.id || `0`}`}
          name={`input-test-run-config-title-${testRunConfig.id || `0`}`}
          value={titleValue || ''}
          onChange={(_ev, value) => handleTitleValueChange(_ev, value)}
        />
        {validatedTitleValue !== 'success' && (
          <FormHelperText>
            <HelperText>
              <HelperTextItem variant='error'>{validatedTitleValue === 'error' ? 'This field is mandatory' : ''}</HelperTextItem>
            </HelperText>
          </FormHelperText>
        )}
      </FormGroup>

      <FormGroup label='Git branch or commit sha' fieldId={`input-test-run-config-ref-${testRunConfig.id || `0`}`}>
        <TextInput
          id={`input-test-run-config-ref-${testRunConfig.id || `0`}`}
          name={`input-test-run-config-ref-${testRunConfig.id || `0`}`}
          placeholder={`keep empty if you want to use the default branch`}
          value={refValue || ''}
          onChange={(_ev, value) => handleRefValueChange(_ev, value)}
        />
      </FormGroup>

      <FormGroup label='Provision type' isRequired fieldId={`select-test-run-config-provision-type-${testRunConfig.id || `0`}`}>
        <FormSelect
          value={provisionTypeValue}
          id={`select-test-run-config-provision-type-${testRunConfig.id || `0`}`}
          onChange={handleProvisionTypeChange}
          aria-label='Test Run Config Provision Type'
        >
          {Constants.provision_type.map((option, index) => (
            <FormSelectOption isDisabled={option.disabled} key={index} value={option.value} label={option.label} />
          ))}
        </FormSelect>
      </FormGroup>

      {provisionTypeValue == 'connect' ? (
        <>
          <FormGroup label='Hostname or IP address' isRequired fieldId={`input-test-run-config-guest-${testRunConfig.id || `0`}`}>
            <TextInput
              isRequired
              id={`input-test-run-config-guest-${testRunConfig.id || `0`}`}
              name={`input-test-run-config-guest-${testRunConfig.id || `0`}`}
              value={guestValue || ''}
              onChange={(_ev, value) => handleGuestValueChange(_ev, value)}
            />
            {validatedGuestValue !== 'success' && (
              <FormHelperText>
                <HelperText>
                  <HelperTextItem variant='error'>{validatedGuestValue === 'error' ? 'This field is mandatory' : ''}</HelperTextItem>
                </HelperText>
              </FormHelperText>
            )}
          </FormGroup>

          <FormGroup label='Port' isRequired fieldId={`input-test-run-config-guest-port-${testRunConfig.id || `0`}`}>
            <TextInput
              isRequired
              id={`input-test-run-config-guest-port-${testRunConfig.id || `0`}`}
              name={`input-test-run-config-guest-port-${testRunConfig.id || `0`}`}
              value={guestPortValue || ''}
              onChange={(_ev, value) => handleGuestPortValueChange(_ev, value)}
            />
            {validatedGuestPortValue !== 'success' && (
              <FormHelperText>
                <HelperText>
                  <HelperTextItem variant='error'>{validatedGuestPortValue === 'error' ? 'This field is mandatory' : ''}</HelperTextItem>
                </HelperText>
              </FormHelperText>
            )}
          </FormGroup>

          <FormGroup label='SSH Key' isRequired fieldId={`input-test-run-config-ssh-key-${testRunConfig.id || `0`}`}>
            <FormSelect
              value={sshKeyValue}
              id={`input-test-run-config-ssh-key-${testRunConfig.id || `0`}`}
              onChange={handleSshKeyChange}
              aria-label='Test Run Config SSH Key'
            >
              <FormSelectOption key={0} value='' label='' />
              {sshKeys?.map((option, index) => <FormSelectOption key={index} value={option.id} label={option.title} />)}
            </FormSelect>
          </FormGroup>
        </>
      ) : (
        ''
      )}

      <FormGroup label='Environment variables' fieldId={`input-test-run-config-env-vars-${testRunConfig.id || `0`}`}>
        <TextInput
          id={`input-test-run-config-env-vars-${testRunConfig.id || `0`}`}
          name={`input-test-run-config-env-vars-${testRunConfig.id || `0`}`}
          value={envVarsValue || ''}
          placeholder={`format: variable_name1=value1;variable_name2=value2`}
          onChange={(_ev, value) => handleEnvVarsValueChange(_ev, value)}
        />
      </FormGroup>

      <FormGroup label='tmt context variables' fieldId={`input-test-run-config-context-vars-${testRunConfig.id || `0`}`}>
        <TextInput
          id={`input-test-run-config-context-vars-${testRunConfig.id || `0`}`}
          name={`input-test-run-config-context-vars-${testRunConfig.id || `0`}`}
          value={contextVarsValue || ''}
          placeholder={`format: variable_name1=value1;variable_name2=value2`}
          onChange={(_ev, value) => handleContextVarsValueChange(_ev, value)}
        />
      </FormGroup>
    </Form>
  )
}
