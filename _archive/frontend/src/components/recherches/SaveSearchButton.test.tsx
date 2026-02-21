/**
 * Unit tests for SaveSearchButton component
 * Phase 11 - Gap 5 fix
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MemoryRouter } from 'react-router-dom'
import { SaveSearchButton } from './SaveSearchButton'
import type { DisplayableProduct } from '../../types/unified'

// Mock the useCreateRecherche hook
const mockMutate = vi.fn()
vi.mock('../../hooks/useRecherches', () => ({
  useCreateRecherche: () => ({
    mutate: mockMutate,
    isPending: false,
    isSuccess: false,
  }),
}))

// Mock react-hot-toast
vi.mock('react-hot-toast', () => ({
  toast: {
    success: vi.fn(),
    error: vi.fn(),
    dismiss: vi.fn(),
  },
}))

// Test data - using correct DisplayableProduct shape
const mockProducts: DisplayableProduct[] = [
  {
    asin: 'B08N5WRWNW',
    title: 'Test Book 1',
    source: 'product_score',
    roi_percent: 35.5,
    velocity_score: 7.2,
    bsr: 45000,
    current_price: 24.99,
    recommendation: 'BUY',
  },
  {
    asin: 'B07XYZ1234',
    title: 'Test Book 2',
    source: 'product_score',
    roi_percent: 42.0,
    velocity_score: 8.1,
    bsr: 32000,
    current_price: 19.99,
    recommendation: 'STRONG_BUY',
  },
]

function renderWithProviders(ui: React.ReactElement) {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  })
  return render(
    <MemoryRouter>
      <QueryClientProvider client={queryClient}>
        {ui}
      </QueryClientProvider>
    </MemoryRouter>
  )
}

describe('SaveSearchButton', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('Rendering', () => {
    it('renders nothing when products array is empty', () => {
      const { container } = renderWithProviders(
        <SaveSearchButton
          products={[]}
          source="niche_discovery"
        />
      )
      expect(container.firstChild).toBeNull()
    })

    it('renders button when products exist', () => {
      renderWithProviders(
        <SaveSearchButton
          products={mockProducts}
          source="niche_discovery"
        />
      )
      expect(screen.getByRole('button')).toBeInTheDocument()
      expect(screen.getByText('Sauvegarder (2)')).toBeInTheDocument()
    })

    it('shows correct product count in button', () => {
      renderWithProviders(
        <SaveSearchButton
          products={[mockProducts[0]]}
          source="autosourcing"
        />
      )
      expect(screen.getByText('Sauvegarder (1)')).toBeInTheDocument()
    })

    it('applies custom className', () => {
      renderWithProviders(
        <SaveSearchButton
          products={mockProducts}
          source="niche_discovery"
          className="custom-class"
        />
      )
      expect(screen.getByRole('button')).toHaveClass('custom-class')
    })

    it('is disabled when disabled prop is true', () => {
      renderWithProviders(
        <SaveSearchButton
          products={mockProducts}
          source="niche_discovery"
          disabled={true}
        />
      )
      expect(screen.getByRole('button')).toBeDisabled()
    })
  })

  describe('Modal behavior', () => {
    it('opens modal when button is clicked', async () => {
      const user = userEvent.setup()
      renderWithProviders(
        <SaveSearchButton
          products={mockProducts}
          source="niche_discovery"
        />
      )

      await user.click(screen.getByRole('button'))
      expect(screen.getByText('Sauvegarder la recherche')).toBeInTheDocument()
    })

    it('shows default name with timestamp when modal opens', async () => {
      const user = userEvent.setup()
      renderWithProviders(
        <SaveSearchButton
          products={mockProducts}
          source="niche_discovery"
        />
      )

      await user.click(screen.getByRole('button'))
      const input = screen.getByPlaceholderText('Nom de la recherche') as HTMLInputElement
      // Value should start with "Recherche" and contain date/time
      expect(input.value).toMatch(/^Recherche \d{2}\/\d{2}\/\d{4}/)
    })

    it('uses defaultName prop when provided', async () => {
      const user = userEvent.setup()
      renderWithProviders(
        <SaveSearchButton
          products={mockProducts}
          source="niche_discovery"
          defaultName="My Custom Search"
        />
      )

      await user.click(screen.getByRole('button'))
      const input = screen.getByPlaceholderText('Nom de la recherche')
      expect(input).toHaveValue('My Custom Search')
    })

    it('closes modal when Annuler is clicked', async () => {
      const user = userEvent.setup()
      renderWithProviders(
        <SaveSearchButton
          products={mockProducts}
          source="niche_discovery"
        />
      )

      await user.click(screen.getByRole('button'))
      expect(screen.getByText('Sauvegarder la recherche')).toBeInTheDocument()

      await user.click(screen.getByText('Annuler'))
      expect(screen.queryByText('Sauvegarder la recherche')).not.toBeInTheDocument()
    })

    it('shows product count in modal', async () => {
      const user = userEvent.setup()
      renderWithProviders(
        <SaveSearchButton
          products={mockProducts}
          source="niche_discovery"
        />
      )

      await user.click(screen.getByRole('button'))
      expect(screen.getByText(/2 produits seront sauvegardes/)).toBeInTheDocument()
    })

    it('shows singular form for 1 product', async () => {
      const user = userEvent.setup()
      renderWithProviders(
        <SaveSearchButton
          products={[mockProducts[0]]}
          source="niche_discovery"
        />
      )

      await user.click(screen.getByRole('button'))
      expect(screen.getByText(/1 produit seront sauvegardes/)).toBeInTheDocument()
    })
  })

  describe('Form validation', () => {
    it('disables save button when name is empty', async () => {
      const user = userEvent.setup()
      renderWithProviders(
        <SaveSearchButton
          products={mockProducts}
          source="niche_discovery"
        />
      )

      await user.click(screen.getByRole('button'))
      const nameInput = screen.getByPlaceholderText('Nom de la recherche')

      // Clear the auto-generated name
      await user.clear(nameInput)

      const saveButtons = screen.getAllByText('Sauvegarder')
      // The modal save button should be disabled
      const modalSaveButton = saveButtons.find((btn) =>
        btn.closest('button')?.className.includes('bg-purple-600')
      )
      expect(modalSaveButton?.closest('button')).toBeDisabled()
    })

    it('enables save button when name is filled', async () => {
      const user = userEvent.setup()
      renderWithProviders(
        <SaveSearchButton
          products={mockProducts}
          source="niche_discovery"
        />
      )

      await user.click(screen.getByRole('button'))
      const nameInput = screen.getByPlaceholderText('Nom de la recherche')

      await user.clear(nameInput)
      await user.type(nameInput, 'Test Search Name')

      // Find the modal's save button (not the main button)
      const saveButtons = screen.getAllByRole('button')
      const modalSaveButton = saveButtons.find(
        (btn) =>
          btn.textContent?.includes('Sauvegarder') &&
          btn.className.includes('bg-purple-600') &&
          !btn.hasAttribute('title')
      )
      expect(modalSaveButton).not.toBeDisabled()
    })
  })

  describe('Save functionality', () => {
    it('calls createRecherche with correct data when save is clicked', async () => {
      const user = userEvent.setup()
      renderWithProviders(
        <SaveSearchButton
          products={mockProducts}
          source="niche_discovery"
          searchParams={{ strategy: 'textbook' }}
        />
      )

      await user.click(screen.getByRole('button'))

      const nameInput = screen.getByPlaceholderText('Nom de la recherche')
      await user.clear(nameInput)
      await user.type(nameInput, 'My Test Search')

      const notesInput = screen.getByPlaceholderText('Notes sur cette recherche...')
      await user.type(notesInput, 'Some notes')

      // Find and click the modal save button
      const saveButtons = screen.getAllByRole('button')
      const modalSaveButton = saveButtons.find(
        (btn) =>
          btn.textContent?.includes('Sauvegarder') &&
          !btn.hasAttribute('title')
      )
      if (modalSaveButton) {
        await user.click(modalSaveButton)
      }

      expect(mockMutate).toHaveBeenCalledWith(
        {
          name: 'My Test Search',
          source: 'niche_discovery',
          products: mockProducts,
          search_params: { strategy: 'textbook' },
          notes: 'Some notes',
        },
        expect.any(Object)
      )
    })

    it('does not include notes when empty', async () => {
      const user = userEvent.setup()
      renderWithProviders(
        <SaveSearchButton
          products={mockProducts}
          source="autosourcing"
        />
      )

      await user.click(screen.getByRole('button'))

      const nameInput = screen.getByPlaceholderText('Nom de la recherche')
      await user.clear(nameInput)
      await user.type(nameInput, 'Search Without Notes')

      // Find and click the modal save button
      const saveButtons = screen.getAllByRole('button')
      const modalSaveButton = saveButtons.find(
        (btn) =>
          btn.textContent?.includes('Sauvegarder') &&
          !btn.hasAttribute('title')
      )
      if (modalSaveButton) {
        await user.click(modalSaveButton)
      }

      expect(mockMutate).toHaveBeenCalledWith(
        expect.objectContaining({
          name: 'Search Without Notes',
          source: 'autosourcing',
          notes: undefined,
        }),
        expect.any(Object)
      )
    })
  })

  describe('Different sources', () => {
    it('passes correct source niche_discovery', async () => {
      const user = userEvent.setup()
      renderWithProviders(
        <SaveSearchButton
          products={mockProducts}
          source="niche_discovery"
        />
      )

      await user.click(screen.getByRole('button'))
      const nameInput = screen.getByPlaceholderText('Nom de la recherche')
      await user.clear(nameInput)
      await user.type(nameInput, 'Test')

      const saveButtons = screen.getAllByRole('button')
      const modalSaveButton = saveButtons.find(
        (btn) => btn.textContent?.includes('Sauvegarder') && !btn.hasAttribute('title')
      )
      if (modalSaveButton) await user.click(modalSaveButton)

      expect(mockMutate).toHaveBeenCalledWith(
        expect.objectContaining({ source: 'niche_discovery' }),
        expect.any(Object)
      )
    })

    it('passes correct source autosourcing', async () => {
      const user = userEvent.setup()
      renderWithProviders(
        <SaveSearchButton
          products={mockProducts}
          source="autosourcing"
        />
      )

      await user.click(screen.getByRole('button'))
      const nameInput = screen.getByPlaceholderText('Nom de la recherche')
      await user.clear(nameInput)
      await user.type(nameInput, 'Test')

      const saveButtons = screen.getAllByRole('button')
      const modalSaveButton = saveButtons.find(
        (btn) => btn.textContent?.includes('Sauvegarder') && !btn.hasAttribute('title')
      )
      if (modalSaveButton) await user.click(modalSaveButton)

      expect(mockMutate).toHaveBeenCalledWith(
        expect.objectContaining({ source: 'autosourcing' }),
        expect.any(Object)
      )
    })

    it('passes correct source manual_analysis', async () => {
      const user = userEvent.setup()
      renderWithProviders(
        <SaveSearchButton
          products={mockProducts}
          source="manual_analysis"
        />
      )

      await user.click(screen.getByRole('button'))
      const nameInput = screen.getByPlaceholderText('Nom de la recherche')
      await user.clear(nameInput)
      await user.type(nameInput, 'Test')

      const saveButtons = screen.getAllByRole('button')
      const modalSaveButton = saveButtons.find(
        (btn) => btn.textContent?.includes('Sauvegarder') && !btn.hasAttribute('title')
      )
      if (modalSaveButton) await user.click(modalSaveButton)

      expect(mockMutate).toHaveBeenCalledWith(
        expect.objectContaining({ source: 'manual_analysis' }),
        expect.any(Object)
      )
    })
  })
})
