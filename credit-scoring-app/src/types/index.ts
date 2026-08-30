export interface ExtractionResult {
  deposito_mes_1: number;
  deposito_mes_2: number;
  deposito_mes_3: number;
  banco_detectado: string;
  observaciones: string;
}

export interface FinancialMetrics {
  depositoPromedio: number;
  capacidadPago: number;
  limiteCredito: number;
  cuotaQuincenal: number;
  porcentajeCapacidad: number;
}

export interface AnalysisState {
  files: (File | null)[];
  isProcessing: boolean;
  processingStep: string;
  extractionResult: ExtractionResult | null;
  error: string | null;
}
