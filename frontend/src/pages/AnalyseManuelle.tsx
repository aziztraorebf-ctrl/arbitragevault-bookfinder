import { useState, useRef, useMemo, type ChangeEvent } from 'react';
import { keepaService } from '../services/keepaService';
import type { IngestResponse } from '../types/keepa';
import ProgressBar from '../components/ProgressBar';
import { UnifiedProductTable, useVerification, AccordionContent } from '../components/unified';
import { normalizeProductScore } from '../types/unified';
import { batchResultsToProductScores } from '../utils/analysisAdapter';
import { SaveSearchButton } from '../components/recherches/SaveSearchButton';
import { Upload, CheckCircle, Play, ChevronDown, FileCheck, AlertCircle } from 'lucide-react';

export default function AnalyseManuelle() {
  // Etats principaux
  const [asins, setAsins] = useState<string[]>([]);
  const [asinInput, setAsinInput] = useState('');
  const [csvFile, setCsvFile] = useState<File | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [progressStatus, setProgressStatus] = useState<'idle' | 'loading' | 'success' | 'error'>('idle');
  const [progressMessage, setProgressMessage] = useState('');
  const [results, setResults] = useState<IngestResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isDragOver, setIsDragOver] = useState(false);

  // Configuration
  const [strategy, setStrategy] = useState<'balanced' | 'aggressive' | 'conservative'>('balanced');
  const [minROI, setMinROI] = useState(30);
  const [maxBSR, setMaxBSR] = useState(50000);
  const [minVelocity, setMinVelocity] = useState(10);

  // Reference pour l'input file
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Gestionnaire Drag & Drop
  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(false);
  };

  const handleDrop = async (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(false);

    const files = Array.from(e.dataTransfer.files);
    const csvFile = files.find(f => f.name.endsWith('.csv'));

    if (csvFile) {
      await handleCSVFile(csvFile);
    } else {
      showError('Veuillez deposer un fichier CSV valide');
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
        showError('Aucun ASIN valide trouve dans le fichier CSV');
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
      showError('Aucun ASIN valide trouve. Verifiez le format (10 ou 13 caracteres)');
      return;
    }

    setAsins(extractedAsins);
    showSuccess(`${extractedAsins.length} ASINs valides`);
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
      // Configuration mappee vers le backend
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
          setProgressMessage(`Traitement des produits ${i + 1} a ${Math.min(i + CHUNK_SIZE, asins.length)}...`);

          const response = await keepaService.ingestBatch({
            identifiers: chunk,
            config_profile: configProfile
          });

          // Fusionner les resultats
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
      setProgressMessage('Analyse terminee avec succes !');
      setResults(allResults);

      // Log pour debug
      console.log('Resultats recus:', allResults);
      console.log('Nombre de resultats:', allResults?.results?.length);

      // Masquer la barre de progression apres 2 secondes
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
    // On pourrait ajouter un toast de succes plus tard
    console.log('Success:', message);
  };

  // Verification hook
  const {
    verifyProduct,
    getVerificationState,
    isVerificationExpanded,
    toggleVerificationExpansion,
  } = useVerification();

  // Convertir les resultats Keepa en ProductScore puis normaliser pour UnifiedProductTable
  const normalizedProducts = useMemo(() => {
    if (!results) return [];
    const productScores = batchResultsToProductScores(results.results);
    return productScores.map(normalizeProductScore);
  }, [results]);

  return (
    <div className="space-y-8 animate-fade-in">
      {/* ========================================
          HEADER SECTION
          ======================================== */}
      <section className="mb-8">
        <h1 className="text-4xl md:text-5xl font-display font-semibold text-vault-text mb-2 tracking-tight">
          Analyse Manuelle
        </h1>
        <p className="text-sm md:text-base text-vault-text-secondary">
          Importez vos ASINs ou un fichier CSV pour lancer une analyse approfondie
        </p>
      </section>

      {/* Toast d'erreur */}
      {error && (
        <div className="fixed bottom-4 right-4 bg-red-500 text-white px-4 py-3 rounded-xl shadow-vault-lg z-50 flex items-center gap-3 animate-fade-in">
          <AlertCircle className="w-5 h-5" />
          <span>{error}</span>
        </div>
      )}

      {/* ========================================
          INPUT ZONES
          ======================================== */}
      <section className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Carte Drag & Drop CSV */}
        <div
          className={`
            bg-vault-card border-2 border-dashed rounded-2xl p-8
            flex flex-col items-center justify-center min-h-[240px]
            cursor-pointer transition-all duration-200
            ${isDragOver
              ? 'border-vault-accent bg-vault-accent/5'
              : 'border-vault-border-light hover:border-vault-accent'
            }
            ${csvFile ? 'border-solid border-vault-accent/50' : ''}
          `}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
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
            {csvFile ? (
              <FileCheck className="w-12 h-12 text-vault-accent mx-auto" />
            ) : (
              <Upload className={`w-12 h-12 mx-auto transition-colors ${isDragOver ? 'text-vault-accent' : 'text-vault-text-muted'}`} />
            )}
            <div>
              <p className="text-lg font-semibold text-vault-text mb-1">
                {csvFile ? csvFile.name : 'Drag & Drop CSV ici'}
              </p>
              <p className="text-sm text-vault-text-secondary">
                {csvFile ? `${asins.length} ASINs charges` : 'ou cliquez pour selectionner'}
              </p>
            </div>
          </div>
        </div>

        {/* Carte Liste ASINs */}
        <div className="bg-vault-card border border-vault-border rounded-2xl p-6 shadow-vault-sm flex flex-col gap-4">
          <label className="text-sm font-medium text-vault-text">
            Coller une liste d'ASINs separes par virgule
          </label>
          <textarea
            value={asinInput}
            onChange={(e) => setAsinInput(e.target.value)}
            className="
              w-full min-h-[120px] px-4 py-3
              bg-vault-bg border border-vault-border rounded-xl
              text-vault-text placeholder:text-vault-text-muted
              focus:ring-2 focus:ring-vault-accent focus:border-transparent
              resize-none transition-all duration-200
            "
            placeholder="B08PGW1HW, B07FZ8C718,&#10;B06XG1NVFW, B07FZW57AR..."
          />
          <button
            onClick={handleValidateASINs}
            disabled={!asinInput.trim() || isLoading}
            className="
              bg-vault-accent text-white font-medium px-6 py-3 rounded-xl
              hover:bg-vault-accent-dark transition-colors duration-200
              disabled:bg-vault-border disabled:text-vault-text-muted disabled:cursor-not-allowed
            "
          >
            Valider ASINs
          </button>
        </div>
      </section>

      {/* ========================================
          FEEDBACK BANNER
          ======================================== */}
      {asins.length > 0 && (
        <div className="bg-vault-accent-light border border-vault-accent/20 rounded-xl px-4 py-3 flex items-center gap-3 animate-fade-in">
          <CheckCircle className="w-5 h-5 text-vault-accent flex-shrink-0" />
          <span className="text-sm font-medium text-vault-accent">
            {asins.length} ASINs valides et prets pour l'analyse
          </span>
        </div>
      )}

      {/* ========================================
          CONFIGURATION SECTION
          ======================================== */}
      <section className="bg-vault-card border border-vault-border rounded-2xl p-6 shadow-vault-sm">
        <h2 className="text-lg font-semibold text-vault-text mb-6">
          Configuration Analyse
        </h2>

        <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
          {/* Strategie primaire */}
          <div className="flex flex-col gap-2">
            <label className="text-sm font-medium text-vault-text-secondary">
              Strategie primaire
            </label>
            <div className="relative">
              <select
                value={strategy}
                onChange={(e) => {
                  const newStrategy = e.target.value as 'balanced' | 'aggressive' | 'conservative';
                  setStrategy(newStrategy);

                  // Ajuster automatiquement les valeurs selon la strategie
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
                className="
                  w-full px-4 py-3 pr-10
                  bg-vault-bg border border-vault-border rounded-xl
                  text-vault-text appearance-none cursor-pointer
                  focus:ring-2 focus:ring-vault-accent focus:border-transparent
                  transition-all duration-200
                "
              >
                <option value="balanced">Balanced</option>
                <option value="aggressive">Aggressive</option>
                <option value="conservative">Conservative</option>
              </select>
              <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-vault-text-muted pointer-events-none" />
            </div>
          </div>

          {/* ROI minimum */}
          <div className="flex flex-col gap-2">
            <label className="text-sm font-medium text-vault-text-secondary">
              ROI minimum [%]
            </label>
            <input
              type="number"
              value={minROI}
              onChange={(e) => setMinROI(Number(e.target.value))}
              className="
                w-full px-4 py-3
                bg-vault-bg border border-vault-border rounded-xl
                text-vault-text
                focus:ring-2 focus:ring-vault-accent focus:border-transparent
                transition-all duration-200
              "
              placeholder="30"
            />
          </div>

          {/* BSR maximum */}
          <div className="flex flex-col gap-2">
            <label className="text-sm font-medium text-vault-text-secondary">
              BSR maximum
            </label>
            <input
              type="number"
              value={maxBSR}
              onChange={(e) => setMaxBSR(Number(e.target.value))}
              className="
                w-full px-4 py-3
                bg-vault-bg border border-vault-border rounded-xl
                text-vault-text
                focus:ring-2 focus:ring-vault-accent focus:border-transparent
                transition-all duration-200
              "
              placeholder="50000"
            />
          </div>

          {/* Velocity min */}
          <div className="flex flex-col gap-2">
            <label className="text-sm font-medium text-vault-text-secondary">
              Velocity min.
            </label>
            <input
              type="number"
              value={minVelocity}
              onChange={(e) => setMinVelocity(Number(e.target.value))}
              className="
                w-full px-4 py-3
                bg-vault-bg border border-vault-border rounded-xl
                text-vault-text
                focus:ring-2 focus:ring-vault-accent focus:border-transparent
                transition-all duration-200
              "
              placeholder="10"
            />
          </div>
        </div>

        {/* Checkboxes */}
        <div className="flex flex-wrap gap-6 mt-6">
          <label className="flex items-center gap-2 text-vault-text-secondary cursor-pointer">
            <input
              type="checkbox"
              className="w-4 h-4 accent-vault-accent rounded"
              disabled
            />
            <span className="text-sm">Analyse multi-strategies</span>
          </label>

          <label className="flex items-center gap-2 text-vault-text-secondary cursor-pointer">
            <input
              type="checkbox"
              className="w-4 h-4 accent-vault-accent rounded"
              disabled
            />
            <span className="text-sm">Verification stock</span>
          </label>

          <label className="flex items-center gap-2 text-vault-text-secondary cursor-pointer">
            <input
              type="checkbox"
              className="w-4 h-4 accent-vault-accent rounded"
              disabled
            />
            <span className="text-sm">Export CSV</span>
          </label>
        </div>
      </section>

      {/* ========================================
          CTA BUTTON
          ======================================== */}
      <div className="flex justify-center">
        <button
          onClick={handleLaunchAnalysis}
          disabled={asins.length === 0 || isLoading}
          className="
            bg-vault-accent hover:bg-vault-accent-dark text-white
            font-medium px-8 py-4 rounded-xl
            shadow-vault-md hover:shadow-vault-lg
            transition-all duration-200
            flex items-center justify-center gap-3
            disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:shadow-vault-md
          "
        >
          <Play className="w-5 h-5" />
          <span className="text-lg">
            {isLoading ? 'Analyse en cours...' : 'Lancer l\'analyse'}
          </span>
        </button>
      </div>

      {/* ========================================
          PROGRESS SECTION
          ======================================== */}
      <ProgressBar
        progress={progress}
        status={progressStatus}
        message={progressMessage}
        itemsProcessed={results?.processed}
        totalItems={asins.length}
      />

      {/* ========================================
          RESULTS SECTION
          ======================================== */}
      {results && results.results.length > 0 && (
        <>
          <div className="flex justify-end mb-4">
            <SaveSearchButton
              products={normalizedProducts}
              source="manual_analysis"
              searchParams={{ strategy, minROI, maxBSR, minVelocity }}
              defaultName={`Analyse ${new Date().toLocaleDateString('fr-FR')}`}
            />
          </div>
          <UnifiedProductTable
            products={normalizedProducts}
            title="Analyse Manuelle - Resultats"
            features={{
              showScore: true,
              showRank: true,
              showAmazonBadges: true,
              showFilters: true,
              showExportCSV: true,
              showFooterSummary: true,
              showAccordion: true,
              showVerifyButton: true,
            }}
            AccordionComponent={AccordionContent}
            onVerify={verifyProduct}
            getVerificationState={getVerificationState}
            isVerificationExpanded={isVerificationExpanded}
            toggleVerificationExpansion={toggleVerificationExpansion}
          />
        </>
      )}
    </div>
  )
}
