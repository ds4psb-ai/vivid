import { useCallback, useState } from "react";
import { Edge, Node } from "@xyflow/react";

interface HistoryState {
  nodes: Node[];
  edges: Edge[];
}

export function useUndoRedo() {
  const [past, setPast] = useState<HistoryState[]>([]);
  const [future, setFuture] = useState<HistoryState[]>([]);

  const takeSnapshot = useCallback((nodes: Node[], edges: Edge[]) => {
    setPast((old) => {
      const newPast = [
        ...old,
        {
          nodes: nodes.map((node) => ({ ...node })),
          edges: edges.map((edge) => ({ ...edge })),
        },
      ];
      if (newPast.length > 50) newPast.shift();
      return newPast;
    });
    setFuture([]);
  }, []);

  const undo = useCallback(
    (currentNodes: Node[], currentEdges: Edge[]) => {
      if (past.length === 0) return null;

      const newPast = [...past];
      const previousState = newPast.pop();
      if (!previousState) return null;

      setPast(newPast);
      setFuture((old) => [{ nodes: currentNodes, edges: currentEdges }, ...old]);
      return previousState;
    },
    [past]
  );

  const redo = useCallback(
    (currentNodes: Node[], currentEdges: Edge[]) => {
      if (future.length === 0) return null;

      const newFuture = [...future];
      const nextState = newFuture.shift();
      if (!nextState) return null;

      setFuture(newFuture);
      setPast((old) => [...old, { nodes: currentNodes, edges: currentEdges }]);
      return nextState;
    },
    [future]
  );

  return {
    takeSnapshot,
    undo,
    redo,
    canUndo: past.length > 0,
    canRedo: future.length > 0,
    pastDepth: past.length,
  };
}
