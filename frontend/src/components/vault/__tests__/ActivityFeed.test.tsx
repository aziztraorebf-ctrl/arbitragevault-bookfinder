import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { ActivityFeed } from '../ActivityFeed'
import type { ActivityEvent } from '../../../data/mockDashboard'

describe('ActivityFeed', () => {
  const mockEvents: ActivityEvent[] = [
    {
      id: '1',
      type: 'analysis',
      timestamp: '10:45 AM',
      message: 'Analysis Complete: 45 products scored'
    },
    {
      id: '2',
      type: 'niche',
      timestamp: 'Yesterday',
      message: 'Niche Found: Psychology Textbooks'
    },
    {
      id: '3',
      type: 'alert',
      timestamp: '2 days ago',
      message: 'Low Balance Alert: 45 tokens remaining'
    }
  ]

  it('renders header title', () => {
    render(<ActivityFeed events={mockEvents} />)
    expect(screen.getByText('Activity Feed')).toBeInTheDocument()
  })

  it('renders all events', () => {
    render(<ActivityFeed events={mockEvents} />)
    expect(screen.getByText(/Analysis Complete/)).toBeInTheDocument()
    expect(screen.getByText(/Niche Found/)).toBeInTheDocument()
    expect(screen.getByText(/Low Balance Alert/)).toBeInTheDocument()
  })

  it('renders timestamps', () => {
    render(<ActivityFeed events={mockEvents} />)
    expect(screen.getByText('10:45 AM')).toBeInTheDocument()
    expect(screen.getByText('Yesterday')).toBeInTheDocument()
    expect(screen.getByText('2 days ago')).toBeInTheDocument()
  })

  it('renders empty state when no events', () => {
    render(<ActivityFeed events={[]} />)
    expect(screen.getByText('Activity Feed')).toBeInTheDocument()
    // Should still render the container even with no events
  })

  it('applies custom className', () => {
    const { container } = render(
      <ActivityFeed events={mockEvents} className="custom-class" />
    )
    expect(container.firstChild).toHaveClass('custom-class')
  })

  it('renders icon for each event type', () => {
    const { container } = render(<ActivityFeed events={mockEvents} />)
    // Each event has an icon in a rounded background
    const iconContainers = container.querySelectorAll('.rounded-full')
    expect(iconContainers.length).toBe(mockEvents.length)
  })

  it('renders verification event type', () => {
    const events: ActivityEvent[] = [{
      id: '1',
      type: 'verification',
      timestamp: 'Now',
      message: 'Verification: B08N5W passed'
    }]
    render(<ActivityFeed events={events} />)
    expect(screen.getByText(/Verification/)).toBeInTheDocument()
  })

  it('renders search_saved event type', () => {
    const events: ActivityEvent[] = [{
      id: '1',
      type: 'search_saved',
      timestamp: 'Now',
      message: 'Search Saved: Q1 Opportunities'
    }]
    render(<ActivityFeed events={events} />)
    expect(screen.getByText(/Search Saved/)).toBeInTheDocument()
  })
})
