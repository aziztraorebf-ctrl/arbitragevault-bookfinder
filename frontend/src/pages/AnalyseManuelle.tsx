import { useState, useRef, type ChangeEvent } from 'react';
import { keepaService } from '../services/keepaService';
import type { IngestResponse } from '../types/keepa';
import ProgressBar from '../components/ProgressBar';
import ResultsTable from '../components/ResultsTable';

export default function AnalyseManuelle() {
  // États principaux
  const [asins, setAsins] = useState<string[]>([]);
  const [asinInput, setAsinInput] = useState('');
  const [csvFile, setCsvFile] = useState<File | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [progressStatus, setProgressStatus] = useState<'idle' | 'loading' | 'success' | 'error'>('idle');
  const [progressMessage, setProgressMessage] = useState('');
  const [results, setResults] = useState<IngestResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Configuration
  const [strategy, setStrategy] = useState<'balanced' | 'aggressive' | 'conservative'>('balanced');
  const [minROI, setMinROI] = useState(30);
  const [maxBSR, setMaxBSR] = useState(50000);
  const [minVelocity, setMinVelocity] = useState(10);

  // Référence pour l'input file
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Gestionnaire Drag & Drop
  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
  };

  const handleDrop = async (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();

    const files = Array.from(e.dataTransfer.files);
    const csvFile = files.find(f => f.name.endsWith('.csv'));

    if (csvFile) {
      await handleCSVFile(csvFile);
    } else {
      showError('Veuillez déposer un fichier CSV valide');
    }
  };

  const handleFileSelect = async (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      await handleCSVFile(file);
    }
  };

  const handleCSVFile = async (file: File) => {
    try {
      setCsvFile(file);
      const extractedAsins = await keepaService.parseCSV(file);

      if (extractedAsins.length === 0) {
        showError('Aucun ASIN valide trouvé dans le fichier CSV');
        return;
      }

      setAsins(extractedAsins);
      showSuccess(`${extractedAsins.length} ASINs extraits du fichier CSV`);
    } catch (err) {
      showError('Erreur lors de la lecture du fichier CSV');
    }
  };

  const handleValidateASINs = () => {
    const extractedAsins = keepaService.extractIdentifiers(asinInput);

    if (extractedAsins.length === 0) {
      showError('Aucun ASIN valide trouvé. Vérifiez le format (10 ou 13 caractères)');
      return;
    }

    setAsins(extractedAsins);
    showSuccess(`${extractedAsins.length} ASINs validés`);
  };

  const handleLaunchAnalysis = async () => {
    if (asins.length === 0) {
      showError('Veuillez d\'abord charger des ASINs via CSV ou saisie manuelle');
      return;
    }

    setIsLoading(true);
    setError(null);
    setResults(null);
    setProgressStatus('loading');
    setProgress(5);
    setProgressMessage('Connexion au serveur Keepa...');

    // Simulation de progression
    const progressInterval = setInterval(() => {
      setProgress(prev => {
        if (prev >= 90) return 90;
        return prev + Math.random() * 10;
      });
    }, 500);

    try {
      // Configuration mappée vers le backend
      const configProfile = strategy === 'balanced' ? 'balanced' :
                           strategy === 'aggressive' ? 'aggressive' :
                           'conservative';

      // Si plus de 100 ASINs, diviser en chunks
      const CHUNK_SIZE = 100;
      let allResults: IngestResponse | null = null;

      if (asins.length > CHUNK_SIZE) {
        setProgressMessage(`Analyse de ${asins.length} produits en ${Math.ceil(asins.length / CHUNK_SIZE)} lots...`);

        for (let i = 0; i < asins.length; i += CHUNK_SIZE) {
          const chunk = asins.slice(i, i + CHUNK_SIZE);
          const chunkProgress = ((i + chunk.length) / asins.length) * 90;
          setProgress(chunkProgress);
          setProgressMessage(`Traitement des produits ${i + 1} à ${Math.min(i + CHUNK_SIZE, asins.length)}...`);

          const response = await keepaService.ingestBatch({
            identifiers: chunk,
            config_profile: configProfile
          });

          // Fusionner les résultats
          if (!allResults) {
            allResults = response;
          } else {
            allResults.results.push(...response.results);
            allResults.total_items += response.total_items;
            allResults.processed += response.processed;
            allResults.successful += response.successful;
            allResults.failed += response.failed;
          }
        }
      } else {
        setProgressMessage(`Analyse de ${asins.length} produits...`);
        allResults = await keepaService.ingestBatch({
          identifiers: asins,
          config_profile: configProfile
        });
      }

      clearInterval(progressInterval);
      setProgress(100);
      setProgressStatus('success');
      setProgressMessage('Analyse terminée avec succès !');
      setResults(allResults);

      // Log pour debug
      console.log('Résultats reçus:', allResults);
      console.log('Nombre de résultats:', allResults?.results?.length);

      // Masquer la barre de progression après 2 secondes
      setTimeout(() => {
        setProgressStatus('idle');
        setProgress(0);
      }, 2000);

    } catch (err) {
      clearInterval(progressInterval);
      setProgress(100);
      setProgressStatus('error');
      setProgressMessage('Erreur lors de l\'analyse');
      showError(err instanceof Error ? err.message : 'Erreur inconnue');
    } finally {
      setIsLoading(false);
    }
  };

  const showError = (message: string) => {
    setError(message);
    setTimeout(() => setError(null), 5000);
  };

  const showSuccess = (message: string) => {
    // Pour l'instant on utilise juste console.log
    // On pourrait ajouter un toast de succès plus tard
    console.log('Success:', message);
  };

  return (
    <div className="max-w-6xl mx-auto space-y-8">
      {/* Titre principal */}
      <h1 className="text-3xl font-bold text-gray-900">
        Analyse manuelle — CSV ou ASIN.
      </h1>

      {/* Toast d'erreur */}
      {error && (
        <div className="fixed bottom-4 right-4 bg-red-500 text-white px-4 py-2 rounded-lg shadow-lg z-50 animate-pulse">
          ⚠️ {error}
        </div>
      )}

      {/* Section Upload CSV / ASINs */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Carte Drag & Drop CSV */}
        <div
          className="bg-white rounded-2xl p-8 border-2 border-dashed border-blue-300 hover:border-blue-500 transition-all duration-200 flex flex-col items-center justify-center min-h-[320px] cursor-pointer group"
          onDragOver={handleDragOver}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept=".csv"
            className="hidden"
            onChange={handleFileSelect}
          />
          <div className="text-center space-y-4">
            <div className="text-6xl mb-4">☁️</div>
            <div>
              <p className="text-lg font-semibold text-gray-700 mb-2">
                {csvFile ? `✅ ${csvFile.name}` : 'Drag & Drop CSV ici'}
              </p>
              <p className="text-sm text-gray-500">
                {csvFile ? `${asins.length} ASINs chargés` : 'ou cliquez pour sélectionner'}
              </p>
            </div>
          </div>
        </div>

        {/* Carte Liste ASINs */}
        <div className="bg-white rounded-2xl p-8 shadow-md flex flex-col gap-4">
          <label className="text-gray-700 font-medium">
            Coller une liste d'ASINs séparés par virgule
          </label>
          <textarea
            value={asinInput}
            onChange={(e) => setAsinInput(e.target.value)}
            className="w-full h-32 p-4 border border-gray-300 rounded-lg resize-none focus:outline-none focus:border-blue-500 text-sm"
            placeholder="B08PGW1HW, B07FZ8C718,&#10;B06XG1NVFW, B07FZW57AR..."
          />
          <button
            onClick={handleValidateASINs}
            disabled={!asinInput.trim() || isLoading}
            className="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white font-semibold rounded-lg px-6 py-3 transition-colors duration-200"
          >
            Valider ASINs
          </button>
        </div>
      </div>

      {/* Indicateur ASINs chargés */}
      {asins.length > 0 && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-4 text-green-800">
          ✅ {asins.length} ASINs prêts pour l'analyse
        </div>
      )}

      {/* Section Configuration Analyse */}
      <div className="bg-white rounded-2xl p-8 shadow-md">
        <h2 className="text-xl font-bold text-gray-900 mb-6">Configuration Analyse</h2>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {/* Stratégie primaire */}
          <div className="flex flex-col gap-2">
            <label className="text-sm font-medium text-gray-700">
              Stratégie primaire
            </label>
            <select
              value={strategy}
              onChange={(e) => {
                const newStrategy = e.target.value as 'balanced' | 'aggressive' | 'conservative';
                setStrategy(newStrategy);

                // Ajuster automatiquement les valeurs selon la stratégie
                switch (newStrategy) {
                  case 'balanced':
                    setMinROI(30);
                    setMaxBSR(50000);
                    setMinVelocity(10);
                    break;
                  case 'aggressive':
                    setMinROI(50);
                    setMaxBSR(10000);
                    setMinVelocity(20);
                    break;
                  case 'conservative':
                    setMinROI(20);
                    setMaxBSR(100000);
                    setMinVelocity(5);
                    break;
                }
              }}
              className="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500"
            >
              <option value="balanced">Balanced</option>
              <option value="aggressive">Aggressive</option>
              <option value="conservative">Conservative</option>
            </select>
          </div>

          {/* ROI minimum */}
          <div className="flex flex-col gap-2">
            <label className="text-sm font-medium text-gray-700">
              ROI minimum [%]
            </label>
            <input
              type="number"
              value={minROI}
              onChange={(e) => setMinROI(Number(e.target.value))}
              className="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500"
              placeholder="30"
            />
          </div>

          {/* BSR maximum */}
          <div className="flex flex-col gap-2">
            <label className="text-sm font-medium text-gray-700">
              BSR maximum
            </label>
            <input
              type="number"
              value={maxBSR}
              onChange={(e) => setMaxBSR(Number(e.target.value))}
              className="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500"
              placeholder="50000"
            />
          </div>

          {/* Velocity min */}
          <div className="flex flex-col gap-2">
            <label className="text-sm font-medium text-gray-700">
              Velocity min.
            </label>
            <input
              type="number"
              value={minVelocity}
              onChange={(e) => setMinVelocity(Number(e.target.value))}
              className="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500"
              placeholder="10"
            />
          </div>
        </div>

        {/* Checkboxes */}
        <div className="flex gap-8 mt-6">
          <label className="flex items-center gap-2 text-gray-700">
            <input
              type="checkbox"
              className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
              disabled
            />
            <span className="text-sm">Analyse multi-stratégies</span>
          </label>

          <label className="flex items-center gap-2 text-gray-700">
            <input
              type="checkbox"
              className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
              disabled
            />
            <span className="text-sm">Vérification stock</span>
          </label>

          <label className="flex items-center gap-2 text-gray-700">
            <input
              type="checkbox"
              className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
              disabled
            />
            <span className="text-sm">Export CSV</span>
          </label>
        </div>
      </div>

      {/* Bouton principal */}
      <div className="flex justify-center">
        <button
          onClick={handleLaunchAnalysis}
          disabled={asins.length === 0 || isLoading}
          className="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white font-bold rounded-lg px-8 py-4 text-lg transition-colors duration-200 flex items-center gap-2"
        >
          <span className="text-xl">🚀</span>
          <span>{isLoading ? 'Analyse en cours...' : 'Lancer analyse'}</span>
        </button>
      </div>

      {/* Section Progression */}
      <ProgressBar
        progress={progress}
        status={progressStatus}
        message={progressMessage}
        itemsProcessed={results?.processed}
        totalItems={asins.length}
      />

      {/* Section Résultats */}
      <ResultsTable data={results} />
    </div>
  )
}