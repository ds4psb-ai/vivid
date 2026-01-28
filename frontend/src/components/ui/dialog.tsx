"use client";

/**
 * Dialog - Accessible modal dialog component
 *
 * Features:
 * - Focus trap (Tab/Shift+Tab cycling)
 * - Escape key to close
 * - Focus restoration on close
 * - Backdrop click to close
 * - ARIA attributes for screen readers
 *
 * 2026 UX Pattern: Accessible by default
 */

import * as React from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useFocusTrap } from "@/hooks/useFocusTrap";
import { useReducedMotion } from "@/hooks/useReducedMotion";
import { cn } from "@/lib/utils";

interface DialogContextValue {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

const DialogContext = React.createContext<DialogContextValue | undefined>(undefined);

interface DialogProps {
  open?: boolean;
  onOpenChange?: (open: boolean) => void;
  children: React.ReactNode;
}

function Dialog({ open: controlledOpen, onOpenChange, children }: DialogProps) {
  const [internalOpen, setInternalOpen] = React.useState(false);
  const open = controlledOpen ?? internalOpen;
  const handleChange = onOpenChange ?? setInternalOpen;

  return (
    <DialogContext.Provider value={{ open, onOpenChange: handleChange }}>
      {children}
    </DialogContext.Provider>
  );
}

function DialogTrigger({ children, ...props }: React.ButtonHTMLAttributes<HTMLButtonElement>) {
  const context = React.useContext(DialogContext);
  return (
    <button onClick={() => context?.onOpenChange(true)} {...props}>
      {children}
    </button>
  );
}

interface DialogContentProps {
  className?: string;
  children: React.ReactNode;
}

function DialogContent({ className, children }: DialogContentProps) {
  const context = React.useContext(DialogContext);
  const prefersReducedMotion = useReducedMotion();

  // Focus trap hook - handles Tab cycling and Escape key
  const { containerRef } = useFocusTrap<HTMLDivElement>({
    isActive: context?.open ?? false,
    onEscape: () => context?.onOpenChange(false),
  });

  if (!context?.open) return null;

  const animationProps = prefersReducedMotion
    ? {}
    : {
        initial: { opacity: 0, scale: 0.95 },
        animate: { opacity: 1, scale: 1 },
        exit: { opacity: 0, scale: 0.95 },
      };

  const backdropProps = prefersReducedMotion
    ? {}
    : {
        initial: { opacity: 0 },
        animate: { opacity: 1 },
        exit: { opacity: 0 },
      };

  return (
    <AnimatePresence>
      {context.open && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          {/* Backdrop */}
          <motion.div
            {...backdropProps}
            transition={{ duration: 0.2 }}
            className="fixed inset-0 dialog-overlay"
            onClick={() => context.onOpenChange(false)}
            aria-hidden="true"
          />

          {/* Dialog Panel */}
          <motion.div
            ref={containerRef}
            {...animationProps}
            transition={{ duration: 0.2 }}
            className={cn(
              "fixed z-50 grid w-full max-w-lg gap-4 p-6 dialog-panel",
              className
            )}
            role="dialog"
            aria-modal="true"
          >
            {children}
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
}

function DialogHeader({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn("flex flex-col space-y-1.5 text-center sm:text-left", className)}
      {...props}
    />
  );
}

function DialogFooter({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn(
        "flex flex-col-reverse sm:flex-row sm:justify-end sm:space-x-2",
        className
      )}
      {...props}
    />
  );
}

function DialogTitle({ className, ...props }: React.HTMLAttributes<HTMLHeadingElement>) {
  return (
    <h2
      className={cn("text-lg font-semibold leading-none tracking-tight text-[var(--fg-0)]", className)}
      {...props}
    />
  );
}

function DialogDescription({ className, ...props }: React.HTMLAttributes<HTMLParagraphElement>) {
  return (
    <p className={cn("text-sm text-[var(--fg-muted)]", className)} {...props} />
  );
}

export {
  Dialog,
  DialogTrigger,
  DialogContent,
  DialogHeader,
  DialogFooter,
  DialogTitle,
  DialogDescription,
};
