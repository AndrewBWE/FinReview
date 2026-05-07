import { cn } from "../lib/utils";
import type { Schema } from "../types";

interface Props {
  schema: Schema | null;
  documentType: string | null;
}

export default function SchemaViewer({ schema, documentType }: Props) {
  if (!schema) {
    return (
      <div className="flex-1 flex items-center justify-center bg-slate-50">
        <div className="text-center">
          <p className="text-slate-400 text-sm">
            {documentType === "unknown" || !documentType
              ? "No schema — document type could not be determined"
              : "Schema not available"}
          </p>
        </div>
      </div>
    );
  }

  const required = schema.fields.filter((f) => f.required);
  const optional = schema.fields.filter((f) => !f.required);

  return (
    <div className="flex-1 flex flex-col bg-slate-50 overflow-hidden">
      {/* Header */}
      <div className="px-4 py-3 bg-white border-b border-slate-200 flex items-center gap-4">
        <div>
          <p className="text-sm font-semibold text-slate-800">{schema.label}</p>
          <p className="text-xs text-slate-400">
            {required.length} required · {optional.length} optional
          </p>
        </div>
        <span className="ml-auto font-mono text-xs bg-slate-100 text-slate-500 rounded px-2 py-1">
          {schema.type}
        </span>
      </div>

      {/* Field table */}
      <div className="flex-1 overflow-y-auto">
        <table className="w-full text-sm">
          <thead className="bg-slate-100 sticky top-0">
            <tr>
              <th className="text-left px-4 py-2.5 text-xs font-semibold text-slate-500 uppercase tracking-wider">
                Field ID
              </th>
              <th className="text-left px-4 py-2.5 text-xs font-semibold text-slate-500 uppercase tracking-wider">
                Label
              </th>
              <th className="text-left px-4 py-2.5 text-xs font-semibold text-slate-500 uppercase tracking-wider w-24">
                Type
              </th>
              <th className="text-left px-4 py-2.5 text-xs font-semibold text-slate-500 uppercase tracking-wider w-20">
                Required
              </th>
              <th className="text-left px-4 py-2.5 text-xs font-semibold text-slate-500 uppercase tracking-wider">
                Notes
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {schema.fields.map((field) => (
              <tr key={field.id} className="bg-white hover:bg-slate-50 transition-colors">
                <td className="px-4 py-3 font-mono text-xs text-slate-600">{field.id}</td>
                <td className="px-4 py-3 text-slate-800 font-medium">{field.label}</td>
                <td className="px-4 py-3">
                  <span className="text-xs bg-slate-100 text-slate-500 rounded px-1.5 py-0.5 font-mono">
                    {field.field_type}
                  </span>
                </td>
                <td className="px-4 py-3">
                  {field.required ? (
                    <span className="text-xs font-semibold text-red-500">Yes</span>
                  ) : (
                    <span className="text-xs text-slate-300">—</span>
                  )}
                </td>
                <td className="px-4 py-3 text-xs text-slate-400">{field.description || "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
