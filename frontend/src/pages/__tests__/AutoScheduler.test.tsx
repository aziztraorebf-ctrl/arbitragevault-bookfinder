/**
 * Tests for AutoScheduler page
 * Phase 9 Senior Review - Gap 5
 */
import { describe, it, expect } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'

import AutoScheduler from '../AutoScheduler'

describe('AutoScheduler', () => {
  it('renders page title', () => {
    render(<AutoScheduler />)
    expect(screen.getByText('AutoScheduler')).toBeInTheDocument()
  })

  it('renders subtitle', () => {
    render(<AutoScheduler />)
    expect(screen.getByText('Planification automatique des analyses')).toBeInTheDocument()
  })

  it('renders development status banner', () => {
    render(<AutoScheduler />)
    expect(screen.getByText('Feature en developpement')).toBeInTheDocument()
    expect(screen.getByText(/sera disponible dans une prochaine version/)).toBeInTheDocument()
  })

  it('renders new task button', () => {
    render(<AutoScheduler />)
    expect(screen.getByText('Nouvelle tache')).toBeInTheDocument()
  })

  it('renders mock scheduled tasks', () => {
    render(<AutoScheduler />)
    expect(screen.getByText('Scan Livres US')).toBeInTheDocument()
    expect(screen.getByText('Analyse Competition')).toBeInTheDocument()
    expect(screen.getByText('Refresh Prix')).toBeInTheDocument()
  })

  it('renders planned features cards', () => {
    render(<AutoScheduler />)
    expect(screen.getByText('Analyse automatique')).toBeInTheDocument()
    expect(screen.getByText('Alertes prix')).toBeInTheDocument()
    expect(screen.getByText('Rapports automatiques')).toBeInTheDocument()
  })

  it('opens create modal on button click', () => {
    render(<AutoScheduler />)

    const newTaskButton = screen.getByText('Nouvelle tache')
    fireEvent.click(newTaskButton)

    expect(screen.getByText('Nouvelle tache planifiee')).toBeInTheDocument()
    expect(screen.getByText('Nom de la tache')).toBeInTheDocument()
    expect(screen.getByText('Frequence')).toBeInTheDocument()
  })

  it('closes modal on close button click', () => {
    render(<AutoScheduler />)

    // Open modal
    fireEvent.click(screen.getByText('Nouvelle tache'))
    expect(screen.getByText('Nouvelle tache planifiee')).toBeInTheDocument()

    // Close modal
    fireEvent.click(screen.getByText('Fermer'))
    expect(screen.queryByText('Nouvelle tache planifiee')).not.toBeInTheDocument()
  })

  it('has disabled create button in modal', () => {
    render(<AutoScheduler />)

    fireEvent.click(screen.getByText('Nouvelle tache'))

    const createButton = screen.getByText('Creer (bientot)')
    expect(createButton).toBeDisabled()
  })

  it('shows task status badges', () => {
    render(<AutoScheduler />)

    expect(screen.getAllByText('Actif').length).toBe(2)
    expect(screen.getByText('En pause')).toBeInTheDocument()
  })
})
