import { useState } from "react";
import { CheckCircle, XCircle, Loader2, MinusCircle, ChevronDown, ChevronRight } from "lucide-react";
import { cn } from "../lib/utils";
import type { TraceEntry } from "../types";

interface Props {
  trace: TraceEntry[];
  error?: string;
}

export default function PipelineTrace({ trace, error }: Props) {
  if (!trace.length) {
    return (
      <div className="flex-1 flex items-center justify-center bg-slate-50">
        <p className="text-slate-400 text-sm">Pipeline not yet started</p>
      </div>
    );
  }

  return (
    <div className="flex-1 flex flex-col bg-slate-50 overflow-hidden">
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg px-4 py-3 text-sm text-red-700">
            <strong>Pipeline Error:</strong> {error}
          </div>
        )}
        {trace.map((entry) => (
          <TraceCard key={entry.step} entry={entry} />
        ))}
      </div>
    </div>
  );
}

function TraceCard({ entry }: { entry: TraceEntry }) {
  const [expanded, setExpanded] = useState(entry.status === "error");

  const statusConfig = {
    running: { icon: <Loader2 size={16} className="animate-spin text-amber-500" />, bg: "bg-amber-50 border-amber-200" },
    success: { icon: <CheckCircle size={16} className="text-emerald-500" />, bg: "bg-white border-slate-200" },
    error: { icon: <XCircle size={16} className="text-red-500" />, bg: "bg-red-50 border-red-200" },
    skipped: { icon: <MinusCircle size={16} className="text-slate-400" />, bg: "bg-slate-50 border-slate-200" },
  };

  const { icon, bg } = statusConfig[entry.status];

  return (
    <div className={cn("rounded-lg border overflow-hidden", bg)}>
      <button
        onClick={() => setExpanded((v) => !v)}
        className="w-full flex items-center gap-3 px-4 py-3 text-left hover:bg-black/5 transition-colors"
      >
        {icon}
        <span className="flex-1 text-sm font-medium text-slate-800">{entry.label}</span>
        {entry.duration_ms > 0 && (
          <span className="text-xs text-slate-400 mr-2">{entry.duration_ms.toLocaleString()}ms</span>
        )}
        {entry.status === "running" ? null : expanded ? (
          <ChevronDown size={14} className="text-slate-400 flex-shrink-0" />
        ) : (
          <ChevronRight size={14} className="text-slate-400 flex-shrink-0" />
        )}
      </button>

      {expanded && entry.status !== "running" && (
        <div className="border-t border-current border-opacity-10 px-4 pb-4 pt-3 space-y-3">
          {Object.keys(entry.input).length > 0 && (
            <JsonBlock label="Input" data={entry.input} />
          )}
          {Object.keys(entry.output).length > 0 && (
            <JsonBlock label="Output" data={entry.output} />
          )}
        </div>
      )}
    </div>
  );
}

function JsonBlock({ label, data }: { label: string; data: Record<string, unknown> }) {
  return (
    <div>
      <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1.5">{label}</p>
      <pre className="text-xs font-mono bg-slate-900 text-slate-100 rounded-lg p-3 overflow-x-auto whitespace-pre-wrap">
        {JSON.stringify(data, null, 2)}
      </pre>
    </div>
  );
}
