import _ from 'lodash'

// Utility functions

export const createUniqWorkItems = (obj, fields) => {
  // get a dictionary from fixture and edit each 'field' form fields of each
  // subdictionary appending date string

  let result = _.cloneDeep(obj)
  const dateString = Date.now().toString()

  for (const main_key in result) {
    for (const sub_key in result[main_key]) {
      if (fields.includes(sub_key)) {
        result[main_key][sub_key] += dateString
        break
      }
    }
  }

  return result
}
