import { ModelInfo } from "@/lib/api";

interface ModelSelectorProps {
  models: ModelInfo[];
  selected: string[];
  onChange: (models: string[]) => void;
}

const MODEL_CONFIG: Record<string, { label: string; color: string; activeColor: string }> = {
  claude: { label: "Claude", color: "text-orange-500", activeColor: "bg-orange-500/10 border-orange-500/30 text-orange-600 dark:text-orange-400" },
  gpt4: { label: "GPT-4", color: "text-emerald-500", activeColor: "bg-emerald-500/10 border-emerald-500/30 text-emerald-600 dark:text-emerald-400" },
  gemini: { label: "Gemini", color: "text-blue-500", activeColor: "bg-blue-500/10 border-blue-500/30 text-blue-600 dark:text-blue-400" },
  mistral: { label: "Mistral", color: "text-purple-500", activeColor: "bg-purple-500/10 border-purple-500/30 text-purple-600 dark:text-purple-400" },
  cohere: { label: "Cohere", color: "text-pink-500", activeColor: "bg-pink-500/10 border-pink-500/30 text-pink-600 dark:text-pink-400" },
  deepseek: { label: "DeepSeek", color: "text-cyan-500", activeColor: "bg-cyan-500/10 border-cyan-500/30 text-cyan-600 dark:text-cyan-400" },
  ollama: { label: "Ollama", color: "text-gray-500", activeColor: "bg-gray-500/10 border-gray-500/30 text-gray-600 dark:text-gray-400" },
};

export default function ModelSelector({ models, selected, onChange }: ModelSelectorProps) {
  const toggle = (name: string) => {
    if (selected.includes(name)) {
      if (selected.length > 1) onChange(selected.filter((m) => m !== name));
    } else {
      onChange([...selected, name]);
    }
  };

  const displayModels = models.length > 0
    ? models
    : Object.keys(MODEL_CONFIG).map((name) => ({ name, configured: false, type: name === "ollama" ? "local" : "cloud" }));

  return (
    <div className="space-y-1.5">
      {displayModels.map((model) => {
        const isSelected = selected.includes(model.name);
        const config = MODEL_CONFIG[model.name] || MODEL_CONFIG.ollama;

        return (
          <button
            key={model.name}
            onClick={() => toggle(model.name)}
            className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-all border ${
              isSelected
                ? config.activeColor
                : "border-transparent text-[var(--text-muted)] hover:bg-[var(--bg-tertiary)]"
            } ${!model.configured ? "opacity-50" : ""}`}
          >
            <div className={`w-2 h-2 rounded-full flex-shrink-0 ${
              isSelected ? "bg-current" : "bg-[var(--text-muted)]"
            }`} />
            <span className="flex-1 text-left font-medium">{config.label}</span>
            {!model.configured && (
              <span className="text-[10px] text-[var(--text-muted)]">non configure</span>
            )}
            {model.type === "local" && model.configured && (
              <span className="text-[10px] px-1.5 py-0.5 rounded bg-[var(--bg-tertiary)] text-[var(--text-muted)]">local</span>
            )}
          </button>
        );
      })}
    </div>
  );
}
