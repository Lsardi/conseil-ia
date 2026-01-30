import { useState } from "react";
import { CouncilResponse } from "@/lib/api";
import ReactMarkdown from "react-markdown";

interface ResponseDisplayProps {
  response: CouncilResponse;
}

const MODEL_STYLES: Record<string, { dot: string }> = {
  claude: { dot: "bg-orange-500" },
  gpt4: { dot: "bg-emerald-500" },
  gemini: { dot: "bg-blue-500" },
  mistral: { dot: "bg-purple-500" },
  cohere: { dot: "bg-pink-500" },
  deepseek: { dot: "bg-cyan-500" },
  ollama: { dot: "bg-gray-500" },
};

const MODEL_LABELS: Record<string, string> = {
  claude: "Claude", gpt4: "GPT-4", gemini: "Gemini", mistral: "Mistral",
  cohere: "Cohere", deepseek: "DeepSeek", ollama: "Ollama",
};

export default function ResponseDisplay({ response }: ResponseDisplayProps) {
  const [expandedModels, setExpandedModels] = useState<Set<string>>(new Set());
  const hasResponses = Object.keys(response.responses).length > 0;

  const toggleModel = (name: string) => {
    setExpandedModels((prev) => {
      const next = new Set(prev);
      if (next.has(name)) next.delete(name);
      else next.add(name);
      return next;
    });
  };

  return (
    <div className="space-y-4 animate-fade-in">
      {/* Synthesis */}
      {response.synthesis && (
        <div className="p-5 rounded-xl bg-[var(--bg-secondary)] border border-[var(--border)]">
          <div className="prose prose-sm max-w-none text-[var(--text-secondary)] leading-relaxed">
            <ReactMarkdown>{response.synthesis}</ReactMarkdown>
          </div>
        </div>
      )}

      {/* Individual responses */}
      {hasResponses && (
        <div className="space-y-2">
          {Object.entries(response.responses).map(([name, modelResp]) => {
            const style = MODEL_STYLES[name] || MODEL_STYLES.ollama;
            const isExpanded = expandedModels.has(name);

            return (
              <div key={name} className="rounded-xl border border-[var(--border)] overflow-hidden">
                <button
                  onClick={() => toggleModel(name)}
                  className="w-full flex items-center gap-3 px-4 py-3 bg-[var(--bg-secondary)] hover:bg-[var(--bg-tertiary)] transition-colors"
                >
                  <div className={`w-2.5 h-2.5 rounded-full ${style.dot}`} />
                  <span className="font-medium text-sm text-[var(--text-primary)]">
                    {MODEL_LABELS[name] || name}
                  </span>
                  {modelResp.error ? (
                    <span className="text-xs text-red-500">erreur</span>
                  ) : (
                    <span className="text-xs text-[var(--text-muted)]">
                      {modelResp.latency_ms.toFixed(0)}ms
                    </span>
                  )}
                  <div className="flex-1" />
                  <div className="flex items-center gap-2 text-[10px] text-[var(--text-muted)]">
                    <span>{modelResp.tokens_output} tokens</span>
                    <span>${modelResp.cost.toFixed(4)}</span>
                  </div>
                  <svg
                    className={`w-4 h-4 text-[var(--text-muted)] transition-transform ${isExpanded ? "rotate-180" : ""}`}
                    fill="none" stroke="currentColor" viewBox="0 0 24 24"
                  >
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </svg>
                </button>
                {isExpanded && (
                  <div className="px-4 py-4 border-t border-[var(--border)] animate-fade-in">
                    {modelResp.error ? (
                      <p className="text-sm text-red-500">{modelResp.error}</p>
                    ) : (
                      <div className="prose prose-sm max-w-none text-[var(--text-secondary)] leading-relaxed">
                        <ReactMarkdown>{modelResp.content}</ReactMarkdown>
                      </div>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}

      {/* Metadata */}
      <div className="flex flex-wrap items-center gap-3 text-[11px] text-[var(--text-muted)] px-1">
        <span>{response.total_latency_ms.toFixed(0)}ms</span>
        <span className="w-px h-3 bg-[var(--border)]" />
        <span>${response.total_cost.toFixed(4)}</span>
        {response.consensus_score !== null && (
          <>
            <span className="w-px h-3 bg-[var(--border)]" />
            <span>Consensus {(response.consensus_score * 100).toFixed(0)}%</span>
          </>
        )}
        {response.cached && (
          <>
            <span className="w-px h-3 bg-[var(--border)]" />
            <span className="text-emerald-500 font-medium">cache</span>
          </>
        )}
        <span className="w-px h-3 bg-[var(--border)]" />
        <span>{response.request_id}</span>
      </div>
    </div>
  );
}
