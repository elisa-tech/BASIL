import * as React from 'react'
import {
  Button,
  MenuToggle,
  MenuToggleElement,
  Select,
  SelectList,
  SelectOption,
  TextInputGroup,
  TextInputGroupMain,
  TextInputGroupUtilities
} from '@patternfly/react-core'
import TimesIcon from '@patternfly/react-icons/dist/esm/icons/times-icon'
import * as Constants from '../Constants/constants'
import { useAuth } from '../User/AuthProvider'
import { UserFilePath } from './UserFilePath'

const SEARCH_DEBOUNCE_MS = 250

export interface UserFileSelectProps {
  id: string
  // filepath of the selected file, empty when none is selected
  value: string
  userFiles
  onChange: (event, value: string) => void
  placeholder?: string
  ariaLabel?: string
}

const getLabel = (userFile) => userFile['relative_path'] || userFile['filename']

// A select of user files that can be searched: typing in it narrows the list
// down to the files whose path holds every typed word, in any order. It runs
// the same backend search as the User Files page, so both match, rank and
// highlight the same way.
const UserFileSelect: React.FunctionComponent<UserFileSelectProps> = ({
  id,
  value,
  userFiles,
  onChange,
  placeholder = 'Select a file from the list',
  ariaLabel
}: UserFileSelectProps) => {
  const auth = useAuth()
  const [isOpen, setIsOpen] = React.useState(false)
  // null while the input shows the selected file rather than what is typed
  const [searchValue, setSearchValue] = React.useState<string | null>(null)
  // the results of the last search that came back, with the term searched
  const [searchResults, setSearchResults] = React.useState<{ term: string; files: Record<string, unknown>[] } | null>(null)
  const [focusedIndex, setFocusedIndex] = React.useState<number | null>(null)
  const textInputRef = React.useRef<HTMLInputElement>()

  const selectedFile = userFiles.find((userFile) => userFile['filepath'] === value)
  const inputValue = searchValue ?? (selectedFile ? getLabel(selectedFile) : '')
  const searchTerm = (searchValue || '').trim()
  const isSearching = searchTerm !== ''
  const isWaitingForResults = isSearching && searchResults?.term !== searchTerm

  // The search covers every user file, so its results are narrowed down to the
  // files this select offers: the form decides which ones are candidates (only
  // .yaml ones for a LAVA job, for instance), and folders are never among them.
  React.useEffect(() => {
    if (!isSearching) {
      setSearchResults(null)
      return
    }

    let cancelled = false
    const timeout = setTimeout(() => {
      const candidates = new Set(userFiles.map((userFile) => userFile['filepath']))
      Constants.searchUserFiles(
        auth,
        (files) => {
          if (!cancelled) {
            setSearchResults({ term: searchTerm, files: files.filter((file) => candidates.has(file['filepath'])) })
            setFocusedIndex(null)
          }
        },
        searchTerm
      )
    }, SEARCH_DEBOUNCE_MS)

    return () => {
      cancelled = true
      clearTimeout(timeout)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchTerm, userFiles])

  // While the results of what was just typed are on their way, the previous
  // ones stay listed, so that the list does not flicker at every key stroke.
  const options = isSearching
    ? (searchResults?.files || []).map((userFile) => ({ userFile, matchIndices: userFile['match_indices'] as number[] }))
    : userFiles.filter((userFile) => userFile['type'] !== 'directory').map((userFile) => ({ userFile, matchIndices: [] }))

  const getEmptyMessage = () => {
    if (isWaitingForResults) {
      return 'Searching...'
    }
    return isSearching ? `No files match "${searchTerm}"` : 'No files to pick from'
  }

  React.useEffect(() => {
    if (focusedIndex !== null) {
      document.getElementById(`${id}-option-${focusedIndex}`)?.scrollIntoView({ block: 'nearest' })
    }
  }, [id, focusedIndex])

  const close = () => {
    setIsOpen(false)
    setSearchValue(null)
    setFocusedIndex(null)
  }

  const select = (event, filepath: string) => {
    onChange(event, filepath)
    close()
    textInputRef.current?.focus()
  }

  const clear = (event) => {
    onChange(event, '')
    setSearchValue(null)
    setFocusedIndex(null)
    textInputRef.current?.focus()
  }

  const onInputChange = (_event, text: string) => {
    setSearchValue(text)
    setFocusedIndex(null)
    setIsOpen(true)
  }

  const onInputKeyDown = (event: React.KeyboardEvent) => {
    switch (event.key) {
      case 'ArrowDown':
      case 'ArrowUp': {
        event.preventDefault()
        if (!isOpen) {
          setIsOpen(true)
          return
        }
        if (options.length === 0) {
          return
        }
        const step = event.key === 'ArrowDown' ? 1 : -1
        const from = focusedIndex ?? (step === 1 ? -1 : 0)
        setFocusedIndex((from + step + options.length) % options.length)
        break
      }
      case 'Enter': {
        // With a single match left, Enter picks it without moving to it first.
        // Nothing is picked from results that do not match what is typed yet.
        const index = focusedIndex ?? (options.length === 1 ? 0 : null)
        if (isOpen && index !== null && !isWaitingForResults) {
          event.preventDefault()
          select(event, options[index].userFile['filepath'])
        }
        break
      }
      case 'Escape':
        if (isOpen) {
          // These selects live in modals that close on Escape too: only the
          // list must close, not the form around it.
          event.stopPropagation()
          close()
        }
        break
    }
  }

  const toggle = (toggleRef: React.Ref<MenuToggleElement>) => (
    <MenuToggle ref={toggleRef} variant='typeahead' onClick={() => setIsOpen(!isOpen)} isExpanded={isOpen} isFullWidth>
      <TextInputGroup isPlain>
        <TextInputGroupMain
          id={id}
          // the selected filepath, as the value of a native select would expose it
          data-value={value}
          value={inputValue}
          onClick={() => setIsOpen(!isOpen)}
          onChange={onInputChange}
          onKeyDown={onInputKeyDown}
          innerRef={textInputRef}
          placeholder={placeholder}
          aria-label={ariaLabel}
          role='combobox'
          isExpanded={isOpen}
          aria-controls={`${id}-listbox`}
          aria-activedescendant={focusedIndex !== null ? `${id}-option-${focusedIndex}` : undefined}
        />
        {inputValue !== '' && (
          <TextInputGroupUtilities>
            <Button variant='plain' onClick={clear} aria-label='Clear selected file'>
              <TimesIcon />
            </Button>
          </TextInputGroupUtilities>
        )}
      </TextInputGroup>
    </MenuToggle>
  )

  return (
    <Select
      id={`${id}-menu`}
      isOpen={isOpen}
      selected={value}
      onSelect={(event, filepath) => select(event, filepath as string)}
      onOpenChange={(open) => !open && close()}
      toggle={toggle}
      isScrollable
    >
      <SelectList id={`${id}-listbox`}>
        {options.length === 0 ? (
          <SelectOption isDisabled>{getEmptyMessage()}</SelectOption>
        ) : (
          options.map((option, index) => (
            <SelectOption
              key={option.userFile['filepath']}
              id={`${id}-option-${index}`}
              value={option.userFile['filepath']}
              isFocused={focusedIndex === index}
            >
              <UserFilePath relativePath={getLabel(option.userFile)} matchIndices={option.matchIndices} />
            </SelectOption>
          ))
        )}
      </SelectList>
    </Select>
  )
}

export { UserFileSelect }
