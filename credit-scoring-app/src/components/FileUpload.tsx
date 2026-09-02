"use client";

import { useCallback, useState } from "react";
import {
  Upload,
  FileText,
  X,
  Loader2,
  CheckCircle2,
  AlertCircle,
} from "lucide-react";

interface FileUploadProps {
  files: (File | null)[];
  onFilesChange: (files: (File | null)[]) => void;
  isProcessing: boolean;
  processingStep: string;
}

export default function FileUpload({
  files,
  onFilesChange,
  isProcessing,
  processingStep,
}: FileUploadProps) {
  const [dragOverIndex, setDragOverIndex] = useState<number | null>(null);

  const handleDragOver = useCallback(
    (e: React.DragEvent, index: number) => {
      e.preventDefault();
      e.stopPropagation();
      setDragOverIndex(index);
    },
    []
  );

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragOverIndex(null);
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent, index: number) => {
      e.preventDefault();
      e.stopPropagation();
      setDragOverIndex(null);

      const droppedFiles = Array.from(e.dataTransfer.files).filter(
        (f) => f.type === "application/pdf"
      );

      if (droppedFiles.length === 0) return;

      const newFiles = [...files];
      newFiles[index] = droppedFiles[0];
      onFilesChange(newFiles);
    },
    [files, onFilesChange]
  );

  const handleFileInput = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>, index: number) => {
      const selectedFile = e.target.files?.[0];
      if (selectedFile && selectedFile.type === "application/pdf") {
        const newFiles = [...files];
        newFiles[index] = selectedFile;
        onFilesChange(newFiles);
      }
    },
    [files, onFilesChange]
  );

  const removeFile = useCallback(
    (index: number) => {
      const newFiles = [...files];
      newFiles[index] = null;
      onFilesChange(newFiles);
    },
    [files, onFilesChange]
  );

  const monthLabels = ["Mes 1 (más reciente)", "Mes 2", "Mes 3 (más antiguo)"];

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2 mb-2">
        <Upload className="h-5 w-5 text-indigo-400" />
        <h3 className="text-sm font-semibold text-slate-200 uppercase tracking-wider">
          Estados de Cuenta Bancarios
        </h3>
      </div>
      <p className="text-xs text-slate-400 mb-4">
        Sube hasta 3 archivos PDF de tus estados de cuenta bancarios de los
        últimos 3 meses. El orden importa: del más reciente al más antiguo.
      </p>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {monthLabels.map((label, index) => (
          <div
            key={index}
            onDragOver={(e) => handleDragOver(e, index)}
            onDragLeave={handleDragLeave}
            onDrop={(e) => handleDrop(e, index)}
            className={`
              relative group rounded-xl border-2 border-dashed transition-all duration-300
              ${
                files[index]
                  ? "border-emerald-500/50 bg-emerald-500/5"
                  : dragOverIndex === index
                  ? "border-indigo-400 bg-indigo-500/10 scale-[1.02]"
                  : "border-slate-600/50 bg-slate-800/30 hover:border-slate-500/70 hover:bg-slate-800/50"
              }
              ${isProcessing ? "pointer-events-none opacity-70" : ""}
            `}
          >
            <input
              type="file"
              accept=".pdf"
              onChange={(e) => handleFileInput(e, index)}
              className="absolute inset-0 w-full h-full opacity-0 cursor-pointer z-10"
              disabled={isProcessing}
            />

            <div className="p-4 flex flex-col items-center justify-center min-h-[140px] text-center">
              {files[index] ? (
                <>
                  <div className="flex items-center justify-center w-10 h-10 rounded-full bg-emerald-500/20 mb-2">
                    <FileText className="h-5 w-5 text-emerald-400" />
                  </div>
                  <p className="text-xs font-medium text-emerald-300 truncate max-w-full px-2">
                    {files[index]!.name}
                  </p>
                  <p className="text-[10px] text-slate-400 mt-1">
                    {(files[index]!.size / 1024 / 1024).toFixed(2)} MB
                  </p>
                  {!isProcessing && (
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        e.preventDefault();
                        removeFile(index);
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
                    className={`
                    flex items-center justify-center w-10 h-10 rounded-full transition-colors
                    ${
                      dragOverIndex === index
                        ? "bg-indigo-500/30"
                        : "bg-slate-700/50 group-hover:bg-slate-700/80"
                    }
                  `}
                  >
                    <Upload
                      className={`h-5 w-5 transition-colors ${
                        dragOverIndex === index
                          ? "text-indigo-300"
                          : "text-slate-400"
                      }`}
                    />
                  </div>
                  <p className="text-xs font-medium text-slate-300 mt-2">
                    {label}
                  </p>
                  <p className="text-[10px] text-slate-500 mt-0.5">
                    Arrastra o haz clic
                  </p>
                </>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* Processing Status */}
      {isProcessing && (
        <div className="mt-4 p-4 rounded-xl bg-indigo-500/10 border border-indigo-500/30">
          <div className="flex items-center gap-3">
            <Loader2 className="h-5 w-5 text-indigo-400 animate-spin" />
            <div>
              <p className="text-sm font-medium text-indigo-300">
                Procesando documentos...
              </p>
              <p className="text-xs text-slate-400 mt-0.5">{processingStep}</p>
            </div>
          </div>
          <div className="mt-3 w-full bg-slate-700/50 rounded-full h-1.5">
            <div className="bg-indigo-500 h-1.5 rounded-full animate-pulse w-2/3" />
          </div>
        </div>
      )}

      {/* File count indicator */}
      <div className="flex items-center gap-2 text-xs text-slate-500">
        {files.filter(Boolean).length > 0 ? (
          <>
            <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400" />
            <span>
              {files.filter(Boolean).length} de 3 archivos cargados
            </span>
          </>
        ) : (
          <>
            <AlertCircle className="h-3.5 w-3.5 text-slate-500" />
            <span>Carga al menos 1 archivo para continuar</span>
          </>
        )}
      </div>
    </div>
  );
}
