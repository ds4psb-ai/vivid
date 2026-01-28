"use client";

/**
 * Sheet - Slide-out drawer component
 *
 * Accessible drawer/sheet component for mobile navigation and side panels.
 * Includes focus trap, backdrop click to close, and escape key handling.
 *
 * 2026 UX Pattern: Mobile-first navigation with smooth interactions
 */

import * as React from "react";
import { X } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { useFocusTrap } from "@/hooks/useFocusTrap";
import { useReducedMotion } from "@/hooks/useReducedMotion";
import { cn } from "@/lib/utils";

// =============================================================================
// Sheet Context
// =============================================================================

interface SheetContextValue {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

const SheetContext = React.createContext<SheetContextValue | undefined>(undefined);

function useSheet() {
  const context = React.useContext(SheetContext);
  if (!context) {
    throw new Error("Sheet components must be used within a Sheet");
  }
  return context;
}

// =============================================================================
// Sheet Root
// =============================================================================

export interface SheetProps {
  /** Controlled open state */
  open?: boolean;
  /** Callback when open state changes */
  onOpenChange?: (open: boolean) => void;
  /** Children components */
  children: React.ReactNode;
}

/**
 * Sheet root component
 *
 * @example
 * ```tsx
 * <Sheet open={open} onOpenChange={setOpen}>
 *   <SheetTrigger asChild>
 *     <Button>Open</Button>
 *   </SheetTrigger>
 *   <SheetContent>
 *     <SheetHeader>
 *       <SheetTitle>Title</SheetTitle>
 *     </SheetHeader>
 *     Content here
 *   </SheetContent>
 * </Sheet>
 * ```
 */
export function Sheet({ open: controlledOpen, onOpenChange, children }: SheetProps) {
  const [internalOpen, setInternalOpen] = React.useState(false);
  const open = controlledOpen ?? internalOpen;
  const handleChange = onOpenChange ?? setInternalOpen;

  return (
    <SheetContext.Provider value={{ open, onOpenChange: handleChange }}>
      {children}
    </SheetContext.Provider>
  );
}

// =============================================================================
// Sheet Trigger
// =============================================================================

export interface SheetTriggerProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  /** Render as child element */
  asChild?: boolean;
}

export function SheetTrigger({
  asChild,
  children,
  onClick,
  ...props
}: SheetTriggerProps) {
  const { onOpenChange } = useSheet();

  const handleClick = (e: React.MouseEvent<HTMLButtonElement>) => {
    onClick?.(e);
    onOpenChange(true);
  };

  if (asChild && React.isValidElement(children)) {
    return React.cloneElement(children as React.ReactElement<{ onClick: typeof handleClick }>, {
      onClick: handleClick,
    });
  }

  return (
    <button onClick={handleClick} {...props}>
      {children}
    </button>
  );
}

// =============================================================================
// Sheet Content
// =============================================================================

export interface SheetContentProps {
  /** Side to slide from */
  side?: "left" | "right" | "top" | "bottom";
  /** Show close button */
  showClose?: boolean;
  /** Callback when close button clicked */
  onClose?: () => void;
  /** Additional className */
  className?: string;
  /** Children */
  children?: React.ReactNode;
}

const SIDE_VARIANTS = {
  left: {
    initial: { x: "-100%" },
    animate: { x: 0 },
    exit: { x: "-100%" },
    className: "left-0 top-0 bottom-0 h-full",
  },
  right: {
    initial: { x: "100%" },
    animate: { x: 0 },
    exit: { x: "100%" },
    className: "right-0 top-0 bottom-0 h-full",
  },
  top: {
    initial: { y: "-100%" },
    animate: { y: 0 },
    exit: { y: "-100%" },
    className: "top-0 left-0 right-0 w-full",
  },
  bottom: {
    initial: { y: "100%" },
    animate: { y: 0 },
    exit: { y: "100%" },
    className: "bottom-0 left-0 right-0 w-full",
  },
};

export function SheetContent({
  side = "right",
  showClose = true,
  onClose,
  className,
  children,
}: SheetContentProps) {
  const { open, onOpenChange } = useSheet();
  const prefersReducedMotion = useReducedMotion();
  const { containerRef } = useFocusTrap<HTMLDivElement>({
    isActive: open,
    onEscape: () => {
      onClose?.();
      onOpenChange(false);
    },
  });

  const variants = SIDE_VARIANTS[side];
  const transition = prefersReducedMotion
    ? { duration: 0 }
    : { type: "spring" as const, damping: 30, stiffness: 300 };

  const handleClose = () => {
    onClose?.();
    onOpenChange(false);
  };

  return (
    <AnimatePresence>
      {open && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={prefersReducedMotion ? { duration: 0 } : { duration: 0.2 }}
            className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm"
            onClick={handleClose}
            aria-hidden="true"
          />

          {/* Sheet Panel */}
          <motion.div
            ref={containerRef}
            initial={prefersReducedMotion ? {} : variants.initial}
            animate={prefersReducedMotion ? {} : variants.animate}
            exit={prefersReducedMotion ? {} : variants.exit}
            transition={transition}
            className={cn(
              "fixed z-50 bg-[var(--surface-0)] border-l border-[var(--border-subtle)]",
              variants.className,
              className
            )}
            role="dialog"
            aria-modal="true"
          >
            {/* Close Button */}
            {showClose && (
              <button
                onClick={handleClose}
                className="absolute top-4 right-4 p-2 rounded-lg hover:bg-white/10 transition-colors z-10"
                aria-label="닫기"
              >
                <X className="w-5 h-5 text-[var(--fg-subtle)]" />
              </button>
            )}

            {children}
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}

// =============================================================================
// Sheet Header / Title / Description
// =============================================================================

export function SheetHeader({
  className,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn("flex flex-col space-y-2 p-6 pb-0", className)}
      {...props}
    />
  );
}

export function SheetTitle({
  className,
  ...props
}: React.HTMLAttributes<HTMLHeadingElement>) {
  return (
    <h2
      className={cn(
        "text-lg font-semibold text-[var(--fg-0)]",
        className
      )}
      {...props}
    />
  );
}

export function SheetDescription({
  className,
  ...props
}: React.HTMLAttributes<HTMLParagraphElement>) {
  return (
    <p
      className={cn("text-sm text-[var(--fg-muted)]", className)}
      {...props}
    />
  );
}

// =============================================================================
// Sheet Footer
// =============================================================================

export function SheetFooter({
  className,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn(
        "flex flex-col-reverse sm:flex-row sm:justify-end sm:space-x-2 p-6 pt-0",
        className
      )}
      {...props}
    />
  );
}

// =============================================================================
// Sheet Close Button
// =============================================================================

export function SheetClose({
  children,
  ...props
}: React.ButtonHTMLAttributes<HTMLButtonElement>) {
  const { onOpenChange } = useSheet();

  return (
    <button onClick={() => onOpenChange(false)} {...props}>
      {children}
    </button>
  );
}
