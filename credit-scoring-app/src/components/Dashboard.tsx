"use client";

import { useState, useMemo } from "react";
import {
  Building2,
  TrendingUp,
  CreditCard,
  DollarSign,
  CalendarDays,
  SlidersHorizontal,
  Copy,
  CheckCircle2,
  AlertTriangle,
  FileText,
  Pencil,
} from "lucide-react";
import { ExtractionResult, FinancialMetrics } from "@/types";
import {
  calculateFinancials,
  formatCurrency,
  formatNumber,
} from "@/lib/calculations";

interface DashboardProps {
  result: ExtractionResult;
}

export default function Dashboard({ result }: DashboardProps) {
  const [deposito1, setDeposito1] = useState(result.deposito_mes_1);
  const [deposito2, setDeposito2] = useState(result.deposito_mes_2);
  const [deposito3, setDeposito3] = useState(result.deposito_mes_3);
  const [porcentaje, setPorcentaje] = useState(30);
  const [copied, setCopied] = useState(false);
  const [editingField, setEditingField] = useState<string | null>(null);

  const currentResult: ExtractionResult = useMemo(
    () => ({
      ...result,
      deposito_mes_1: deposito1,
      deposito_mes_2: deposito2,
      deposito_mes_3: deposito3,
    }),
    [result, deposito1, deposito2, deposito3]
  );

  const metrics: FinancialMetrics = useMemo(
    () => calculateFinancials(currentResult, porcentaje),
    [currentResult, porcentaje]
  );

  const handleCopy = async () => {
    const report = `
=== REPORTE DE ANÁLISIS DE CAPACIDAD DE PAGO ===
Fecha: ${new Date().toLocaleDateString("es-VE")}

--- DATOS EXTRAÍDOS ---
Banco Detectado: ${currentResult.banco_detectado}
Observaciones: ${currentResult.observaciones}

--- DEPÓSITOS POR MES ---
Mes 1 (más reciente): ${formatCurrency(currentResult.deposito_mes_1)}
Mes 2: ${formatCurrency(currentResult.deposito_mes_2)}
Mes 3 (más antiguo): ${formatCurrency(currentResult.deposito_mes_3)}

--- CÁLCULOS FINANCIEROS ---
Depósito Promedio Mensual: ${formatCurrency(metrics.depositoPromedio)}
Porcentaje de Capacidad de Pago: ${metrics.porcentajeCapacidad}%
Capacidad de Pago Mensual: ${formatCurrency(metrics.capacidadPago)}

--- LÍMITES DE CRÉDITO APROBADOS ---
Límite de Crédito Global: ${formatCurrency(metrics.limiteCredito)}
Cuota Quincenal Máxima: ${formatCurrency(metrics.cuotaQuincenal)}

========================================
Reporte generado automáticamente por CreditScorer AI
    `.trim();

    try {
      await navigator.clipboard.writeText(report);
      setCopied(true);
      setTimeout(() => setCopied(false), 2500);
    } catch {
      // Fallback for older browsers
      const textarea = document.createElement("textarea");
      textarea.value = report;
      document.body.appendChild(textarea);
      textarea.select();
      document.execCommand("copy");
      document.body.removeChild(textarea);
      setCopied(true);
      setTimeout(() => setCopied(false), 2500);
    }
  };

  const EditableCurrencyField = ({
    label,
    value,
    onChange,
    fieldId,
    icon: Icon,
  }: {
    label: string;
    value: number;
    onChange: (v: number) => void;
    fieldId: string;
    icon: React.ElementType;
  }) => {
    const isEditing = editingField === fieldId;

    return (
      <div className="group relative">
        <div className="flex items-center gap-1.5 mb-1.5">
          <Icon className="h-3.5 w-3.5 text-slate-400" />
          <span className="text-xs text-slate-400 font-medium">{label}</span>
          <button
            onClick={() =>
              setEditingField(isEditing ? null : fieldId)
            }
            className="ml-auto opacity-0 group-hover:opacity-100 transition-opacity"
          >
            <Pencil className="h-3 w-3 text-slate-500 hover:text-indigo-400" />
          </button>
        </div>
        {isEditing ? (
          <div className="relative">
            <span className="absolute left-3 top-1/2 -translate-y-1/2 text-sm text-slate-400">
              $
            </span>
            <input
              type="number"
              value={value}
              onChange={(e) => onChange(Number(e.target.value) || 0)}
              onBlur={() => setEditingField(null)}
              autoFocus
              className="w-full pl-7 pr-3 py-2 bg-slate-700/50 border border-indigo-500/50 rounded-lg text-sm text-white focus:outline-none focus:ring-2 focus:ring-indigo-500/30"
            />
          </div>
        ) : (
          <p className="text-lg font-bold text-white tabular-nums">
            {formatCurrency(value)}
          </p>
        )}
      </div>
    );
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <TrendingUp className="h-5 w-5 text-indigo-400" />
            Resultado del Análisis
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Valores editables — haz clic en el icono ✏️ para corregir
          </p>
        </div>
        <button
          onClick={handleCopy}
          className={`
            flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all duration-300
            ${
              copied
                ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/30"
                : "bg-slate-700/50 text-slate-300 border border-slate-600/50 hover:bg-slate-700 hover:border-slate-500"
            }
          `}
        >
          {copied ? (
            <>
              <CheckCircle2 className="h-4 w-4" />
              Copiado
            </>
          ) : (
            <>
              <Copy className="h-4 w-4" />
              Exportar Reporte
            </>
          )}
        </button>
      </div>

      {/* Bank Info Card */}
      <div className="rounded-xl bg-gradient-to-r from-indigo-500/10 to-slate-800/50 border border-indigo-500/20 p-5">
        <div className="flex items-start gap-4">
          <div className="flex items-center justify-center w-12 h-12 rounded-xl bg-indigo-500/20 shrink-0">
            <Building2 className="h-6 w-6 text-indigo-400" />
          </div>
          <div className="flex-1 min-w-0">
            <h3 className="text-sm font-semibold text-slate-300 uppercase tracking-wider mb-1">
              Banco Detectado
            </h3>
            <p className="text-lg font-bold text-white">
              {currentResult.banco_detectado}
            </p>
            <div className="mt-3 flex items-start gap-2">
              <AlertTriangle className="h-3.5 w-3.5 text-amber-400 mt-0.5 shrink-0" />
              <p className="text-xs text-slate-400 leading-relaxed">
                {currentResult.observaciones}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Deposits Grid - Editable */}
      <div className="rounded-xl bg-slate-800/40 border border-slate-700/50 p-5">
        <div className="flex items-center gap-2 mb-4">
          <FileText className="h-4 w-4 text-slate-400" />
          <h3 className="text-sm font-semibold text-slate-300 uppercase tracking-wider">
            Depósitos Extraídos por Mes
          </h3>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="p-3 rounded-lg bg-slate-700/30 border border-slate-600/30">
            <EditableCurrencyField
              label="Mes 1 (más reciente)"
              value={deposito1}
              onChange={setDeposito1}
              fieldId="mes1"
              icon={CalendarDays}
            />
          </div>
          <div className="p-3 rounded-lg bg-slate-700/30 border border-slate-600/30">
            <EditableCurrencyField
              label="Mes 2"
              value={deposito2}
              onChange={setDeposito2}
              fieldId="mes2"
              icon={CalendarDays}
            />
          </div>
          <div className="p-3 rounded-lg bg-slate-700/30 border border-slate-600/30">
            <EditableCurrencyField
              label="Mes 3 (más antiguo)"
              value={deposito3}
              onChange={setDeposito3}
              fieldId="mes3"
              icon={CalendarDays}
            />
          </div>
        </div>
      </div>

      {/* Capacity Slider */}
      <div className="rounded-xl bg-slate-800/40 border border-slate-700/50 p-5">
        <div className="flex items-center gap-2 mb-4">
          <SlidersHorizontal className="h-4 w-4 text-slate-400" />
          <h3 className="text-sm font-semibold text-slate-300 uppercase tracking-wider">
            Capacidad de Pago (% sobre promedio)
          </h3>
        </div>
        <div className="space-y-3">
          <div className="flex items-center gap-4">
            <input
              type="range"
              min="10"
              max="50"
              step="1"
              value={porcentaje}
              onChange={(e) => setPorcentaje(Number(e.target.value))}
              className="flex-1 h-2 bg-slate-700 rounded-lg appearance-none cursor-pointer accent-indigo-500"
            />
            <div className="flex items-center gap-1 px-3 py-1.5 bg-indigo-500/10 border border-indigo-500/30 rounded-lg min-w-[70px] justify-center">
              <span className="text-lg font-bold text-indigo-300 tabular-nums">
                {porcentaje}
              </span>
              <span className="text-xs text-indigo-400">%</span>
            </div>
          </div>
          <div className="flex justify-between text-[10px] text-slate-500 px-1">
            <span>10% (Conservador)</span>
            <span>30% (Estándar)</span>
            <span>50% (Agresivo)</span>
          </div>
        </div>
      </div>

      {/* Results Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Promedio */}
        <div className="rounded-xl bg-gradient-to-br from-slate-800/60 to-slate-800/30 border border-slate-700/50 p-5">
          <div className="flex items-center gap-3 mb-3">
            <div className="flex items-center justify-center w-10 h-10 rounded-xl bg-blue-500/15">
              <DollarSign className="h-5 w-5 text-blue-400" />
            </div>
            <div>
              <p className="text-xs text-slate-400 font-medium">
                Depósito Promedio Mensual
              </p>
              <p className="text-[10px] text-slate-500">
                Promedio de los 3 meses
              </p>
            </div>
          </div>
          <p className="text-2xl font-bold text-white tabular-nums">
            {formatCurrency(metrics.depositoPromedio)}
          </p>
          <div className="mt-2 flex items-center gap-1.5">
            <div className="text-[10px] text-slate-500">
              = ({formatNumber(currentResult.deposito_mes_1)} +{" "}
              {formatNumber(currentResult.deposito_mes_2)} +{" "}
              {formatNumber(currentResult.deposito_mes_3)}) / 3
            </div>
          </div>
        </div>

        {/* Capacidad de Pago */}
        <div className="rounded-xl bg-gradient-to-br from-indigo-800/30 to-indigo-900/10 border border-indigo-500/20 p-5">
          <div className="flex items-center gap-3 mb-3">
            <div className="flex items-center justify-center w-10 h-10 rounded-xl bg-indigo-500/15">
              <CreditCard className="h-5 w-5 text-indigo-400" />
            </div>
            <div>
              <p className="text-xs text-slate-400 font-medium">
                Capacidad de Pago Mensual
              </p>
              <p className="text-[10px] text-slate-500">
                {porcentaje}% del promedio
              </p>
            </div>
          </div>
          <p className="text-2xl font-bold text-indigo-300 tabular-nums">
            {formatCurrency(metrics.capacidadPago)}
          </p>
          <div className="mt-2 flex items-center gap-1.5">
            <div className="text-[10px] text-slate-500">
              = {formatNumber(metrics.depositoPromedio)} x {porcentaje}%
            </div>
          </div>
        </div>
      </div>

      {/* Credit Limits */}
      <div className="rounded-xl bg-gradient-to-br from-emerald-800/20 to-emerald-900/5 border border-emerald-500/20 p-6">
        <div className="flex items-center gap-2 mb-5">
          <CheckCircle2 className="h-5 w-5 text-emerald-400" />
          <h3 className="text-sm font-semibold text-emerald-300 uppercase tracking-wider">
            Límites de Crédito Calculados
          </h3>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <p className="text-xs text-slate-400 font-medium mb-1">
              Límite de Crédito Global
            </p>
            <p className="text-3xl font-bold text-emerald-300 tabular-nums">
              {formatCurrency(metrics.limiteCredito)}
            </p>
            <p className="text-[10px] text-slate-500 mt-1">
              Capacidad de Pago x 2
            </p>
          </div>
          <div>
            <p className="text-xs text-slate-400 font-medium mb-1">
              Cuota Quincenal Máxima
            </p>
            <p className="text-3xl font-bold text-emerald-300 tabular-nums">
              {formatCurrency(metrics.cuotaQuincenal)}
            </p>
            <p className="text-[10px] text-slate-500 mt-1">
              Capacidad de Pago / 2
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
