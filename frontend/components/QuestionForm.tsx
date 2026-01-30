import { useState, FormEvent, useRef, useEffect } from "react";

interface QuestionFormProps {
  onSubmit: (question: string) => void;
  loading: boolean;
}

export default function QuestionForm({ onSubmit, loading }: QuestionFormProps) {
  const [question, setQuestion] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = Math.min(textareaRef.current.scrollHeight, 200) + "px";
    }
  }, [question]);

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    if (question.trim() && !loading) {
      onSubmit(question.trim());
      setQuestion("");
    }
  };

  return (
    <form onSubmit={handleSubmit} className="relative">
      <div className="flex items-end gap-2 p-2 rounded-2xl border border-[var(--border)] bg-[var(--bg-secondary)] focus-within:border-[var(--accent)] focus-within:ring-2 focus-within:ring-[var(--accent)]/20 transition-all shadow-sm">
        <textarea
          ref={textareaRef}
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="Posez votre question au conseil..."
          rows={1}
          className="flex-1 px-3 py-2.5 bg-transparent text-[var(--text-primary)] placeholder-[var(--text-muted)] resize-none outline-none text-sm leading-relaxed"
          disabled={loading}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              handleSubmit(e);
            }
          }}
        />
        <button
          type="submit"
          disabled={loading || !question.trim()}
          className="flex-shrink-0 w-9 h-9 rounded-xl bg-[var(--accent)] hover:bg-[var(--accent-hover)] disabled:opacity-30 disabled:cursor-not-allowed text-white flex items-center justify-center transition-all"
        >
          {loading ? (
            <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
          ) : (
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 12h14m-7-7l7 7-7 7" />
            </svg>
          )}
        </button>
      </div>
      <p className="text-center text-[10px] text-[var(--text-muted)] mt-2">
        Shift+Enter pour un retour a la ligne
      </p>
    </form>
  );
}
