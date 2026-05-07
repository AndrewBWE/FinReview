import { FileText } from "lucide-react";

interface Props {
  sourceUrl: string | null;
  filename: string;
}

export default function SourceViewer({ sourceUrl, filename }: Props) {
  if (!sourceUrl) {
    return (
      <div className="flex-1 flex items-center justify-center bg-slate-50">
        <div className="text-center">
          <FileText size={40} className="text-slate-300 mx-auto mb-3" />
          <p className="text-slate-400 text-sm">Source PDF not available</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 flex flex-col bg-slate-100 h-full">
      <div className="px-4 py-2 bg-white border-b border-slate-200 text-xs text-slate-500 font-mono truncate">
        {filename}
      </div>
      <iframe
        src={sourceUrl}
        title={filename}
        className="flex-1 w-full border-0"
        style={{ height: "calc(100vh - 140px)" }}
      />
    </div>
  );
}
