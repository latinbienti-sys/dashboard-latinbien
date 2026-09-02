// ============================================================
// LatinBien Mobile — Cálculo de Planes de Pago (cuotas quincenales)
// Replica EXACTAMENTE la lógica del sitio latinbien.com
// (módulo payment_installment_kanak / payment_installment)
//
// Fórmula verificada:
//   cuota_administrativa_porcentaje = 2.7 * nº_cuotas   (2.7% por quincena)
//   saldo_administrativo_monto = (%/100) * monto_financiar
//   valor_cuota = (monto_financiar + saldo_admin_monto) / nº_cuotas
// ============================================================

// Tasa administrativa por quincena (2.7%): constante en la instancia
export const ADMIN_FEE_PER_QUINCENA = 2.7;

// Opciones de inicial (porcentaje) como en el sitio
export const INITIAL_OPTIONS = [
  { value: 0.5, label: '50%' },
  { value: 0.4, label: '40%' },
  { value: 0.3, label: '30%' },
  { value: 0.2, label: '20%' },
];

// Opciones de cuotas quincenales
export const INSTALLMENT_OPTIONS = [6, 10, 15, 20];

function round(num, decimals = 2) {
  const factor = Math.pow(10, decimals);
  return Math.round(num * factor) / factor;
}

/**
 * Calcula el plan de pago para un precio contado dado.
 * @param {number} listPrice - Precio contado (USD)
 * @param {number} initialPct - Porcentaje de inicial (0.2 = 20%)
 * @param {number} numInstallments - Cantidad de cuotas quincenales (6,10,15,20)
 * @param {number} adminFee - Tasa administrativa por quincena (default 2.7)
 */
export function calculatePlan(listPrice, initialPct, numInstallments, adminFee = ADMIN_FEE_PER_QUINCENA) {
  const amount = round(listPrice, 2);
  const incomePlans = round(initialPct * amount, 2); // valor de inicial $
  const montoFinanciar = round(amount - incomePlans, 2);

  const adminPctTotal = round(adminFee * numInstallments, 2); // ej: 2.7*20 = 54%
  const adminAmount = round((adminPctTotal / 100) * montoFinanciar, 2); // saldo administrativo $
  const cuotaNeta = montoFinanciar / numInstallments;
  const cuotaAdmin = adminAmount / numInstallments;
  const cuota = round(cuotaNeta + cuotaAdmin, 2);

  return {
    listPrice: amount,
    initialPct,
    initialAmount: incomePlans,
    montoFinanciar,
    numInstallments,
    months: numInstallments / 2,
    adminPctTotal,
    adminAmount,
    cuota,
    finalCreditPrice: round(adminAmount + amount, 2), // Precio Final a Crédito
    totalToFinance: round(cuota * numInstallments, 2),
  };
}

/**
 * Plan referencial mostrado en tarjetas: 20% inicial / 20 cuotas
 */
export function getReferencePlan(listPrice, adminFee = ADMIN_FEE_PER_QUINCENA) {
  return calculatePlan(listPrice, 0.2, 20, adminFee);
}
