/**
 * Verification Service
 * Phase 8: Pre-purchase product verification using Keepa API
 */

const API_URL = import.meta.env.VITE_API_URL || 'https://arbitragevault-backend-v2.onrender.com';

export type VerificationStatus = 'ok' | 'changed' | 'avoid';

export interface VerificationChange {
  field: string;
  saved_value: number | string;
  current_value: number | string;
  severity: 'info' | 'warning' | 'critical';
  message: string;
}

export interface VerificationRequest {
  asin: string;
  saved_price?: number;
  saved_bsr?: number;
  saved_fba_count?: number;
}

export interface VerificationResponse {
  asin: string;
  status: VerificationStatus;
  message: string;
  verified_at: string;
  current_price?: number;
  current_bsr?: number;
  current_fba_count?: number;
  amazon_selling: boolean;
  changes: VerificationChange[];
  estimated_profit?: number;
  profit_change_percent?: number;
}

class VerificationService {
  private baseUrl: string;

  constructor() {
    this.baseUrl = `${API_URL}/api/v1/products`;
  }

  /**
   * Verify a product before purchase
   * Compares saved analysis data against current Keepa data
   */
  async verifyProduct(request: VerificationRequest): Promise<VerificationResponse> {
    const response = await fetch(`${this.baseUrl}/${request.asin}/verify`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        asin: request.asin,
        saved_price: request.saved_price,
        saved_bsr: request.saved_bsr,
        saved_fba_count: request.saved_fba_count,
      }),
    });

    if (!response.ok) {
      const error = await response.text();
      throw new Error(error || `HTTP ${response.status}: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Get status badge color classes
   */
  getStatusBadge(status: VerificationStatus): { label: string; color: string; icon: string } {
    const badges: Record<VerificationStatus, { label: string; color: string; icon: string }> = {
      ok: { label: 'OK', color: 'bg-green-100 text-green-800 border-green-300', icon: 'check' },
      changed: { label: 'Modifie', color: 'bg-yellow-100 text-yellow-800 border-yellow-300', icon: 'alert' },
      avoid: { label: 'Eviter', color: 'bg-red-100 text-red-800 border-red-300', icon: 'x' },
    };
    return badges[status] || badges.avoid;
  }
}

export const verificationService = new VerificationService();
