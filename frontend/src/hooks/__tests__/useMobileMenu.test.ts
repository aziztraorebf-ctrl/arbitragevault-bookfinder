import { renderHook, act } from '@testing-library/react'
import { useMobileMenu } from '../useMobileMenu'

describe('useMobileMenu', () => {
  it('should start closed', () => {
    const { result } = renderHook(() => useMobileMenu())
    expect(result.current.isOpen).toBe(false)
  })

  it('should toggle open/close', () => {
    const { result } = renderHook(() => useMobileMenu())

    act(() => {
      result.current.toggle()
    })
    expect(result.current.isOpen).toBe(true)

    act(() => {
      result.current.toggle()
    })
    expect(result.current.isOpen).toBe(false)
  })

  it('should close explicitly', () => {
    const { result } = renderHook(() => useMobileMenu())

    act(() => {
      result.current.toggle()
    })
    expect(result.current.isOpen).toBe(true)

    act(() => {
      result.current.close()
    })
    expect(result.current.isOpen).toBe(false)
  })
})
