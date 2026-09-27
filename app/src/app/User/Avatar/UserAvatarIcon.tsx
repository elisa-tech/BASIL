import React from 'react'
import { Avatar, AvatarProps } from '@patternfly/react-core'
import { useAuth } from '@app/User/AuthProvider'
import { DEFAULT_AVATAR, UserAvatarData, fetchUserAvatar, getAvatarSrc } from './UserAvatar'

export interface UserAvatarIconProps {
  userId: number | string | null | undefined
  size?: AvatarProps['size']
}

// Avatar of any user, to be shown next to the user name
export const UserAvatarIcon: React.FunctionComponent<UserAvatarIconProps> = ({ userId, size = 'sm' }: UserAvatarIconProps) => {
  const auth = useAuth()
  const [avatar, setAvatar] = React.useState<UserAvatarData>(DEFAULT_AVATAR)
  const { userId: currentUserId, token } = auth
  const isCurrentUser = userId != null && String(userId) === String(currentUserId)

  React.useEffect(() => {
    if (isCurrentUser || userId == null || !currentUserId || !token) {
      return
    }
    let active = true
    fetchUserAvatar(currentUserId, token, userId).then((data) => {
      if (active) {
        setAvatar(data)
      }
    })
    return () => {
      active = false
    }
  }, [userId, isCurrentUser, currentUserId, token])

  // The avatar of the current user is kept up to date by the AuthProvider
  const src = getAvatarSrc(isCurrentUser ? auth.userAvatar : avatar)
  return <Avatar className='user-avatar-icon' src={src} alt='' size={size} />
}
