import { useState } from 'react'

/**
 * hook to set and get data from localStorage
 * @param key name of item to fetch
 * @param initialValue default value of item
 * @returns [storedValue, setValue]
 */
export function useLocalStorage<T>(key: string, initialValue: T) {
  const [storedValue, setStoredValue] = useState<T>(() => {
    try {
      // get from local storage by key
      const item = window.localStorage.getItem(key)
      return item ? JSON.parse(item) : initialValue
    } catch (error) {
      // defaults to initialValue
      return initialValue
    }
  })

  const setValue = (value: T | ((val: T) => T)) => {
    const valueToStore = value instanceof Function ? value(storedValue) : value
    setStoredValue(valueToStore)
    window.localStorage.setItem(key, JSON.stringify(valueToStore))
  }
  return [storedValue, setValue] as const
}
