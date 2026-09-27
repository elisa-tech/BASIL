import * as Constants from '@app/Constants/constants'
import imgAvatarDefault from '@app/bgimages/avatarImg.svg'
import imgAvatarBlue from '@app/bgimages/avatars/avatar_blue.svg'
import imgAvatarCyan from '@app/bgimages/avatars/avatar_cyan.svg'
import imgAvatarGreen from '@app/bgimages/avatars/avatar_green.svg'
import imgAvatarOrange from '@app/bgimages/avatars/avatar_orange.svg'
import imgAvatarPurple from '@app/bgimages/avatars/avatar_purple.svg'
import imgAvatarRed from '@app/bgimages/avatars/avatar_red.svg'

// Avatar as returned by the /user/avatar endpoint
export type UserAvatarData = { type: 'default' } | { type: 'builtin'; name: string } | { type: 'custom'; data: string }

export const DEFAULT_AVATAR: UserAvatarData = { type: 'default' }

// Names must match USER_AVATAR_BUILTIN_NAMES in api/api_utils.py
export const BUILTIN_AVATARS: { name: string; src: string }[] = [
  { name: 'blue', src: imgAvatarBlue },
  { name: 'cyan', src: imgAvatarCyan },
  { name: 'green', src: imgAvatarGreen },
  { name: 'orange', src: imgAvatarOrange },
  { name: 'purple', src: imgAvatarPurple },
  { name: 'red', src: imgAvatarRed }
]

// image/jpg is not a registered mime type, but some systems report it for .jpg files.
// The API detects the format from the file content, so the declared type is only a first filter.
export const AVATAR_UPLOAD_ACCEPT = {
  'image/png': ['.png'],
  'image/jpeg': ['.jpg', '.jpeg'],
  'image/jpg': ['.jpg', '.jpeg'],
  'image/gif': ['.gif'],
  'image/webp': ['.webp']
}
export const AVATAR_UPLOAD_MAX_SIZE = 512 * 1024 // bytes, as USER_AVATAR_MAX_SIZE in api/api_utils.py

const AVATAR_UPLOAD_EXTENSIONS = Object.values(AVATAR_UPLOAD_ACCEPT).flat()

// Some systems report an empty type, in that case rely on the file extension
export const isAcceptedAvatarFile = (file: File): boolean => {
  if (file.size > AVATAR_UPLOAD_MAX_SIZE) {
    return false
  }
  if (file.type) {
    return file.type in AVATAR_UPLOAD_ACCEPT
  }
  const dotIndex = file.name.lastIndexOf('.')
  return dotIndex >= 0 && AVATAR_UPLOAD_EXTENSIONS.includes(file.name.slice(dotIndex).toLowerCase())
}

export const getAvatarSrc = (avatar?: UserAvatarData | null): string => {
  if (avatar?.type === 'builtin') {
    const builtin = BUILTIN_AVATARS.find((a) => a.name === avatar.name)
    if (builtin) {
      return builtin.src
    }
  }
  if (avatar?.type === 'custom' && avatar.data) {
    return avatar.data
  }
  return imgAvatarDefault
}

// Avatars of other users, shared by all the components showing them,
// so that each avatar is requested only once, until the page is reloaded
const avatarCache = new Map<string, Promise<UserAvatarData>>()

// The user whose avatar is shown: by id when it is known, otherwise by
// username, which is all a work item carries about who created it
export type UserAvatarTarget = { userId: number | string } | { username: string }

export const fetchUserAvatar = (currentUserId: number | string, token: string, target: UserAvatarTarget): Promise<UserAvatarData> => {
  const key = 'userId' in target ? 'id:' + target.userId : 'username:' + target.username
  const cached = avatarCache.get(key)
  if (cached) {
    return cached
  }
  let url = Constants.API_BASE_URL + Constants.API_USER_AVATAR_ENDPOINT
  url += '?user-id=' + currentUserId
  url += '&token=' + token
  if ('userId' in target) {
    url += '&target-user-id=' + encodeURIComponent(target.userId)
  } else {
    url += '&target-username=' + encodeURIComponent(target.username)
  }
  const request = fetch(url, { method: 'GET', headers: Constants.JSON_HEADER })
    .then((res) => (res.ok ? res.json() : DEFAULT_AVATAR))
    .catch(() => DEFAULT_AVATAR)
  avatarCache.set(key, request)
  return request
}
