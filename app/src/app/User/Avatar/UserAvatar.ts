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

export const AVATAR_UPLOAD_ACCEPT = {
  'image/png': ['.png'],
  'image/jpeg': ['.jpg', '.jpeg'],
  'image/gif': ['.gif'],
  'image/webp': ['.webp']
}
export const AVATAR_UPLOAD_MAX_SIZE = 512 * 1024 // bytes, as USER_AVATAR_MAX_SIZE in api/api_utils.py

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
