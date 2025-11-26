interface ProgressBarProps {
  progress: number; // 0-100
  status: 'idle' | 'loading' | 'success' | 'error';
  message?: string;
  itemsProcessed?: number;
  totalItems?: number;
}

export default function ProgressBar({
  progress,
  status,
  message,
  itemsProcessed,
  totalItems
}: ProgressBarProps) {
  const getColorClass = () => {
    switch (status) {
      case 'success': return 'bg-green-500';
      case 'error': return 'bg-red-500';
      case 'loading': return 'bg-blue-500';
      default: return 'bg-gray-300';
    }
  };

  const getStatusIcon = () => {
    switch (status) {
      case 'success': return '[OK]';
      case 'error': return '[X]';
      case 'loading': return '[...]';
      default: return '';
    }
  };

  if (status === 'idle') return null;

  return (
    <div className="bg-white rounded-xl p-6 shadow-md space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <span className="text-2xl">{getStatusIcon()}</span>
          <div>
            <p className="text-sm font-medium text-gray-700">
              {message || 'Analyse en cours...'}
            </p>
            {itemsProcessed !== undefined && totalItems !== undefined && (
              <p className="text-xs text-gray-500 mt-1">
                {itemsProcessed} / {totalItems} produits traités
              </p>
            )}
          </div>
        </div>
        <span className="text-lg font-bold text-gray-700">{progress}%</span>
      </div>

      <div className="w-full bg-gray-200 rounded-full h-3 overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-500 ease-out ${getColorClass()}`}
          style={{ width: `${Math.min(100, Math.max(0, progress))}%` }}
        >
          <div className="h-full bg-white/20 animate-pulse"></div>
        </div>
      </div>

      {status === 'loading' && (
        <div className="flex items-center gap-2 text-sm text-gray-600">
          <div className="animate-spin h-4 w-4 border-2 border-blue-500 border-t-transparent rounded-full"></div>
          <span>Connexion à Keepa et analyse des données...</span>
        </div>
      )}

      {status === 'error' && (
        <div className="text-sm text-red-600">
          Une erreur est survenue. Veuillez reessayer.
        </div>
      )}

      {status === 'success' && (
        <div className="text-sm text-green-600">
          Analyse terminee avec succes !
        </div>
      )}
    </div>
  );
}