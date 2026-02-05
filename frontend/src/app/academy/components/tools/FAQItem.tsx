"use client";

interface FAQItemProps {
  question: string;
  answer: string;
  isOpen: boolean;
  onToggle: () => void;
}

export function FAQItem({
  question,
  answer,
  isOpen,
  onToggle,
}: FAQItemProps) {
  return (
    <div className="rounded-lg border border-white/10 overflow-hidden">
      <button
        onClick={onToggle}
        className="w-full p-3 flex items-center justify-between text-left hover:bg-white/5 transition-colors"
      >
        <span className="text-white text-sm font-medium">{question}</span>
        <span className={`material-symbols-outlined text-gray-400 text-lg transition-transform ${isOpen ? 'rotate-180' : ''}`}>
          expand_more
        </span>
      </button>
      {isOpen && (
        <div className="px-3 pb-3 pt-0">
          <p className="text-gray-400 text-xs whitespace-pre-line leading-relaxed">{answer}</p>
        </div>
      )}
    </div>
  );
}
