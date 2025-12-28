type StartViewTransition = (callback: () => void) => void;

export const withViewTransition = (callback: () => void): void => {
  if (typeof document === "undefined") {
    callback();
    return;
  }

  const doc = document as Document & { startViewTransition?: StartViewTransition };
  if (typeof doc.startViewTransition === "function") {
    doc.startViewTransition(callback);
    return;
  }

  callback();
};
