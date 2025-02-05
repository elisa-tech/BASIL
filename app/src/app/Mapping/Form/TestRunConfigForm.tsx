import React from 'react'
import * as Constants from '../../Constants/constants'
import {
  Divider,
  Form,
  FormGroup,
  FormHelperText,
  FormSelect,
  FormSelectOption,
  HelperText,
  HelperTextItem,
  Hint,
  HintBody,
  Label,
  LabelGroup,
  TextInput
} from '@patternfly/react-core'
import { useAuth } from '../../User/AuthProvider'

export interface TestRunConfigFormProps {
  api
  loadSSHKeys
  sshKeys
  testRunConfig
  setTestRunConfig
  infoLabel
  setInfoLabel
}

export const TestRunConfigForm: React.FunctionComponent<TestRunConfigFormProps> = ({
  api,
  loadSSHKeys,
  sshKeys,
  testRunConfig,
  setTestRunConfig,
  infoLabel,
  setInfoLabel
}: TestRunConfigFormProps) => {
  const auth = useAuth()

  const [messageValue, setMessageValue] = React.useState('')

  const [pluginPresetsValue, setPluginPresetsValue] = React.useState([])
  const [pluginValue, setPluginValue] = React.useState(testRunConfig.plugin || 'tmt')

  // tmt
  // - Mandatory fields
  const [titleValue, setTitleValue] = React.useState(testRunConfig.title || '')
  const [validatedTitleValue, setValidatedTitleValue] = React.useState<Constants.validate>('error')

  const [provisionTypeValue, setProvisionTypeValue] = React.useState(testRunConfig.provision_type || '')
  const [validatedProvisionTypeValue, setValidatedProvisionTypeValue] = React.useState<Constants.validate>('error')

  const [guestValue, setGuestValue] = React.useState(testRunConfig.provision_guest || '')
  const [validatedGuestValue, setValidatedGuestValue] = React.useState<Constants.validate>('error')

  const [guestPortValue, setGuestPortValue] = React.useState(testRunConfig.provision_guest_port || '')
  const [validatedGuestPortValue, setValidatedGuestPortValue] = React.useState<Constants.validate>('error')

  const [sshKeyValue, setSshKeyValue] = React.useState(testRunConfig.ssh_key || '')
  const [validatedSSHKeyValue, setValidatedSSHKeyValue] = React.useState<Constants.validate>('error')

  const [refValue, setRefValue] = React.useState(testRunConfig.git_repo_ref || '')
  const [envVarsValue, setEnvVarsValue] = React.useState(testRunConfig.environment_vars || '')
  const [contextVarsValue, setContextVarsValue] = React.useState(testRunConfig.context_vars || '')

  // - Optional fields
  // eslint-disable-next-line  @typescript-eslint/no-unused-vars
  const [pluginVarsValue, setPluginVarsValue] = React.useState(testRunConfig.plugin_vars || '')
  const [pluginPresetValue, setPluginPresetValue] = React.useState('')

  //Gitlab CI
  // - Mandatory fields
  const [gitlabCIUrlValue, setGitlabCIUrlValue] = React.useState('')
  const [validatedGitlabCIUrlValue, setValidatedGitlabCIUrlValue] = React.useState<Constants.validate>('error')

  const [gitlabCIProjectIdValue, setGitlabCIProjectIdValue] = React.useState('')
  const [validatedGitlabCIProjectIdValue, setValidatedGitlabCIProjectIdValue] = React.useState<Constants.validate>('error')

  const [gitlabCITriggerTokenValue, setGitlabCITriggerTokenValue] = React.useState('')
  const [validatedGitlabCITriggerTokenValue, setValidatedGitlabCITriggerTokenValue] = React.useState<Constants.validate>('error')

  const [gitlabCIPrivateTokenValue, setGitlabCIPrivateTokenValue] = React.useState('')
  const [validatedGitlabCIPrivateTokenValue, setValidatedGitlabCIPrivateTokenValue] = React.useState<Constants.validate>('error')

  // - Optional fields
  const [gitlabCIStageValue, setGitlabCIStageValue] = React.useState('')
  const [gitlabCIJobValue, setGitlabCIJobValue] = React.useState('')

  // Github Actions
  // - Mandatory fields
  const [githubActionsUrlValue, setGithubActionsUrlValue] = React.useState('')
  const [validatedGithubActionsUrlValue, setValidatedGithubActionsUrlValue] = React.useState<Constants.validate>('error')

  const [githubActionsPrivateTokenValue, setGithubActionsPrivateTokenValue] = React.useState('')
  const [validatedGithubActionsPrivateTokenValue, setValidatedGithubActionsPrivateTokenValue] = React.useState<Constants.validate>('error')

  // - Optional fields
  const [githubActionsWorkflowIdValue, setGithubActionsWorkflowIdValue] = React.useState('')
  const [githubActionsJobValue, setGithubActionsJobValue] = React.useState('')

  // Testing Farm
  // - Mandatory fields
  const [testingFarmArchValue, setTestingFarmArchValue] = React.useState('')
  const [validatedTestingFarmArchValue, setValidatedTestingFarmArchValue] = React.useState<Constants.validate>('error')

  const [testingFarmComposeValue, setTestingFarmComposeValue] = React.useState('')
  const [validatedTestingFarmComposeValue, setValidatedTestingFarmComposeValue] = React.useState<Constants.validate>('error')

  const [testingFarmPrivateTokenValue, setTestingFarmPrivateTokenValue] = React.useState('')
  const [validatedTestingFarmPrivateTokenValue, setValidatedTestingFarmPrivateTokenValue] = React.useState<Constants.validate>('error')

  const [testingFarmUrlValue, setTestingFarmUrlValue] = React.useState('')
  const [validatedTestingFarmUrlValue, setValidatedTestingFarmUrlValue] = React.useState<Constants.validate>('error')

  const [testingFarmComposes, setTestingFarmComposes] = React.useState<string[]>([])

  const loadTestingFarmCompose = () => {
    setMessageValue('')
    setTestingFarmComposes([]) // clean the list before showing it again

    fetch(Constants.TESTING_FARM_COMPOSES_URL)
      .then((res) => {
        if (!res.ok) {
          setMessageValue('Error loading Testing Farm Composes')
          return []
        } else {
          return res.json()
        }
      })
      .then((data) => {
        const tmp: string[] = []
        const skip_chars: string[] = ['+', '*']
        let skip: boolean = false
        for (let i = 0; i < data['composes'].length; i++) {
          skip = false
          for (let j = 0; j < skip_chars.length; j++) {
            if (data['composes'][i]['name'].indexOf(skip_chars[j]) > -1) {
              skip = true
              break
            }
          }
          if (!skip) {
            tmp.push(data['composes'][i]['name'])
          }
        }
        setTestingFarmComposes(tmp)
      })
      .catch((err) => {
        console.log(err.message)
        setMessageValue('Error reading Testing Farm composes: ' + err.message)
      })
  }

  const load_plugin_presets = (_plugin) => {
    let url = Constants.API_BASE_URL + '/mapping/api/test-run-plugins-presets?plugin=' + _plugin
    url += '&api-id=' + api.id

    if (auth.isLogged()) {
      url += '&user-id=' + auth.userId + '&token=' + auth.token
    } else {
      return
    }

    fetch(url)
      .then((res) => res.json())
      .then((data) => {
        setPluginPresetsValue(data)
      })
      .catch((err) => {
        console.log(err.message)
      })
  }

  React.useEffect(() => {
    // Inject data to the js object in case of existing data
    if (testRunConfig?.id == 0 || testRunConfig?.id == undefined) {
      return
    }
    if (testRunConfig?.title != null) {
      setTitleValue(testRunConfig.title)
    }
    if (testRunConfig?.plugin != null) {
      setPluginValue(testRunConfig.plugin)
      load_plugin_presets(testRunConfig.plugin)
    }
    if (testRunConfig?.plugin_preset != null) {
      setPluginPresetValue(testRunConfig.plugin_preset)
    }
    if (testRunConfig?.plugin_vars != null) {
      setPluginVarsValue(testRunConfig.plugin_vars)
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
    //gitlab_ci
    if (testRunConfig?.plugin == Constants.gitlab_ci_plugin) {
      if (testRunConfig?.url != null) {
        setGitlabCIUrlValue(testRunConfig.url)
      }
      if (testRunConfig?.project_id != null) {
        setGitlabCIProjectIdValue(testRunConfig.project_id)
      }
      if (testRunConfig?.trigger_token != null) {
        setGitlabCITriggerTokenValue(testRunConfig.trigger_token)
      }
      if (testRunConfig?.private_token != null) {
        setGitlabCIPrivateTokenValue(testRunConfig.private_token)
      }
      if (testRunConfig?.stage != null) {
        setGitlabCIStageValue(testRunConfig.stage)
      }
      if (testRunConfig?.job != null) {
        setGitlabCIJobValue(testRunConfig.job)
      }
    } else if (testRunConfig?.plugin == Constants.github_actions_plugin) {
      if (testRunConfig?.job != null) {
        setGithubActionsJobValue(testRunConfig.job)
      }
      if (testRunConfig?.url != null) {
        setGithubActionsUrlValue(testRunConfig.url)
      }
      if (testRunConfig?.workflow_id != null) {
        setGithubActionsWorkflowIdValue(testRunConfig.workflow_id)
      }
      if (testRunConfig?.private_token != null) {
        setGithubActionsPrivateTokenValue(testRunConfig.private_token)
      }
    } else if (testRunConfig?.plugin == Constants.testing_farm_plugin) {
      if (testRunConfig?.compose != null) {
        setTestingFarmComposes(testRunConfig.compose)
      }
      if (testRunConfig?.arch != null) {
        setTestingFarmArchValue(testRunConfig.arch)
      }
      if (testRunConfig?.private_token != null) {
        setTestingFarmPrivateTokenValue(testRunConfig.private_token)
      }
      if (testRunConfig?.url != null) {
        setTestingFarmUrlValue(testRunConfig.url)
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
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
    if (provisionTypeValue.trim() === '') {
      setValidatedProvisionTypeValue('error')
    } else {
      setValidatedProvisionTypeValue('success')
    }

    if (provisionTypeValue == 'connect') {
      loadSSHKeys()
    }

    updateTestRunConfig()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [provisionTypeValue])

  React.useEffect(() => {
    updateTestRunConfig()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [refValue, envVarsValue, contextVarsValue])

  React.useEffect(() => {
    if (sshKeyValue.trim() === '') {
      setValidatedSSHKeyValue('error')
    } else {
      setValidatedSSHKeyValue('success')
    }

    updateTestRunConfig()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sshKeyValue])

  React.useEffect(() => {
    updateTestRunConfig()
    load_plugin_presets(pluginValue)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [pluginValue, pluginPresetValue])

  React.useEffect(() => {
    if (gitlabCIUrlValue.trim() === '') {
      setValidatedGitlabCIUrlValue('error')
    } else {
      setValidatedGitlabCIUrlValue('success')
    }

    if (gitlabCIProjectIdValue.trim() === '') {
      setValidatedGitlabCIProjectIdValue('error')
    } else {
      setValidatedGitlabCIProjectIdValue('success')
    }

    if (gitlabCITriggerTokenValue.trim() === '') {
      setValidatedGitlabCITriggerTokenValue('error')
    } else {
      setValidatedGitlabCITriggerTokenValue('success')
    }

    if (gitlabCIPrivateTokenValue.trim() === '') {
      setValidatedGitlabCIPrivateTokenValue('error')
    } else {
      setValidatedGitlabCIPrivateTokenValue('success')
    }

    updateTestRunConfig()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [gitlabCIJobValue, gitlabCIPrivateTokenValue, gitlabCIProjectIdValue, gitlabCIStageValue, gitlabCITriggerTokenValue, gitlabCIUrlValue])

  React.useEffect(() => {
    if (githubActionsUrlValue.trim() === '') {
      setValidatedGithubActionsUrlValue('error')
    } else {
      setValidatedGithubActionsUrlValue('success')
    }

    if (githubActionsPrivateTokenValue.trim() === '') {
      setValidatedGithubActionsPrivateTokenValue('error')
    } else {
      setValidatedGithubActionsPrivateTokenValue('success')
    }

    updateTestRunConfig()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [githubActionsJobValue, githubActionsUrlValue, githubActionsWorkflowIdValue, githubActionsPrivateTokenValue])

  React.useEffect(() => {
    if (testingFarmArchValue.trim() === '') {
      setValidatedTestingFarmArchValue('error')
    } else {
      setValidatedTestingFarmArchValue('success')
    }

    if (testingFarmComposeValue.trim() === '') {
      setValidatedTestingFarmComposeValue('error')
    } else {
      setValidatedTestingFarmComposeValue('success')
    }

    if (testingFarmPrivateTokenValue.trim() === '') {
      setValidatedTestingFarmPrivateTokenValue('error')
    } else {
      setValidatedTestingFarmPrivateTokenValue('success')
    }

    if (testingFarmUrlValue.trim() === '') {
      setValidatedTestingFarmUrlValue('error')
    } else {
      setValidatedTestingFarmUrlValue('success')
    }

    updateTestRunConfig()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [testingFarmArchValue, testingFarmComposeValue, testingFarmUrlValue, testingFarmPrivateTokenValue])

  const set_test_run_config_forked = () => {
    const tmpConfig = testRunConfig
    tmpConfig['id'] = 0
    setTestRunConfig(tmpConfig)
    setInfoLabel('new')
  }

  const handleTitleValueChange = (_event, value: string) => {
    setTitleValue(value)
    set_test_run_config_forked()
  }

  const handlePluginChange = (_event, value: string) => {
    setPluginValue(value)
    load_plugin_presets(value)
    if (value == Constants.testing_farm_plugin) {
      if (testingFarmComposes.length == 0) {
        loadTestingFarmCompose()
      }
    }
    set_test_run_config_forked()
  }

  const handlePluginPresetChange = (_event, value: string) => {
    setPluginPresetValue(value)
    set_test_run_config_forked()
  }

  const handleProvisionTypeChange = (_event, value: string) => {
    setProvisionTypeValue(value)
    set_test_run_config_forked()
  }

  const handleGuestValueChange = (_event, value: string) => {
    setGuestValue(value)
    set_test_run_config_forked()
  }

  const handleGuestPortValueChange = (_event, value: string) => {
    setGuestPortValue(value)
    set_test_run_config_forked()
  }

  const handleSshKeyChange = (_event, value: string) => {
    setSshKeyValue(value)
    set_test_run_config_forked()
  }

  const handleRefValueChange = (_event, value: string) => {
    setRefValue(value)
    set_test_run_config_forked()
  }

  const handleEnvVarsValueChange = (_event, value: string) => {
    setEnvVarsValue(value)
    set_test_run_config_forked()
  }

  const handleContextVarsValueChange = (_event, value: string) => {
    setContextVarsValue(value)
    set_test_run_config_forked()
  }

  // Gitlab CI
  const handleGitlabCIUrlValueChange = (_event, value: string) => {
    setGitlabCIUrlValue(value)
    set_test_run_config_forked()
  }

  const handleGitlabCIProjectIdValueChange = (_event, value: string) => {
    setGitlabCIProjectIdValue(value)
    set_test_run_config_forked()
  }

  const handleGitlabCIStageValueChange = (_event, value: string) => {
    setGitlabCIStageValue(value)
    set_test_run_config_forked()
  }

  const handleGitlabCIJobValueChange = (_event, value: string) => {
    setGitlabCIJobValue(value)
    set_test_run_config_forked()
  }

  const handleGitlabCITriggerTokenValueChange = (_event, value: string) => {
    setGitlabCITriggerTokenValue(value)
    set_test_run_config_forked()
  }

  const handleGitlabCIPrivateTokenValueChange = (_event, value: string) => {
    setGitlabCIPrivateTokenValue(value)
    set_test_run_config_forked()
  }

  // Github Actions
  const handleGithubActionsUrlValueChange = (_event, value: string) => {
    setGithubActionsUrlValue(value)
    set_test_run_config_forked()
  }

  const handleGithubActionsWorkflowIdValueChange = (_event, value: string) => {
    setGithubActionsWorkflowIdValue(value)
    set_test_run_config_forked()
  }

  const handleGithubActionsPrivateTokenValueChange = (_event, value: string) => {
    setGithubActionsPrivateTokenValue(value)
    set_test_run_config_forked()
  }

  const handleGithubActionsJobValueChange = (_event, value: string) => {
    setGithubActionsJobValue(value)
    set_test_run_config_forked()
  }

  //Testing Farm
  const handleTestingFarmArchChange = (_event, value: string) => {
    setTestingFarmArchValue(value)
    set_test_run_config_forked()
  }

  const handleTestingFarmComposeChange = (_event, value: string) => {
    setTestingFarmComposeValue(value)
    set_test_run_config_forked()
  }

  const handleTestingFarmUrlChange = (_event, value: string) => {
    setTestingFarmUrlValue(value)
    set_test_run_config_forked()
  }

  const handleTestingFarmPrivateTokenChange = (_event, value: string) => {
    setTestingFarmPrivateTokenValue(value)
    set_test_run_config_forked()
  }

  const updateTestRunConfig = () => {
    const tmpConfig = testRunConfig

    tmpConfig['title'] = titleValue
    tmpConfig['git_repo_ref'] = refValue
    tmpConfig['plugin'] = pluginValue
    tmpConfig['plugin_preset'] = pluginPresetValue
    tmpConfig['environment_vars'] = envVarsValue

    if (pluginValue == Constants.gitlab_ci_plugin) {
      tmpConfig['job'] = pluginPresetValue == '' ? gitlabCIJobValue : ''
      tmpConfig['private_token'] = pluginPresetValue == '' ? gitlabCIPrivateTokenValue : ''
      tmpConfig['project_id'] = pluginPresetValue == '' ? gitlabCIProjectIdValue : ''
      tmpConfig['stage'] = pluginPresetValue == '' ? gitlabCIStageValue : ''
      tmpConfig['trigger_token'] = pluginPresetValue == '' ? gitlabCITriggerTokenValue : ''
      tmpConfig['url'] = pluginPresetValue == '' ? gitlabCIUrlValue : ''
    } else if (pluginValue == Constants.github_actions_plugin) {
      tmpConfig['job'] = pluginPresetValue == '' ? githubActionsJobValue : ''
      tmpConfig['private_token'] = pluginPresetValue == '' ? githubActionsPrivateTokenValue : ''
      tmpConfig['workflow_id'] = pluginPresetValue == '' ? githubActionsWorkflowIdValue : ''
      tmpConfig['url'] = pluginPresetValue == '' ? githubActionsUrlValue : ''
    } else if (pluginValue == Constants.tmt_plugin) {
      tmpConfig['context_vars'] = contextVarsValue
      tmpConfig['provision_type'] = pluginPresetValue == '' ? provisionTypeValue : ''
      tmpConfig['provision_guest'] = pluginPresetValue == '' ? guestValue : ''
      tmpConfig['provision_guest_port'] = pluginPresetValue == '' ? guestPortValue : ''
      tmpConfig['ssh_key'] = pluginPresetValue == '' ? sshKeyValue : ''
    } else if (pluginValue == Constants.testing_farm_plugin) {
      tmpConfig['context_vars'] = contextVarsValue
      tmpConfig['compose'] = testingFarmComposeValue
      tmpConfig['arch'] = testingFarmArchValue
      tmpConfig['private_token'] = pluginPresetValue == '' ? testingFarmPrivateTokenValue : ''
      tmpConfig['url'] = pluginPresetValue == '' ? testingFarmUrlValue : ''
    }
  }

  return (
    <Form>
      {messageValue ? (
        <>
          <Hint>
            <HintBody>{messageValue}</HintBody>
          </Hint>
          <br />
        </>
      ) : (
        ''
      )}
      <LabelGroup categoryName='This config is'>
        <Label>{infoLabel}</Label>
      </LabelGroup>
      <Divider></Divider>
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

      <FormGroup label='Plugin' isRequired fieldId={`select-test-run-config-plugin-${testRunConfig.id || `0`}`}>
        <FormSelect
          value={pluginValue}
          id={`select-test-run-config-plugin-${testRunConfig.id || `0`}`}
          onChange={handlePluginChange}
          aria-label='Test Run Config Plugin'
        >
          {Constants.test_run_plugins.map((option, index) => (
            <FormSelectOption isDisabled={!option.trigger} key={index} value={option.value} label={option.label} />
          ))}
        </FormSelect>
      </FormGroup>

      {pluginPresetsValue.length > 0 ? (
        <FormGroup label='Plugin Presets' fieldId={`select-test-run-config-plugin-preset-${testRunConfig.id || `0`}`}>
          <FormSelect
            value={pluginPresetValue}
            id={`select-test-run-config-plugin-preset-${testRunConfig.id || `0`}`}
            onChange={handlePluginPresetChange}
            aria-label='Test Run Config Plugin Preset'
          >
            <FormSelectOption isDisabled={false} key={0} value={``} label={`Do not use a preset configuration`} />
            {pluginPresetsValue.map((option, index) => (
              <FormSelectOption isDisabled={false} key={index + 1} value={option} label={option} />
            ))}
          </FormSelect>
        </FormGroup>
      ) : (
        ''
      )}

      <FormGroup label='Git branch or commit sha' fieldId={`input-test-run-config-ref-${testRunConfig.id || `0`}`}>
        <TextInput
          id={`input-test-run-config-ref-${testRunConfig.id || `0`}`}
          name={`input-test-run-config-ref-${testRunConfig.id || `0`}`}
          placeholder={`keep empty if you want to use the default branch`}
          value={refValue || ''}
          onChange={(_ev, value) => handleRefValueChange(_ev, value)}
        />
      </FormGroup>

      {pluginValue == Constants.tmt_plugin && pluginPresetValue == '' ? (
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
          {validatedProvisionTypeValue !== 'success' && (
            <FormHelperText>
              <HelperText>
                <HelperTextItem variant='error'>{validatedProvisionTypeValue === 'error' ? 'This field is mandatory' : ''}</HelperTextItem>
              </HelperText>
            </FormHelperText>
          )}
        </FormGroup>
      ) : (
        ''
      )}

      {pluginValue == Constants.tmt_plugin && pluginPresetValue == '' && provisionTypeValue == 'connect' ? (
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
            {validatedSSHKeyValue !== 'success' && (
              <FormHelperText>
                <HelperText>
                  <HelperTextItem variant='error'>{validatedSSHKeyValue === 'error' ? 'This field is mandatory' : ''}</HelperTextItem>
                </HelperText>
              </FormHelperText>
            )}
          </FormGroup>
        </>
      ) : (
        ''
      )}

      {pluginValue == Constants.testing_farm_plugin && pluginPresetValue == '' ? (
        <>
          <FormGroup label='Url (Testing Farm)' isRequired fieldId={`input-test-run-config-tf-url-${testRunConfig.id || `0`}`}>
            <TextInput
              isRequired
              id={`input-test-run-config-tf-url-${testRunConfig.id || `0`}`}
              name={`input-test-run-config-tf-url-${testRunConfig.id || `0`}`}
              value={testingFarmUrlValue || ''}
              placeholder={`example: https://api.dev.testing-farm.io/v0.1/requests`}
              onChange={(_ev, value) => handleTestingFarmUrlChange(_ev, value)}
            />
            {validatedTestingFarmUrlValue !== 'success' && (
              <FormHelperText>
                <HelperText>
                  <HelperTextItem variant='error'>
                    {validatedTestingFarmUrlValue === 'error' ? 'This field is mandatory' : ''}
                  </HelperTextItem>
                </HelperText>
              </FormHelperText>
            )}
          </FormGroup>

          <FormGroup label='Api Token (Testing Farm)' isRequired fieldId={`input-test-run-config-tf-token-${testRunConfig.id || `0`}`}>
            <TextInput
              isRequired
              id={`input-test-run-config-tf-token-${testRunConfig.id || `0`}`}
              name={`input-test-run-config-tf-token-${testRunConfig.id || `0`}`}
              value={testingFarmPrivateTokenValue || ''}
              placeholder={`your token`}
              onChange={(_ev, value) => handleTestingFarmPrivateTokenChange(_ev, value)}
            />
            {validatedTestingFarmPrivateTokenValue !== 'success' && (
              <FormHelperText>
                <HelperText>
                  <HelperTextItem variant='error'>
                    {validatedTestingFarmPrivateTokenValue === 'error' ? 'This field is mandatory' : ''}
                  </HelperTextItem>
                </HelperText>
              </FormHelperText>
            )}
          </FormGroup>

          <FormGroup label='Compose' isRequired fieldId={`input-test-run-config-tf-compose-${testRunConfig.id || `0`}`}>
            <FormSelect
              value={testingFarmComposeValue}
              id={`input-test-run-config-tf-compose-${testRunConfig.id || `0`}`}
              onChange={handleTestingFarmComposeChange}
              aria-label='Test Run Config Testing Farm Compose'
            >
              <FormSelectOption key={0} value='' label='' />
              {testingFarmComposes?.map((option, index) => <FormSelectOption key={index} value={option} label={option} />)}
            </FormSelect>
            {validatedTestingFarmComposeValue !== 'success' && (
              <FormHelperText>
                <HelperText>
                  <HelperTextItem variant='error'>
                    {validatedTestingFarmComposeValue === 'error' ? 'This field is mandatory' : ''}
                  </HelperTextItem>
                </HelperText>
              </FormHelperText>
            )}
          </FormGroup>

          <FormGroup label='Arch' isRequired fieldId={`input-test-run-config-tf-arch-${testRunConfig.id || `0`}`}>
            <FormSelect
              value={testingFarmArchValue}
              id={`input-test-run-config-tf-arch-${testRunConfig.id || `0`}`}
              onChange={handleTestingFarmArchChange}
              aria-label='Test Run Config Testing Farm Arch'
            >
              <FormSelectOption key={0} value='' label='' />
              {Constants.testing_farm_archs?.map((option, index) => (
                <FormSelectOption key={index} value={option.value} label={option.label} />
              ))}
            </FormSelect>
            {validatedTestingFarmArchValue !== 'success' && (
              <FormHelperText>
                <HelperText>
                  <HelperTextItem variant='error'>
                    {validatedTestingFarmArchValue === 'error' ? 'This field is mandatory' : ''}
                  </HelperTextItem>
                </HelperText>
              </FormHelperText>
            )}
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

      {pluginValue == Constants.tmt_plugin || pluginValue == Constants.testing_farm_plugin ? (
        <FormGroup label='tmt context variables' fieldId={`input-test-run-config-context-vars-${testRunConfig.id || `0`}`}>
          <TextInput
            id={`input-test-run-config-context-vars-${testRunConfig.id || `0`}`}
            name={`input-test-run-config-context-vars-${testRunConfig.id || `0`}`}
            value={contextVarsValue || ''}
            placeholder={`format: variable_name1=value1;variable_name2=value2`}
            onChange={(_ev, value) => handleContextVarsValueChange(_ev, value)}
          />
        </FormGroup>
      ) : (
        ''
      )}

      {pluginValue == Constants.gitlab_ci_plugin && pluginPresetValue == '' ? (
        <>
          <FormGroup label='Url (gitlab ci)' isRequired fieldId={`input-test-run-config-gitlab-ci-url-${testRunConfig.id || `0`}`}>
            <TextInput
              isRequired
              id={`input-test-run-config-gitlab-ci-url-${testRunConfig.id || `0`}`}
              name={`input-test-run-config-gitlab-ci-url-${testRunConfig.id || `0`}`}
              value={gitlabCIUrlValue || ''}
              placeholder={`example: http://www.gitlab.com`}
              onChange={(_ev, value) => handleGitlabCIUrlValueChange(_ev, value)}
            />
            {validatedGitlabCIUrlValue !== 'success' && (
              <FormHelperText>
                <HelperText>
                  <HelperTextItem variant='error'>{validatedGitlabCIUrlValue === 'error' ? 'This field is mandatory' : ''}</HelperTextItem>
                </HelperText>
              </FormHelperText>
            )}
          </FormGroup>

          <FormGroup
            label='Project ID (gitlab ci)'
            isRequired
            fieldId={`input-test-run-config-gitlab-ci-project-id-${testRunConfig.id || `0`}`}
          >
            <TextInput
              isRequired
              id={`input-test-run-config-gitlab-ci-project-id-${testRunConfig.id || `0`}`}
              name={`input-test-run-config-gitlab-ci-project-id-${testRunConfig.id || `0`}`}
              value={gitlabCIProjectIdValue || ''}
              placeholder={`format: 111111111`}
              onChange={(_ev, value) => handleGitlabCIProjectIdValueChange(_ev, value)}
            />
            {validatedGitlabCIProjectIdValue !== 'success' && (
              <FormHelperText>
                <HelperText>
                  <HelperTextItem variant='error'>
                    {validatedGitlabCIProjectIdValue === 'error' ? 'This field is mandatory' : ''}
                  </HelperTextItem>
                </HelperText>
              </FormHelperText>
            )}
          </FormGroup>

          <FormGroup
            label='Pipeline Trigger Token (gitlab ci)'
            isRequired
            fieldId={`input-test-run-config-gitlab-ci-trigger-token-${testRunConfig.id || `0`}`}
          >
            <TextInput
              isRequired
              id={`input-test-run-config-gitlab-ci-trigger-token-${testRunConfig.id || `0`}`}
              name={`input-test-run-config-gitlab-ci-trigger-token-${testRunConfig.id || `0`}`}
              value={gitlabCITriggerTokenValue || ''}
              placeholder={`example: your-token-here`}
              onChange={(_ev, value) => handleGitlabCITriggerTokenValueChange(_ev, value)}
            />
            {validatedGitlabCITriggerTokenValue !== 'success' && (
              <FormHelperText>
                <HelperText>
                  <HelperTextItem variant='error'>
                    {validatedGitlabCITriggerTokenValue === 'error' ? 'This field is mandatory' : ''}
                  </HelperTextItem>
                </HelperText>
              </FormHelperText>
            )}
          </FormGroup>

          <FormGroup
            label='Private Token (gitlab ci)'
            isRequired
            fieldId={`input-test-run-config-gitlab-ci-api-token-${testRunConfig.id || `0`}`}
          >
            <TextInput
              isRequired
              id={`input-test-run-config-gitlab-ci-api-token-${testRunConfig.id || `0`}`}
              name={`input-test-run-config-gitlab-ci-api-token-${testRunConfig.id || `0`}`}
              value={gitlabCIPrivateTokenValue || ''}
              placeholder={`example: your-token-here`}
              onChange={(_ev, value) => handleGitlabCIPrivateTokenValueChange(_ev, value)}
            />
            {validatedGitlabCIPrivateTokenValue !== 'success' && (
              <FormHelperText>
                <HelperText>
                  <HelperTextItem variant='error'>
                    {validatedGitlabCIPrivateTokenValue === 'error' ? 'This field is mandatory' : ''}
                  </HelperTextItem>
                </HelperText>
              </FormHelperText>
            )}
          </FormGroup>

          <FormGroup label='Pipeline Stage Name (gitlab ci)' fieldId={`input-test-run-config-gitlab-ci-stage-${testRunConfig.id || `0`}`}>
            <TextInput
              id={`input-test-run-config-gitlab-ci-stage-${testRunConfig.id || `0`}`}
              name={`input-test-run-config-gitlab-ci-stage-${testRunConfig.id || `0`}`}
              value={gitlabCIStageValue || ''}
              placeholder={`example: test`}
              onChange={(_ev, value) => handleGitlabCIStageValueChange(_ev, value)}
            />
          </FormGroup>

          <FormGroup label='Pipeline Job Name (gitlab ci)' fieldId={`input-test-run-config-gitlab-ci-job-${testRunConfig.id || `0`}`}>
            <TextInput
              id={`input-test-run-config-gitlab-ci-job-${testRunConfig.id || `0`}`}
              name={`input-test-run-config-gitlab-ci-job-${testRunConfig.id || `0`}`}
              value={gitlabCIJobValue || ''}
              placeholder={`example: job-name-x`}
              onChange={(_ev, value) => handleGitlabCIJobValueChange(_ev, value)}
            />
          </FormGroup>
        </>
      ) : (
        ''
      )}

      {pluginValue == Constants.github_actions_plugin && pluginPresetValue == '' ? (
        <>
          <FormGroup
            label='Url (github actions)'
            isRequired
            fieldId={`input-test-run-config-github-actions-url-${testRunConfig.id || `0`}`}
          >
            <TextInput
              isRequired
              id={`input-test-run-config-github-actions-url-${testRunConfig.id || `0`}`}
              name={`input-test-run-config-github-actions-url-${testRunConfig.id || `0`}`}
              value={githubActionsUrlValue || ''}
              placeholder={`example: https://github.com/elisa-tech/BASIL`}
              onChange={(_ev, value) => handleGithubActionsUrlValueChange(_ev, value)}
            />
            {validatedGithubActionsUrlValue !== 'success' && (
              <FormHelperText>
                <HelperText>
                  <HelperTextItem variant='error'>
                    {validatedGithubActionsUrlValue === 'error' ? 'This field is mandatory' : ''}
                  </HelperTextItem>
                </HelperText>
              </FormHelperText>
            )}
          </FormGroup>

          <FormGroup
            label='Workflow ID (github actions)'
            fieldId={`input-test-run-config-github-actions-workflow-id-${testRunConfig.id || `0`}`}
          >
            <TextInput
              id={`input-test-run-config-github-actions-workflow-id-${testRunConfig.id || `0`}`}
              name={`input-test-run-config-github-actions-workflow-id-${testRunConfig.id || `0`}`}
              value={githubActionsWorkflowIdValue || ''}
              placeholder={`example: build.yaml`}
              onChange={(_ev, value) => handleGithubActionsWorkflowIdValueChange(_ev, value)}
            />
          </FormGroup>

          <FormGroup
            label='Private Token (github actions)'
            isRequired
            fieldId={`input-test-run-config-github-actions-api-token-${testRunConfig.id || `0`}`}
          >
            <TextInput
              isRequired
              id={`input-test-run-config-github-actions-api-token-${testRunConfig.id || `0`}`}
              name={`input-test-run-config-github-actions-api-token-${testRunConfig.id || `0`}`}
              value={githubActionsPrivateTokenValue || ''}
              placeholder={`example: your-token`}
              onChange={(_ev, value) => handleGithubActionsPrivateTokenValueChange(_ev, value)}
            />
            {validatedGithubActionsPrivateTokenValue !== 'success' && (
              <FormHelperText>
                <HelperText>
                  <HelperTextItem variant='error'>
                    {validatedGithubActionsPrivateTokenValue === 'error' ? 'This field is mandatory' : ''}
                  </HelperTextItem>
                </HelperText>
              </FormHelperText>
            )}
          </FormGroup>

          <FormGroup label='Job (github actions)' fieldId={`input-test-run-config-github-actions-job-${testRunConfig.id || `0`}`}>
            <TextInput
              id={`input-test-run-config-github-actions-job-${testRunConfig.id || `0`}`}
              name={`input-test-run-config-github-actions-job-${testRunConfig.id || `0`}`}
              value={githubActionsJobValue || ''}
              placeholder={`example: test`}
              onChange={(_ev, value) => handleGithubActionsJobValueChange(_ev, value)}
            />
          </FormGroup>
        </>
      ) : (
        ''
      )}
    </Form>
  )
}
