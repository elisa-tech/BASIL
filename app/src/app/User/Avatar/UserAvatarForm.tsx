import React from 'react'
import {
  Avatar,
  Button,
  DropEvent,
  FileUpload,
  Flex,
  FlexItem,
  FormGroup,
  FormHelperText,
  HelperText,
  HelperTextItem
} from '@patternfly/react-core'
import * as Constants from '@app/Constants/constants'
import { useAuth } from '@app/User/AuthProvider'
import { AVATAR_UPLOAD_ACCEPT, AVATAR_UPLOAD_MAX_SIZE, BUILTIN_AVATARS, DEFAULT_AVATAR, UserAvatarData, getAvatarSrc } from './UserAvatar'

export interface UserAvatarFormProps {
  setMessageValue: (message: string) => void
}

const selectedStyle = { outline: '3px solid var(--pf-v5-global--primary-color--100)', borderRadius: '50%' }

export const UserAvatarForm: React.FunctionComponent<UserAvatarFormProps> = ({ setMessageValue }: UserAvatarFormProps) => {
  const auth = useAuth()
  const [selectedAvatar, setSelectedAvatar] = React.useState<UserAvatarData>(auth.userAvatar || DEFAULT_AVATAR)
  const [uploadFilename, setUploadFilename] = React.useState('')
  const [uploadError, setUploadError] = React.useState('')
  // Files selected from the file input are not filtered by the dropzone, check them here
  const isInvalidFile = React.useRef(false)

  React.useEffect(() => {
    setSelectedAvatar(auth.userAvatar || DEFAULT_AVATAR)
  }, [auth.userAvatar])

  const choices: { id: string; label: string; avatar: UserAvatarData }[] = [
    { id: 'default', label: 'Default', avatar: DEFAULT_AVATAR },
    ...BUILTIN_AVATARS.map((a) => ({ id: a.name, label: a.name, avatar: { type: 'builtin', name: a.name } as UserAvatarData }))
  ]

  const isSelected = (avatar: UserAvatarData) => {
    if (avatar.type === 'builtin') {
      return selectedAvatar.type === 'builtin' && selectedAvatar.name === avatar.name
    }
    return selectedAvatar.type === avatar.type
  }

  const selectAvatar = (avatar: UserAvatarData) => {
    setUploadFilename('')
    setUploadError('')
    setSelectedAvatar(avatar)
  }

  const handleFileInputChange = (_event: DropEvent, file: File) => {
    isInvalidFile.current = !(file.type in AVATAR_UPLOAD_ACCEPT) || file.size > AVATAR_UPLOAD_MAX_SIZE
    if (isInvalidFile.current) {
      handleDropRejected()
      return
    }
    setUploadError('')
    setUploadFilename(file.name)
  }

  const handleDataChange = (_event: DropEvent, data: string) => {
    if (isInvalidFile.current) {
      return
    }
    setSelectedAvatar({ type: 'custom', data: data })
  }

  const handleClear = () => {
    setUploadFilename('')
    setUploadError('')
    setSelectedAvatar(auth.userAvatar || DEFAULT_AVATAR)
  }

  const handleDropRejected = () => {
    setUploadFilename('')
    setUploadError(`Supported formats are PNG, JPEG, GIF and WebP, with a maximum size of ${AVATAR_UPLOAD_MAX_SIZE / 1024} KB`)
  }

  const saveAvatar = () => {
    setMessageValue('')
    if (!auth.isLogged()) {
      return
    }

    let method = 'PUT'
    const data = {
      'user-id': auth.userId,
      token: auth.token
    }
    if (selectedAvatar.type === 'builtin') {
      data['type'] = 'builtin'
      data['name'] = selectedAvatar.name
    } else if (selectedAvatar.type === 'custom') {
      data['type'] = 'custom'
      data['data'] = selectedAvatar.data
    } else {
      method = 'DELETE'
    }

    let status: number = 0
    let status_text: string = ''

    fetch(Constants.API_BASE_URL + Constants.API_USER_AVATAR_ENDPOINT, {
      method: method,
      headers: Constants.JSON_HEADER,
      body: JSON.stringify(data)
    })
      .then((response) => {
        status = response.status
        status_text = response.statusText
        if (!Constants.isHttpSuccessStatus(status)) {
          return response.text()
        } else {
          return response.json()
        }
      })
      .then((data) => {
        if (!Constants.isHttpSuccessStatus(status)) {
          setMessageValue(Constants.getResponseErrorMessage(status, status_text, data))
        } else {
          setUploadFilename('')
          auth.setUserAvatar(data)
          setMessageValue('Avatar updated')
        }
      })
      .catch((err) => {
        setMessageValue(err.toString())
      })
  }

  return (
    <React.Fragment>
      <FormGroup label='Preview' fieldId='user-avatar-preview'>
        <Avatar id='user-avatar-preview' src={getAvatarSrc(selectedAvatar)} alt='Selected avatar' size='xl' />
      </FormGroup>
      <br></br>
      <FormGroup label='Choose an avatar' fieldId='user-avatar-choices'>
        <Flex id='user-avatar-choices'>
          {choices.map((choice) => (
            <FlexItem key={choice.id}>
              <Button
                id={`btn-user-avatar-${choice.id}`}
                variant='plain'
                aria-label={`Select ${choice.label} avatar`}
                aria-pressed={isSelected(choice.avatar)}
                onClick={() => selectAvatar(choice.avatar)}
              >
                <Avatar src={getAvatarSrc(choice.avatar)} alt='' size='lg' style={isSelected(choice.avatar) ? selectedStyle : {}} />
              </Button>
            </FlexItem>
          ))}
        </Flex>
      </FormGroup>
      <br></br>
      <FormGroup label='Or upload an image' fieldId='user-avatar-upload'>
        <FileUpload
          id='user-avatar-upload'
          type='dataURL'
          value=''
          filename={uploadFilename}
          filenamePlaceholder='Drag and drop an image or upload one'
          browseButtonText='Upload'
          hideDefaultPreview
          onFileInputChange={handleFileInputChange}
          onDataChange={handleDataChange}
          onClearClick={handleClear}
          dropzoneProps={{
            accept: AVATAR_UPLOAD_ACCEPT,
            maxSize: AVATAR_UPLOAD_MAX_SIZE,
            onDropRejected: handleDropRejected
          }}
        />
        <FormHelperText>
          <HelperText>
            <HelperTextItem id='user-avatar-upload-helper' variant={uploadError ? 'error' : 'default'}>
              {uploadError ? uploadError : `PNG, JPEG, GIF or WebP, up to ${AVATAR_UPLOAD_MAX_SIZE / 1024} KB`}
            </HelperTextItem>
          </HelperText>
        </FormHelperText>
      </FormGroup>
      <br></br>
      <br></br>
      <Button id='btn-user-avatar-save' onClick={saveAvatar}>
        Save
      </Button>
    </React.Fragment>
  )
}
