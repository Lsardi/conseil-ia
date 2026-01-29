import { ModelInfo } from "@/lib/api";

interface ModelSelectorProps {
  models: ModelInfo[];
  selected: string[];
  onChange: (models: string[]) => void;
}

const MODEL_LABELS: Record<string, string> = {
  claude: "Claude",
  gpt4: "GPT-4",
  gemini: "Gemini",
  mistral: "Mistral",
  cohere: "Cohere",
  deepseek: "DeepSeek",
  ollama: "Ollama (local)",
};

const MODEL_COLORS: Record<string, string> = {
  claude: "bg-orange-100 dark:bg-orange-900/30 border-orange-300 dark:border-orange-700 text-orange-800 dark:text-orange-300",
  gpt4: "bg-green-100 dark:bg-green-900/30 border-green-300 dark:border-green-700 text-green-800 dark:text-green-300",
  gemini: "bg-blue-100 dark:bg-blue-900/30 border-blue-300 dark:border-blue-700 text-blue-800 dark:text-blue-300",
  mistral: "bg-purple-100 dark:bg-purple-900/30 border-purple-300 dark:border-purple-700 text-purple-800 dark:text-purple-300",
  cohere: "bg-pink-100 dark:bg-pink-900/30 border-pink-300 dark:border-pink-700 text-pink-800 dark:text-pink-300",
  deepseek: "bg-cyan-100 dark:bg-cyan-900/30 border-cyan-300 dark:border-cyan-700 text-cyan-800 dark:text-cyan-300",
  ollama: "bg-gray-100 dark:bg-gray-700/50 border-gray-300 dark:border-gray-600 text-gray-800 dark:text-gray-300",
};

export default function ModelSelector({
  models,
  selected,
  onChange,
}: ModelSelectorProps) {
  const toggle = (name: string) => {
    if (selected.includes(name)) {
      if (selected.length > 1) {
        onChange(selected.filter((m) => m !== name));
      }
    } else {
      onChange([...selected, name]);
    }
  };

  const displayModels =
    models.length > 0
      ? models
      : Object.keys(MODEL_LABELS).map((name) => ({
          name,
          configured: false,
          type: name === "ollama" ? "local" : "cloud",
        }));

  return (
    <div className="mb-6 flex flex-wrap gap-2 justify-center">
      {displayModels.map((model) => {
        const isSelected = selected.includes(model.name);
        const colorClass = MODEL_COLORS[model.name] || MODEL_COLORS.ollama;

        return (
          <button
            key={model.name}
            onClick={() => toggle(model.name)}
            className={`px-3 py-1.5 rounded-full text-sm font-medium border transition-all ${
              isSelected
                ? `${colorClass} shadow-sm`
                : "bg-gray-50 dark:bg-gray-800 border-gray-200 dark:border-gray-700 text-gray-400 dark:text-gray-500"
            } ${!model.configured ? "opacity-60" : ""}`}
            title={
              model.configured
                ? `${MODEL_LABELS[model.name]} (${model.type})`
                : `${MODEL_LABELS[model.name]} - non configure`
            }
          >
            {MODEL_LABELS[model.name] || model.name}
            {!model.configured && " *"}
          </button>
        );
      })}
    </div>
  );
}
