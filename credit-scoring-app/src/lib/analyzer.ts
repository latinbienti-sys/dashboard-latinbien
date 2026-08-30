export interface ExtractionResult {
  deposito_mes_1: number;
  deposito_mes_2: number;
  deposito_mes_3: number;
  banco_detectado: string;
  observaciones: string;
}

// Bank detection
const BANK_PATTERNS: { name: string; patterns: RegExp[] }[] = [
  { name: "Banco Mercantil", patterns: [/mercantil/i] },
  { name: "Banco Banesco", patterns: [/banesco/i] },
  { name: "BBVA Banco Universal", patterns: [/bbva/i, /provincial/i] },
  { name: "Banco Santander", patterns: [/santander/i] },
  { name: "Banco de Venezuela", patterns: [/banco\s*de\s*venezuela/i, /bandev/i] },
  { name: "Banco Plaza", patterns: [/banco\s*plaza/i] },
  { name: "BOD", patterns: [/bod\b/i, /occidental\s*de\s*descuento/i] },
  { name: "Banco Nacional de Credito", patterns: [/nacional\s*de\s*cr/i] },
  { name: "Banco Exterior", patterns: [/exterior/i] },
  { name: "Banco Caroni", patterns: [/caron[ií]/i] },
  { name: "Banco Fondo Comun", patterns: [/fondo\s*com/i] },
  { name: "Banco Tesoro", patterns: [/tesoro/i] },
  { name: "Bancaribe", patterns: [/bancaribe/i] },
  { name: "Bancrecer", patterns: [/bancrecer/i] },
  { name: "Banco Activo", patterns: [/banco\s*activo/i] },
  { name: "Banco Mi Banco", patterns: [/mi\s*banco/i] },
  { name: "Banco Plaza", patterns: [/plaza/i] },
  { name: "Banco Venezolano de Credito", patterns: [/venezolano\s*de\s*cr/i] },
  { name: "Bancamiga", patterns: [/bancamiga/i] },
  { name: "Bancoro", patterns: [/bancoro/i] },
];

function detectBank(text: string): string {
  for (const bank of BANK_PATTERNS) {
    for (const pat of bank.patterns) {
      if (pat.test(text)) return bank.name;
    }
  }
  return "Banco no detectado";
}

// Parse Venezuelan number format: 1.234,56 or 1234.56 or 1,234.56
function parseAmount(str: string): number {
  let cleaned = str.replace(/\s/g, "").trim();
  // Handle "1.234,56" format (European/Venezuelan)
  if (/^\d{1,3}(\.\d{3})+,\d{1,2}$/.test(cleaned)) {
    cleaned = cleaned.replace(/\./g, "").replace(",", ".");
  }
  // Handle "1,234.56" format (US)
  else if (/^\d{1,3}(,\d{3})+\.\d{1,2}$/.test(cleaned)) {
    cleaned = cleaned.replace(/,/g, "");
  }
  // Handle "1234,56" format
  else if (/^\d+,\d{1,2}$/.test(cleaned) && !/^\d+\.\d+$/.test(cleaned)) {
    cleaned = cleaned.replace(",", ".");
  }
  const num = parseFloat(cleaned);
  return isNaN(num) ? 0 : Math.abs(num);
}

// Check if a line is a credit/deposit
function isCreditLine(line: string): boolean {
  const creditKeywords = [
    /abono/i,
    /dep[oó]s/i,
    /transfer/i,
    /n[oó]mina/i,
    /pago\s*recib/i,
    /ingreso/i,
    /cr[eé]dito/i,
    /bono/i,
    /comisi[oó]n\s*(?:por|a\s*favor)/i,
    /acredit/i,
    /consign/i,
    /devoluci/i,
    /reembolso/i,
    /abono\s*(?:por|de)/i,
    /transferencia\s*(?:entrante|recibida|a\s*favor)/i,
  ];

  const debitKeywords = [
    /d[eé]bito/i,
    /retiro/i,
    /cargo/i,
    /comisi[oó]n\s*(?:por|de)/i,
    /comisi[oó]n\s*(?:mant|administr)/i,
    /impuesto/i,
    /iv(?:a|tan)/i,
    /pago\s*(?:de|por)/i,
    /giro/i,
    /cheque\s*(?:no|diferido)/i,
    /mora/i,
    /reversion/i,
  ];

  // If line has credit keywords and no strong debit keywords
  const hasCredit = creditKeywords.some((k) => k.test(line));
  const hasDebit = debitKeywords.some((k) => k.test(line));

  return hasCredit && !hasDebit;
}

// Extract amounts from a line
function extractAmounts(line: string): number[] {
  // Match patterns like: 1.234,56 or 1234.56 or 1,234.56 or Bs. 1234.56 or USD 1234.56
  const patterns = [
    /(?:Bs\.?\s*|USD\s*|\$\s*)(\d{1,3}(?:[.,]\d{3})*(?:[.,]\d{2})?)/g,
    /(\d{1,3}(?:[.,]\d{3})*(?:[.,]\d{2}))/g,
  ];

  const amounts: number[] = [];
  for (const pat of patterns) {
    let match;
    while ((match = pat.exec(line)) !== null) {
      const val = parseAmount(match[1]);
      if (val > 0) amounts.push(val);
    }
    if (amounts.length > 0) break;
  }
  return amounts;
}

// Try to split text into months based on date patterns
function splitIntoMonths(text: string): string[] {
  // Look for month/year headers
  const monthPatterns = [
    // "Enero 2025", "Feb 2025", etc
    /(?:enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre|ene|feb|mar|abr|may|jun|jul|ago|sep|oct|nov|dic)[.\s]*(?:de\s*)?\d{4}/gi,
    // "01/2025", "01-2025"
    /\d{2}[\/\-]\d{4}/g,
    // "Periodo: 01/01/2025 - 31/01/2025"
    /per[ií]odo[:\s]*\d{2}[\/\-]\d{2}[\/\-]\d{4}/gi,
  ];

  const splitPoints: { pos: number; label: string }[] = [];

  for (const pat of monthPatterns) {
    let match;
    while ((match = pat.exec(text)) !== null) {
      splitPoints.push({ pos: match.index, label: match[0] });
    }
    if (splitPoints.length >= 2) break;
  }

  // Sort by position
  splitPoints.sort((a, b) => a.pos - b.pos);

  if (splitPoints.length >= 2) {
    const months: string[] = [];
    for (let i = 0; i < splitPoints.length; i++) {
      const start = splitPoints[i].pos;
      const end = i + 1 < splitPoints.length ? splitPoints[i + 1].pos : text.length;
      months.push(text.substring(start, end));
    }
    // Return last 3 months (most recent first = last in array)
    return months.slice(-3).reverse();
  }

  // If no month headers found, try to split by large gaps or page breaks
  const lines = text.split("\n");
  if (lines.length > 50) {
    const chunkSize = Math.floor(lines.length / 3);
    return [
      lines.slice(0, chunkSize).join("\n"),
      lines.slice(chunkSize, chunkSize * 2).join("\n"),
      lines.slice(chunkSize * 2).join("\n"),
    ];
  }

  // Return whole text as single month
  return [text];
}

function calculateMonthDeposits(monthText: string): number {
  const lines = monthText.split("\n");
  let totalDeposits = 0;

  for (const line of lines) {
    if (isCreditLine(line)) {
      const amounts = extractAmounts(line);
      if (amounts.length > 0) {
        // Use the largest amount on the line (likely the transaction amount, not balance)
        totalDeposits += Math.max(...amounts);
      }
    }
  }

  return totalDeposits;
}

export function analyzeBankStatement(texts: string[]): ExtractionResult {
  const allText = texts.join("\n\n");

  // Detect bank from all texts combined
  const banco = detectBank(allText);

  const allMonths: string[] = [];
  for (const text of texts) {
    const months = splitIntoMonths(text);
    allMonths.push(...months);
  }

  // Take last 3 months max
  const recentMonths = allMonths.slice(-3);

  const deposits = recentMonths.map((m) => calculateMonthDeposits(m));

  // Pad to 3 if needed
  while (deposits.length < 3) {
    deposits.push(0);
  }

  const observaciones = [];

  if (banco === "Banco no detectado") {
    observaciones.push("No se pudo identificar el banco automaticamente");
  }

  if (deposits.some((d) => d === 0)) {
    observaciones.push(
      "Algunos meses no pudieron ser identificados. Verifica los montos manualmente."
    );
  }

  if (recentMonths.length === 1 && deposits[1] === 0 && deposits[2] === 0) {
    observaciones.push(
      "Solo se detecto un mes de datos. Los meses 2 y 3 estan en 0."
    );
  }

  if (observaciones.length === 0) {
    observaciones.push(
      "Analisis completado. Los montos representan la suma de depositos, transferencias recibidas y abonos detectados."
    );
  }

  return {
    deposito_mes_1: deposits[0],
    deposito_mes_2: deposits[1],
    deposito_mes_3: deposits[2],
    banco_detectado: banco,
    observaciones: observaciones.join(" "),
  };
}
