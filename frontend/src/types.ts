export interface OcrTable {
  row_count: number;
  column_count: number;
  cells: Array<{
    row: number;
    col: number;
    content: string;
    row_span: number;
    col_span: number;
  }>;
}

export interface OcrPage {
  page_number: number;
  text: string;
  tables: OcrTable[];
}

export interface ExtractedField {
  id: string;
  label: string;
  field_type: "text" | "number" | "date" | "currency" | "percentage";
  required: boolean;
  value: string | number | null;
  confidence: "high" | "medium" | "low" | null;
  source: string | null;
  alternatives: string[];
}

export interface SchemaField {
  id: string;
  label: string;
  field_type: string;
  required: boolean;
  description: string;
}

export interface Schema {
  type: string;
  label: string;
  fields: SchemaField[];
}

export interface TraceEntry {
  step: string;
  label: string;
  status: "running" | "success" | "error" | "skipped";
  input: Record<string, unknown>;
  output: Record<string, unknown>;
  duration_ms: number;
}

export interface PromptPair {
  system: string;
  user: string;
  response: string;
}

export interface PipelineResult {
  id: string;
  filename: string;
  status: "processing" | "complete" | "error";
  document_type: string | null;
  classification_confidence: number | null;
  page_count: number;
  ocr_pages: OcrPage[];
  schema: Schema | null;
  extracted_fields: ExtractedField[];
  prompts: {
    classification: PromptPair;
    extraction: PromptPair | null;
  } | null;
  trace: TraceEntry[];
  error?: string;
}

export interface DocumentRecord {
  id: string;
  filename: string;
  status: "processing" | "complete" | "error";
  sourceUrl: string | null;
  result: PipelineResult | null;
}

export type TabId = "source" | "ocr" | "schema" | "prompts" | "extracted" | "trace";
