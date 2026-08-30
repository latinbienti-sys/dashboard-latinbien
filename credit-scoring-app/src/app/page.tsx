"use client";

import { useState, useCallback, useMemo } from "react";
import {
  Shield,
  Zap,
  BarChart3,
  ArrowRight,
  RotateCcw,
  FileSearch,
  Sparkles,
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
  Upload,
  X,
  Loader2,
  AlertCircle,
  Brain,
} from "lucide-react";
import { extractTextFromPDF } from "@/lib/pdf-extract";
import { formatCurrency } from "@/lib/calculations";
import { analyzeBankStatement, ExtractionResult } from "@/lib/analyzer";

export default function Home() {
  const [files, setFiles] = useState<(File | null)[]>([null, null, null]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [processingStep, setProcessingStep] = useState("");
  const [result, setResult] = useState<ExtractionResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [deposito1, setDeposito1] = useState(0);
  const [deposito2, setDeposito2] = useState(0);
  const [deposito3, setDeposito3] = useState(0);
  const [porcentaje, setPorcentaje] = useState(30);
  const [copied, setCopied] = useState(false);
  const [editingField, setEditingField] = useState<string | null>(null);

  const hasFiles = files.some(Boolean);

  const metrics = useMemo(() => {
    const promedio = (deposito1 + deposito2 + deposito3) / 3;
    const capacidad = promedio * (porcentaje / 100);
    return {
      depositoPromedio: promedio,
      capacidadPago: capacidad,
      limiteCredito: capacidad * 2,
      cuotaQuincenal: capacidad / 2,
    };
  }, [deposito1, deposito2, deposito3, porcentaje]);

  const handleAnalyze = useCallback(async () => {
    const selectedFiles = files.filter(Boolean) as File[];
    if (selectedFiles.length === 0) return;
    setIsProcessing(true);
    setError(null);
    setResult(null);

    try {
      const allTexts: string[] = [];
      for (let i = 0; i < selectedFiles.length; i++) {
        setProcessingStep(`Leyendo PDF ${i + 1} de ${selectedFiles.length}...`);
        await new Promise((r) => setTimeout(r, 300));
        const text = await extractTextFromPDF(selectedFiles[i]);
        allTexts.push(text);
      }

      setProcessingStep("Analizando depositos por mes...");
      await new Promise((r) => setTimeout(r, 400));

      const extraction = analyzeBankStatement(allTexts);
      setResult(extraction);
      setDeposito1(extraction.deposito_mes_1);
      setDeposito2(extraction.deposito_mes_2);
      setDeposito3(extraction.deposito_mes_3);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error al procesar");
    } finally {
      setIsProcessing(false);
      setProcessingStep("");
    }
  }, [files]);

  const handleCopy = useCallback(async () => {
    const report = `=== REPORTE DE CAPACIDAD DE PAGO ===
Fecha: ${new Date().toLocaleDateString("es-VE")}

Banco: ${result?.banco_detectado || "N/A"}
Observaciones: ${result?.observaciones || "N/A"}

DEPOSITOS:
  Mes 1: ${formatCurrency(deposito1)}
  Mes 2: ${formatCurrency(deposito2)}
  Mes 3: ${formatCurrency(deposito3)}

PROMEDIO MENSUAL: ${formatCurrency(metrics.depositoPromedio)}
CAPACIDAD DE PAGO (${porcentaje}%): ${formatCurrency(metrics.capacidadPago)}

LIMITE CREDITO GLOBAL: ${formatCurrency(metrics.limiteCredito)}
CUOTA QUINCENAL: ${formatCurrency(metrics.cuotaQuincenal)}`;
    try {
      await navigator.clipboard.writeText(report);
      setCopied(true);
      setTimeout(() => setCopied(false), 2500);
    } catch {
      const ta = document.createElement("textarea");
      ta.value = report;
      document.body.appendChild(ta);
      ta.select();
      document.execCommand("copy");
      document.body.removeChild(ta);
      setCopied(true);
      setTimeout(() => setCopied(false), 2500);
    }
  }, [result, deposito1, deposito2, deposito3, metrics, porcentaje]);

  const handleReset = useCallback(() => {
    setFiles([null, null, null]);
    setResult(null);
    setError(null);
    setDeposito1(0);
    setDeposito2(0);
    setDeposito3(0);
    setPorcentaje(30);
  }, []);

  const monthLabels = ["Mes 1 (mas reciente)", "Mes 2", "Mes 3 (mas antiguo)"];

  return (
    <div className="min-h-screen bg-slate-950">
      <div className="fixed inset-0 bg-[linear-gradient(rgba(99,102,241,0.03)_1px,transparent_1px),linear-gradient(90deg,rgba(99,102,241,0.03)_1px,transparent_1px)] bg-[size:40px_40px] pointer-events-none" />
      <div className="fixed top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-indigo-500/50 to-transparent" />

      <div className="relative max-w-4xl mx-auto px-4 py-8 sm:px-6 lg:px-8">
        <header className="text-center mb-10">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-500/10 border border-indigo-500/20 mb-4">
            <Brain className="h-3.5 w-3.5 text-indigo-400" />
            <span className="text-xs font-medium text-indigo-300">
              Analisis Automatico - Gratis
            </span>
          </div>
          <h1 className="text-3xl sm:text-4xl font-bold text-white tracking-tight">
            Credit
            <span className="bg-gradient-to-r from-indigo-400 to-emerald-400 bg-clip-text text-transparent">
              Scorer
            </span>
          </h1>
          <p className="text-sm text-slate-400 mt-2 max-w-lg mx-auto">
            Sube tus estados de cuenta PDF y obtene tu capacidad de pago y limites de credito.
            Sin API key, sin costo, 100% en tu navegador.
          </p>
          <div className="flex flex-wrap items-center justify-center gap-3 mt-5">
            {[
              { icon: Shield, text: "100% Gratis" },
              { icon: Zap, text: "Sin API key" },
              { icon: BarChart3, text: "Resultados al instante" },
            ].map((b) => (
              <div key={b.text} className="flex items-center gap-1.5 text-xs text-slate-500">
                <b.icon className="h-3.5 w-3.5" />
                <span>{b.text}</span>
              </div>
            ))}
          </div>
        </header>

        <main className="space-y-6">
          {!result ? (
            <>
              <div className="rounded-2xl bg-slate-900/60 border border-slate-800/60 p-5 backdrop-blur-sm">
                <div className="flex items-center gap-2 mb-2">
                  <Upload className="h-5 w-5 text-indigo-400" />
                  <h3 className="text-sm font-semibold text-slate-200 uppercase tracking-wider">
                    Estados de Cuenta Bancarios
                  </h3>
                </div>
                <p className="text-xs text-slate-400 mb-4">
                  Sube hasta 3 archivos PDF. Del mas reciente al mas antiguo.
                </p>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  {monthLabels.map((label, index) => (
                    <FileSlot
                      key={index}
                      label={label}
                      file={files[index]}
                      isProcessing={isProcessing}
                      onDrop={(file) => {
                        const n = [...files];
                        n[index] = file;
                        setFiles(n);
                      }}
                      onRemove={() => {
                        const n = [...files];
                        n[index] = null;
                        setFiles(n);
                      }}
                    />
                  ))}
                </div>
                <div className="flex items-center gap-2 text-xs text-slate-500 mt-4">
                  {files.filter(Boolean).length > 0 ? (
                    <>
                      <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400" />
                      <span>{files.filter(Boolean).length} de 3 archivos cargados</span>
                    </>
                  ) : (
                    <>
                      <AlertCircle className="h-3.5 w-3.5 text-slate-500" />
                      <span>Carga al menos 1 archivo para continuar</span>
                    </>
                  )}
                </div>
                {isProcessing && (
                  <div className="mt-4 p-4 rounded-xl bg-indigo-500/10 border border-indigo-500/30">
                    <div className="flex items-center gap-3">
                      <Loader2 className="h-5 w-5 text-indigo-400 animate-spin" />
                      <div>
                        <p className="text-sm font-medium text-indigo-300">Procesando...</p>
                        <p className="text-xs text-slate-400 mt-0.5">{processingStep}</p>
                      </div>
                    </div>
                    <div className="mt-3 w-full bg-slate-700/50 rounded-full h-1.5">
                      <div className="bg-indigo-500 h-1.5 rounded-full animate-pulse w-2/3" />
                    </div>
                  </div>
                )}
              </div>

              {error && (
                <div className="rounded-xl bg-red-500/10 border border-red-500/30 p-4">
                  <div className="flex items-start gap-3">
                    <div className="flex items-center justify-center w-8 h-8 rounded-full bg-red-500/20 shrink-0">
                      <span className="text-red-400 text-sm font-bold">!</span>
                    </div>
                    <div>
                      <p className="text-sm font-medium text-red-300">Error</p>
                      <p className="text-xs text-slate-400 mt-1">{error}</p>
                    </div>
                  </div>
                </div>
              )}

              <button
                onClick={handleAnalyze}
                disabled={!hasFiles || isProcessing}
                className={`w-full flex items-center justify-center gap-3 py-4 px-6 rounded-xl text-base font-semibold transition-all duration-300 ${
                  hasFiles && !isProcessing
                    ? "bg-gradient-to-r from-indigo-600 to-indigo-500 text-white hover:from-indigo-500 hover:to-indigo-400 shadow-lg shadow-indigo-500/25 hover:shadow-indigo-500/40 active:scale-[0.98]"
                    : "bg-slate-800/50 text-slate-500 cursor-not-allowed border border-slate-700/50"
                }`}
              >
                {isProcessing ? (
                  <>
                    <div className="h-5 w-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    Analizando...
                  </>
                ) : (
                  <>
                    <FileSearch className="h-5 w-5" />
                    Analizar Estados de Cuenta
                    <ArrowRight className="h-4 w-4" />
                  </>
                )}
              </button>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-2">
                {[
                  { step: "1", title: "Sube tus PDFs", desc: "Arrastra tus estados de cuenta bancarios" },
                  { step: "2", title: "Analisis automatico", desc: "El sistema detecta el banco y suma depositos" },
                  { step: "3", title: "Obten tu Score", desc: "Capacidad de pago y limites al instante" },
                ].map((item) => (
                  <div
                    key={item.step}
                    className="flex items-start gap-3 p-4 rounded-xl bg-slate-900/40 border border-slate-800/40"
                  >
                    <div className="flex items-center justify-center w-7 h-7 rounded-lg bg-indigo-500/15 shrink-0">
                      <span className="text-xs font-bold text-indigo-400">{item.step}</span>
                    </div>
                    <div>
                      <p className="text-sm font-semibold text-slate-200">{item.title}</p>
                      <p className="text-xs text-slate-500 mt-0.5">{item.desc}</p>
                    </div>
                  </div>
                ))}
              </div>
            </>
          ) : (
            <>
              <div className="space-y-6">
                <div className="flex items-center justify-between flex-wrap gap-3">
                  <div>
                    <h2 className="text-xl font-bold text-white flex items-center gap-2">
                      <TrendingUp className="h-5 w-5 text-indigo-400" />
                      Resultado del Analisis
                    </h2>
                    <p className="text-xs text-slate-400 mt-1">
                      Haz clic en el lapiz para corregir valores manualmente
                    </p>
                  </div>
                  <button
                    onClick={handleCopy}
                    className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all duration-300 ${
                      copied
                        ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/30"
                        : "bg-slate-700/50 text-slate-300 border border-slate-600/50 hover:bg-slate-700 hover:border-slate-500"
                    }`}
                  >
                    {copied ? <CheckCircle2 className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
                    {copied ? "Copiado" : "Exportar Reporte"}
                  </button>
                </div>

                <div className="rounded-xl bg-gradient-to-r from-indigo-500/10 to-slate-800/50 border border-indigo-500/20 p-5">
                  <div className="flex items-start gap-4">
                    <div className="flex items-center justify-center w-12 h-12 rounded-xl bg-indigo-500/20 shrink-0">
                      <Building2 className="h-6 w-6 text-indigo-400" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <h3 className="text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1">
                        Banco Detectado
                      </h3>
                      <p className="text-lg font-bold text-white">{result.banco_detectado}</p>
                      <div className="mt-2 flex items-start gap-2">
                        <AlertTriangle className="h-3.5 w-3.5 text-amber-400 mt-0.5 shrink-0" />
                        <p className="text-xs text-slate-400 leading-relaxed">
                          {result.observaciones}
                        </p>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="rounded-xl bg-slate-800/40 border border-slate-700/50 p-5">
                  <div className="flex items-center gap-2 mb-4">
                    <FileText className="h-4 w-4 text-slate-400" />
                    <h3 className="text-sm font-semibold text-slate-300 uppercase tracking-wider">
                      Depositos Extraidos
                    </h3>
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    {[
                      { label: "Mes 1 (reciente)", value: deposito1, set: setDeposito1, id: "m1" },
                      { label: "Mes 2", value: deposito2, set: setDeposito2, id: "m2" },
                      { label: "Mes 3 (antiguo)", value: deposito3, set: setDeposito3, id: "m3" },
                    ].map((f) => (
                      <div key={f.id} className="p-3 rounded-lg bg-slate-700/30 border border-slate-600/30 group">
                        <div className="flex items-center gap-1.5 mb-1.5">
                          <CalendarDays className="h-3.5 w-3.5 text-slate-400" />
                          <span className="text-xs text-slate-400 font-medium">{f.label}</span>
                          <button
                            onClick={() => setEditingField(editingField === f.id ? null : f.id)}
                            className="ml-auto opacity-0 group-hover:opacity-100 transition-opacity"
                          >
                            <Pencil className="h-3 w-3 text-slate-500 hover:text-indigo-400" />
                          </button>
                        </div>
                        {editingField === f.id ? (
                          <div className="relative">
                            <span className="absolute left-3 top-1/2 -translate-y-1/2 text-sm text-slate-400">$</span>
                            <input
                              type="number"
                              value={f.value}
                              onChange={(e) => f.set(Number(e.target.value) || 0)}
                              onBlur={() => setEditingField(null)}
                              autoFocus
                              className="w-full pl-7 pr-3 py-2 bg-slate-700/50 border border-indigo-500/50 rounded-lg text-sm text-white focus:outline-none focus:ring-2 focus:ring-indigo-500/30"
                            />
                          </div>
                        ) : (
                          <p className="text-lg font-bold text-white tabular-nums">
                            {formatCurrency(f.value)}
                          </p>
                        )}
                      </div>
                    ))}
                  </div>
                </div>

                <div className="rounded-xl bg-slate-800/40 border border-slate-700/50 p-5">
                  <div className="flex items-center gap-2 mb-4">
                    <SlidersHorizontal className="h-4 w-4 text-slate-400" />
                    <h3 className="text-sm font-semibold text-slate-300 uppercase tracking-wider">
                      Capacidad de Pago (% sobre promedio)
                    </h3>
                  </div>
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
                      <span className="text-lg font-bold text-indigo-300 tabular-nums">{porcentaje}</span>
                      <span className="text-xs text-indigo-400">%</span>
                    </div>
                  </div>
                  <div className="flex justify-between text-[10px] text-slate-500 px-1 mt-1">
                    <span>10% Conservador</span>
                    <span>30% Estandar</span>
                    <span>50% Agresivo</span>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="rounded-xl bg-gradient-to-br from-slate-800/60 to-slate-800/30 border border-slate-700/50 p-5">
                    <div className="flex items-center gap-3 mb-3">
                      <div className="flex items-center justify-center w-10 h-10 rounded-xl bg-blue-500/15">
                        <DollarSign className="h-5 w-5 text-blue-400" />
                      </div>
                      <div>
                        <p className="text-xs text-slate-400 font-medium">Deposito Promedio Mensual</p>
                        <p className="text-[10px] text-slate-500">Promedio de los 3 meses</p>
                      </div>
                    </div>
                    <p className="text-2xl font-bold text-white tabular-nums">
                      {formatCurrency(metrics.depositoPromedio)}
                    </p>
                  </div>
                  <div className="rounded-xl bg-gradient-to-br from-indigo-800/30 to-indigo-900/10 border border-indigo-500/20 p-5">
                    <div className="flex items-center gap-3 mb-3">
                      <div className="flex items-center justify-center w-10 h-10 rounded-xl bg-indigo-500/15">
                        <CreditCard className="h-5 w-5 text-indigo-400" />
                      </div>
                      <div>
                        <p className="text-xs text-slate-400 font-medium">Capacidad de Pago Mensual</p>
                        <p className="text-[10px] text-slate-500">{porcentaje}% del promedio</p>
                      </div>
                    </div>
                    <p className="text-2xl font-bold text-indigo-300 tabular-nums">
                      {formatCurrency(metrics.capacidadPago)}
                    </p>
                  </div>
                </div>

                <div className="rounded-xl bg-gradient-to-br from-emerald-800/20 to-emerald-900/5 border border-emerald-500/20 p-6">
                  <div className="flex items-center gap-2 mb-5">
                    <CheckCircle2 className="h-5 w-5 text-emerald-400" />
                    <h3 className="text-sm font-semibold text-emerald-300 uppercase tracking-wider">
                      Limites de Credito Calculados
                    </h3>
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div>
                      <p className="text-xs text-slate-400 font-medium mb-1">Limite de Credito Global</p>
                      <p className="text-3xl font-bold text-emerald-300 tabular-nums">
                        {formatCurrency(metrics.limiteCredito)}
                      </p>
                      <p className="text-[10px] text-slate-500 mt-1">Capacidad de Pago x 2</p>
                    </div>
                    <div>
                      <p className="text-xs text-slate-400 font-medium mb-1">Cuota Quincenal Maxima</p>
                      <p className="text-3xl font-bold text-emerald-300 tabular-nums">
                        {formatCurrency(metrics.cuotaQuincenal)}
                      </p>
                      <p className="text-[10px] text-slate-500 mt-1">Capacidad de Pago / 2</p>
                    </div>
                  </div>
                </div>
              </div>

              <button
                onClick={handleReset}
                className="w-full flex items-center justify-center gap-2 py-3 px-6 rounded-xl text-sm font-medium bg-slate-800/50 text-slate-300 border border-slate-700/50 hover:bg-slate-800 hover:border-slate-600 transition-all duration-300"
              >
                <RotateCcw className="h-4 w-4" />
                Nuevo Analisis
              </button>
            </>
          )}
        </main>

        <footer className="text-center mt-12 pt-6 border-t border-slate-800/50">
          <p className="text-xs text-slate-600">
            CreditScorer AI - Analisis crediticio automatizado, 100% gratis
          </p>
        </footer>
      </div>
    </div>
  );
}

function FileSlot({
  label,
  file,
  isProcessing,
  onDrop,
  onRemove,
}: {
  label: string;
  file: File | null;
  isProcessing: boolean;
  onDrop: (file: File) => void;
  onRemove: () => void;
}) {
  const [dragOver, setDragOver] = useState(false);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setDragOver(false);
      const f = Array.from(e.dataTransfer.files).find(
        (x) => x.type === "application/pdf"
      );
      if (f) onDrop(f);
    },
    [onDrop]
  );

  const handleInput = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const f = e.target.files?.[0];
      if (f && f.type === "application/pdf") onDrop(f);
    },
    [onDrop]
  );

  return (
    <div
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      className={`relative group rounded-xl border-2 border-dashed transition-all duration-300 ${
        file
          ? "border-emerald-500/50 bg-emerald-500/5"
          : dragOver
          ? "border-indigo-400 bg-indigo-500/10 scale-[1.02]"
          : "border-slate-600/50 bg-slate-800/30 hover:border-slate-500/70 hover:bg-slate-800/50"
      } ${isProcessing ? "pointer-events-none opacity-70" : ""}`}
    >
      <input
        type="file"
        accept=".pdf"
        onChange={handleInput}
        className="absolute inset-0 w-full h-full opacity-0 cursor-pointer z-10"
        disabled={isProcessing}
      />
      <div className="p-4 flex flex-col items-center justify-center min-h-[140px] text-center">
        {file ? (
          <>
            <div className="flex items-center justify-center w-10 h-10 rounded-full bg-emerald-500/20 mb-2">
              <FileText className="h-5 w-5 text-emerald-400" />
            </div>
            <p className="text-xs font-medium text-emerald-300 truncate max-w-full px-2">
              {file.name}
            </p>
            <p className="text-[10px] text-slate-400 mt-1">
              {(file.size / 1024 / 1024).toFixed(2)} MB
            </p>
            {!isProcessing && (
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  e.preventDefault();
                  onRemove();
                }}
                className="absolute top-2 right-2 p-1 rounded-full bg-slate-700/80 hover:bg-red-500/80 transition-colors z-20"
              >
                <X className="h-3 w-3 text-slate-300" />
              </button>
            )}
          </>
        ) : (
          <>
            <div
              className={`flex items-center justify-center w-10 h-10 rounded-full transition-colors ${
                dragOver ? "bg-indigo-500/30" : "bg-slate-700/50 group-hover:bg-slate-700/80"
              }`}
            >
              <Upload
                className={`h-5 w-5 transition-colors ${
                  dragOver ? "text-indigo-300" : "text-slate-400"
                }`}
              />
            </div>
            <p className="text-xs font-medium text-slate-300 mt-2">{label}</p>
            <p className="text-[10px] text-slate-500 mt-0.5">Arrastra o haz clic</p>
          </>
        )}
      </div>
    </div>
  );
}
