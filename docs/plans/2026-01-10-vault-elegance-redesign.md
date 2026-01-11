# Vault Elegance Redesign - 4 Pages Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Redesign 4 pages (MesNiches, AutoScheduler, AutoSourcing, RechercheDetail) to match the Vault Elegance design system already implemented in NicheDiscovery.

**Architecture:** Apply the existing Vault Elegance design tokens (vault-bg, vault-card, vault-text, vault-accent, etc.) consistently across all pages. Use the same component patterns: rounded-2xl cards, font-display for headers, vault shadows, and semantic color tokens for states.

**Tech Stack:** React + TypeScript + Tailwind CSS with Vault Elegance custom theme (defined in theme.css and tailwind.config.js)

---

## Design System Reference

**Colors (Tailwind classes):**
- Background: `bg-vault-bg`
- Cards: `bg-vault-card`
- Text: `text-vault-text`, `text-vault-text-secondary`, `text-vault-text-muted`
- Accent: `text-vault-accent`, `bg-vault-accent`, `hover:bg-vault-accent-hover`
- Borders: `border-vault-border`, `border-vault-border-light`
- Semantic: `text-vault-success`, `text-vault-danger`, `text-vault-warning`

**Typography:**
- Headers: `font-display font-semibold`
- Body: `font-sans` (default)

**Shadows:**
- `shadow-vault-sm`, `shadow-vault-md`, `shadow-vault-lg`

**Border Radius:**
- Cards: `rounded-2xl`
- Buttons: `rounded-xl`
- Small elements: `rounded-vault-sm` (12px), `rounded-vault-xs` (8px)

**Patterns from NicheDiscovery:**
- Page wrapper: `min-h-screen bg-vault-bg`
- Container: `max-w-7xl mx-auto`
- Header: `text-3xl md:text-5xl font-display font-semibold text-vault-text tracking-tight`
- Subtitle: `text-vault-text-secondary text-sm md:text-base mt-2`
- Empty state card: `bg-vault-card border border-vault-border rounded-2xl shadow-vault-sm`
- Button primary: `bg-vault-accent text-white hover:bg-vault-accent-hover rounded-xl`
- Button secondary: `bg-vault-card text-vault-accent border border-vault-border rounded-xl hover:bg-vault-hover`

---

## Task 1: Redesign MesNiches Page

**Files:**
- Modify: `frontend/src/pages/MesNiches.tsx`
- Modify: `frontend/src/components/bookmarks/NicheListItem.tsx` (if exists, apply vault styles)

**Step 1: Update page wrapper and header**

Replace:
```tsx
<div className="min-h-screen bg-gray-50 p-8">
  <div className="max-w-6xl mx-auto space-y-6">
    {/* Header */}
    <div className="flex items-center justify-between">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">
          Mes Niches Sauvegardees
        </h1>
        <p className="text-gray-600 mt-2">
          Gerez vos niches decouvertes et relancez l'analyse
        </p>
      </div>
      <div className="text-sm text-gray-400">Phase 5</div>
    </div>
```

With:
```tsx
<div className="min-h-screen bg-vault-bg">
  <div className="max-w-7xl mx-auto p-4 md:p-8 space-y-6 md:space-y-8">
    {/* Header */}
    <div className="flex items-center justify-between">
      <div>
        <h1 className="text-3xl md:text-5xl font-display font-semibold text-vault-text tracking-tight">
          Mes Niches
        </h1>
        <p className="text-vault-text-secondary text-sm md:text-base mt-2">
          Gerez vos niches decouvertes et relancez l'analyse
        </p>
      </div>
    </div>
```

**Step 2: Update loading state**

Replace:
```tsx
{isLoading && (
  <div className="flex items-center justify-center py-12">
    <Loader2 className="w-8 h-8 animate-spin text-purple-600" />
    <span className="ml-3 text-gray-600">
      Chargement de vos niches...
    </span>
  </div>
)}
```

With:
```tsx
{isLoading && (
  <div className="flex items-center justify-center py-12">
    <div className="animate-spin h-12 w-12 border-4 border-vault-accent border-t-transparent rounded-full"></div>
    <span className="ml-4 text-vault-text-secondary">
      Chargement de vos niches...
    </span>
  </div>
)}
```

**Step 3: Update error state**

Replace:
```tsx
{error && (
  <div className="bg-red-50 border border-red-200 rounded-lg p-4">
    <p className="text-red-800">
```

With:
```tsx
{error && (
  <div className="bg-vault-danger-light border border-vault-danger/20 rounded-2xl p-4">
    <p className="text-vault-danger">
```

**Step 4: Update empty state**

Replace:
```tsx
<div className="bg-white rounded-lg shadow-md p-12 text-center">
  <Inbox className="w-16 h-16 text-gray-400 mx-auto mb-4" />
  <h2 className="text-xl font-semibold text-gray-700 mb-2">
    Aucune niche sauvegardee
  </h2>
  <p className="text-gray-500 mb-6">
    ...
  </p>
  <a
    href="/niche-discovery"
    className="inline-block px-6 py-3 bg-purple-600 hover:bg-purple-700 text-white rounded-lg transition-colors duration-200"
  >
    Decouvrir des niches
  </a>
</div>
```

With:
```tsx
<div className="bg-vault-card border border-vault-border rounded-2xl shadow-vault-sm p-12 text-center">
  <Inbox className="w-16 h-16 text-vault-text-muted mx-auto mb-4" />
  <h2 className="text-xl font-display font-semibold text-vault-text mb-2">
    Aucune niche sauvegardee
  </h2>
  <p className="text-vault-text-secondary mb-6">
    Decouvrez des niches dans la page "Niche Discovery" et
    sauvegardez-les pour y acceder rapidement.
  </p>
  <a
    href="/niche-discovery"
    className="inline-block px-6 py-3 bg-vault-accent hover:bg-vault-accent-hover text-white rounded-xl font-medium transition-colors duration-200"
  >
    Decouvrir des niches
  </a>
</div>
```

**Step 5: Update list counter**

Replace:
```tsx
<div className="text-sm text-gray-600">
```

With:
```tsx
<div className="text-sm text-vault-text-secondary">
```

**Step 6: Update info footer**

Replace:
```tsx
<div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
  <h3 className="text-sm font-semibold text-blue-900 mb-2">
    Info: Gestion des niches
  </h3>
  <ul className="text-sm text-blue-800 space-y-1">
```

With:
```tsx
<div className="bg-vault-accent-light border border-vault-accent/20 rounded-2xl p-4">
  <h3 className="text-sm font-semibold text-vault-accent mb-2">
    Info: Gestion des niches
  </h3>
  <ul className="text-sm text-vault-text-secondary space-y-1">
```

**Step 7: Run build to verify no errors**

Run: `cd frontend && npm run build`
Expected: Build succeeds with no TypeScript errors

**Step 8: Commit**

```bash
git add frontend/src/pages/MesNiches.tsx
git commit -m "style(MesNiches): apply Vault Elegance design system

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"
```

---

## Task 2: Redesign AutoScheduler Page

**Files:**
- Modify: `frontend/src/pages/AutoScheduler.tsx`

**Step 1: Update page wrapper and header**

Replace:
```tsx
<div className="p-8 max-w-6xl mx-auto">
  <div className="flex justify-between items-center mb-6">
    <div>
      <h1 className="text-2xl font-bold text-gray-900">AutoScheduler</h1>
      <p className="text-gray-600 mt-1">Planification automatique des analyses</p>
    </div>
    <button
      onClick={() => setShowCreateModal(true)}
      className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
    >
      Nouvelle tache
    </button>
  </div>
```

With:
```tsx
<div className="min-h-screen bg-vault-bg p-4 md:p-8">
  <div className="max-w-7xl mx-auto space-y-6 md:space-y-8">
    <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
      <div>
        <h1 className="text-3xl md:text-5xl font-display font-semibold text-vault-text tracking-tight">
          AutoScheduler
        </h1>
        <p className="text-vault-text-secondary text-sm md:text-base mt-2">
          Planification automatique des analyses
        </p>
      </div>
      <button
        onClick={() => setShowCreateModal(true)}
        className="px-6 py-3 bg-vault-accent text-white rounded-xl hover:bg-vault-accent-hover font-medium transition-colors"
      >
        Nouvelle tache
      </button>
    </div>
```

**Step 2: Update feature status banner**

Replace:
```tsx
<div className="bg-amber-50 border border-amber-200 rounded-lg p-4 mb-6">
  <div className="flex items-start gap-3">
    <div className="flex-shrink-0 text-amber-500 text-xl">!</div>
    <div>
      <h3 className="text-amber-800 font-semibold">Fonctionnalite a venir - Phase 12</h3>
      <p className="text-amber-700 text-sm mt-1">
```

With:
```tsx
<div className="bg-vault-warning-light border border-vault-warning/20 rounded-2xl p-6">
  <div className="flex items-start gap-4">
    <div className="flex-shrink-0 w-10 h-10 bg-vault-warning/20 rounded-full flex items-center justify-center">
      <span className="text-vault-warning text-xl font-bold">!</span>
    </div>
    <div>
      <h3 className="text-vault-text font-display font-semibold">Fonctionnalite a venir</h3>
      <p className="text-vault-text-secondary text-sm mt-2">
```

Also update the links:
```tsx
<a href="/autosourcing" className="text-vault-accent underline font-medium hover:text-vault-accent-hover">AutoSourcing</a>
<a href="/niche-discovery" className="text-vault-accent underline font-medium hover:text-vault-accent-hover">Niche Discovery</a>
```

**Step 3: Update scheduled tasks list**

Replace:
```tsx
<div className="bg-white rounded-lg shadow">
  <div className="px-4 py-3 border-b border-gray-200">
    <h2 className="font-semibold text-gray-900">Taches planifiees</h2>
  </div>
  <div className="divide-y divide-gray-200">
    {MOCK_SCHEDULES.map((schedule) => (
      <div key={schedule.id} className="p-4 hover:bg-gray-50">
```

With:
```tsx
<div className="bg-vault-card rounded-2xl shadow-vault-sm border border-vault-border">
  <div className="px-6 py-4 border-b border-vault-border">
    <h2 className="font-display font-semibold text-vault-text">Taches planifiees</h2>
  </div>
  <div className="divide-y divide-vault-border">
    {MOCK_SCHEDULES.map((schedule) => (
      <div key={schedule.id} className="p-4 md:p-6 hover:bg-vault-hover transition-colors">
```

**Step 4: Update schedule item styling**

Replace:
```tsx
<div className={`w-3 h-3 rounded-full ${
  schedule.status === 'active' ? 'bg-green-500' : 'bg-gray-300'
}`} />
<div>
  <h3 className="font-medium text-gray-900">{schedule.name}</h3>
  <p className="text-sm text-gray-500">
```

With:
```tsx
<div className={`w-3 h-3 rounded-full ${
  schedule.status === 'active' ? 'bg-vault-success' : 'bg-vault-text-muted'
}`} />
<div>
  <h3 className="font-medium text-vault-text">{schedule.name}</h3>
  <p className="text-sm text-vault-text-secondary">
```

**Step 5: Update status badges**

Replace:
```tsx
<span className={`px-2 py-1 text-xs rounded-full ${
  schedule.status === 'active'
    ? 'bg-green-100 text-green-800'
    : 'bg-gray-100 text-gray-800'
}`}>
```

With:
```tsx
<span className={`px-3 py-1 text-xs font-medium rounded-full ${
  schedule.status === 'active'
    ? 'bg-vault-success-light text-vault-success'
    : 'bg-vault-hover text-vault-text-muted'
}`}>
```

**Step 6: Update feature cards grid**

Replace:
```tsx
<div className="mt-8 grid grid-cols-1 md:grid-cols-3 gap-4">
  <div className="bg-white rounded-lg shadow p-4">
    <h3 className="font-semibold text-gray-900 mb-2">Analyse automatique</h3>
    <p className="text-sm text-gray-600">
```

With:
```tsx
<div className="grid grid-cols-1 md:grid-cols-3 gap-4 md:gap-6">
  <div className="bg-vault-card rounded-2xl shadow-vault-sm border border-vault-border p-6">
    <h3 className="font-display font-semibold text-vault-text mb-2">Analyse automatique</h3>
    <p className="text-sm text-vault-text-secondary">
```

**Step 7: Update modal styling**

Replace:
```tsx
<div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
  <div className="bg-white rounded-lg shadow-xl max-w-md w-full mx-4">
    <div className="px-6 py-4 border-b border-gray-200">
      <h2 className="text-lg font-semibold text-gray-900">Nouvelle tache planifiee</h2>
    </div>
```

With:
```tsx
<div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
  <div className="bg-vault-card rounded-2xl shadow-vault-lg max-w-md w-full border border-vault-border">
    <div className="px-6 py-4 border-b border-vault-border">
      <h2 className="text-lg font-display font-semibold text-vault-text">Nouvelle tache planifiee</h2>
    </div>
```

**Step 8: Update modal form fields**

Replace:
```tsx
<label className="block text-sm font-medium text-gray-700 mb-1">
<input
  type="text"
  className="w-full border rounded-lg px-3 py-2"
<select className="w-full border rounded-lg px-3 py-2" disabled>
```

With:
```tsx
<label className="block text-sm font-medium text-vault-text-secondary mb-1">
<input
  type="text"
  className="w-full border border-vault-border rounded-xl px-4 py-2 bg-vault-bg text-vault-text focus:ring-2 focus:ring-vault-accent focus:border-transparent"
<select className="w-full border border-vault-border rounded-xl px-4 py-2 bg-vault-bg text-vault-text" disabled>
```

**Step 9: Update modal warning and buttons**

Replace:
```tsx
<p className="text-sm text-amber-600 bg-amber-50 p-2 rounded">
```

With:
```tsx
<p className="text-sm text-vault-warning bg-vault-warning-light p-3 rounded-xl">
```

Replace modal footer:
```tsx
<div className="px-6 py-4 border-t border-gray-200 flex justify-end gap-3">
  <button
    onClick={() => setShowCreateModal(false)}
    className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-lg"
  >
    Fermer
  </button>
  <button
    className="px-4 py-2 bg-gray-300 text-gray-500 rounded-lg cursor-not-allowed"
    disabled
  >
    Creer (bientot)
  </button>
</div>
```

With:
```tsx
<div className="px-6 py-4 border-t border-vault-border flex justify-end gap-3">
  <button
    onClick={() => setShowCreateModal(false)}
    className="px-4 py-2 text-vault-text hover:bg-vault-hover rounded-xl transition-colors"
  >
    Fermer
  </button>
  <button
    className="px-4 py-2 bg-vault-text-muted text-vault-bg rounded-xl cursor-not-allowed opacity-50"
    disabled
  >
    Creer (bientot)
  </button>
</div>
```

**Step 10: Run build to verify no errors**

Run: `cd frontend && npm run build`
Expected: Build succeeds with no TypeScript errors

**Step 11: Commit**

```bash
git add frontend/src/pages/AutoScheduler.tsx
git commit -m "style(AutoScheduler): apply Vault Elegance design system

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"
```

---

## Task 3: Redesign AutoSourcing Page

**Files:**
- Modify: `frontend/src/pages/AutoSourcing.tsx`

**Step 1: Update page wrapper and header**

Replace:
```tsx
<div className="min-h-screen bg-gray-50 p-8">
  <div className="max-w-7xl mx-auto space-y-8">
    <div className="flex items-center justify-between">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">AutoSourcing</h1>
        <p className="text-gray-500 mt-1">
          Decouverte automatique et analyse de produits
        </p>
      </div>
      <div className="text-sm text-gray-400">
        Phase 6 * E2E Testing
      </div>
    </div>
```

With:
```tsx
<div className="min-h-screen bg-vault-bg">
  <div className="max-w-7xl mx-auto p-4 md:p-8 space-y-6 md:space-y-8">
    <div className="flex items-center justify-between">
      <div>
        <h1 className="text-3xl md:text-5xl font-display font-semibold text-vault-text tracking-tight">
          AutoSourcing
        </h1>
        <p className="text-vault-text-secondary text-sm md:text-base mt-2">
          Decouverte automatique et analyse de produits
        </p>
      </div>
    </div>
```

**Step 2: Update tabs navigation**

Replace:
```tsx
<div className="border-b border-gray-200">
  <nav className="-mb-px flex space-x-8">
    <button
      onClick={() => setActiveTab('jobs')}
      className={`${
        activeTab === 'jobs'
          ? 'border-blue-500 text-blue-600'
          : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
      } whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm`}
    >
```

With:
```tsx
<div className="border-b border-vault-border">
  <nav className="-mb-px flex space-x-8">
    <button
      onClick={() => setActiveTab('jobs')}
      className={`${
        activeTab === 'jobs'
          ? 'border-vault-accent text-vault-accent'
          : 'border-transparent text-vault-text-muted hover:text-vault-text hover:border-vault-border'
      } whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm transition-colors`}
    >
```

**Step 3: Update error alerts**

Replace:
```tsx
{error && (
  <div className="bg-red-50 border border-red-200 rounded-lg p-4">
    <p className="text-red-800 text-sm">{error}</p>
  </div>
)}
```

With:
```tsx
{error && (
  <div className="bg-vault-danger-light border border-vault-danger/20 rounded-2xl p-4">
    <p className="text-vault-danger text-sm">{error}</p>
  </div>
)}
```

**Step 4: Update Jobs tab header and button**

Replace:
```tsx
<div className="flex justify-between items-center">
  <h2 className="text-xl font-semibold text-gray-900">Jobs Recents</h2>
  <button
    onClick={() => setIsModalOpen(true)}
    data-testid="new-job-button"
    className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-medium"
  >
```

With:
```tsx
<div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
  <h2 className="text-xl md:text-2xl font-display font-semibold text-vault-text">Jobs Recents</h2>
  <button
    onClick={() => setIsModalOpen(true)}
    data-testid="new-job-button"
    className="px-6 py-3 bg-vault-accent text-white rounded-xl hover:bg-vault-accent-hover font-medium transition-colors"
  >
```

**Step 5: Update jobs list container**

Replace:
```tsx
<div className="bg-white rounded-lg shadow-md">
  <div className="p-6">
    {jobs.length === 0 ? (
      <div data-testid="empty-jobs" className="text-center py-12">
        <p className="text-gray-500">Aucun job trouve. Creez votre premiere recherche!</p>
      </div>
```

With:
```tsx
<div className="bg-vault-card rounded-2xl shadow-vault-sm border border-vault-border">
  <div className="p-6">
    {jobs.length === 0 ? (
      <div data-testid="empty-jobs" className="text-center py-12">
        <p className="text-vault-text-secondary">Aucun job trouve. Creez votre premiere recherche!</p>
      </div>
```

**Step 6: Update job cards**

Replace:
```tsx
<div
  key={job.id}
  data-testid="job-card"
  className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50 cursor-pointer"
  onClick={() => handleViewJobResults(job.id)}
>
  <div className="flex justify-between items-start">
    <div className="flex-1">
      <h3 data-testid="job-name" className="font-semibold text-gray-900">
        {job.profile_name}
      </h3>
      <p data-testid="job-id" className="text-sm text-gray-500">
```

With:
```tsx
<div
  key={job.id}
  data-testid="job-card"
  className="border border-vault-border rounded-xl p-4 md:p-6 hover:bg-vault-hover cursor-pointer transition-colors"
  onClick={() => handleViewJobResults(job.id)}
>
  <div className="flex justify-between items-start">
    <div className="flex-1">
      <h3 data-testid="job-name" className="font-semibold text-vault-text">
        {job.profile_name}
      </h3>
      <p data-testid="job-id" className="text-sm text-vault-text-muted">
```

**Step 7: Update job status badges**

Replace:
```tsx
<span
  data-testid="job-status"
  className={`inline-block px-3 py-1 rounded-full text-sm font-medium ${
    job.status === 'COMPLETED'
      ? 'bg-green-100 text-green-800'
      : job.status === 'RUNNING'
      ? 'bg-blue-100 text-blue-800'
      : 'bg-gray-100 text-gray-800'
  }`}
>
```

With:
```tsx
<span
  data-testid="job-status"
  className={`inline-block px-3 py-1 rounded-full text-sm font-medium ${
    job.status === 'COMPLETED'
      ? 'bg-vault-success-light text-vault-success'
      : job.status === 'RUNNING'
      ? 'bg-vault-accent-light text-vault-accent'
      : 'bg-vault-hover text-vault-text-muted'
  }`}
>
```

Also update:
```tsx
<p className="text-sm text-gray-600 mt-2">
```
With:
```tsx
<p className="text-sm text-vault-text-secondary mt-2">
```

**Step 8: Update selected job results container**

Replace:
```tsx
<div className="bg-white rounded-lg shadow-md">
  <div className="p-6 border-b border-gray-200">
    <h2 className="text-xl font-semibold text-gray-900">
```

With:
```tsx
<div className="bg-vault-card rounded-2xl shadow-vault-sm border border-vault-border">
  <div className="p-6 border-b border-vault-border">
    <h2 className="text-xl font-display font-semibold text-vault-text">
```

**Step 9: Update pick cards**

Replace:
```tsx
<div
  key={pick.id}
  data-testid="pick"
  className="border border-gray-200 rounded-lg p-4"
>
  <div className="flex justify-between items-start">
    <div className="flex-1">
      <h4 data-testid="pick-title" className="font-semibold text-gray-900">
        {pick.title}
      </h4>
      <p data-testid="pick-asin" className="text-sm text-gray-500">
```

With:
```tsx
<div
  key={pick.id}
  data-testid="pick"
  className="border border-vault-border rounded-xl p-4"
>
  <div className="flex justify-between items-start">
    <div className="flex-1">
      <h4 data-testid="pick-title" className="font-semibold text-vault-text">
        {pick.title}
      </h4>
      <p data-testid="pick-asin" className="text-sm text-vault-text-muted">
```

**Step 10: Update pick metrics colors**

Replace:
```tsx
<span className="text-green-600">{pick.roi_percentage.toFixed(1)}%</span>
<span className="text-blue-600">{pick.velocity_score}</span>
<span className="text-purple-600">{pick.confidence_score}</span>
<span className="text-gray-700">{pick.overall_rating}</span>
```

With:
```tsx
<span className="text-vault-success">{pick.roi_percentage.toFixed(1)}%</span>
<span className="text-vault-accent">{pick.velocity_score}</span>
<span className="text-vault-accent">{pick.confidence_score}</span>
<span className="text-vault-text">{pick.overall_rating}</span>
```

**Step 11: Update Analyze tab form card**

Replace:
```tsx
<div className="bg-white rounded-xl shadow-md p-6 space-y-4">
  <div>
    <label className="block text-sm font-medium text-gray-700 mb-2">
      ASINs / ISBNs a analyser
    </label>
    <textarea
      className="w-full h-32 px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent resize-none"
```

With:
```tsx
<div className="bg-vault-card rounded-2xl shadow-vault-sm border border-vault-border p-6 space-y-4">
  <div>
    <label className="block text-sm font-medium text-vault-text-secondary mb-2">
      ASINs / ISBNs a analyser
    </label>
    <textarea
      className="w-full h-32 px-4 py-3 border border-vault-border bg-vault-bg text-vault-text rounded-xl focus:ring-2 focus:ring-vault-accent focus:border-transparent resize-none"
```

**Step 12: Update strategy select**

Replace:
```tsx
<label className="block text-sm font-medium text-gray-700 mb-2">
  Strategie de boost (optionnel)
</label>
<select
  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
```

With:
```tsx
<label className="block text-sm font-medium text-vault-text-secondary mb-2">
  Strategie de boost (optionnel)
</label>
<select
  className="w-full px-4 py-2 border border-vault-border bg-vault-bg text-vault-text rounded-xl focus:ring-2 focus:ring-vault-accent focus:border-transparent"
```

**Step 13: Update action buttons**

Replace:
```tsx
<button
  onClick={handleAnalyze}
  disabled={loading}
  className="flex-1 bg-purple-600 hover:bg-purple-700 disabled:bg-gray-400 text-white font-medium py-3 px-6 rounded-lg transition-colors duration-200"
>
  {loading ? 'Analyse en cours...' : 'Analyser avec scoring Velocity prioritaire'}
</button>
<button
  onClick={handleClear}
  disabled={loading}
  className="px-6 py-3 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors duration-200"
>
  Effacer
</button>
```

With:
```tsx
<button
  onClick={handleAnalyze}
  disabled={loading}
  className="flex-1 bg-vault-accent hover:bg-vault-accent-hover disabled:bg-vault-text-muted text-white font-medium py-3 px-6 rounded-xl transition-colors duration-200"
>
  {loading ? 'Analyse en cours...' : 'Analyser avec scoring Velocity prioritaire'}
</button>
<button
  onClick={handleClear}
  disabled={loading}
  className="px-6 py-3 border border-vault-border text-vault-text rounded-xl hover:bg-vault-hover transition-colors duration-200"
>
  Effacer
</button>
```

**Step 14: Update info box**

Replace:
```tsx
<div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
  <h3 className="text-sm font-semibold text-purple-900 mb-2">
    Scoring AutoSourcing (Phase 2)
  </h3>
  <ul className="text-sm text-purple-800 space-y-1">
```

With:
```tsx
<div className="bg-vault-accent-light border border-vault-accent/20 rounded-2xl p-4">
  <h3 className="text-sm font-semibold text-vault-accent mb-2">
    Scoring AutoSourcing
  </h3>
  <ul className="text-sm text-vault-text-secondary space-y-1">
```

**Step 15: Run build to verify no errors**

Run: `cd frontend && npm run build`
Expected: Build succeeds with no TypeScript errors

**Step 16: Commit**

```bash
git add frontend/src/pages/AutoSourcing.tsx
git commit -m "style(AutoSourcing): apply Vault Elegance design system

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"
```

---

## Task 4: Redesign RechercheDetail Page

**Files:**
- Modify: `frontend/src/pages/RechercheDetail.tsx`

**Step 1: Update loading state**

Replace:
```tsx
<div className="min-h-screen bg-gray-50 p-8">
  <div className="max-w-7xl mx-auto">
    <div className="flex items-center justify-center py-12">
      <Loader2 className="w-8 h-8 animate-spin text-purple-600" />
      <span className="ml-3 text-gray-600">
```

With:
```tsx
<div className="min-h-screen bg-vault-bg p-4 md:p-8">
  <div className="max-w-7xl mx-auto">
    <div className="flex items-center justify-center py-12">
      <div className="animate-spin h-12 w-12 border-4 border-vault-accent border-t-transparent rounded-full"></div>
      <span className="ml-4 text-vault-text-secondary">
```

**Step 2: Update error state back button**

Replace:
```tsx
<button
  onClick={handleBack}
  className="flex items-center gap-2 text-gray-600 hover:text-gray-900 mb-6"
>
```

With:
```tsx
<button
  onClick={handleBack}
  className="flex items-center gap-2 text-vault-text-secondary hover:text-vault-text mb-6 transition-colors"
>
```

**Step 3: Update error state alert**

Replace:
```tsx
<div className="bg-red-50 border border-red-200 rounded-lg p-4">
  <p className="text-red-800">
```

With:
```tsx
<div className="bg-vault-danger-light border border-vault-danger/20 rounded-2xl p-4">
  <p className="text-vault-danger">
```

**Step 4: Update not found state**

Replace:
```tsx
<div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
  <p className="text-yellow-800">Recherche non trouvee ou expiree.</p>
</div>
```

With:
```tsx
<div className="bg-vault-warning-light border border-vault-warning/20 rounded-2xl p-4">
  <p className="text-vault-warning">Recherche non trouvee ou expiree.</p>
</div>
```

**Step 5: Update main page wrapper**

Replace:
```tsx
<div className="min-h-screen bg-gray-50 p-8">
  <div className="max-w-7xl mx-auto space-y-6">
    {/* Back button */}
    <button
      onClick={handleBack}
      className="flex items-center gap-2 text-gray-600 hover:text-gray-900"
    >
```

With:
```tsx
<div className="min-h-screen bg-vault-bg p-4 md:p-8">
  <div className="max-w-7xl mx-auto space-y-6">
    {/* Back button */}
    <button
      onClick={handleBack}
      className="flex items-center gap-2 text-vault-text-secondary hover:text-vault-text transition-colors"
    >
```

**Step 6: Update header card**

Replace:
```tsx
<div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
```

With:
```tsx
<div className="bg-vault-card rounded-2xl shadow-vault-sm border border-vault-border p-6">
```

**Step 7: Update edit form styling**

Replace:
```tsx
<label className="block text-sm font-medium text-gray-700 mb-1">
  Nom
</label>
<input
  type="text"
  value={editName}
  onChange={(e) => setEditName(e.target.value)}
  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
```

With:
```tsx
<label className="block text-sm font-medium text-vault-text-secondary mb-1">
  Nom
</label>
<input
  type="text"
  value={editName}
  onChange={(e) => setEditName(e.target.value)}
  className="w-full px-4 py-2 border border-vault-border bg-vault-bg text-vault-text rounded-xl focus:ring-2 focus:ring-vault-accent focus:border-transparent"
```

Do the same for textarea:
```tsx
<label className="block text-sm font-medium text-vault-text-secondary mb-1">
<textarea
  ...
  className="w-full px-4 py-2 border border-vault-border bg-vault-bg text-vault-text rounded-xl focus:ring-2 focus:ring-vault-accent focus:border-transparent"
```

**Step 8: Update edit form buttons**

Replace:
```tsx
<button
  onClick={handleSaveEdit}
  disabled={isUpdating || !editName.trim()}
  className="flex items-center gap-2 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50"
>
...
<button
  onClick={handleCancelEdit}
  disabled={isUpdating}
  className="flex items-center gap-2 px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200"
>
```

With:
```tsx
<button
  onClick={handleSaveEdit}
  disabled={isUpdating || !editName.trim()}
  className="flex items-center gap-2 px-4 py-2 bg-vault-accent text-white rounded-xl hover:bg-vault-accent-hover disabled:opacity-50 transition-colors"
>
...
<button
  onClick={handleCancelEdit}
  disabled={isUpdating}
  className="flex items-center gap-2 px-4 py-2 bg-vault-hover text-vault-text rounded-xl hover:bg-vault-border transition-colors"
>
```

**Step 9: Update display mode header**

Replace:
```tsx
<span className="text-sm text-gray-400">ID: {data.id.slice(0, 8)}...</span>
<h1 className="text-2xl font-bold text-gray-900">{data.name}</h1>
{data.notes && (
  <p className="text-gray-600 mt-2">{data.notes}</p>
)}
<div className="flex items-center gap-6 mt-4 text-sm text-gray-500">
```

With:
```tsx
<span className="text-sm text-vault-text-muted">ID: {data.id.slice(0, 8)}...</span>
<h1 className="text-2xl md:text-3xl font-display font-semibold text-vault-text">{data.name}</h1>
{data.notes && (
  <p className="text-vault-text-secondary mt-2">{data.notes}</p>
)}
<div className="flex flex-wrap items-center gap-4 md:gap-6 mt-4 text-sm text-vault-text-muted">
```

**Step 10: Update action buttons**

Replace:
```tsx
<button
  onClick={handleStartEdit}
  className="flex items-center gap-2 px-3 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200"
>
  <Edit2 className="w-4 h-4" />
  Modifier
</button>
<button
  onClick={handleDelete}
  disabled={isDeleting}
  className="flex items-center gap-2 px-3 py-2 text-red-600 bg-red-50 rounded-lg hover:bg-red-100 disabled:opacity-50"
>
```

With:
```tsx
<button
  onClick={handleStartEdit}
  className="flex items-center gap-2 px-4 py-2 text-vault-text bg-vault-hover rounded-xl hover:bg-vault-border transition-colors"
>
  <Edit2 className="w-4 h-4" />
  Modifier
</button>
<button
  onClick={handleDelete}
  disabled={isDeleting}
  className="flex items-center gap-2 px-4 py-2 text-vault-danger bg-vault-danger-light rounded-xl hover:bg-vault-danger/20 disabled:opacity-50 transition-colors"
>
```

**Step 11: Update products table container**

Replace:
```tsx
<div className="bg-white rounded-lg shadow-sm border border-gray-200">
  <div className="p-4 border-b border-gray-200">
    <h2 className="text-lg font-semibold text-gray-900">
      Produits ({data.product_count})
    </h2>
  </div>
```

With:
```tsx
<div className="bg-vault-card rounded-2xl shadow-vault-sm border border-vault-border">
  <div className="p-4 md:p-6 border-b border-vault-border">
    <h2 className="text-lg font-display font-semibold text-vault-text">
      Produits ({data.product_count})
    </h2>
  </div>
```

**Step 12: Update empty products message**

Replace:
```tsx
<div className="p-8 text-center text-gray-500">
  Aucun produit dans cette recherche.
</div>
```

With:
```tsx
<div className="p-8 text-center text-vault-text-muted">
  Aucun produit dans cette recherche.
</div>
```

**Step 13: Update SourceBadge colors**

Replace:
```tsx
const colorClasses: Record<string, string> = {
  purple: 'bg-purple-100 text-purple-800',
  blue: 'bg-blue-100 text-blue-800',
  green: 'bg-green-100 text-green-800',
}
```

With:
```tsx
const colorClasses: Record<string, string> = {
  purple: 'bg-vault-accent-light text-vault-accent',
  blue: 'bg-vault-accent-light text-vault-accent',
  green: 'bg-vault-success-light text-vault-success',
}
```

Also update fallback:
```tsx
const classes = colorClasses[color] || 'bg-vault-hover text-vault-text-muted'
```

**Step 14: Run build to verify no errors**

Run: `cd frontend && npm run build`
Expected: Build succeeds with no TypeScript errors

**Step 15: Commit**

```bash
git add frontend/src/pages/RechercheDetail.tsx
git commit -m "style(RechercheDetail): apply Vault Elegance design system

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"
```

---

## Task 5: Update MesRecherches Page (Bonus - Consistency)

**Files:**
- Modify: `frontend/src/pages/MesRecherches.tsx`

**Note:** Cette page utilise deja certains patterns mais pas le design system complet. Mise a jour pour coherence.

**Step 1: Update page wrapper**

Replace:
```tsx
<div className="min-h-screen bg-gray-50 p-8">
  <div className="max-w-6xl mx-auto space-y-6">
```

With:
```tsx
<div className="min-h-screen bg-vault-bg">
  <div className="max-w-7xl mx-auto p-4 md:p-8 space-y-6 md:space-y-8">
```

**Step 2: Update header**

Replace:
```tsx
<h1 className="text-3xl font-bold text-gray-900">
  Mes Recherches
</h1>
<p className="text-gray-600 mt-2">
```

With:
```tsx
<h1 className="text-3xl md:text-5xl font-display font-semibold text-vault-text tracking-tight">
  Mes Recherches
</h1>
<p className="text-vault-text-secondary text-sm md:text-base mt-2">
```

Remove phase indicator:
```tsx
<div className="text-sm text-gray-400">Phase 11</div>
```

**Step 3: Update stats cards**

Replace:
```tsx
<div className="grid grid-cols-4 gap-4">
  <div className="bg-white rounded-lg p-4 shadow-sm border">
    <div className="text-2xl font-bold text-gray-900">{stats.total}</div>
    <div className="text-sm text-gray-500">Total</div>
  </div>
  <div className="bg-purple-50 rounded-lg p-4 shadow-sm border border-purple-100">
```

With:
```tsx
<div className="grid grid-cols-2 md:grid-cols-4 gap-4">
  <div className="bg-vault-card rounded-2xl p-4 shadow-vault-sm border border-vault-border">
    <div className="text-2xl font-bold text-vault-text">{stats.total}</div>
    <div className="text-sm text-vault-text-secondary">Total</div>
  </div>
  <div className="bg-vault-accent-light rounded-2xl p-4 shadow-vault-sm border border-vault-accent/20">
```

Update other stat cards similarly with vault colors.

**Step 4: Update filter buttons**

Replace:
```tsx
<button
  key={btn.label}
  onClick={() => setSourceFilter(btn.value)}
  className={`px-3 py-1.5 text-sm rounded-full transition-colors ${
    sourceFilter === btn.value
      ? 'bg-purple-600 text-white'
      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
  }`}
>
```

With:
```tsx
<button
  key={btn.label}
  onClick={() => setSourceFilter(btn.value)}
  className={`px-4 py-2 text-sm rounded-xl transition-colors ${
    sourceFilter === btn.value
      ? 'bg-vault-accent text-white'
      : 'bg-vault-card text-vault-text-secondary border border-vault-border hover:bg-vault-hover'
  }`}
>
```

**Step 5: Update loading state**

Replace:
```tsx
<Loader2 className="w-8 h-8 animate-spin text-purple-600" />
<span className="ml-3 text-gray-600">
```

With:
```tsx
<div className="animate-spin h-12 w-12 border-4 border-vault-accent border-t-transparent rounded-full"></div>
<span className="ml-4 text-vault-text-secondary">
```

**Step 6: Update error state**

Replace:
```tsx
<div className="bg-red-50 border border-red-200 rounded-lg p-4">
  <p className="text-red-800">
```

With:
```tsx
<div className="bg-vault-danger-light border border-vault-danger/20 rounded-2xl p-4">
  <p className="text-vault-danger">
```

**Step 7: Update empty state**

Replace:
```tsx
<div className="bg-white rounded-lg shadow-md p-12 text-center">
  <Inbox className="w-16 h-16 text-gray-400 mx-auto mb-4" />
  <h2 className="text-xl font-semibold text-gray-700 mb-2">
```

With:
```tsx
<div className="bg-vault-card rounded-2xl shadow-vault-sm border border-vault-border p-12 text-center">
  <Inbox className="w-16 h-16 text-vault-text-muted mx-auto mb-4" />
  <h2 className="text-xl font-display font-semibold text-vault-text mb-2">
```

**Step 8: Update CTA buttons in empty state**

Replace:
```tsx
<a
  href="/niche-discovery"
  className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors"
>
<a
  href="/autosourcing"
  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
>
```

With:
```tsx
<a
  href="/niche-discovery"
  className="px-6 py-3 bg-vault-accent text-white rounded-xl hover:bg-vault-accent-hover transition-colors font-medium"
>
<a
  href="/autosourcing"
  className="px-6 py-3 bg-vault-card text-vault-accent border border-vault-border rounded-xl hover:bg-vault-hover transition-colors font-medium"
>
```

**Step 9: Update results counter**

Replace:
```tsx
<div className="text-sm text-gray-500">
```

With:
```tsx
<div className="text-sm text-vault-text-secondary">
```

**Step 10: Update SearchResultCard**

Replace:
```tsx
<div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 hover:shadow-md transition-shadow">
```

With:
```tsx
<div className="bg-vault-card rounded-2xl shadow-vault-sm border border-vault-border p-4 md:p-6 hover:shadow-vault-md transition-shadow">
```

Update text colors:
```tsx
<span className="text-xs text-vault-text-muted">
<h3 className="text-lg font-semibold text-vault-text truncate">
<span className="flex items-center gap-1 text-vault-text-secondary">
<p className="text-sm text-vault-text-muted mt-2 truncate">{result.notes}</p>
```

Update action buttons:
```tsx
<button
  onClick={() => onView(result.id)}
  className="p-2 text-vault-accent hover:bg-vault-accent-light rounded-xl transition-colors"
  title="Voir les resultats"
>
<button
  onClick={() => onDelete(result.id)}
  disabled={isDeleting}
  className="p-2 text-vault-danger hover:bg-vault-danger-light rounded-xl transition-colors disabled:opacity-50"
  title="Supprimer"
>
```

**Step 11: Update SourceBadge**

Replace:
```tsx
const colorClasses: Record<string, string> = {
  purple: 'bg-purple-100 text-purple-800',
  blue: 'bg-blue-100 text-blue-800',
  green: 'bg-green-100 text-green-800',
}
```

With:
```tsx
const colorClasses: Record<string, string> = {
  purple: 'bg-vault-accent-light text-vault-accent',
  blue: 'bg-vault-accent-light text-vault-accent',
  green: 'bg-vault-success-light text-vault-success',
}
```

**Step 12: Update Load More button**

Replace:
```tsx
<button
  onClick={() => fetchNextPage()}
  disabled={isFetchingNextPage}
  className="flex items-center gap-2 px-6 py-3 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 disabled:opacity-50 transition-colors"
>
```

With:
```tsx
<button
  onClick={() => fetchNextPage()}
  disabled={isFetchingNextPage}
  className="flex items-center gap-2 px-6 py-3 bg-vault-card text-vault-text border border-vault-border rounded-xl hover:bg-vault-hover disabled:opacity-50 transition-colors"
>
```

**Step 13: Run build to verify no errors**

Run: `cd frontend && npm run build`
Expected: Build succeeds with no TypeScript errors

**Step 14: Commit**

```bash
git add frontend/src/pages/MesRecherches.tsx
git commit -m "style(MesRecherches): apply Vault Elegance design system

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"
```

---

## Final Verification

**Step 1: Run full build**

Run: `cd frontend && npm run build`
Expected: Build succeeds

**Step 2: Run linter**

Run: `cd frontend && npm run lint`
Expected: No errors

**Step 3: Visual inspection (manual)**

Start dev server and verify each page visually:
- MesNiches: Vault colors, rounded cards, proper typography
- AutoScheduler: Warning banner styled, cards styled, modal styled
- AutoSourcing: Tabs styled, job cards styled, form styled
- RechercheDetail: Header card styled, edit mode styled
- MesRecherches: Stats cards styled, result cards styled

**Step 4: Final commit with all changes**

```bash
git add -A
git commit -m "style: complete Vault Elegance redesign for remaining pages

Pages updated:
- MesNiches
- AutoScheduler
- AutoSourcing
- RechercheDetail
- MesRecherches (consistency update)

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"
```

---

## Summary

| Task | Page | Complexity | Changes |
|------|------|------------|---------|
| 1 | MesNiches | Simple | 8 steps |
| 2 | AutoScheduler | Simple | 11 steps |
| 3 | AutoSourcing | Medium | 16 steps |
| 4 | RechercheDetail | Simple | 15 steps |
| 5 | MesRecherches | Bonus | 14 steps |

**Total estimated steps:** ~64 individual code changes
**Parallelization opportunity:** Tasks 1-5 are independent and can be executed in parallel by separate agents.
