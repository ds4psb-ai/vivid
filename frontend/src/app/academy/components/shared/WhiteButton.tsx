"use client";

interface WhiteButtonProps {
  href?: string;
  onClick?: () => void;
  children: React.ReactNode;
  large?: boolean;
}

export function WhiteButton({ href, onClick, children, large }: WhiteButtonProps) {
  const className = `w-full flex items-center justify-center gap-3 ${
    large ? "px-10 py-5 text-lg" : "px-6 py-4 text-sm"
  } rounded-2xl bg-[var(--fg-0)] text-[var(--bg-0)] font-bold hover:opacity-90 transition-all duration-200`;

  if (href) {
    return (
      <a href={href} target="_blank" rel="noopener noreferrer" className={className}>
        {children}
        <span className="material-symbols-outlined text-[var(--fg-muted)] text-sm ml-auto">open_in_new</span>
      </a>
    );
  }
  return <button onClick={onClick} className={className}>{children}</button>;
}
