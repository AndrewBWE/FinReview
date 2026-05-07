import { cn, formatValue } from "../lib/utils";
import type { ExtractedField } from "../types";

interface Props {
  fields: ExtractedField[];
  documentType: string | null;
  confidence: number | null;
  onWriteToStorage: () => void;
  storageStatus: "idle" | "writing" | "written" | "error" | "not_configured";
}

export default function ExtractionResults({
  fields,
  documentType,
  confidence,
  onWriteToStorage,
  storageStatus,
}: Props) {
  if (!fields.length) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <p className="text-slate-400 text-sm">No extracted fields</p>
      </div>
    );
  }

  const extracted = fields.filter((f) => f.value !== null && f.value !== undefined);
  const highCount = extracted.filter((f) => f.confidence === "high").length;
  const medCount = extracted.filter((f) => f.confidence === "medium").length;
  const lowCount = extracted.filter((f) => f.confidence === "low").length;
  const missingRequired = fields.filter((f) => f.required && (f.value === null || f.value === undefined));

  return (
    <div className="flex-1 flex flex-col bg-slate-50 overflow-hidden">
      {/* Stats bar */}
      <div className="px-4 py-3 bg-white border-b border-slate-200 flex items-center gap-6 flex-wrap">
        <StatPill label="Extracted" value={extracted.length} total={fields.length} color="slate" />
        <StatPill label="High" value={highCount} color="emerald" />
        <StatPill label="Medium" value={medCount} color="amber" />
        <StatPill label="Low" value={lowCount} color="red" />
        {missingRequired.length > 0 && (
          <StatPill label="Missing Required" value={missingRequired.length} color="red" />
        )}
        {confidence !== null && (
          <span className="text-xs text-slate-400 ml-auto">
            Classification confidence: <strong>{Math.round(confidence * 100)}%</strong>
          </span>
        )}

        {/* Write to storage */}
        <WriteButton status={storageStatus} onClick={onWriteToStorage} />
      </div>

      {/* Field table */}
      <div className="flex-1 overflow-y-auto">
        <table className="w-full text-sm">
          <thead className="bg-slate-100 sticky top-0">
            <tr>
              <th className="text-left px-4 py-2.5 text-xs font-semibold text-slate-500 uppercase tracking-wider w-1/4">
                Field
              </th>
              <th className="text-left px-4 py-2.5 text-xs font-semibold text-slate-500 uppercase tracking-wider w-1/3">
                Value
              </th>
              <th className="text-left px-4 py-2.5 text-xs font-semibold text-slate-500 uppercase tracking-wider w-24">
                Confidence
              </th>
              <th className="text-left px-4 py-2.5 text-xs font-semibold text-slate-500 uppercase tracking-wider">
                Source
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {fields.map((field) => (
              <FieldRow key={field.id} field={field} />
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function FieldRow({ field }: { field: ExtractedField }) {
  const hasValue = field.value !== null && field.value !== undefined;

  return (
    <tr className={cn("bg-white hover:bg-slate-50 transition-colors", !hasValue && "opacity-60")}>
      <td className="px-4 py-3">
        <span className="text-slate-800 font-medium">{field.label}</span>
        {field.required && <span className="text-red-400 ml-1 text-xs">*</span>}
        <p className="text-xs text-slate-400 font-mono mt-0.5">{field.id}</p>
      </td>
      <td className="px-4 py-3">
        {hasValue ? (
          <div>
            <span className="text-slate-900 font-mono text-sm">
              {formatValue(field.value, field.field_type)}
            </span>
            {field.alternatives.length > 0 && (
              <div className="mt-1 flex flex-wrap gap-1">
                {field.alternatives.slice(0, 3).map((alt, i) => (
                  <span
                    key={i}
                    className="text-xs bg-slate-100 text-slate-500 rounded px-1.5 py-0.5 font-mono"
                    title="Alternative value"
                  >
                    {String(alt)}
                  </span>
                ))}
              </div>
            )}
          </div>
        ) : (
          <span className="text-slate-300 text-sm">—</span>
        )}
      </td>
      <td className="px-4 py-3">
        <ConfidenceBadge confidence={field.confidence} />
      </td>
      <td className="px-4 py-3">
        <span className="text-xs text-slate-400">{field.source ?? "—"}</span>
      </td>
    </tr>
  );
}

function ConfidenceBadge({ confidence }: { confidence: ExtractedField["confidence"] }) {
  if (!confidence) return <span className="text-slate-300 text-xs">—</span>;
  const styles = {
    high: "bg-emerald-100 text-emerald-700",
    medium: "bg-amber-100 text-amber-700",
    low: "bg-red-100 text-red-700",
  };
  return (
    <span className={cn("text-xs font-medium rounded-full px-2 py-0.5 capitalize", styles[confidence])}>
      {confidence}
    </span>
  );
}

function StatPill({
  label,
  value,
  total,
  color,
}: {
  label: string;
  value: number;
  total?: number;
  color: "slate" | "emerald" | "amber" | "red";
}) {
  const colors = {
    slate: "text-slate-700",
    emerald: "text-emerald-600",
    amber: "text-amber-600",
    red: "text-red-600",
  };
  return (
    <div className="flex items-center gap-1.5">
      <span className={cn("font-semibold text-sm", colors[color])}>
        {value}
        {total !== undefined && <span className="text-slate-400 font-normal">/{total}</span>}
      </span>
      <span className="text-xs text-slate-400">{label}</span>
    </div>
  );
}

function WriteButton({
  status,
  onClick,
}: {
  status: Props["storageStatus"];
  onClick: () => void;
}) {
  const labels: Record<Props["storageStatus"], string> = {
    idle: "Write to Blob Storage",
    writing: "Writing…",
    written: "Written ✓",
    error: "Write Failed",
    not_configured: "Storage Not Configured",
  };

  const styles: Record<Props["storageStatus"], string> = {
    idle: "bg-blue-600 hover:bg-blue-700 text-white",
    writing: "bg-blue-400 text-white cursor-not-allowed",
    written: "bg-emerald-600 text-white cursor-default",
    error: "bg-red-100 text-red-700 border border-red-300",
    not_configured: "bg-slate-100 text-slate-400 cursor-not-allowed",
  };

  return (
    <button
      onClick={onClick}
      disabled={status !== "idle"}
      className={cn("ml-auto text-xs font-medium rounded-lg px-3 py-1.5 transition-colors", styles[status])}
    >
      {labels[status]}
    </button>
  );
}
