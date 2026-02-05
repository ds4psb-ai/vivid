"use client";

interface WhiteButtonProps {
  href?: string;
  onClick?: () => void;
  children: React.ReactNode;
  large?: boolean;
}

export function WhiteButton({ href, onClick, children, large }: WhiteButtonProps) {
  const className = `w-full flex items-center justify-center gap-3 ${large ? 'px-10 py-5 text-lg' : 'px-6 py-4 text-sm'} rounded-2xl bg-white text-gray-900 font-bold shadow-[0_10px_30px_-10px_rgba(255,255,255,0.3)] hover:scale-105 transition-transform duration-300`;

  if (href) {
    return (
      <a href={href} target="_blank" rel="noopener noreferrer" className={className}>
        {children}
        <span className="material-symbols-outlined text-gray-400 text-sm ml-auto">open_in_new</span>
      </a>
    );
  }
  return <button onClick={onClick} className={className}>{children}</button>;
}
