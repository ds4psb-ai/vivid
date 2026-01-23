/**
 * Canvas API Types
 * 
 * Types for canvas, graph, templates, and related operations.
 */

import type { Edge, Node } from "@xyflow/react";

export interface CanvasGraph {
    nodes: Node[];
    edges: Edge[];
    meta?: Record<string, unknown>;
}

export interface Canvas {
    id: string;
    title: string;
    graph_data: CanvasGraph;
    is_public: boolean;
    version: number;
    owner_id?: string | null;
    created_at: string;
    updated_at: string;
}

export interface CanvasCreate {
    title: string;
    graph_data: CanvasGraph;
    is_public?: boolean;
    owner_id?: string | null;
}

export interface Template {
    id: string;
    slug: string;
    title: string;
    description: string;
    tags: string[];
    graph_data: CanvasGraph;
    is_public: boolean;
    creator_id?: string | null;
    version?: number;
    preview_video_url?: string;
}

export interface TemplateVersion {
    id: string;
    template_id: string;
    version: number;
    graph_data: CanvasGraph;
    notes?: string | null;
    creator_id?: string | null;
    created_at: string;
}

export interface TemplateSeedPayload {
    notebook_id: string;
    slug: string;
    title: string;
    description?: string;
    capsule_key: string;
    capsule_version: string;
    tags?: string[];
    is_public?: boolean;
    creator_id?: string | null;
}
