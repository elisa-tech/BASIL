import * as React from 'react'

interface PathSegment {
  text: string
  isMatch: boolean
  isName: boolean
}

const getPathSegments = (relativePath: string, matchIndices: number[]): PathSegment[] => {
  const matched = new Set(matchIndices)
  const nameStart = relativePath.lastIndexOf('/') + 1
  const segments: PathSegment[] = []

  for (let i = 0; i < relativePath.length; i++) {
    const isMatch = matched.has(i)
    const isName = i >= nameStart
    const previous = segments[segments.length - 1]
    if (previous && previous.isMatch === isMatch && previous.isName === isName) {
      previous.text += relativePath[i]
    } else {
      segments.push({ text: relativePath[i], isMatch, isName })
    }
  }

  return segments
}

export interface UserFilePathProps {
  relativePath: string
  matchIndices?: number[]
}

// A relative path with its folders dimmed, the entry name bold and the
// characters matched by a search highlighted, like the file finder of a code
// forge.
export const UserFilePath: React.FunctionComponent<UserFilePathProps> = ({ relativePath, matchIndices = [] }: UserFilePathProps) => (
  <>
    {getPathSegments(relativePath, matchIndices).map((segment, index) => (
      <span
        key={index}
        style={{
          color: segment.isName ? 'inherit' : '#6a6e73',
          fontWeight: segment.isName ? 600 : 400,
          backgroundColor: segment.isMatch ? '#f0ab00' : 'transparent'
        }}
      >
        {segment.text}
      </span>
    ))}
  </>
)
