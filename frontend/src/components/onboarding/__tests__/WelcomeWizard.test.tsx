import { render, screen, fireEvent } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { WelcomeWizard } from '../WelcomeWizard'

const mockOnComplete = vi.fn()

const renderWizard = () => {
  return render(
    <BrowserRouter>
      <WelcomeWizard onComplete={mockOnComplete} />
    </BrowserRouter>
  )
}

describe('WelcomeWizard', () => {
  beforeEach(() => {
    mockOnComplete.mockClear()
  })

  it('renders first step by default', () => {
    renderWizard()
    expect(screen.getByText(/Bienvenue/i)).toBeInTheDocument()
    expect(screen.getByText(/1/)).toBeInTheDocument()
    expect(screen.getByText(/3/)).toBeInTheDocument()
  })

  it('navigates to next step on button click', () => {
    renderWizard()
    const nextButton = screen.getByRole('button', { name: /Suivant/i })
    fireEvent.click(nextButton)
    expect(screen.getByText(/2/)).toBeInTheDocument()
  })

  it('navigates back on previous button click', () => {
    renderWizard()
    fireEvent.click(screen.getByRole('button', { name: /Suivant/i }))
    fireEvent.click(screen.getByRole('button', { name: /Retour/i }))
    expect(screen.getByText(/Bienvenue/i)).toBeInTheDocument()
  })

  it('calls onComplete on last step', () => {
    renderWizard()
    fireEvent.click(screen.getByRole('button', { name: /Suivant/i }))
    fireEvent.click(screen.getByRole('button', { name: /Suivant/i }))
    fireEvent.click(screen.getByRole('button', { name: /Commencer/i }))
    expect(mockOnComplete).toHaveBeenCalledTimes(1)
  })

  it('shows skip button', () => {
    renderWizard()
    // Two skip buttons exist: X icon (header) and text "Passer" (footer)
    const skipButtons = screen.getAllByRole('button', { name: /Passer/i })
    expect(skipButtons.length).toBeGreaterThanOrEqual(1)
    // Click the footer skip button (the one with text content)
    const footerSkipButton = skipButtons.find(btn => btn.textContent === 'Passer')
    expect(footerSkipButton).toBeInTheDocument()
    fireEvent.click(footerSkipButton!)
    expect(mockOnComplete).toHaveBeenCalledTimes(1)
  })
})
