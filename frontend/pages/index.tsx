import { useState, useEffect, useRef } from "react";
import QuestionForm from "@/components/QuestionForm";
import ResponseDisplay from "@/components/ResponseDisplay";
import ModelSelector from "@/components/ModelSelector";
import { askCouncil, getModels, CouncilResponse, ModelInfo } from "@/lib/api";

type Mode = "synthesis" | "detailed" | "debate";

interface Conversation {
  id: number;
  question: string;
  response: CouncilResponse | null;
  loading: boolean;
  error: string | null;
  mode: Mode;
  models: string[];
}

interface HomeProps {
  darkMode: boolean;
  toggleDarkMode: () => void;
}

const MODE_INFO: Record<Mode, { label: string; desc: string; icon: string }> = {
  synthesis: { label: "Synthese", desc: "Reponse unifiee", icon: "M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" },
  detailed: { label: "Detaille", desc: "Chaque IA repond", icon: "M4 6h16M4 10h16M4 14h16M4 18h16" },
  debate: { label: "Debat", desc: "Les IA debattent", icon: "M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" },
};

export default function Home({ darkMode, toggleDarkMode }: HomeProps) {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [models, setModels] = useState<ModelInfo[]>([]);
  const [selectedModels, setSelectedModels] = useState<string[]>(["claude", "gpt4", "gemini"]);
  const [mode, setMode] = useState<Mode>("synthesis");
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [backendStatus, setBackendStatus] = useState<"checking" | "online" | "offline">("checking");
  const scrollRef = useRef<HTMLDivElement>(null);
  const nextId = useRef(1);

  useEffect(() => {
    getModels()
      .then((data) => {
        setModels(data.models);
        setBackendStatus("online");
      })
      .catch(() => setBackendStatus("offline"));
  }, []);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [conversations]);

  const handleSubmit = async (question: string) => {
    const id = nextId.current++;
    const conv: Conversation = {
      id, question, response: null, loading: true, error: null, mode, models: selectedModels,
    };
    setConversations((prev) => [...prev, conv]);

    try {
      const result = await askCouncil({ question, mode, models: selectedModels, optimize_prompts: true });
      setConversations((prev) =>
        prev.map((c) => (c.id === id ? { ...c, response: result, loading: false } : c))
      );
    } catch (err) {
      setConversations((prev) =>
        prev.map((c) =>
          c.id === id ? { ...c, error: err instanceof Error ? err.message : "Erreur inconnue", loading: false } : c
        )
      );
    }
  };

  return (
    <div className="h-full flex bg-[var(--bg-primary)]">
      {/* Sidebar */}
      <aside className={`${sidebarOpen ? "w-72" : "w-0"} transition-all duration-300 overflow-hidden border-r border-[var(--border)] bg-[var(--bg-secondary)] flex flex-col flex-shrink-0`}>
        {/* Logo */}
        <div className="p-5 border-b border-[var(--border)]">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center shadow-lg shadow-indigo-500/25">
              <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
            </div>
            <div>
              <h1 className="text-base font-bold text-[var(--text-primary)] leading-tight">Conseil des IA</h1>
              <p className="text-[11px] text-[var(--text-muted)]">Multi-model AI platform</p>
            </div>
          </div>
        </div>

        {/* Mode */}
        <div className="p-4 border-b border-[var(--border)]">
          <p className="text-[11px] font-semibold text-[var(--text-muted)] uppercase tracking-wider mb-2">Mode</p>
          <div className="space-y-1">
            {(Object.entries(MODE_INFO) as [Mode, typeof MODE_INFO[Mode]][]).map(([key, info]) => (
              <button
                key={key}
                onClick={() => setMode(key)}
                className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-all ${
                  mode === key
                    ? "bg-[var(--accent-light)] text-[var(--accent)] font-semibold"
                    : "text-[var(--text-secondary)] hover:bg-[var(--bg-tertiary)]"
                }`}
              >
                <svg className="w-4 h-4 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d={info.icon} />
                </svg>
                <div className="text-left">
                  <div className="leading-tight">{info.label}</div>
                  <div className="text-[11px] text-[var(--text-muted)] font-normal">{info.desc}</div>
                </div>
              </button>
            ))}
          </div>
        </div>

        {/* Models */}
        <div className="p-4 flex-1 overflow-y-auto">
          <p className="text-[11px] font-semibold text-[var(--text-muted)] uppercase tracking-wider mb-2">Modeles IA</p>
          <ModelSelector models={models} selected={selectedModels} onChange={setSelectedModels} />
        </div>

        {/* Bottom */}
        <div className="p-3 border-t border-[var(--border)] space-y-1">
          {conversations.length > 0 && (
            <button
              onClick={() => { setConversations([]); nextId.current = 1; }}
              className="w-full flex items-center gap-2 px-3 py-2 rounded-lg text-xs text-[var(--text-muted)] hover:text-[var(--text-secondary)] hover:bg-[var(--bg-tertiary)] transition-colors"
            >
              <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
              </svg>
              Effacer l'historique
            </button>
          )}
          <button
            onClick={toggleDarkMode}
            className="w-full flex items-center gap-2 px-3 py-2 rounded-lg text-xs text-[var(--text-muted)] hover:text-[var(--text-secondary)] hover:bg-[var(--bg-tertiary)] transition-colors"
          >
            {darkMode ? (
              <svg className="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 2a1 1 0 011 1v1a1 1 0 11-2 0V3a1 1 0 011-1zm4 8a4 4 0 11-8 0 4 4 0 018 0zm-.464 4.95l.707.707a1 1 0 001.414-1.414l-.707-.707a1 1 0 00-1.414 1.414zm2.12-10.607a1 1 0 010 1.414l-.706.707a1 1 0 11-1.414-1.414l.707-.707a1 1 0 011.414 0zM17 11a1 1 0 100-2h-1a1 1 0 100 2h1zm-7 4a1 1 0 011 1v1a1 1 0 11-2 0v-1a1 1 0 011-1zM5.05 6.464A1 1 0 106.465 5.05l-.708-.707a1 1 0 00-1.414 1.414l.707.707zm1.414 8.486l-.707.707a1 1 0 01-1.414-1.414l.707-.707a1 1 0 011.414 1.414zM4 11a1 1 0 100-2H3a1 1 0 000 2h1z" clipRule="evenodd" />
              </svg>
            ) : (
              <svg className="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 20 20">
                <path d="M17.293 13.293A8 8 0 016.707 2.707a8.001 8.001 0 1010.586 10.586z" />
              </svg>
            )}
            {darkMode ? "Mode clair" : "Mode sombre"}
          </button>
        </div>
      </aside>

      {/* Main */}
      <main className="flex-1 flex flex-col min-w-0">
        {/* Top bar */}
        <header className="h-12 flex items-center justify-between px-4 border-b border-[var(--border)]">
          <button onClick={() => setSidebarOpen(!sidebarOpen)} className="p-1.5 rounded-lg hover:bg-[var(--bg-tertiary)] transition-colors">
            <svg className="w-5 h-5 text-[var(--text-muted)]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d={sidebarOpen ? "M11 19l-7-7 7-7m8 14l-7-7 7-7" : "M4 6h16M4 12h16M4 18h16"} />
            </svg>
          </button>
          <div className="flex items-center gap-2">
            <div className={`w-1.5 h-1.5 rounded-full ${
              backendStatus === "online" ? "bg-emerald-500" :
              backendStatus === "offline" ? "bg-red-500" : "bg-amber-500 animate-pulse-slow"
            }`} />
            <span className="text-[11px] text-[var(--text-muted)]">
              {backendStatus === "online" ? "API connectee" : backendStatus === "offline" ? "API hors ligne" : "Connexion..."}
            </span>
          </div>
        </header>

        {/* Chat area */}
        <div ref={scrollRef} className="flex-1 overflow-y-auto">
          {conversations.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center px-4">
              <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center mb-6 shadow-xl shadow-indigo-500/20">
                <svg className="w-10 h-10 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
              </div>
              <h2 className="text-2xl font-bold text-[var(--text-primary)] mb-2">Posez votre question</h2>
              <p className="text-[var(--text-muted)] text-center max-w-lg mb-10 text-sm leading-relaxed">
                Interrogez simultanement plusieurs modeles IA et obtenez une synthese intelligente de leurs reponses.
              </p>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 max-w-2xl w-full">
                {[
                  { q: "Explique la theorie de la relativite simplement", emoji: "physics" },
                  { q: "Compare Python et Rust pour le backend", emoji: "code" },
                  { q: "Quels sont les enjeux ethiques de l'IA ?", emoji: "ethics" },
                ].map(({ q }) => (
                  <button
                    key={q}
                    onClick={() => handleSubmit(q)}
                    className="group p-4 rounded-xl border border-[var(--border)] hover:border-[var(--accent)] bg-[var(--bg-secondary)] hover:bg-[var(--accent-light)] transition-all text-left"
                  >
                    <p className="text-sm text-[var(--text-secondary)] group-hover:text-[var(--accent)] transition-colors leading-relaxed">{q}</p>
                  </button>
                ))}
              </div>
            </div>
          ) : (
            <div className="max-w-4xl mx-auto px-4 py-6 space-y-8">
              {conversations.map((conv) => (
                <div key={conv.id} className="animate-fade-in">
                  {/* Question */}
                  <div className="flex gap-3 mb-5">
                    <div className="w-8 h-8 rounded-lg bg-[var(--accent)] flex items-center justify-center flex-shrink-0 mt-0.5">
                      <svg className="w-4 h-4 text-white" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M10 9a3 3 0 100-6 3 3 0 000 6zm-7 9a7 7 0 1114 0H3z" clipRule="evenodd" />
                      </svg>
                    </div>
                    <div>
                      <p className="text-[var(--text-primary)] font-medium leading-relaxed">{conv.question}</p>
                      <div className="flex items-center gap-2 mt-1.5">
                        <span className="text-[11px] px-2 py-0.5 rounded-full bg-[var(--bg-tertiary)] text-[var(--text-muted)]">
                          {MODE_INFO[conv.mode].label}
                        </span>
                        <span className="text-[11px] text-[var(--text-muted)]">
                          {conv.models.length} modele{conv.models.length > 1 ? "s" : ""}
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* Response */}
                  <div className="flex gap-3">
                    <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center flex-shrink-0 mt-0.5">
                      <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                      </svg>
                    </div>
                    <div className="flex-1 min-w-0">
                      {conv.loading && (
                        <div className="py-4">
                          <div className="flex items-center gap-3 mb-3">
                            <div className="w-5 h-5 border-2 border-[var(--accent)] border-t-transparent rounded-full animate-spin" />
                            <span className="text-sm text-[var(--text-muted)]">Le conseil delibere...</span>
                          </div>
                          <div className="space-y-2">
                            {[1, 2, 3].map((i) => (
                              <div key={i} className="h-4 rounded-full bg-[var(--bg-tertiary)] animate-shimmer" style={{ width: `${90 - i * 15}%` }} />
                            ))}
                          </div>
                        </div>
                      )}
                      {conv.error && (
                        <div className="p-4 rounded-xl bg-red-50 dark:bg-red-950/30 border border-red-200 dark:border-red-900 text-sm text-red-600 dark:text-red-400">
                          <strong>Erreur :</strong> {conv.error}
                        </div>
                      )}
                      {conv.response && <ResponseDisplay response={conv.response} />}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Input */}
        <div className="border-t border-[var(--border)] bg-[var(--bg-primary)]">
          <div className="max-w-4xl mx-auto px-4 py-3">
            <QuestionForm onSubmit={handleSubmit} loading={conversations.some((c) => c.loading)} />
          </div>
        </div>
      </main>
    </div>
  );
}
