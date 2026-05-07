import { useState } from "react";
import { ChevronLeft, ChevronRight, Table2 } from "lucide-react";
import type { OcrPage, OcrTable } from "../types";

interface Props {
  pages: OcrPage[];
}

export default function OcrViewer({ pages }: Props) {
  const [pageIndex, setPageIndex] = useState(0);

  if (!pages.length) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <p className="text-slate-400 text-sm">No OCR data available</p>
      </div>
    );
  }

  const page = pages[pageIndex];

  return (
    <div className="flex-1 flex flex-col bg-slate-50 overflow-hidden">
      {/* Page nav */}
      <div className="flex items-center gap-3 px-4 py-2.5 bg-white border-b border-slate-200">
        <button
          onClick={() => setPageIndex((i) => Math.max(0, i - 1))}
          disabled={pageIndex === 0}
          className="p-1 rounded hover:bg-slate-100 disabled:opacity-30 transition-colors"
        >
          <ChevronLeft size={16} />
        </button>
        <span className="text-sm text-slate-600">
          Page <strong>{page.page_number}</strong> of <strong>{pages.length}</strong>
        </span>
        <button
          onClick={() => setPageIndex((i) => Math.min(pages.length - 1, i + 1))}
          disabled={pageIndex === pages.length - 1}
          className="p-1 rounded hover:bg-slate-100 disabled:opacity-30 transition-colors"
        >
          <ChevronRight size={16} />
        </button>
        {page.tables.length > 0 && (
          <span className="ml-auto flex items-center gap-1 text-xs text-slate-400">
            <Table2 size={13} />
            {page.tables.length} table{page.tables.length !== 1 ? "s" : ""} detected
          </span>
        )}
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {/* Raw text */}
        <div className="bg-white rounded-lg border border-slate-200 p-4">
          <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3">
            Extracted Text
          </p>
          <pre className="text-xs text-slate-700 font-mono whitespace-pre-wrap leading-relaxed">
            {page.text || "(no text on this page)"}
          </pre>
        </div>

        {/* Tables */}
        {page.tables.map((table, i) => (
          <OcrTableView key={i} table={table} index={i} />
        ))}
      </div>
    </div>
  );
}

function OcrTableView({ table, index }: { table: OcrTable; index: number }) {
  const grid: string[][] = Array.from({ length: table.row_count }, () =>
    Array(table.column_count).fill("")
  );
  for (const cell of table.cells) {
    if (cell.row < table.row_count && cell.col < table.column_count) {
      grid[cell.row][cell.col] = cell.content;
    }
  }

  return (
    <div className="bg-white rounded-lg border border-slate-200 p-4">
      <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3">
        Table {index + 1} — {table.row_count} rows × {table.column_count} columns
      </p>
      <div className="overflow-x-auto">
        <table className="text-xs border-collapse w-full">
          <tbody>
            {grid.map((row, ri) => (
              <tr key={ri} className={ri === 0 ? "bg-slate-50 font-semibold" : "hover:bg-slate-50"}>
                {row.map((cell, ci) => (
                  <td
                    key={ci}
                    className="border border-slate-200 px-2 py-1.5 text-slate-700 max-w-48 truncate"
                    title={cell}
                  >
                    {cell}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
