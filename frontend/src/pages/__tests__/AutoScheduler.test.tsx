/**
 * Tests for AutoScheduler page
 * Phase 9 Senior Review - Gap 5
 */
import { describe, it, expect } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'

import AutoScheduler from '../AutoScheduler'

// Helper to render with router for links
const renderWithRouter = (component: React.ReactElement) => {
  return render(
    <MemoryRouter>
      {component}
    </MemoryRouter>
  )
}

describe('AutoScheduler', () => {
  it('renders page title', () => {
    renderWithRouter(<AutoScheduler />)
    expect(screen.getByText('AutoScheduler')).toBeInTheDocument()
  })

  it('renders subtitle', () => {
    renderWithRouter(<AutoScheduler />)
    expect(screen.getByText('Planification automatique des analyses')).toBeInTheDocument()
  })

  it('renders development status banner', () => {
    renderWithRouter(<AutoScheduler />)
    expect(screen.getByText('Fonctionnalite a venir - Phase 12')).toBeInTheDocument()
    expect(screen.getByText(/sera disponible apres l'integration N8N/)).toBeInTheDocument()
  })

  it('renders new task button', () => {
    renderWithRouter(<AutoScheduler />)
    expect(screen.getByText('Nouvelle tache')).toBeInTheDocument()
  })

  it('renders mock scheduled tasks', () => {
    renderWithRouter(<AutoScheduler />)
    expect(screen.getByText('Scan Livres US')).toBeInTheDocument()
    expect(screen.getByText('Analyse Competition')).toBeInTheDocument()
    expect(screen.getByText('Refresh Prix')).toBeInTheDocument()
  })

  it('renders planned features cards', () => {
    renderWithRouter(<AutoScheduler />)
    expect(screen.getByText('Analyse automatique')).toBeInTheDocument()
    expect(screen.getByText('Alertes prix')).toBeInTheDocument()
    expect(screen.getByText('Rapports automatiques')).toBeInTheDocument()
  })

  it('opens create modal on button click', () => {
    renderWithRouter(<AutoScheduler />)

    const newTaskButton = screen.getByText('Nouvelle tache')
    fireEvent.click(newTaskButton)

    expect(screen.getByText('Nouvelle tache planifiee')).toBeInTheDocument()
    expect(screen.getByText('Nom de la tache')).toBeInTheDocument()
    expect(screen.getByText('Frequence')).toBeInTheDocument()
  })

  it('closes modal on close button click', () => {
    renderWithRouter(<AutoScheduler />)

    // Open modal
    fireEvent.click(screen.getByText('Nouvelle tache'))
    expect(screen.getByText('Nouvelle tache planifiee')).toBeInTheDocument()

    // Close modal
    fireEvent.click(screen.getByText('Fermer'))
    expect(screen.queryByText('Nouvelle tache planifiee')).not.toBeInTheDocument()
  })

  it('has disabled create button in modal', () => {
    renderWithRouter(<AutoScheduler />)

    fireEvent.click(screen.getByText('Nouvelle tache'))

    const createButton = screen.getByText('Creer (bientot)')
    expect(createButton).toBeDisabled()
  })

  it('shows task status badges', () => {
    renderWithRouter(<AutoScheduler />)

    expect(screen.getAllByText('Actif').length).toBe(2)
    expect(screen.getByText('En pause')).toBeInTheDocument()
  })
})
