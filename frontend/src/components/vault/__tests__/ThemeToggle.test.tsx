import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { ThemeToggle } from '../ThemeToggle'
import { ThemeProvider } from '../../../contexts/ThemeContext'

// Mock localStorage
const localStorageMock = (() => {
  let store: Record<string, string> = {}
  return {
    getItem: vi.fn((key: string) => store[key] || null),
    setItem: vi.fn((key: string, value: string) => {
      store[key] = value
    }),
    clear: vi.fn(() => {
      store = {}
    })
  }
})()

Object.defineProperty(window, 'localStorage', { value: localStorageMock })

describe('ThemeToggle', () => {
  beforeEach(() => {
    localStorageMock.clear()
    document.documentElement.removeAttribute('data-theme')
  })

  const renderWithProvider = () => {
    return render(
      <ThemeProvider>
        <ThemeToggle />
      </ThemeProvider>
    )
  }

  it('renders toggle button', () => {
    renderWithProvider()
    const button = screen.getByRole('button')
    expect(button).toBeInTheDocument()
  })

  it('has accessible label for light mode', () => {
    renderWithProvider()
    const button = screen.getByLabelText('Switch to dark mode')
    expect(button).toBeInTheDocument()
  })

  it('toggles theme on click', () => {
    renderWithProvider()
    const button = screen.getByRole('button')

    // Initial state is light
    expect(document.documentElement.getAttribute('data-theme')).toBe('light')

    // Click to switch to dark
    fireEvent.click(button)
    expect(document.documentElement.getAttribute('data-theme')).toBe('dark')

    // Click to switch back to light
    fireEvent.click(button)
    expect(document.documentElement.getAttribute('data-theme')).toBe('light')
  })

  it('persists theme to localStorage', () => {
    renderWithProvider()
    const button = screen.getByRole('button')

    fireEvent.click(button)
    expect(localStorageMock.setItem).toHaveBeenCalledWith(
      'vault-elegance-theme',
      'dark'
    )
  })

  it('applies custom className', () => {
    render(
      <ThemeProvider>
        <ThemeToggle className="custom-class" />
      </ThemeProvider>
    )
    const button = screen.getByRole('button')
    expect(button).toHaveClass('custom-class')
  })

  it('renders sun icon in light mode', () => {
    const { container } = renderWithProvider()
    // In light mode, sun should be visible (opacity-100)
    const svgs = container.querySelectorAll('svg')
    expect(svgs.length).toBe(2) // Sun and Moon both rendered
  })

  it('updates aria-label when theme changes', () => {
    renderWithProvider()
    const button = screen.getByRole('button')

    expect(button).toHaveAttribute('aria-label', 'Switch to dark mode')

    fireEvent.click(button)
    expect(button).toHaveAttribute('aria-label', 'Switch to light mode')
  })
})
