import { useRef, useState } from "react";
import { Upload, FileText, AlertCircle } from "lucide-react";

interface Props {
  onUpload: (file: File) => void;
}

export default function UploadZone({ onUpload }: Props) {
  const [dragging, setDragging] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  function handleFile(file: File | undefined) {
    if (!file) return;
    const allowed = [".pdf", ".xlsx", ".xls"];
    const valid = allowed.some((ext) => file.name.toLowerCase().endsWith(ext));
    if (!valid) {
      setError(`"${file.name}" is not supported. Upload a PDF or Excel file (.pdf, .xlsx, .xls).`);
      return;
    }
    setError(null);
    onUpload(file);
  }

  function handleDrop(e: React.DragEvent) {
    e.preventDefault();
    setDragging(false);
    handleFile(e.dataTransfer.files[0]);
  }

  function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    handleFile(e.target.files?.[0]);
    e.target.value = "";
  }

  return (
    <div
      className="flex-1 flex flex-col items-center justify-center bg-slate-50 p-12"
      onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
      onDragLeave={(e) => { if (!e.currentTarget.contains(e.relatedTarget as Node)) setDragging(false); }}
      onDrop={handleDrop}
    >
      <div
        onClick={() => inputRef.current?.click()}
        className={`
          w-full max-w-md border-2 border-dashed rounded-2xl p-12 text-center cursor-pointer transition-colors
          ${dragging
            ? "border-emerald-400 bg-emerald-50 scale-[1.01]"
            : "border-slate-300 hover:border-emerald-400 hover:bg-emerald-50/50 bg-white"
          }
        `}
      >
        <input ref={inputRef} type="file" accept=".pdf,.xlsx,.xls" className="hidden" onChange={handleFileChange} />
        <div className="flex justify-center mb-4">
          <div className={`p-4 rounded-full transition-colors ${dragging ? "bg-emerald-100" : "bg-slate-100"}`}>
            <FileText size={32} className={dragging ? "text-emerald-500" : "text-slate-400"} />
          </div>
        </div>
        <p className="text-slate-700 font-semibold text-lg mb-1">
          {dragging ? "Drop to upload" : "Drop a file here"}
        </p>
        <p className="text-slate-400 text-sm mb-4">PDF or Excel · click to browse</p>
        <div className="flex items-center justify-center gap-2">
          <Upload size={14} className="text-emerald-500" />
          <span className="text-emerald-600 text-sm font-medium">
            Rent rolls, operating statements, tax documents
          </span>
        </div>
      </div>

      {error && (
        <div className="mt-4 flex items-center gap-2 bg-red-50 border border-red-200 text-red-700 text-sm rounded-lg px-4 py-2.5 max-w-md w-full">
          <AlertCircle size={15} className="flex-shrink-0" />
          {error}
        </div>
      )}
    </div>
  );
}
