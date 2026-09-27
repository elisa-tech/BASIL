import React from 'react'
import { Avatar, AvatarProps } from '@patternfly/react-core'
import { useAuth } from '@app/User/AuthProvider'
import { DEFAULT_AVATAR, UserAvatarData, fetchUserAvatar, getAvatarSrc } from './UserAvatar'

export interface UserAvatarIconProps {
  // the user to show, by id or, when the id is not known, by username
  userId?: number | string | null
  username?: string | null
  size?: AvatarProps['size']
  style?: React.CSSProperties
}

// Avatar of any user, to be shown next to the user name
export const UserAvatarIcon: React.FunctionComponent<UserAvatarIconProps> = ({
  userId,
  username,
  size = 'sm',
  style
}: UserAvatarIconProps) => {
  const auth = useAuth()
  const [avatar, setAvatar] = React.useState<UserAvatarData>(DEFAULT_AVATAR)
  const { userId: currentUserId, userName: currentUsername, token } = auth
  const hasUserId = userId != null && userId !== ''
  const hasUsername = !hasUserId && !!username
  const isCurrentUser = hasUserId ? String(userId) === String(currentUserId) : hasUsername && username === currentUsername

  React.useEffect(() => {
    if (isCurrentUser || (!hasUserId && !hasUsername) || !currentUserId || !token) {
      return
    }
    let active = true
    const target = hasUserId ? { userId: userId as number | string } : { username: username as string }
    fetchUserAvatar(currentUserId, token, target).then((data) => {
      if (active) {
        setAvatar(data)
      }
    })
    return () => {
      active = false
    }
  }, [userId, username, hasUserId, hasUsername, isCurrentUser, currentUserId, token])

  // The avatar of the current user is kept up to date by the AuthProvider
  const src = getAvatarSrc(isCurrentUser ? auth.userAvatar : avatar)
  return <Avatar className='user-avatar-icon' src={src} alt='' size={size} style={style} />
}
