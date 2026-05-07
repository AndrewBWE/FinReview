import { useState, useCallback, useEffect, useRef } from "react";
import { Loader2, Upload, Mail, FolderCheck, FolderX } from "lucide-react";
import { cn, docTypeLabel } from "./lib/utils";
import type { DocumentRecord, PipelineResult, TabId } from "./types";

import SidebarNav from "./components/SidebarNav";
import UploadZone from "./components/UploadZone";
import SourceViewer from "./components/SourceViewer";
import OcrViewer from "./components/OcrViewer";
import ExtractionResults from "./components/ExtractionResults";
import SchemaViewer from "./components/SchemaViewer";
import PromptViewer from "./components/PromptViewer";
import PipelineTrace from "./components/PipelineTrace";

const TABS: { id: TabId; label: string }[] = [
  { id: "extracted", label: "Extracted Data" },
  { id: "source", label: "Source PDF" },
  { id: "ocr", label: "OCR Text" },
  { id: "schema", label: "Schema" },
  { id: "prompts", label: "Prompts" },
  { id: "trace", label: "Pipeline Trace" },
];

type StorageStatus = "idle" | "writing" | "written" | "error" | "not_configured";
type SortStatus = "idle" | "sorting" | "sorted" | "no_folder" | "error";
type SortResult = { status: SortStatus; deal_path?: string; blobs?: { blob_name: string }[] };

export default function App() {
  const [documents, setDocuments] = useState<DocumentRecord[]>([]);
  const [selectedDocId, setSelectedDocId] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<TabId>("extracted");
  const [storageStatus, setStorageStatus] = useState<Record<string, StorageStatus>>({});
  const [sortStatus, setSortStatus] = useState<Record<string, SortResult>>({});
  const [senderEmail, setSenderEmail] = useState("");
  const [loanNumber, setLoanNumber] = useState("");
  const [globalDragging, setGlobalDragging] = useState(false);
  const pollingRefs = useRef<Record<string, ReturnType<typeof setInterval>>>({});
  const dragCounter = useRef(0);

  const selectedDoc = documents.find((d) => d.id === selectedDocId) ?? null;

  const updateDocument = useCallback((id: string, result: PipelineResult) => {
    setDocuments((prev) =>
      prev.map((doc) =>
        doc.id === id ? { ...doc, status: result.status, result } : doc
      )
    );
  }, []);

  const startPolling = useCallback(
    (id: string) => {
      if (pollingRefs.current[id]) return;
      const interval = setInterval(async () => {
        try {
          const res = await fetch(`/pipeline/${id}`);
          const result: PipelineResult = await res.json();
          updateDocument(id, result);
          if (result.status === "complete" || result.status === "error") {
            clearInterval(pollingRefs.current[id]);
            delete pollingRefs.current[id];
          }
        } catch {
          clearInterval(pollingRefs.current[id]);
          delete pollingRefs.current[id];
        }
      }, 1500);
      pollingRefs.current[id] = interval;
    },
    [updateDocument]
  );

  const handleUpload = useCallback(
    async (file: File) => {
      const sourceUrl = URL.createObjectURL(file);
      const tempDoc: DocumentRecord = {
        id: "pending",
        filename: file.name,
        status: "processing",
        sourceUrl,
        result: null,
      };

      const formData = new FormData();
      formData.append("file", file);

      try {
        const res = await fetch("/pipeline/run", { method: "POST", body: formData });
        const { id } = await res.json();

        const doc: DocumentRecord = { ...tempDoc, id };
        setDocuments((prev) => [doc, ...prev]);
        setSelectedDocId(id);
        setActiveTab("extracted");
        startPolling(id);
      } catch (err) {
        console.error("Upload failed", err);
      }
    },
    [startPolling]
  );

  const handleGlobalDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      dragCounter.current = 0;
      setGlobalDragging(false);
      const file = e.dataTransfer.files[0];
      if (!file) return;
      const allowed = [".pdf", ".xlsx", ".xls"];
      if (!allowed.some((ext) => file.name.toLowerCase().endsWith(ext))) return;
      handleUpload(file);
    },
    [handleUpload]
  );

  const handleSort = useCallback(async () => {
    if (!selectedDocId) return;
    setSortStatus((s) => ({ ...s, [selectedDocId]: { status: "sorting" } }));
    try {
      const res = await fetch(`/pipeline/${selectedDocId}/sort`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          loan_number: loanNumber.trim() || null,
          am_email: senderEmail.trim() || null,
        }),
      });
      const data = await res.json();
      if (data.status === "sorted") {
        setSortStatus((s) => ({
          ...s,
          [selectedDocId]: { status: "sorted", deal_path: data.deal_path, blobs: data.blobs },
        }));
      } else if (data.status === "no_folder") {
        setSortStatus((s) => ({ ...s, [selectedDocId]: { status: "no_folder" } }));
      } else {
        setSortStatus((s) => ({ ...s, [selectedDocId]: { status: "error" } }));
      }
    } catch {
      setSortStatus((s) => ({ ...s, [selectedDocId]: { status: "error" } }));
    }
  }, [selectedDocId, senderEmail, loanNumber]);

  const handleWriteToStorage = useCallback(async () => {
    if (!selectedDocId) return;
    setStorageStatus((s) => ({ ...s, [selectedDocId]: "writing" }));
    try {
      const res = await fetch(`/pipeline/${selectedDocId}/write`, { method: "POST" });
      const result = await res.json();
      if (result.status === "written") {
        setStorageStatus((s) => ({ ...s, [selectedDocId]: "written" }));
      } else if (result.status === "not_configured") {
        setStorageStatus((s) => ({ ...s, [selectedDocId]: "not_configured" }));
      } else {
        setStorageStatus((s) => ({ ...s, [selectedDocId]: "error" }));
      }
    } catch {
      setStorageStatus((s) => ({ ...s, [selectedDocId]: "error" }));
    }
  }, [selectedDocId]);

  // Cleanup blob URLs on unmount
  useEffect(() => {
    return () => {
      documents.forEach((d) => { if (d.sourceUrl) URL.revokeObjectURL(d.sourceUrl); });
      Object.values(pollingRefs.current).forEach(clearInterval);
    };
  }, []);

  return (
    <div
      className="flex h-screen bg-slate-50 overflow-hidden"
      onDragEnter={(e) => { e.preventDefault(); dragCounter.current++; setGlobalDragging(true); }}
      onDragLeave={() => { dragCounter.current--; if (dragCounter.current === 0) setGlobalDragging(false); }}
      onDragOver={(e) => e.preventDefault()}
      onDrop={handleGlobalDrop}
    >
      {globalDragging && selectedDoc && (
        <div className="absolute inset-0 z-50 bg-slate-900/60 flex items-center justify-center pointer-events-none">
          <div className="bg-white rounded-2xl px-16 py-12 text-center shadow-2xl border-2 border-dashed border-emerald-400">
            <Upload size={36} className="text-emerald-500 mx-auto mb-3" />
            <p className="text-slate-800 font-semibold text-lg">Drop PDF to upload</p>
          </div>
        </div>
      )}
      <SidebarNav
        documents={documents}
        selectedDocId={selectedDocId}
        onSelectDoc={setSelectedDocId}
        onUpload={handleUpload}
      />

      <main className="flex-1 flex flex-col min-w-0">
        {/* Simulated email metadata bar */}
        <div className="bg-slate-100 border-b border-slate-200 px-5 py-2 flex items-center gap-3 flex-wrap">
          <div className="flex items-center gap-1.5 text-slate-500">
            <Mail size={13} />
            <span className="text-xs font-medium uppercase tracking-wide">Simulated Email</span>
          </div>
          <div className="flex items-center gap-1.5">
            <label className="text-xs text-slate-500">From:</label>
            <input
              type="email"
              placeholder="sender@bwe.com"
              value={senderEmail}
              onChange={(e) => setSenderEmail(e.target.value)}
              className="text-xs border border-slate-300 rounded px-2 py-1 bg-white w-48 focus:outline-none focus:ring-1 focus:ring-blue-400"
            />
          </div>
          <div className="flex items-center gap-1.5">
            <label className="text-xs text-slate-500">Loan #:</label>
            <input
              type="text"
              placeholder="optional"
              value={loanNumber}
              onChange={(e) => setLoanNumber(e.target.value)}
              className="text-xs border border-slate-300 rounded px-2 py-1 bg-white w-32 focus:outline-none focus:ring-1 focus:ring-blue-400"
            />
          </div>
        </div>

        {selectedDoc ? (
          <>
            {/* Doc header */}
            <div className="bg-white border-b border-slate-200 px-5 py-3 flex items-center gap-3 flex-wrap">
              <div className="flex items-center gap-2 min-w-0">
                {selectedDoc.status === "processing" && (
                  <Loader2 size={15} className="text-amber-500 animate-spin flex-shrink-0" />
                )}
                <h1 className="text-slate-800 font-semibold text-sm truncate">
                  {selectedDoc.filename}
                </h1>
              </div>
              {selectedDoc.result && (
                <>
                  <span className="text-slate-200">·</span>
                  <span className="text-xs font-medium text-slate-500">
                    {docTypeLabel(selectedDoc.result.document_type)}
                  </span>
                  {selectedDoc.result.page_count > 0 && (
                    <>
                      <span className="text-slate-200">·</span>
                      <span className="text-xs text-slate-400">
                        {selectedDoc.result.page_count}p
                      </span>
                    </>
                  )}
                  {selectedDoc.result.status === "error" && (
                    <span className="text-xs text-red-500 font-medium ml-1">
                      Error: {selectedDoc.result.error}
                    </span>
                  )}
                </>
              )}
              {/* Sort button + result */}
              {selectedDoc.status === "complete" && (
                <div className="ml-auto flex items-center gap-2 flex-shrink-0">
                  <SortButton
                    sortResult={sortStatus[selectedDocId ?? ""] ?? { status: "idle" }}
                    onSort={handleSort}
                  />
                </div>
              )}
            </div>

            {/* Tab bar */}
            <div className="bg-white border-b border-slate-200 px-4 flex">
              {TABS.map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={cn(
                    "text-sm px-3 py-2.5 border-b-2 transition-colors whitespace-nowrap",
                    activeTab === tab.id
                      ? "border-blue-600 text-blue-700 font-medium"
                      : "border-transparent text-slate-500 hover:text-slate-700 hover:border-slate-300"
                  )}
                >
                  {tab.label}
                </button>
              ))}
            </div>

            {/* Tab content */}
            <div className="flex-1 flex flex-col min-h-0 overflow-hidden">
              {selectedDoc.status === "processing" && activeTab !== "trace" ? (
                <ProcessingOverlay trace={selectedDoc.result?.trace ?? []} />
              ) : (
                <>
                  {activeTab === "extracted" && (
                    <ExtractionResults
                      fields={selectedDoc.result?.extracted_fields ?? []}
                      documentType={selectedDoc.result?.document_type ?? null}
                      confidence={selectedDoc.result?.classification_confidence ?? null}
                      onWriteToStorage={handleWriteToStorage}
                      storageStatus={storageStatus[selectedDocId ?? ""] ?? "idle"}
                    />
                  )}
                  {activeTab === "source" && (
                    <SourceViewer
                      sourceUrl={selectedDoc.sourceUrl}
                      filename={selectedDoc.filename}
                    />
                  )}
                  {activeTab === "ocr" && (
                    <OcrViewer pages={selectedDoc.result?.ocr_pages ?? []} />
                  )}
                  {activeTab === "schema" && (
                    <SchemaViewer
                      schema={selectedDoc.result?.schema ?? null}
                      documentType={selectedDoc.result?.document_type ?? null}
                    />
                  )}
                  {activeTab === "prompts" && (
                    <PromptViewer prompts={selectedDoc.result?.prompts ?? null} />
                  )}
                  {activeTab === "trace" && (
                    <PipelineTrace
                      trace={selectedDoc.result?.trace ?? []}
                      error={selectedDoc.result?.error}
                    />
                  )}
                </>
              )}
            </div>
          </>
        ) : (
          <UploadZone onUpload={handleUpload} />
        )}
      </main>
    </div>
  );
}

function SortButton({
  sortResult,
  onSort,
}: {
  sortResult: SortResult;
  onSort: () => void;
}) {
  const { status, deal_path, blobs } = sortResult;

  if (status === "sorted") {
    return (
      <div className="flex items-center gap-1.5 text-emerald-600">
        <FolderCheck size={14} />
        <span className="text-xs font-medium">
          Sorted → {deal_path}
          {blobs && blobs.length > 1 && ` (${blobs.length} files)`}
        </span>
      </div>
    );
  }

  if (status === "no_folder") {
    return (
      <div className="flex items-center gap-1.5 text-amber-600">
        <FolderX size={14} />
        <span className="text-xs font-medium">No deal folder found</span>
      </div>
    );
  }

  if (status === "error") {
    return (
      <div className="flex items-center gap-1.5 text-red-500">
        <FolderX size={14} />
        <span className="text-xs font-medium">Sort failed</span>
      </div>
    );
  }

  return (
    <button
      onClick={onSort}
      disabled={status === "sorting"}
      className={cn(
        "flex items-center gap-1.5 text-xs font-medium px-3 py-1.5 rounded border transition-colors",
        status === "sorting"
          ? "border-slate-200 text-slate-400 bg-slate-50 cursor-not-allowed"
          : "border-blue-300 text-blue-700 bg-blue-50 hover:bg-blue-100"
      )}
    >
      {status === "sorting" ? (
        <Loader2 size={12} className="animate-spin" />
      ) : (
        <FolderCheck size={12} />
      )}
      {status === "sorting" ? "Sorting…" : "Sort to Blob"}
    </button>
  );
}

function ProcessingOverlay({ trace }: { trace: { label: string; status: string }[] }) {
  const currentStep = trace.findLast((t) => t.status === "running");
  return (
    <div className="flex-1 flex items-center justify-center bg-slate-50">
      <div className="text-center">
        <Loader2 size={36} className="text-emerald-500 animate-spin mx-auto mb-4" />
        <p className="text-slate-700 font-medium">Processing document…</p>
        {currentStep && (
          <p className="text-slate-400 text-sm mt-1">{currentStep.label}</p>
        )}
        <p className="text-slate-400 text-xs mt-3">
          Switch to <strong>Pipeline Trace</strong> to watch live progress
        </p>
      </div>
    </div>
  );
}
