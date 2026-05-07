import { useState } from "react";
import { cn } from "../lib/utils";
import type { PromptPair } from "../types";

interface Props {
  prompts: {
    classification: PromptPair;
    extraction: PromptPair | null;
  } | null;
}

type Section = "classification" | "extraction";
type PromptTab = "system" | "user" | "response";

export default function PromptViewer({ prompts }: Props) {
  const [section, setSection] = useState<Section>("classification");
  const [tab, setTab] = useState<PromptTab>("system");

  if (!prompts) {
    return (
      <div className="flex-1 flex items-center justify-center bg-slate-50">
        <p className="text-slate-400 text-sm">No prompt data — pipeline not yet complete</p>
      </div>
    );
  }

  const current = section === "classification" ? prompts.classification : prompts.extraction;

  return (
    <div className="flex-1 flex flex-col bg-slate-50 overflow-hidden">
      {/* Section selector */}
      <div className="px-4 py-3 bg-white border-b border-slate-200 flex items-center gap-2">
        {(["classification", "extraction"] as Section[]).map((s) => {
          const disabled = s === "extraction" && !prompts.extraction;
          return (
            <button
              key={s}
              onClick={() => { if (!disabled) setSection(s); }}
              disabled={disabled}
              className={cn(
                "text-sm font-medium rounded-lg px-3 py-1.5 capitalize transition-colors",
                section === s && !disabled
                  ? "bg-slate-900 text-white"
                  : disabled
                  ? "text-slate-300 cursor-not-allowed"
                  : "text-slate-500 hover:text-slate-800 hover:bg-slate-100"
              )}
            >
              {s}
            </button>
          );
        })}
      </div>

      {current ? (
        <>
          {/* Prompt type tabs */}
          <div className="flex border-b border-slate-200 bg-white px-4">
            {(["system", "user", "response"] as PromptTab[]).map((t) => (
              <button
                key={t}
                onClick={() => setTab(t)}
                className={cn(
                  "text-sm px-3 py-2.5 capitalize border-b-2 transition-colors",
                  tab === t
                    ? "border-blue-600 text-blue-700 font-medium"
                    : "border-transparent text-slate-500 hover:text-slate-700"
                )}
              >
                {t === "response" ? "LLM Response" : `${t.charAt(0).toUpperCase() + t.slice(1)} Prompt`}
              </button>
            ))}
          </div>

          {/* Content */}
          <div className="flex-1 overflow-y-auto p-4">
            <div className="bg-white rounded-lg border border-slate-200 p-4">
              <pre className="text-xs text-slate-700 font-mono whitespace-pre-wrap leading-relaxed">
                {current[tab] || "(empty)"}
              </pre>
            </div>
          </div>
        </>
      ) : (
        <div className="flex-1 flex items-center justify-center">
          <p className="text-slate-400 text-sm">No extraction prompt — document type not matched to a schema</p>
        </div>
      )}
    </div>
  );
}
