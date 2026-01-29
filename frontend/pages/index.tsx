import { useState, useEffect } from "react";
import QuestionForm from "@/components/QuestionForm";
import ResponseDisplay from "@/components/ResponseDisplay";
import Header from "@/components/Header";
import ModelSelector from "@/components/ModelSelector";
import { askCouncil, getModels, CouncilResponse, ModelInfo } from "@/lib/api";

interface HomeProps {
  darkMode: boolean;
  toggleDarkMode: () => void;
}

export default function Home({ darkMode, toggleDarkMode }: HomeProps) {
  const [response, setResponse] = useState<CouncilResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [models, setModels] = useState<ModelInfo[]>([]);
  const [selectedModels, setSelectedModels] = useState<string[]>([
    "claude",
    "gpt4",
    "gemini",
  ]);
  const [mode, setMode] = useState<"synthesis" | "detailed" | "debate">(
    "synthesis"
  );

  useEffect(() => {
    getModels()
      .then((data) => setModels(data.models))
      .catch(() => setModels([]));
  }, []);

  const handleSubmit = async (question: string) => {
    setLoading(true);
    setError(null);
    setResponse(null);

    try {
      const result = await askCouncil({
        question,
        mode,
        models: selectedModels,
        optimize_prompts: true,
      });
      setResponse(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erreur inconnue");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 transition-colors">
      <Header darkMode={darkMode} toggleDarkMode={toggleDarkMode} />

      <main className="max-w-6xl mx-auto px-4 py-8">
        {/* Sélection du mode */}
        <div className="mb-6 flex flex-wrap gap-3 justify-center">
          {(["synthesis", "detailed", "debate"] as const).map((m) => (
            <button
              key={m}
              onClick={() => setMode(m)}
              className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                mode === m
                  ? "bg-primary-600 text-white shadow-lg"
                  : "bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 border border-gray-200 dark:border-gray-700 hover:bg-gray-100 dark:hover:bg-gray-700"
              }`}
            >
              {m === "synthesis"
                ? "Synthese"
                : m === "detailed"
                ? "Detail"
                : "Debat"}
            </button>
          ))}
        </div>

        {/* Sélection des modèles */}
        <ModelSelector
          models={models}
          selected={selectedModels}
          onChange={setSelectedModels}
        />

        {/* Formulaire */}
        <QuestionForm onSubmit={handleSubmit} loading={loading} />

        {/* Erreur */}
        {error && (
          <div className="mt-6 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg text-red-700 dark:text-red-400 animate-fade-in">
            <strong>Erreur :</strong> {error}
          </div>
        )}

        {/* Chargement */}
        {loading && (
          <div className="mt-8 text-center animate-fade-in">
            <div className="inline-flex items-center gap-2 text-primary-600 dark:text-primary-400">
              <span className="loading-dot" />
              <span className="loading-dot" />
              <span className="loading-dot" />
              <span className="ml-2 text-lg">Consultation du conseil en cours...</span>
            </div>
          </div>
        )}

        {/* Réponse */}
        {response && <ResponseDisplay response={response} />}
      </main>
    </div>
  );
}
