import { useState, FormEvent } from "react";

interface QuestionFormProps {
  onSubmit: (question: string) => void;
  loading: boolean;
}

export default function QuestionForm({ onSubmit, loading }: QuestionFormProps) {
  const [question, setQuestion] = useState("");

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    if (question.trim() && !loading) {
      onSubmit(question.trim());
    }
  };

  return (
    <form onSubmit={handleSubmit} className="w-full max-w-3xl mx-auto">
      <div className="relative">
        <textarea
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="Posez votre question au conseil des IA..."
          rows={3}
          className="w-full p-4 pr-20 rounded-xl border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 focus:ring-2 focus:ring-primary-500 focus:border-transparent resize-none shadow-sm"
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
          className="absolute right-3 bottom-3 px-4 py-2 bg-primary-600 hover:bg-primary-700 disabled:bg-gray-400 text-white rounded-lg font-medium transition-colors shadow-sm disabled:cursor-not-allowed"
        >
          {loading ? "..." : "Envoyer"}
        </button>
      </div>
    </form>
  );
}
