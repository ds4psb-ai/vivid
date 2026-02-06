"use client";

interface WhiteButtonProps {
  href?: string;
  onClick?: () => void;
  children: React.ReactNode;
  large?: boolean;
  icon?: string;
}

export function WhiteButton({
  href,
  onClick,
  children,
  large,
  icon = "add",
}: WhiteButtonProps) {
  const className = `inline-flex w-full items-center justify-between rounded-xl border border-[var(--border-muted)] bg-[var(--fg-0)] px-4 font-semibold text-[var(--bg-0)] transition-opacity hover:opacity-90 ${
    large ? "min-h-12 text-base" : "min-h-11 text-sm"
  }`;

  const content = (
    <>
      <span className="inline-flex items-center gap-2">
        <span className="material-symbols-outlined text-[18px]" aria-hidden>
          {icon}
        </span>
        <span>{children}</span>
      </span>
      {href ? (
        <span className="material-symbols-outlined text-[18px] opacity-80" aria-hidden>
          north_east
        </span>
      ) : null}
    </>
  );

  if (href) {
    return (
      <a href={href} target="_blank" rel="noopener noreferrer" className={className}>
        {content}
      </a>
    );
  }

  return (
    <button type="button" onClick={onClick} className={className}>
      {content}
    </button>
  );
}
