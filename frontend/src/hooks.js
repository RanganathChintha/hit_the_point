import { useEffect, useRef, useState } from 'react'

// Generic data-fetching hook. `fn` should return a promise.
// `deps` controls re-fetching.
export function useAsync(fn, deps = []) {
  const [state, setState] = useState({ loading: true, data: null, error: null })
  const fnRef = useRef(fn)
  fnRef.current = fn

  useEffect(() => {
    let alive = true
    setState({ loading: true, data: null, error: null })
    fnRef.current()
      .then((data) => alive && setState({ loading: false, data, error: null }))
      .catch((error) => alive && setState({ loading: false, data: null, error }))
    return () => { alive = false }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps)

  return state
}

// Debounce a fast-changing value (e.g. a search box).
export function useDebounced(value, delay = 300) {
  const [debounced, setDebounced] = useState(value)
  useEffect(() => {
    const t = setTimeout(() => setDebounced(value), delay)
    return () => clearTimeout(t)
  }, [value, delay])
  return debounced
}
