import { ExtractionResult, FinancialMetrics } from "@/types";

export function calculateFinancials(
  result: ExtractionResult,
  porcentajeCapacidad: number
): FinancialMetrics {
  const depositoPromedio =
    (result.deposito_mes_1 + result.deposito_mes_2 + result.deposito_mes_3) / 3;

  const capacidadPago = depositoPromedio * (porcentajeCapacidad / 100);
  const limiteCredito = capacidadPago * 2;
  const cuotaQuincenal = capacidadPago / 2;

  return {
    depositoPromedio,
    capacidadPago,
    limiteCredito,
    cuotaQuincenal,
    porcentajeCapacidad,
  };
}

export function formatCurrency(value: number): string {
  return new Intl.NumberFormat("es-VE", {
    style: "currency",
    currency: "USD",
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(value);
}

export function formatNumber(value: number): string {
  return new Intl.NumberFormat("es-VE", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(value);
}
