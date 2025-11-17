# Phase 9.0: UI/UX Polish - Plan Implementation

**Status:** Planifie
**Timeline estimee:** 2-3 semaines
**Priority:** Medium (after Phase 8.0 Advanced Analytics)
**Dependencies:** Phase 7.0 complete, Phase 8.0 Analytics complete

---

## Vue d'Ensemble

### Objectif Principal
Ameliorer l'experience utilisateur globale et la coherence visuelle de la plateforme ArbitrageVault BookFinder suite a l'implementation des fonctionnalites business critiques (Phases 1-8).

### Value Proposition
- **Professionnalisme accru** - Interface cohesive et professionnelle
- **Adoption utilisateur** - Experience fluide reduit friction
- **Accessibilite** - Conformite WCAG 2.1 Level AA
- **Performance percue** - Micro-interactions et feedback immediat
- **Onboarding facilite** - Documentation integree et guide interactif

### Pourquoi Maintenant (Apres Phase 8.0)
1. Fonctionnalites business critiques completees (Analytics, Risk, Decision)
2. UI actuelle fonctionnelle mais manque coherence visuelle
3. Feedback utilisateur montre besoins UX amelioration
4. Fondation technique stable pour polish sans refactoring majeur

---

## Phase 9.1: Visual Design Consistency (Semaine 1)

### Objectifs
Etablir et appliquer un design system coherent a travers toute l'application.

### Livrables

#### 1. Design Tokens & Variables
**Fichier:** `frontend/src/styles/design-tokens.ts`

```typescript
export const designTokens = {
  colors: {
    primary: {
      50: '#f0f9ff',
      100: '#e0f2fe',
      500: '#0ea5e9',
      600: '#0284c7',
      700: '#0369a1'
    },
    success: {
      50: '#f0fdf4',
      500: '#22c55e',
      700: '#15803d'
    },
    warning: {
      50: '#fffbeb',
      500: '#f59e0b',
      700: '#b45309'
    },
    danger: {
      50: '#fef2f2',
      500: '#ef4444',
      700: '#b91c1c'
    },
    neutral: {
      50: '#f9fafb',
      100: '#f3f4f6',
      500: '#6b7280',
      900: '#111827'
    }
  },
  typography: {
    fontFamily: {
      sans: ['Inter', 'system-ui', 'sans-serif'],
      mono: ['Fira Code', 'monospace']
    },
    fontSize: {
      xs: '0.75rem',
      sm: '0.875rem',
      base: '1rem',
      lg: '1.125rem',
      xl: '1.25rem',
      '2xl': '1.5rem',
      '3xl': '1.875rem'
    },
    fontWeight: {
      normal: 400,
      medium: 500,
      semibold: 600,
      bold: 700
    },
    lineHeight: {
      tight: 1.25,
      normal: 1.5,
      relaxed: 1.75
    }
  },
  spacing: {
    xs: '0.25rem',
    sm: '0.5rem',
    md: '1rem',
    lg: '1.5rem',
    xl: '2rem',
    '2xl': '3rem'
  },
  borderRadius: {
    sm: '0.25rem',
    md: '0.375rem',
    lg: '0.5rem',
    xl: '0.75rem',
    full: '9999px'
  },
  shadows: {
    sm: '0 1px 2px 0 rgb(0 0 0 / 0.05)',
    md: '0 4px 6px -1px rgb(0 0 0 / 0.1)',
    lg: '0 10px 15px -3px rgb(0 0 0 / 0.1)',
    xl: '0 20px 25px -5px rgb(0 0 0 / 0.1)'
  }
};
```

#### 2. Tailwind Configuration Update
**Fichier:** `frontend/tailwind.config.js`

Synchroniser avec design tokens pour coherence.

#### 3. Component Library Standardization

**Button Component:**
```typescript
// frontend/src/components/ui/Button.tsx
type ButtonVariant = 'primary' | 'secondary' | 'success' | 'danger' | 'ghost';
type ButtonSize = 'sm' | 'md' | 'lg';

interface ButtonProps {
  variant?: ButtonVariant;
  size?: ButtonSize;
  loading?: boolean;
  disabled?: boolean;
  children: React.ReactNode;
  onClick?: () => void;
}

export const Button: React.FC<ButtonProps> = ({
  variant = 'primary',
  size = 'md',
  loading = false,
  disabled = false,
  children,
  onClick
}) => {
  const baseClasses = 'font-medium rounded-lg transition-all duration-200';

  const variantClasses = {
    primary: 'bg-primary-600 text-white hover:bg-primary-700',
    secondary: 'bg-neutral-200 text-neutral-900 hover:bg-neutral-300',
    success: 'bg-success-600 text-white hover:bg-success-700',
    danger: 'bg-danger-600 text-white hover:bg-danger-700',
    ghost: 'bg-transparent hover:bg-neutral-100'
  };

  const sizeClasses = {
    sm: 'px-3 py-1.5 text-sm',
    md: 'px-4 py-2 text-base',
    lg: 'px-6 py-3 text-lg'
  };

  return (
    <button
      className={cn(baseClasses, variantClasses[variant], sizeClasses[size])}
      disabled={disabled || loading}
      onClick={onClick}
    >
      {loading ? <Spinner size={size} /> : children}
    </button>
  );
};
```

**Card Component:**
```typescript
// frontend/src/components/ui/Card.tsx
interface CardProps {
  title?: string;
  subtitle?: string;
  children: React.ReactNode;
  actions?: React.ReactNode;
  variant?: 'default' | 'bordered' | 'elevated';
}

export const Card: React.FC<CardProps> = ({
  title,
  subtitle,
  children,
  actions,
  variant = 'default'
}) => {
  const variantClasses = {
    default: 'bg-white',
    bordered: 'bg-white border border-neutral-200',
    elevated: 'bg-white shadow-lg'
  };

  return (
    <div className={cn('rounded-lg p-6', variantClasses[variant])}>
      {(title || actions) && (
        <div className="flex items-center justify-between mb-4">
          <div>
            {title && <h3 className="text-xl font-semibold">{title}</h3>}
            {subtitle && <p className="text-sm text-neutral-500">{subtitle}</p>}
          </div>
          {actions && <div className="flex gap-2">{actions}</div>}
        </div>
      )}
      {children}
    </div>
  );
};
```

#### 4. Iconographie Coherente
**Integration:** Utiliser `lucide-react` pour icones consistentes

```typescript
import {
  TrendingUp,
  TrendingDown,
  AlertCircle,
  CheckCircle,
  Clock,
  DollarSign,
  ShoppingCart
} from 'lucide-react';
```

#### 5. Audit & Migration Checklist
- [ ] Identifier tous les boutons custom et migrer vers `<Button>`
- [ ] Remplacer divs avec borders par `<Card>`
- [ ] Uniformiser couleurs (remplacer hardcoded hex par design tokens)
- [ ] Standardiser spacing (remplacer custom margins par spacing scale)
- [ ] Verifier conformite typographie

---

## Phase 9.2: User Experience Flows (Semaine 2)

### Objectifs
Optimiser les parcours utilisateur et ameliorer feedback immediat.

### Livrables

#### 1. Navigation Optimisee

**Breadcrumbs Component:**
```typescript
// frontend/src/components/navigation/Breadcrumbs.tsx
interface BreadcrumbItem {
  label: string;
  href?: string;
}

export const Breadcrumbs: React.FC<{ items: BreadcrumbItem[] }> = ({ items }) => {
  return (
    <nav className="flex items-center space-x-2 text-sm text-neutral-600">
      {items.map((item, index) => (
        <React.Fragment key={index}>
          {index > 0 && <ChevronRight className="w-4 h-4" />}
          {item.href ? (
            <Link to={item.href} className="hover:text-primary-600">
              {item.label}
            </Link>
          ) : (
            <span className="font-medium text-neutral-900">{item.label}</span>
          )}
        </React.Fragment>
      ))}
    </nav>
  );
};
```

**Sidebar Active State:**
Ameliorer indication page active avec bordure gauche et background.

#### 2. Loading States Ameliores

**Skeleton Loader Component:**
```typescript
// frontend/src/components/ui/Skeleton.tsx
export const Skeleton: React.FC<{ className?: string }> = ({ className }) => {
  return (
    <div className={cn('animate-pulse bg-neutral-200 rounded', className)} />
  );
};

// Usage pour ProductCard
export const ProductCardSkeleton = () => {
  return (
    <Card>
      <Skeleton className="h-6 w-32 mb-4" />
      <Skeleton className="h-4 w-full mb-2" />
      <Skeleton className="h-4 w-3/4 mb-4" />
      <div className="flex gap-2">
        <Skeleton className="h-10 w-24" />
        <Skeleton className="h-10 w-24" />
      </div>
    </Card>
  );
};
```

**Progress Indicator:**
```typescript
// frontend/src/components/ui/ProgressBar.tsx
interface ProgressBarProps {
  value: number;
  max: number;
  label?: string;
  showPercentage?: boolean;
}

export const ProgressBar: React.FC<ProgressBarProps> = ({
  value,
  max,
  label,
  showPercentage = true
}) => {
  const percentage = Math.min(100, (value / max) * 100);

  return (
    <div className="w-full">
      {label && (
        <div className="flex justify-between mb-1">
          <span className="text-sm font-medium">{label}</span>
          {showPercentage && (
            <span className="text-sm text-neutral-600">{percentage.toFixed(0)}%</span>
          )}
        </div>
      )}
      <div className="w-full bg-neutral-200 rounded-full h-2">
        <div
          className="bg-primary-600 h-2 rounded-full transition-all duration-300"
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  );
};
```

#### 3. Error Recovery Flows

**Error Boundary avec Retry:**
```typescript
// frontend/src/components/ErrorBoundary.tsx
export const ErrorBoundary: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  return (
    <ReactErrorBoundary
      FallbackComponent={ErrorFallback}
      onReset={() => window.location.reload()}
    >
      {children}
    </ReactErrorBoundary>
  );
};

const ErrorFallback: React.FC<FallbackProps> = ({ error, resetErrorBoundary }) => {
  return (
    <Card variant="bordered" className="max-w-md mx-auto mt-8">
      <div className="text-center">
        <AlertCircle className="w-12 h-12 text-danger-500 mx-auto mb-4" />
        <h2 className="text-xl font-semibold mb-2">Une erreur est survenue</h2>
        <p className="text-neutral-600 mb-4">{error.message}</p>
        <Button onClick={resetErrorBoundary}>Reessayer</Button>
      </div>
    </Card>
  );
};
```

#### 4. Toast Notifications System

**Integration:** `react-hot-toast`

```typescript
// frontend/src/utils/toast.ts
import toast from 'react-hot-toast';

export const showSuccess = (message: string) => {
  toast.success(message, {
    duration: 3000,
    position: 'top-right',
    icon: <CheckCircle className="w-5 h-5 text-success-500" />
  });
};

export const showError = (message: string) => {
  toast.error(message, {
    duration: 5000,
    position: 'top-right',
    icon: <AlertCircle className="w-5 h-5 text-danger-500" />
  });
};

export const showLoading = (message: string) => {
  return toast.loading(message, {
    position: 'top-right'
  });
};
```

#### 5. Confirmation Dialogs

**Modal Component:**
```typescript
// frontend/src/components/ui/ConfirmDialog.tsx
interface ConfirmDialogProps {
  isOpen: boolean;
  title: string;
  message: string;
  confirmText?: string;
  cancelText?: string;
  onConfirm: () => void;
  onCancel: () => void;
  variant?: 'danger' | 'warning' | 'info';
}

export const ConfirmDialog: React.FC<ConfirmDialogProps> = ({
  isOpen,
  title,
  message,
  confirmText = 'Confirmer',
  cancelText = 'Annuler',
  onConfirm,
  onCancel,
  variant = 'info'
}) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <Card className="max-w-md w-full">
        <h3 className="text-lg font-semibold mb-2">{title}</h3>
        <p className="text-neutral-600 mb-6">{message}</p>
        <div className="flex gap-2 justify-end">
          <Button variant="ghost" onClick={onCancel}>
            {cancelText}
          </Button>
          <Button
            variant={variant === 'danger' ? 'danger' : 'primary'}
            onClick={onConfirm}
          >
            {confirmText}
          </Button>
        </div>
      </Card>
    </div>
  );
};
```

---

## Phase 9.3: Responsive & Accessibility (Semaine 2-3)

### Objectifs
Garantir accessibilite WCAG 2.1 Level AA et responsive design mobile-first.

### Livrables

#### 1. Mobile-First Responsive Design

**Breakpoints Tailwind:**
```javascript
// tailwind.config.js
module.exports = {
  theme: {
    screens: {
      'sm': '640px',
      'md': '768px',
      'lg': '1024px',
      'xl': '1280px',
      '2xl': '1536px'
    }
  }
};
```

**Responsive Navigation:**
```typescript
// frontend/src/components/navigation/MobileNav.tsx
export const MobileNav: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div className="lg:hidden">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="p-2"
        aria-label="Toggle menu"
      >
        {isOpen ? <X /> : <Menu />}
      </button>

      {isOpen && (
        <div className="absolute top-16 left-0 right-0 bg-white shadow-lg z-40">
          <nav className="p-4 space-y-2">
            <NavLink to="/dashboard">Dashboard</NavLink>
            <NavLink to="/autosourcing">AutoSourcing</NavLink>
            <NavLink to="/niches">Niche Discovery</NavLink>
          </nav>
        </div>
      )}
    </div>
  );
};
```

**Responsive Table:**
```typescript
// frontend/src/components/ui/ResponsiveTable.tsx
export const ResponsiveTable: React.FC<TableProps> = ({ data, columns }) => {
  return (
    <>
      {/* Desktop Table */}
      <div className="hidden md:block overflow-x-auto">
        <table className="min-w-full">
          <thead>
            <tr>
              {columns.map(col => (
                <th key={col.key}>{col.label}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {data.map(row => (
              <tr key={row.id}>
                {columns.map(col => (
                  <td key={col.key}>{row[col.key]}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Mobile Cards */}
      <div className="md:hidden space-y-4">
        {data.map(row => (
          <Card key={row.id}>
            {columns.map(col => (
              <div key={col.key} className="flex justify-between mb-2">
                <span className="font-medium">{col.label}:</span>
                <span>{row[col.key]}</span>
              </div>
            ))}
          </Card>
        ))}
      </div>
    </>
  );
};
```

#### 2. WCAG 2.1 Level AA Compliance

**Color Contrast Checker:**
```typescript
// Minimum contrast ratios:
// - Normal text: 4.5:1
// - Large text (18pt+): 3:1
// - UI components: 3:1

// Example validated colors:
const validatedColors = {
  primary: '#0369a1', // Contrast 4.52:1 on white
  success: '#15803d', // Contrast 4.54:1 on white
  danger: '#b91c1c',  // Contrast 5.03:1 on white
};
```

**Keyboard Navigation:**
```typescript
// frontend/src/hooks/useKeyboardNav.ts
export const useKeyboardNav = (items: string[], onSelect: (item: string) => void) => {
  const [activeIndex, setActiveIndex] = useState(0);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      switch (e.key) {
        case 'ArrowDown':
          e.preventDefault();
          setActiveIndex(prev => Math.min(prev + 1, items.length - 1));
          break;
        case 'ArrowUp':
          e.preventDefault();
          setActiveIndex(prev => Math.max(prev - 1, 0));
          break;
        case 'Enter':
          e.preventDefault();
          onSelect(items[activeIndex]);
          break;
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [activeIndex, items, onSelect]);

  return activeIndex;
};
```

**ARIA Labels & Roles:**
```typescript
// Example accessible form
<form role="form" aria-labelledby="form-title">
  <h2 id="form-title">AutoSourcing Configuration</h2>

  <label htmlFor="min-roi" className="block mb-2">
    ROI Minimum
    <span className="text-danger-500" aria-label="required">*</span>
  </label>
  <input
    id="min-roi"
    type="number"
    aria-required="true"
    aria-describedby="min-roi-help"
  />
  <p id="min-roi-help" className="text-sm text-neutral-600">
    Entrez le ROI minimum souhaite (ex: 30 pour 30%)
  </p>
</form>
```

**Screen Reader Support:**
```typescript
// Announce live updates
<div
  role="status"
  aria-live="polite"
  aria-atomic="true"
  className="sr-only"
>
  {statusMessage}
</div>

// Skip to main content
<a
  href="#main-content"
  className="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4"
>
  Passer au contenu principal
</a>
```

#### 3. Focus Management

**Focus Trap for Modals:**
```typescript
// frontend/src/hooks/useFocusTrap.ts
import { useEffect, useRef } from 'react';

export const useFocusTrap = (isActive: boolean) => {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!isActive || !containerRef.current) return;

    const focusableElements = containerRef.current.querySelectorAll(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    );

    const firstElement = focusableElements[0] as HTMLElement;
    const lastElement = focusableElements[focusableElements.length - 1] as HTMLElement;

    const handleTabKey = (e: KeyboardEvent) => {
      if (e.key !== 'Tab') return;

      if (e.shiftKey) {
        if (document.activeElement === firstElement) {
          lastElement.focus();
          e.preventDefault();
        }
      } else {
        if (document.activeElement === lastElement) {
          firstElement.focus();
          e.preventDefault();
        }
      }
    };

    firstElement?.focus();
    document.addEventListener('keydown', handleTabKey);

    return () => document.removeEventListener('keydown', handleTabKey);
  }, [isActive]);

  return containerRef;
};
```

---

## Phase 9.4: Performance & Feel (Semaine 3)

### Objectifs
Optimiser performance bundle et ajouter micro-interactions pour perceived performance.

### Livrables

#### 1. Bundle Size Optimization

**Code Splitting:**
```typescript
// frontend/src/App.tsx
import { lazy, Suspense } from 'react';

const Dashboard = lazy(() => import('./pages/Dashboard'));
const AutoSourcing = lazy(() => import('./pages/AutoSourcing'));
const NicheDiscovery = lazy(() => import('./pages/NicheDiscovery'));

export const App = () => {
  return (
    <Suspense fallback={<PageLoader />}>
      <Routes>
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/autosourcing" element={<AutoSourcing />} />
        <Route path="/niches" element={<NicheDiscovery />} />
      </Routes>
    </Suspense>
  );
};
```

**Dynamic Imports:**
```typescript
// Import heavy libraries dynamically
const loadChart = async () => {
  const { Chart } = await import('recharts');
  return Chart;
};
```

**Vite Build Optimization:**
```javascript
// vite.config.ts
export default defineConfig({
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          'react-vendor': ['react', 'react-dom', 'react-router-dom'],
          'ui-vendor': ['lucide-react', 'react-hot-toast'],
          'charts': ['recharts']
        }
      }
    },
    chunkSizeWarningLimit: 600
  }
});
```

#### 2. Lazy Loading Components

**Image Lazy Loading:**
```typescript
// frontend/src/components/ui/LazyImage.tsx
export const LazyImage: React.FC<{
  src: string;
  alt: string;
  className?: string;
}> = ({ src, alt, className }) => {
  return (
    <img
      src={src}
      alt={alt}
      loading="lazy"
      className={className}
      decoding="async"
    />
  );
};
```

**Intersection Observer for Heavy Components:**
```typescript
// frontend/src/hooks/useInView.ts
export const useInView = (options?: IntersectionObserverInit) => {
  const [isInView, setIsInView] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const observer = new IntersectionObserver(([entry]) => {
      setIsInView(entry.isIntersecting);
    }, options);

    if (ref.current) {
      observer.observe(ref.current);
    }

    return () => observer.disconnect();
  }, [options]);

  return [ref, isInView] as const;
};

// Usage
const [ref, isInView] = useInView({ threshold: 0.1 });

return (
  <div ref={ref}>
    {isInView ? <HeavyChart data={data} /> : <ChartSkeleton />}
  </div>
);
```

#### 3. Micro-Interactions & Animations

**Button Hover/Active States:**
```typescript
// Using Tailwind transitions
<button className="
  bg-primary-600
  hover:bg-primary-700
  active:scale-95
  transition-all
  duration-200
  ease-in-out
">
  Click me
</button>
```

**Card Hover Effect:**
```css
/* frontend/src/styles/animations.css */
.card-hover {
  @apply transition-all duration-300 ease-in-out;
  @apply hover:shadow-xl hover:-translate-y-1;
}
```

**Loading Spinner:**
```typescript
// frontend/src/components/ui/Spinner.tsx
export const Spinner: React.FC<{ size?: 'sm' | 'md' | 'lg' }> = ({ size = 'md' }) => {
  const sizeClasses = {
    sm: 'w-4 h-4',
    md: 'w-8 h-8',
    lg: 'w-12 h-12'
  };

  return (
    <div className={cn('animate-spin rounded-full border-2 border-primary-600 border-t-transparent', sizeClasses[size])} />
  );
};
```

**Fade In Animation:**
```typescript
// frontend/src/components/ui/FadeIn.tsx
export const FadeIn: React.FC<{
  children: React.ReactNode;
  delay?: number;
}> = ({ children, delay = 0 }) => {
  return (
    <div
      className="animate-fade-in"
      style={{ animationDelay: `${delay}ms` }}
    >
      {children}
    </div>
  );
};

// tailwind.config.js
module.exports = {
  theme: {
    extend: {
      animation: {
        'fade-in': 'fadeIn 0.5s ease-in-out'
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0', transform: 'translateY(10px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' }
        }
      }
    }
  }
};
```

#### 4. Perceived Performance Techniques

**Optimistic UI Updates:**
```typescript
// frontend/src/hooks/useOptimisticUpdate.ts
export const useOptimisticUpdate = <T,>(
  queryKey: string[],
  mutationFn: (data: T) => Promise<T>
) => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn,
    onMutate: async (newData) => {
      await queryClient.cancelQueries({ queryKey });
      const previousData = queryClient.getQueryData(queryKey);

      queryClient.setQueryData(queryKey, newData);

      return { previousData };
    },
    onError: (err, newData, context) => {
      queryClient.setQueryData(queryKey, context?.previousData);
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey });
    }
  });
};
```

**Prefetching:**
```typescript
// Prefetch data on hover
const prefetchProduct = (asin: string) => {
  queryClient.prefetchQuery({
    queryKey: ['product', asin],
    queryFn: () => fetchProduct(asin)
  });
};

<Link
  to={`/product/${asin}`}
  onMouseEnter={() => prefetchProduct(asin)}
>
  View Product
</Link>
```

---

## Phase 9.5: Documentation Utilisateur (Semaine 3)

### Objectifs
Creer documentation interactive et tooltips contextuels pour faciliter onboarding.

### Livrables

#### 1. Guide Interactif (Tour Guide)

**Integration:** `react-joyride`

```typescript
// frontend/src/components/onboarding/ProductTour.tsx
import Joyride, { Step } from 'react-joyride';

const tourSteps: Step[] = [
  {
    target: '[data-tour="autosourcing-btn"]',
    content: 'Cliquez ici pour lancer une recherche AutoSourcing et decouvrir des opportunites profitables automatiquement.',
    disableBeacon: true
  },
  {
    target: '[data-tour="config-panel"]',
    content: 'Configurez vos criteres de recherche: ROI minimum, BSR range, categories cibles.',
  },
  {
    target: '[data-tour="cost-estimate"]',
    content: 'Verifiez le cout estime en tokens Keepa avant de lancer la recherche.',
  },
  {
    target: '[data-tour="results-table"]',
    content: 'Les resultats sont tries par score global. Cliquez sur une ligne pour voir details complets.',
  }
];

export const ProductTour: React.FC = () => {
  const [runTour, setRunTour] = useState(false);

  useEffect(() => {
    const hasSeenTour = localStorage.getItem('hasSeenTour');
    if (!hasSeenTour) {
      setRunTour(true);
    }
  }, []);

  const handleTourEnd = () => {
    localStorage.setItem('hasSeenTour', 'true');
    setRunTour(false);
  };

  return (
    <Joyride
      steps={tourSteps}
      run={runTour}
      continuous
      showSkipButton
      callback={(data) => {
        if (data.status === 'finished' || data.status === 'skipped') {
          handleTourEnd();
        }
      }}
      styles={{
        options: {
          primaryColor: '#0369a1',
          zIndex: 1000
        }
      }}
    />
  );
};
```

#### 2. Tooltips Contextuels

**Tooltip Component:**
```typescript
// frontend/src/components/ui/Tooltip.tsx
import * as TooltipPrimitive from '@radix-ui/react-tooltip';

export const Tooltip: React.FC<{
  children: React.ReactNode;
  content: string;
}> = ({ children, content }) => {
  return (
    <TooltipPrimitive.Provider delayDuration={200}>
      <TooltipPrimitive.Root>
        <TooltipPrimitive.Trigger asChild>
          {children}
        </TooltipPrimitive.Trigger>
        <TooltipPrimitive.Content
          className="bg-neutral-900 text-white px-3 py-2 rounded-md text-sm max-w-xs"
          sideOffset={5}
        >
          {content}
          <TooltipPrimitive.Arrow className="fill-neutral-900" />
        </TooltipPrimitive.Content>
      </TooltipPrimitive.Root>
    </TooltipPrimitive.Provider>
  );
};

// Usage
<Tooltip content="Le ROI net inclut tous les frais Amazon: referral, FBA, prep, shipping, retours, storage.">
  <span className="inline-flex items-center gap-1">
    ROI Net <HelpCircle className="w-4 h-4 text-neutral-400" />
  </span>
</Tooltip>
```

#### 3. FAQ Integration

**FAQ Component:**
```typescript
// frontend/src/components/help/FAQ.tsx
import * as Accordion from '@radix-ui/react-accordion';

const faqData = [
  {
    question: 'Comment fonctionne AutoSourcing?',
    answer: 'AutoSourcing utilise l\'API Keepa pour decouvrir automatiquement des produits profitables...'
  },
  {
    question: 'Qu\'est-ce que le token Keepa?',
    answer: 'Les tokens Keepa sont consommes pour chaque requete API. Un produit analyse = 1 token...'
  },
  {
    question: 'Comment interpreter le score de risque?',
    answer: 'Le score de risque combine 5 facteurs: dead inventory, competition, Amazon presence...'
  }
];

export const FAQ: React.FC = () => {
  return (
    <Card title="Questions Frequentes">
      <Accordion.Root type="single" collapsible>
        {faqData.map((item, index) => (
          <Accordion.Item key={index} value={`item-${index}`}>
            <Accordion.Trigger className="flex justify-between w-full py-4 text-left font-medium">
              {item.question}
              <ChevronDown className="w-5 h-5 transition-transform ui-state-open:rotate-180" />
            </Accordion.Trigger>
            <Accordion.Content className="pb-4 text-neutral-600">
              {item.answer}
            </Accordion.Content>
          </Accordion.Item>
        ))}
      </Accordion.Root>
    </Card>
  );
};
```

#### 4. Contextual Help Panels

**Help Sidebar:**
```typescript
// frontend/src/components/help/HelpSidebar.tsx
export const HelpSidebar: React.FC<{ topic: string }> = ({ topic }) => {
  const helpContent = {
    autosourcing: {
      title: 'AutoSourcing',
      description: 'Decouverte automatique de produits profitables',
      tips: [
        'Commencez avec un BSR range large (ex: 100k-1M) pour plus de resultats',
        'Utilisez cost estimation pour eviter depassement budget tokens',
        'Sauvegardez vos configurations en profiles pour reutilisation'
      ],
      videoUrl: '/videos/autosourcing-guide.mp4'
    },
    // ... other topics
  };

  const content = helpContent[topic];

  return (
    <aside className="w-80 bg-neutral-50 p-6 border-l border-neutral-200">
      <div className="flex items-center gap-2 mb-4">
        <HelpCircle className="w-6 h-6 text-primary-600" />
        <h3 className="text-lg font-semibold">{content.title}</h3>
      </div>
      <p className="text-sm text-neutral-600 mb-4">{content.description}</p>

      <div className="mb-4">
        <h4 className="font-medium mb-2">Astuces</h4>
        <ul className="space-y-2">
          {content.tips.map((tip, index) => (
            <li key={index} className="text-sm text-neutral-700 flex gap-2">
              <CheckCircle className="w-4 h-4 text-success-500 flex-shrink-0 mt-0.5" />
              {tip}
            </li>
          ))}
        </ul>
      </div>

      {content.videoUrl && (
        <Button variant="secondary" className="w-full">
          Voir le guide video
        </Button>
      )}
    </aside>
  );
};
```

#### 5. Empty States avec Call-to-Action

**Empty State Component:**
```typescript
// frontend/src/components/ui/EmptyState.tsx
export const EmptyState: React.FC<{
  icon: React.ReactNode;
  title: string;
  description: string;
  action?: {
    label: string;
    onClick: () => void;
  };
}> = ({ icon, title, description, action }) => {
  return (
    <div className="flex flex-col items-center justify-center py-12 text-center">
      <div className="w-16 h-16 rounded-full bg-neutral-100 flex items-center justify-center mb-4">
        {icon}
      </div>
      <h3 className="text-lg font-semibold mb-2">{title}</h3>
      <p className="text-neutral-600 max-w-md mb-6">{description}</p>
      {action && (
        <Button onClick={action.onClick}>{action.label}</Button>
      )}
    </div>
  );
};

// Usage
<EmptyState
  icon={<ShoppingCart className="w-8 h-8 text-neutral-400" />}
  title="Aucun produit decouvert"
  description="Lancez votre premiere recherche AutoSourcing pour decouvrir des opportunites profitables."
  action={{
    label: 'Lancer AutoSourcing',
    onClick: () => navigate('/autosourcing')
  }}
/>
```

---

## Testing & Validation

### Checklist Phase 9.0

#### Visual Design Consistency
- [ ] Design tokens implementes
- [ ] Tailwind config synchronise
- [ ] Component library standardise (Button, Card, Input)
- [ ] Iconographie uniforme (lucide-react)
- [ ] Audit couleurs/spacing complete

#### User Experience Flows
- [ ] Breadcrumbs navigation
- [ ] Loading states (Skeleton, ProgressBar)
- [ ] Error boundaries avec retry
- [ ] Toast notifications
- [ ] Confirmation dialogs

#### Responsive & Accessibility
- [ ] Mobile navigation fonctionnelle
- [ ] Responsive tables/cards
- [ ] Color contrast WCAG AA valide
- [ ] Keyboard navigation complete
- [ ] ARIA labels corrects
- [ ] Screen reader teste
- [ ] Focus trap modals

#### Performance & Feel
- [ ] Code splitting implemente
- [ ] Dynamic imports pour libraries lourdes
- [ ] Lazy loading images/components
- [ ] Micro-interactions polished
- [ ] Optimistic UI updates
- [ ] Prefetching strategique

#### Documentation Utilisateur
- [ ] Product tour interactif
- [ ] Tooltips contextuels
- [ ] FAQ integree
- [ ] Help sidebar par page
- [ ] Empty states avec CTA
- [ ] Video guides (si applicable)

---

## Metriques de Succes Phase 9.0

### Performance Metrics
- **Bundle Size:** < 500KB gzipped (initial load)
- **First Contentful Paint:** < 1.5s
- **Time to Interactive:** < 3s
- **Lighthouse Score:** > 90

### Accessibility Metrics
- **WCAG Compliance:** Level AA (100%)
- **Keyboard Navigation:** All interactive elements
- **Screen Reader:** No errors in NVDA/JAWS
- **Color Contrast:** All text > 4.5:1

### User Experience Metrics
- **Tour Completion Rate:** > 60%
- **Help Documentation Usage:** Track clicks on tooltips/FAQ
- **Error Recovery Rate:** Users successfully retry after errors
- **Mobile Usage:** Responsive UI functional on all breakpoints

---

## Timeline & Resources

### Phase 9.1: Visual Design (Week 1)
- Design tokens setup
- Component library refactor
- Color/typography audit
- Icon standardization

### Phase 9.2: UX Flows (Week 2)
- Navigation improvements
- Loading/error states
- Toast notifications
- Confirmation flows

### Phase 9.3: Responsive & A11y (Week 2-3)
- Mobile-first refactor
- WCAG compliance fixes
- Keyboard navigation
- Screen reader testing

### Phase 9.4: Performance (Week 3)
- Bundle optimization
- Lazy loading
- Micro-interactions
- Perceived performance

### Phase 9.5: Documentation (Week 3)
- Product tour
- Tooltips integration
- FAQ creation
- Help panels

---

## Post-Phase 9.0 Considerations

### Maintenance
- Design system documentation
- Component storybook (optionnel)
- Accessibility audit schedule (quarterly)
- Performance monitoring

### Future Enhancements (Phase 10+)
- Dark mode support
- Advanced theme customization
- Multi-language support (i18n)
- Offline mode (PWA)
- Advanced analytics dashboard
- Mobile app (React Native)

---

**Document cree:** 16 Novembre 2025
**Responsable:** UX/UI Development Team
**Status:** Planifie (apres Phase 8.0 Advanced Analytics)
