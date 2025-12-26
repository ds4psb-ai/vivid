"use client";

import { useCallback } from "react";
import { Node } from "@xyflow/react";
import { CanvasNodeData, CanvasNodeKind } from "@/components/canvas/CustomNodes";

type NodeStatus = "idle" | "loading" | "streaming" | "complete" | "error" | "cancelled";

type SetNodes = React.Dispatch<React.SetStateAction<Node<CanvasNodeData>[]>>;
type SetSelectedNode = React.Dispatch<React.SetStateAction<Node<CanvasNodeData> | null>>;

export function useNodeLifecycle(
  setNodes: SetNodes,
  setSelectedNode?: SetSelectedNode
) {
  const updateNodeData = useCallback(
    (nodeId: string, data: Partial<CanvasNodeData>) => {
      setNodes((current) =>
        current.map((node) =>
          node.id === nodeId ? { ...node, data: { ...node.data, ...data } } : node
        )
      );
      if (setSelectedNode) {
        setSelectedNode((current) =>
          current && current.id === nodeId
            ? ({ ...current, data: { ...current.data, ...data } } as Node<CanvasNodeData>)
            : current
        );
      }
    },
    [setNodes, setSelectedNode]
  );

  const updateNodesByType = useCallback(
    (kind: CanvasNodeKind, data: Partial<CanvasNodeData>) => {
      setNodes((current) =>
        current.map((node) =>
          node.type === kind ? { ...node, data: { ...node.data, ...data } } : node
        )
      );
      if (setSelectedNode) {
        setSelectedNode((current) =>
          current && current.type === kind
            ? ({ ...current, data: { ...current.data, ...data } } as Node<CanvasNodeData>)
            : current
        );
      }
    },
    [setNodes, setSelectedNode]
  );

  const setNodeStatus = useCallback(
    (nodeId: string, status: NodeStatus, data?: Partial<CanvasNodeData>) => {
      updateNodeData(nodeId, { status, ...(data || {}) });
    },
    [updateNodeData]
  );

  const setNodesStatusByType = useCallback(
    (kind: CanvasNodeKind, status: NodeStatus, data?: Partial<CanvasNodeData>) => {
      updateNodesByType(kind, { status, ...(data || {}) });
    },
    [updateNodesByType]
  );

  return {
    updateNodeData,
    updateNodesByType,
    setNodeStatus,
    setNodesStatusByType,
  };
}
