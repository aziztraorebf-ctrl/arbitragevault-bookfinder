import type { IngestRequest, IngestResponse } from '../types/keepa';

const API_URL = import.meta.env.VITE_API_URL || 'https://arbitragevault-backend-v2.onrender.com';

class KeepaService {
  private baseUrl: string;

  constructor() {
    this.baseUrl = `${API_URL}/api/v1/keepa`;
  }

  /**
   * Analyse un batch d'ASINs/ISBNs
   */
  async ingestBatch(request: IngestRequest): Promise<IngestResponse> {
    const response = await fetch(`${this.baseUrl}/ingest`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      const error = await response.text();
      throw new Error(error || `HTTP ${response.status}: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Valide le format d'un ASIN/ISBN
   */
  validateIdentifier(identifier: string): boolean {
    const cleaned = identifier.trim().replace(/[-\s]/g, '');
    return cleaned.length === 10 || cleaned.length === 13;
  }

  /**
   * Extrait les ASINs d'un texte (séparés par virgules, espaces ou retours à la ligne)
   */
  extractIdentifiers(text: string): string[] {
    return text
      .split(/[,\n\r]+/)
      .map(id => id.trim())
      .filter(id => id.length > 0 && this.validateIdentifier(id));
  }

  /**
   * Parse un fichier CSV et extrait les ASINs
   */
  async parseCSV(file: File): Promise<string[]> {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();

      reader.onload = (e) => {
        const text = e.target?.result as string;
        const lines = text.split(/\r?\n/);
        const asins: string[] = [];

        // Assume première colonne contient les ASINs
        for (const line of lines) {
          if (line.trim()) {
            const columns = line.split(/[,;\t]/);
            const firstColumn = columns[0]?.trim();
            if (firstColumn && this.validateIdentifier(firstColumn)) {
              asins.push(firstColumn);
            }
          }
        }

        resolve(asins);
      };

      reader.onerror = () => {
        reject(new Error('Erreur lors de la lecture du fichier CSV'));
      };

      reader.readAsText(file);
    });
  }

  /**
   * Export les résultats en CSV
   */
  exportToCSV(data: IngestResponse): string {
    const headers = ['ASIN', 'Titre', 'Prix', 'BSR', 'ROI %', 'Score Velocity', 'Rating', 'Recommandation'];
    const rows = data.results
      .filter(r => r.status === 'success' && r.analysis)
      .map(r => {
        const a = r.analysis!;
        const roi = 'roi_percentage' in a.roi ? parseFloat(a.roi.roi_percentage).toFixed(2) : 'N/A';
        return [
          a.asin,
          a.title || '',
          a.current_price || '',
          a.current_bsr || '',
          roi,
          a.velocity_score,
          a.overall_rating,
          a.recommendation
        ].map(v => `"${v}"`).join(',');
      });

    return [headers.join(','), ...rows].join('\n');
  }

  /**
   * Télécharge un fichier CSV
   */
  downloadCSV(csvContent: string, filename: string = 'analyse_resultats.csv'): void {
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);

    link.setAttribute('href', url);
    link.setAttribute('download', filename);
    link.style.visibility = 'hidden';

    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  }
}

export const keepaService = new KeepaService();