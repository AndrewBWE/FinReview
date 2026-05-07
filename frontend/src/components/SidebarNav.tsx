import { useRef } from "react";
import { FileText, Upload, CheckCircle, XCircle, Loader2, BarChart3 } from "lucide-react";
import { cn, docTypeLabel } from "../lib/utils";
import type { DocumentRecord } from "../types";

interface Props {
  documents: DocumentRecord[];
  selectedDocId: string | null;
  onSelectDoc: (id: string) => void;
  onUpload: (file: File) => void;
}

export default function SidebarNav({ documents, selectedDocId, onSelectDoc, onUpload }: Props) {
  const inputRef = useRef<HTMLInputElement>(null);

  function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (file) {
      onUpload(file);
      e.target.value = "";
    }
  }

  return (
    <aside className="w-64 flex-shrink-0 bg-slate-900 flex flex-col h-screen">
      {/* Logo */}
      <div className="px-5 py-5 border-b border-slate-700">
        <div className="flex items-center gap-2">
          <BarChart3 className="text-emerald-400" size={22} />
          <span className="text-white font-semibold text-lg tracking-tight">FinReview</span>
        </div>
        <p className="text-slate-400 text-xs mt-1">Financial Document Extraction</p>
      </div>

      {/* Upload */}
      <div className="px-4 py-4 border-b border-slate-700">
        <input
          ref={inputRef}
          type="file"
          accept=".pdf,.xlsx,.xls"
          className="hidden"
          onChange={handleFileChange}
        />
        <button
          onClick={() => inputRef.current?.click()}
          className="w-full flex items-center justify-center gap-2 bg-emerald-600 hover:bg-emerald-500 text-white text-sm font-medium rounded-lg px-3 py-2.5 transition-colors"
        >
          <Upload size={15} />
          Upload PDF
        </button>
      </div>

      {/* Document list */}
      <div className="flex-1 overflow-y-auto py-3">
        {documents.length === 0 ? (
          <p className="text-slate-500 text-xs px-5 mt-2">No documents yet</p>
        ) : (
          <ul className="space-y-0.5 px-2">
            {documents.map((doc) => (
              <li key={doc.id}>
                <button
                  onClick={() => onSelectDoc(doc.id)}
                  className={cn(
                    "w-full text-left rounded-lg px-3 py-2.5 transition-colors group",
                    selectedDocId === doc.id
                      ? "bg-slate-700 border-l-2 border-emerald-400 pl-2.5"
                      : "hover:bg-slate-800 border-l-2 border-transparent"
                  )}
                >
                  <div className="flex items-start gap-2">
                    <StatusIcon status={doc.status} />
                    <div className="min-w-0 flex-1">
                      <p className="text-slate-100 text-sm font-medium truncate leading-tight">
                        {doc.filename}
                      </p>
                      <p className="text-slate-400 text-xs mt-0.5">
                        {doc.status === "processing"
                          ? "Processing…"
                          : doc.status === "error"
                          ? "Error"
                          : docTypeLabel(doc.result?.document_type ?? null)}
                      </p>
                    </div>
                  </div>
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>

      {/* Footer */}
      <div className="px-5 py-3 border-t border-slate-700">
        <p className="text-slate-500 text-xs">
          {documents.filter((d) => d.status === "complete").length} extracted ·{" "}
          {documents.filter((d) => d.status === "processing").length} processing
        </p>
      </div>
    </aside>
  );
}

function StatusIcon({ status }: { status: DocumentRecord["status"] }) {
  if (status === "processing")
    return <Loader2 size={15} className="text-amber-400 animate-spin mt-0.5 flex-shrink-0" />;
  if (status === "complete")
    return <CheckCircle size={15} className="text-emerald-400 mt-0.5 flex-shrink-0" />;
  return <XCircle size={15} className="text-red-400 mt-0.5 flex-shrink-0" />;
}
