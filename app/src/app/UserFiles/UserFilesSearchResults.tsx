import * as React from 'react'
import { Table, Tbody, Td, Th, Thead, Tr } from '@patternfly/react-table'
import { UserFilesMenuKebab } from './Menu/UserFilesMenuKebab'
import FileIcon from '@patternfly/react-icons/dist/esm/icons/file-icon'
import FolderIcon from '@patternfly/react-icons/dist/esm/icons/folder-icon'
import { Button } from '@patternfly/react-core'

export interface UserFilesSearchResultsTableProps {
  modalAction
  modalFileName
  modalRelativePath
  userFiles
  setModalShowState
  searchValue: string
  isSearching: boolean
  navigateTo: (path: string) => void
}

interface PathSegment {
  text: string
  isMatch: boolean
  isName: boolean
}

const getFolderPath = (relativePath: string) => {
  const separatorIndex = relativePath.lastIndexOf('/')
  return separatorIndex === -1 ? '' : relativePath.substring(0, separatorIndex)
}

// The API reports which characters of the relative path the search matched, so
// a fuzzy match can be highlighted exactly where it hit. The folders are
// dimmed and the entry name is bold, like the file finder of a code forge.
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

const renderPath = (relativePath: string, matchIndices: number[]) =>
  getPathSegments(relativePath, matchIndices || []).map((segment, index) => (
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
  ))

const UserFilesSearchResultsTable: React.FunctionComponent<UserFilesSearchResultsTableProps> = ({
  userFiles,
  modalAction,
  modalFileName,
  modalRelativePath,
  setModalShowState,
  searchValue,
  isSearching,
  navigateTo
}: UserFilesSearchResultsTableProps) => {
  const getTable = () => {
    if (isSearching) {
      return (
        <Tbody>
          <Tr>
            <Td colSpan={4} style={{ textAlign: 'center', color: '#6a6e73', padding: '24px' }}>
              Searching...
            </Td>
          </Tr>
        </Tbody>
      )
    }

    if (userFiles.length === 0) {
      return (
        <Tbody>
          <Tr>
            <Td colSpan={4} style={{ textAlign: 'center', color: '#6a6e73', padding: '24px' }}>
              Nothing matches &quot;{searchValue}&quot; in any of your folders
            </Td>
          </Tr>
        </Tbody>
      )
    }

    return userFiles.map((userFile) => {
      const isDirectory = userFile.type === 'directory'
      // Opening a folder result browses it, opening a file result browses the
      // folder holding it, which is the only place its neighbours are visible.
      const destination = isDirectory ? userFile.relative_path : getFolderPath(userFile.relative_path)
      return (
        <Tbody key={userFile.relative_path}>
          <Tr>
            <Td dataLabel='type' style={{ width: '32px' }}>
              {isDirectory ? <FolderIcon style={{ color: '#f0ab00' }} /> : <FileIcon style={{ color: '#6a6e73' }} />}
            </Td>
            <Td dataLabel='filename'>
              <Button
                variant='link'
                isInline
                id={'btn-user-file-search-result-' + userFile.index}
                onClick={() => navigateTo(destination)}
                title={isDirectory ? 'Open this folder' : 'Open the folder of this file'}
              >
                {renderPath(userFile.relative_path, userFile.match_indices)}
              </Button>
            </Td>
            <Td dataLabel='updated_at'>{userFile.updated_at}</Td>
            <Td dataLabel='actions'>
              <UserFilesMenuKebab
                modalAction={modalAction}
                modalFileName={modalFileName}
                modalRelativePath={modalRelativePath}
                userFile={userFile}
                setModalShowState={setModalShowState}
              />
            </Td>
          </Tr>
        </Tbody>
      )
    })
  }

  return (
    <React.Fragment>
      <Table id='table-user-files-search-results' aria-label='User files search results table' variant='compact'>
        <Thead>
          <Tr>
            <Th style={{ width: '32px' }}></Th>
            <Th>Path</Th>
            <Th>Updated at</Th>
            <Th>Actions</Th>
          </Tr>
        </Thead>
        {getTable()}
      </Table>
    </React.Fragment>
  )
}

export { UserFilesSearchResultsTable }
