// Documentation Index Page
import { Link } from 'react-router-dom'
import DocsLayout from './DocsLayout'
import {
  Search,
  BarChart3,
  Bookmark,
  BookOpen,
  HelpCircle,
  ArrowRight
} from 'lucide-react'

const quickLinks = [
  {
    title: 'Recherche de Produits',
    description: 'Apprenez a rechercher des produits par ASIN ou mot-cle',
    href: '/docs/search',
    icon: Search,
  },
  {
    title: 'Comprendre les Scores',
    description: 'ROI, BSR, Velocity - tout ce que vous devez savoir',
    href: '/docs/analysis',
    icon: BarChart3,
  },
  {
    title: 'Produits Sauvegardes',
    description: 'Gerez et suivez vos produits favoris',
    href: '/docs/saved-products',
    icon: Bookmark,
  },
  {
    title: 'Glossaire',
    description: 'Definitions des termes techniques',
    href: '/docs/glossary',
    icon: BookOpen,
  },
]

export default function DocsIndex() {
  return (
    <DocsLayout
      title="Documentation ArbitrageVault"
      description="Guide complet pour utiliser ArbitrageVault efficacement"
    >
      {/* Welcome Section */}
      <div className="mb-8">
        <p className="text-lg text-vault-text-secondary mb-4">
          Bienvenue dans la documentation d'ArbitrageVault. Ce guide vous aidera
          a comprendre et utiliser toutes les fonctionnalites de l'application.
        </p>
        <div className="bg-vault-accent-light/50 border border-vault-accent/20 rounded-xl p-4">
          <div className="flex items-start gap-3">
            <HelpCircle className="w-5 h-5 text-vault-accent flex-shrink-0 mt-0.5" />
            <div>
              <p className="text-sm text-vault-text font-medium mb-1">
                Nouveau sur ArbitrageVault?
              </p>
              <p className="text-sm text-vault-text-secondary">
                Commencez par le{' '}
                <Link to="/docs/getting-started" className="text-vault-accent hover:underline">
                  guide de demarrage rapide
                </Link>
                {' '}pour apprendre les bases.
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Quick Links Grid */}
      <h2 className="text-xl font-semibold text-vault-text mb-4">
        Guides Rapides
      </h2>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-8">
        {quickLinks.map((link) => {
          const Icon = link.icon
          return (
            <Link
              key={link.href}
              to={link.href}
              className="group block p-4 bg-vault-bg rounded-xl border border-vault-border hover:border-vault-accent/50 transition-all duration-200"
            >
              <div className="flex items-start gap-3">
                <div className="p-2 bg-vault-accent-light rounded-lg">
                  <Icon className="w-5 h-5 text-vault-accent" />
                </div>
                <div className="flex-1">
                  <h3 className="font-medium text-vault-text group-hover:text-vault-accent transition-colors flex items-center gap-2">
                    {link.title}
                    <ArrowRight className="w-4 h-4 opacity-0 group-hover:opacity-100 transition-opacity" />
                  </h3>
                  <p className="text-sm text-vault-text-secondary mt-1">
                    {link.description}
                  </p>
                </div>
              </div>
            </Link>
          )
        })}
      </div>

      {/* What You'll Learn */}
      <h2 className="text-xl font-semibold text-vault-text mb-4">
        Ce que vous apprendrez
      </h2>
      <ul className="space-y-3 text-vault-text-secondary">
        <li className="flex items-start gap-2">
          <span className="text-vault-accent">-</span>
          Comment rechercher et analyser des produits Amazon
        </li>
        <li className="flex items-start gap-2">
          <span className="text-vault-accent">-</span>
          Comprendre les metriques (ROI, BSR, Velocity Score)
        </li>
        <li className="flex items-start gap-2">
          <span className="text-vault-accent">-</span>
          Configurer vos criteres de sourcing
        </li>
        <li className="flex items-start gap-2">
          <span className="text-vault-accent">-</span>
          Utiliser les fonctionnalites d'automatisation
        </li>
        <li className="flex items-start gap-2">
          <span className="text-vault-accent">-</span>
          Resoudre les problemes courants
        </li>
      </ul>
    </DocsLayout>
  )
}
