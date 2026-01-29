import { CouncilResponse } from "@/lib/api";
import ReactMarkdown from "react-markdown";

interface ResponseDisplayProps {
  response: CouncilResponse;
}

const MODEL_COLORS: Record<string, string> = {
  claude: "border-l-orange-500",
  gpt4: "border-l-green-500",
  gemini: "border-l-blue-500",
  mistral: "border-l-purple-500",
  cohere: "border-l-pink-500",
  deepseek: "border-l-cyan-500",
  ollama: "border-l-gray-500",
};

export default function ResponseDisplay({ response }: ResponseDisplayProps) {
  return (
    <div className="mt-8 space-y-6 animate-fade-in">
      {/* Métadonnées */}
      <div className="flex flex-wrap gap-4 justify-center text-sm text-gray-500 dark:text-gray-400">
        <span>
          Latence: {response.total_latency_ms.toFixed(0)}ms
        </span>
        <span>
          Cout: ${response.total_cost.toFixed(4)}
        </span>
        {response.consensus_score !== null && (
          <span>
            Consensus: {(response.consensus_score * 100).toFixed(0)}%
          </span>
        )}
        {response.cached && (
          <span className="text-green-600 dark:text-green-400 font-medium">
            Cache
          </span>
        )}
        <span className="text-xs text-gray-400">ID: {response.request_id}</span>
      </div>

      {/* Synthèse */}
      {response.synthesis && (
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6">
          <div className="prose dark:prose-invert max-w-none">
            <ReactMarkdown>{response.synthesis}</ReactMarkdown>
          </div>
        </div>
      )}

      {/* Réponses individuelles */}
      {Object.keys(response.responses).length > 0 && (
        <div>
          <h3 className="text-lg font-semibold text-gray-700 dark:text-gray-300 mb-4">
            Reponses individuelles
          </h3>
          <div className="grid gap-4 md:grid-cols-2">
            {Object.entries(response.responses).map(([name, modelResp]) => (
              <div
                key={name}
                className={`bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 border-l-4 ${
                  MODEL_COLORS[name] || "border-l-gray-500"
                } p-4`}
              >
                <div className="flex items-center justify-between mb-3">
                  <h4 className="font-semibold text-gray-900 dark:text-white capitalize">
                    {name}
                  </h4>
                  <div className="flex gap-2 text-xs text-gray-400">
                    <span>{modelResp.latency_ms.toFixed(0)}ms</span>
                    <span>${modelResp.cost.toFixed(4)}</span>
                  </div>
                </div>

                {modelResp.error ? (
                  <p className="text-red-500 text-sm">
                    Erreur: {modelResp.error}
                  </p>
                ) : (
                  <div className="prose dark:prose-invert prose-sm max-w-none">
                    <ReactMarkdown>{modelResp.content}</ReactMarkdown>
                  </div>
                )}

                <div className="mt-3 flex gap-3 text-xs text-gray-400">
                  <span>In: {modelResp.tokens_input} tokens</span>
                  <span>Out: {modelResp.tokens_output} tokens</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
