import { NextRequest, NextResponse } from "next/server";
import OpenAI from "openai";

function getOpenAIClient() {
  return new OpenAI({
    apiKey: process.env.OPENAI_API_KEY,
  });
}

const EXTRACTION_PROMPT = `Eres un experto en análisis financiero y estados de cuenta bancarios venezolanos y latinoamericanos. 

Tu tarea es analizar el texto extraído de un estado de cuenta bancario PDF y extraer la información financiera clave.

INSTRUCCIONES:
1. Identifica el banco automáticamente (Mercantil, Banesco, BBVA, Santander, Banco de Venezuela, Provincial, BOD, Banco Plaza, etc.)
2. Analiza TODOS los movimientos del mes para determinar el total de depósitos/abonos/ingresos
3. Los depósitos incluyen: transferencias recibidas, consignaciones, abonos, nóminas, pagos recibidos
4. NO incluyas: débitos, retiros, pagos de servicios, comisiones, cargos
5. Si el estado de cuenta cubre más de un mes, separa por mes calendario
6. Si solo hay un mes de datos, usa ese monto para deposito_mes_1 y pon 0 en los otros
7. Si hay dos meses, usa deposito_mes_1 y deposito_mes_2, pon 0 en deposito_mes_3

RESPONDE EXCLUSIVAMENTE EN JSON VÁLIDO con esta estructura exacta:
{
  "deposito_mes_1": número,
  "deposito_mes_2": número,
  "deposito_mes_3": número,
  "banco_detectado": "string con nombre del banco",
  "observaciones": "string con notas relevantes del análisis"
}

NO incluyas texto adicional, solo el JSON.`;

export async function POST(request: NextRequest) {
  try {
    const formData = await request.formData();
    const files = formData.getAll("files") as File[];

    if (!files || files.length === 0) {
      return NextResponse.json(
        { error: "No se recibieron archivos PDF" },
        { status: 400 }
      );
    }

    const allTexts: string[] = [];

    for (const file of files) {
      const bytes = await file.arrayBuffer();
      const buffer = Buffer.from(bytes);

      // Use pdf-parse v2 API with PDFParse class
      const { PDFParse } = await import("pdf-parse");
      const parser = new PDFParse({ data: new Uint8Array(buffer) });
      const textResult = await parser.getText();
      allTexts.push(textResult.text);
      await parser.destroy();
    }

    const combinedText = allTexts
      .map(
        (text, i) =>
          `=== ESTADO DE CUENTA ${i + 1} de ${files.length} ===\n${text}`
      )
      .join("\n\n");

    // Truncate if too long for the model
    const maxLength = 12000;
    const truncatedText =
      combinedText.length > maxLength
        ? combinedText.substring(0, maxLength) +
          "\n\n[TEXTO TRUNCADO POR LONGITUD]"
        : combinedText;

    const openai = getOpenAIClient();
    const completion = await openai.chat.completions.create({
      model: "gpt-4o-mini",
      messages: [
        {
          role: "system",
          content: EXTRACTION_PROMPT,
        },
        {
          role: "user",
          content: `Analiza este(s) estado(s) de cuenta bancario(s) y extrae la información financiera:\n\n${truncatedText}`,
        },
      ],
      temperature: 0.1,
      max_tokens: 1000,
    });

    const responseContent = completion.choices[0]?.message?.content;

    if (!responseContent) {
      return NextResponse.json(
        { error: "La IA no pudo procesar el documento" },
        { status: 500 }
      );
    }

    // Parse the JSON response
    let extractedData;
    try {
      const jsonMatch = responseContent.match(/\{[\s\S]*\}/);
      if (jsonMatch) {
        extractedData = JSON.parse(jsonMatch[0]);
      } else {
        extractedData = JSON.parse(responseContent);
      }
    } catch {
      return NextResponse.json(
        {
          error: "Error al parsear la respuesta de la IA",
          rawResponse: responseContent,
        },
        { status: 500 }
      );
    }

    // Validate the structure
    const result = {
      deposito_mes_1: Number(extractedData.deposito_mes_1) || 0,
      deposito_mes_2: Number(extractedData.deposito_mes_2) || 0,
      deposito_mes_3: Number(extractedData.deposito_mes_3) || 0,
      banco_detectado: String(extractedData.banco_detectado || "No detectado"),
      observaciones: String(extractedData.observaciones || "Sin observaciones"),
    };

    return NextResponse.json(result);
  } catch (error) {
    console.error("Error processing PDF:", error);
    return NextResponse.json(
      {
        error:
          error instanceof Error
            ? error.message
            : "Error interno al procesar el documento",
      },
      { status: 500 }
    );
  }
}
