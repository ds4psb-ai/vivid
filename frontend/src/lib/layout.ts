import dagre from 'dagre';
import { Node, Edge, Position } from '@xyflow/react';

const dagreGraph = new dagre.graphlib.Graph();
dagreGraph.setDefaultEdgeLabel(() => ({}));

export const getLayoutedElements = (
    nodes: Node[],
    edges: Edge[],
    options: { direction: 'TB' | 'LR' } = { direction: 'LR' }
) => {
    const isHorizontal = options.direction === 'LR';

    // Set graph configuration based on direction
    dagreGraph.setGraph({
        rankdir: options.direction,
        align: 'DL', // Align nodes to top-left to keep layout compact
        nodesep: 50, // Horizontal separation between nodes
        ranksep: 80, // Vertical separation between ranks
        marginx: 20,
        marginy: 20
    });

    // Add nodes to the graph
    nodes.forEach((node) => {
        // Estimating node dimensions if not provided. 
        // VibeBoard nodes are roughly 250px wide and variable height.
        const width = node.measured?.width ?? 300;
        const height = node.measured?.height ?? 150;

        dagreGraph.setNode(node.id, { width, height });
    });

    // Add edges to the graph
    edges.forEach((edge) => {
        dagreGraph.setEdge(edge.source, edge.target);
    });

    // Calculate layout
    dagre.layout(dagreGraph);

    // Apply calculated positions back to nodes
    const layoutedNodes = nodes.map((node) => {
        const nodeWithPosition = dagreGraph.node(node.id);

        // Dagre returns center coordinates, convert to top-left
        const x = nodeWithPosition.x - nodeWithPosition.width / 2;
        const y = nodeWithPosition.y - nodeWithPosition.height / 2;

        return {
            ...node,
            targetPosition: isHorizontal ? Position.Left : Position.Top,
            sourcePosition: isHorizontal ? Position.Right : Position.Bottom,
            position: { x, y },
        };
    });

    return { nodes: layoutedNodes, edges };
};
