"use client";

import { useEffect, useMemo, useState } from "react";
import {
    ChevronDown,
    ChevronUp,
    Film,
    Grid3X3,
    Headphones,
    List,
    Table2,
    FileVideo,
} from "lucide-react";
import { useLanguage } from "@/contexts/LanguageContext";
import { downloadCsvFromRecords, formatCsvPlainValue } from "@/lib/csv";

/**
 * Artifact types matching backend schemas.
 */
export type ArtifactType =
    | "storyboard"
    | "shot_list"
    | "data_table"
    | "scene_card"
    | "video_summary"
    | "audio_overview";

interface StoryboardCard {
    shot_id: string;
    shot_type: string;
    description: string;
    composition: string;
    duration_sec: number;
    dominant_color: string;
    accent_color: string;
    note?: string;
}

interface ShotListItem {
    shot_id: string;
    sequence: string;
    scene: string;
    shot_size: string;
    action: string;
    dialogue?: string;
    duration: string;
    notes?: string;
}

interface DataTableColumn {
    id: string;
    name: string;
    type: string;
}

interface DataTableGridProps {
    columns: DataTableColumn[];
    rows: Record<string, unknown>[];
    tableClassName: string;
    headerClassName: string;
    headerRowClassName?: string;
    headerCellClassName: string;
    cellClassName: string;
}

const DataTableGrid = ({
    columns,
    rows,
    tableClassName,
    headerClassName,
    headerRowClassName = "text-left text-slate-400",
    headerCellClassName,
    cellClassName,
}: DataTableGridProps) => {
    return (
        <table className={tableClassName}>
            <thead className={headerClassName}>
                <tr className={headerRowClassName}>
                    {columns.map((col) => (
                        <th key={col.id} className={headerCellClassName}>
                            {col.name}
                        </th>
                    ))}
                </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
                {rows.map((row, rowIndex) => (
                    <tr key={rowIndex} className="text-slate-200">
                        {columns.map((col) => (
                            <td key={col.id} className={cellClassName}>
                                {formatCsvPlainValue(row[col.id])}
                            </td>
                        ))}
                    </tr>
                ))}
            </tbody>
        </table>
    );
};

interface ShotListColumn {
    id: string;
    label: string;
    value: (shot: ShotListItem) => unknown;
    cellClassName?: string;
    previewCellClassName?: string;
}

const createShotListColumns = (labels: {
    shot: string;
    sequence: string;
    scene: string;
    size: string;
    action: string;
    dialogue: string;
    duration: string;
    notes: string;
}): ShotListColumn[] => [
    {
        id: "shot_id",
        label: labels.shot,
        value: (shot) => shot.shot_id,
        cellClassName: "font-mono text-slate-400",
    },
    { id: "sequence", label: labels.sequence, value: (shot) => shot.sequence },
    { id: "scene", label: labels.scene, value: (shot) => shot.scene },
    { id: "shot_size", label: labels.size, value: (shot) => shot.shot_size },
    {
        id: "action",
        label: labels.action,
        value: (shot) => shot.action,
        cellClassName: "max-w-[220px] truncate",
        previewCellClassName: "max-w-[150px] truncate",
    },
    {
        id: "dialogue",
        label: labels.dialogue,
        value: (shot) => shot.dialogue ?? "",
        cellClassName: "max-w-[160px] truncate",
    },
    { id: "duration", label: labels.duration, value: (shot) => shot.duration },
    {
        id: "notes",
        label: labels.notes,
        value: (shot) => shot.notes ?? "",
        cellClassName: "max-w-[200px] truncate",
    },
];

function ShotListTable({
    shots,
    columns,
    variant,
    tableClassName,
    headerClassName,
    headerCellClassName,
    cellClassName,
}: {
    shots: ShotListItem[];
    columns: ShotListColumn[];
    variant: "preview" | "detail";
    tableClassName: string;
    headerClassName: string;
    headerCellClassName: string;
    cellClassName: string;
}) {
    const resolveCellClassName = (column: ShotListColumn) => {
        if (variant === "preview") {
            return column.previewCellClassName ?? column.cellClassName;
        }
        return column.cellClassName;
    };

    return (
        <table className={tableClassName}>
            <thead className={headerClassName}>
                <tr className="text-left text-slate-400">
                    {columns.map((column) => (
                        <th key={column.id} className={headerCellClassName}>
                            {column.label}
                        </th>
                    ))}
                </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
                {shots.map((shot) => (
                    <tr key={shot.shot_id} className="text-slate-200">
                        {columns.map((column) => (
                            <td
                                key={column.id}
                                className={`${cellClassName} ${resolveCellClassName(column) || ""}`}
                            >
                                {formatCsvPlainValue(column.value(shot))}
                            </td>
                        ))}
                    </tr>
                ))}
            </tbody>
        </table>
    );
}

const TABLE_PAGE_SIZE = 50;

const isAudioReadyStatus = (status?: string): boolean => {
    const normalizedStatus = (status || "").toUpperCase();
    return ["READY", "COMPLETED", "DONE"].includes(normalizedStatus);
};

const toSafeFilename = (value: string, fallback: string): string => {
    const base = value.trim().replace(/\s+/g, "_").replace(/[^\w-]+/g, "_");
    return base || fallback;
};

export interface ArtifactPayload {
    artifact_type: ArtifactType;
    artifact_id: string;
    title?: string;
    // Storyboard fields
    cards?: StoryboardCard[];
    total_duration_sec?: number;
    capsule_id?: string;
    // Shot list fields
    shots?: ShotListItem[];
    total_shots?: number;
    // Data table fields
    columns?: DataTableColumn[];
    rows?: Record<string, unknown>[];
    source_refs?: string[];
    // Scene card fields
    scene_number?: number;
    description?: string;
    mood?: string;
    color_palette?: string[];
    duration_sec?: number;
    evidence_refs?: string[];
    storyboard_card_ids?: string[];
    // Video summary fields
    synopsis?: string;
    key_themes?: string[];
    scene_count?: number;
    visual_style?: string;
    // Audio overview fields
    status?: string;
    focus?: string;
    language_code?: string;
    notebook_id?: string;
    audio_overview_id?: string;
}

interface ArtifactPreviewProps {
    artifact: ArtifactPayload;
    variant?: "compact" | "expanded";
    onExpand?: () => void;
}

const ARTIFACT_ICONS: Record<ArtifactType, typeof Film> = {
    storyboard: Grid3X3,
    shot_list: List,
    data_table: Table2,
    scene_card: Film,
    video_summary: FileVideo,
    audio_overview: Headphones,
};

/**
 * StoryboardStats - Shared header summary for storyboard artifacts
 */
function StoryboardStats({
    cardCount,
    totalDuration,
    capsuleId,
    shotsLabel,
    totalLabel,
    secondsSuffix,
}: {
    cardCount: number;
    totalDuration?: number;
    capsuleId?: string;
    shotsLabel: string;
    totalLabel: string;
    secondsSuffix: string;
}) {
    return (
        <div className="flex items-center gap-4 text-xs text-slate-400">
            <span>
                {cardCount} {shotsLabel}
            </span>
            {totalDuration && (
                <span>
                    {totalDuration}
                    {secondsSuffix} {totalLabel}
                </span>
            )}
            {capsuleId && (
                <span className="rounded-full bg-purple-500/20 px-2 py-0.5 text-purple-300">
                    {capsuleId.replace("auteur.", "")}
                </span>
            )}
        </div>
    );
}

/**
 * ShotListStats - Shared summary for shot list artifacts
 */
function ShotListStats({ count, shotsLabel }: { count: number; shotsLabel: string }) {
    return (
        <div className="text-xs text-slate-400">
            {count} {shotsLabel}
        </div>
    );
}


/**
 * StoryboardPreview - Compact card grid for storyboard artifacts
 */
function StoryboardPreview({
    cards,
    totalDuration,
    capsuleId,
    shotsLabel,
    totalLabel,
    secondsSuffix,
}: {
    cards: StoryboardCard[];
    totalDuration?: number;
    capsuleId?: string;
    shotsLabel: string;
    totalLabel: string;
    secondsSuffix: string;
}) {
    const displayCards = cards.slice(0, 4);
    const remaining = cards.length - 4;

    return (
        <div className="space-y-3">
            <StoryboardStats
                cardCount={cards.length}
                totalDuration={totalDuration}
                capsuleId={capsuleId}
                shotsLabel={shotsLabel}
                totalLabel={totalLabel}
                secondsSuffix={secondsSuffix}
            />

            {/* Card grid */}
            <div className="grid grid-cols-2 gap-2">
                {displayCards.map((card) => (
                    <div
                        key={card.shot_id}
                        className="rounded-lg border border-white/10 bg-white/5 p-2"
                    >
                        <div className="flex items-center justify-between text-[10px] text-slate-500">
                            <span className="font-mono">{card.shot_id}</span>
                            <span>
                                {card.duration_sec}
                                {secondsSuffix}
                            </span>
                        </div>
                        <div className="mt-1 text-xs text-slate-200 line-clamp-2">
                            {card.description || card.note}
                        </div>
                        <div className="mt-1 flex items-center gap-1">
                            <div
                                className="h-2 w-2 rounded-full"
                                style={{ backgroundColor: card.dominant_color }}
                            />
                            <span className="text-[10px] text-slate-400">{card.shot_type}</span>
                        </div>
                    </div>
                ))}
            </div>

            {remaining > 0 && (
                <div className="text-center text-xs text-slate-500">
                    +{remaining} {shotsLabel}
                </div>
            )}
        </div>
    );
}

/**
 * StoryboardDetail - Full storyboard list for expanded view
 */
function StoryboardDetail({
    cards,
    totalDuration,
    capsuleId,
    shotsLabel,
    totalLabel,
    secondsSuffix,
}: {
    cards: StoryboardCard[];
    totalDuration?: number;
    capsuleId?: string;
    shotsLabel: string;
    totalLabel: string;
    secondsSuffix: string;
}) {
    return (
        <div className="space-y-3">
            <StoryboardStats
                cardCount={cards.length}
                totalDuration={totalDuration}
                capsuleId={capsuleId}
                shotsLabel={shotsLabel}
                totalLabel={totalLabel}
                secondsSuffix={secondsSuffix}
            />
            <div className="max-h-[420px] space-y-3 overflow-y-auto pr-1">
                {cards.map((card) => (
                    <div
                        key={card.shot_id}
                        className="rounded-lg border border-white/10 bg-white/5 p-3"
                    >
                        <div className="flex items-center justify-between text-[11px] text-slate-400">
                            <span className="font-mono">{card.shot_id}</span>
                            <span>
                                {card.duration_sec}
                                {secondsSuffix}
                            </span>
                        </div>
                        <div className="mt-2 text-sm text-slate-100">{card.description}</div>
                        {card.composition && (
                            <div className="mt-1 text-xs text-slate-400">{card.composition}</div>
                        )}
                        {card.note && (
                            <div className="mt-2 text-xs text-slate-300">{card.note}</div>
                        )}
                        <div className="mt-3 flex flex-wrap items-center gap-2 text-[10px] text-slate-400">
                            <span className="rounded-full border border-white/10 bg-slate-900/40 px-2 py-1">
                                {card.shot_type}
                            </span>
                            <div className="flex items-center gap-1">
                                <div
                                    className="h-2 w-2 rounded-full"
                                    style={{ backgroundColor: card.dominant_color }}
                                />
                                <div
                                    className="h-2 w-2 rounded-full"
                                    style={{ backgroundColor: card.accent_color }}
                                />
                            </div>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
}

/**
 * SceneCardPreview - Compact scene card
 */
function SceneCardPreview({
    sceneNumber,
    title,
    description,
    mood,
    colorPalette,
    durationSec,
    sceneLabel,
    secondsSuffix,
    untitledLabel,
}: {
    sceneNumber?: number;
    title?: string;
    description?: string;
    mood?: string;
    colorPalette?: string[];
    durationSec?: number;
    sceneLabel: string;
    secondsSuffix: string;
    untitledLabel: string;
}) {
    return (
        <div className="space-y-2">
            <div className="flex items-center gap-3 text-xs text-slate-400">
                {sceneNumber !== undefined && (
                    <span>
                        {sceneLabel} {sceneNumber}
                    </span>
                )}
                {durationSec !== undefined && (
                    <span>
                        {durationSec}
                        {secondsSuffix}
                    </span>
                )}
            </div>
            <div className="text-sm font-semibold text-slate-100">{title || untitledLabel}</div>
            {description && <p className="text-xs text-slate-300 line-clamp-3">{description}</p>}
            <div className="flex flex-wrap items-center gap-2">
                {mood && (
                    <span className="rounded-full border border-white/10 bg-white/5 px-2 py-0.5 text-[10px] text-slate-300">
                        {mood}
                    </span>
                )}
                {colorPalette && colorPalette.length > 0 && (
                    <div className="flex items-center gap-1">
                        {colorPalette.slice(0, 5).map((color, index) => (
                            <span
                                key={`${color}-${index}`}
                                className="h-2 w-2 rounded-full border border-white/10"
                                style={{ backgroundColor: color }}
                            />
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
}

/**
 * SceneCardDetail - Expanded scene card
 */
function SceneCardDetail({
    sceneNumber,
    title,
    description,
    mood,
    colorPalette,
    durationSec,
    evidenceRefs,
    storyboardCardIds,
    sceneLabel,
    storyboardLabel,
    evidenceLabel,
    secondsSuffix,
    untitledLabel,
}: {
    sceneNumber?: number;
    title?: string;
    description?: string;
    mood?: string;
    colorPalette?: string[];
    durationSec?: number;
    evidenceRefs?: string[];
    storyboardCardIds?: string[];
    sceneLabel: string;
    storyboardLabel: string;
    evidenceLabel: string;
    secondsSuffix: string;
    untitledLabel: string;
}) {
    return (
        <div className="space-y-3">
            <div className="flex items-center gap-3 text-xs text-slate-400">
                {sceneNumber !== undefined && (
                    <span>
                        {sceneLabel} {sceneNumber}
                    </span>
                )}
                {durationSec !== undefined && (
                    <span>
                        {durationSec}
                        {secondsSuffix}
                    </span>
                )}
            </div>
            <div>
                <div className="text-lg font-semibold text-slate-100">{title || untitledLabel}</div>
                {description && <p className="mt-2 text-sm text-slate-200">{description}</p>}
            </div>
            <div className="flex flex-wrap items-center gap-2">
                {mood && (
                    <span className="rounded-full border border-white/10 bg-white/5 px-2 py-1 text-xs text-slate-200">
                        {mood}
                    </span>
                )}
                {colorPalette && colorPalette.length > 0 && (
                    <div className="flex items-center gap-2">
                        {colorPalette.map((color, index) => (
                            <span
                                key={`${color}-${index}`}
                                className="h-3 w-3 rounded-full border border-white/10"
                                style={{ backgroundColor: color }}
                            />
                        ))}
                    </div>
                )}
            </div>
            {storyboardCardIds && storyboardCardIds.length > 0 && (
                <div>
                    <div className="text-[10px] uppercase tracking-[0.2em] text-slate-500">
                        {storyboardLabel}
                    </div>
                    <div className="mt-2 flex flex-wrap gap-2">
                        {storyboardCardIds.map((cardId, index) => (
                            <span
                                key={`${cardId}-${index}`}
                                className="rounded-full border border-white/10 bg-slate-900/40 px-2 py-1 text-[10px] text-slate-300"
                            >
                                {cardId}
                            </span>
                        ))}
                    </div>
                </div>
            )}
            {evidenceRefs && evidenceRefs.length > 0 && (
                <div>
                    <div className="text-[10px] uppercase tracking-[0.2em] text-slate-500">
                        {evidenceLabel}
                    </div>
                    <div className="mt-2 flex flex-wrap gap-2">
                        {evidenceRefs.map((ref, index) => (
                            <span
                                key={`${ref}-${index}`}
                                className="rounded-full border border-white/10 bg-slate-900/40 px-2 py-1 text-[10px] text-slate-300"
                            >
                                {ref}
                            </span>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
}

/**
 * ShotListPreview - Compact table for shot list artifacts
 */
function ShotListPreview({
    shots,
    moreLabel,
    shotsLabel,
    columns,
}: {
    shots: ShotListItem[];
    moreLabel: string;
    shotsLabel: string;
    columns: ShotListColumn[];
}) {
    const displayShots = shots.slice(0, 5);

    return (
        <div className="space-y-2">
            <ShotListStats count={shots.length} shotsLabel={shotsLabel} />
            <div className="overflow-hidden rounded-lg border border-white/10">
                <ShotListTable
                    shots={displayShots}
                    columns={columns}
                    variant="preview"
                    tableClassName="w-full text-xs"
                    headerClassName="bg-white/5"
                    headerCellClassName="px-2 py-1.5 font-medium"
                    cellClassName="px-2 py-1.5"
                />
                {shots.length > 5 && (
                    <div className="bg-white/5 px-2 py-1 text-center text-[10px] text-slate-500">
                        +{shots.length - 5} {moreLabel}
                    </div>
                )}
            </div>
        </div>
    );
}

/**
 * ShotListDetail - Full shot list table for expanded view
 */
function ShotListDetail({
    shots,
    shotsLabel,
    columns,
}: {
    shots: ShotListItem[];
    shotsLabel: string;
    columns: ShotListColumn[];
}) {
    return (
        <div className="space-y-2">
            <ShotListStats count={shots.length} shotsLabel={shotsLabel} />
            <div className="max-h-[420px] overflow-auto rounded-lg border border-white/10">
                <ShotListTable
                    shots={shots}
                    columns={columns}
                    variant="detail"
                    tableClassName="min-w-[720px] w-full text-xs"
                    headerClassName="sticky top-0 bg-slate-950/80"
                    headerCellClassName="px-2 py-2 font-medium"
                    cellClassName="px-2 py-1.5"
                />
            </div>
        </div>
    );
}

/**
 * DataTablePreview - Compact table for data table artifacts
 */
function DataTablePreview({
    columns,
    rows,
    columnsLabel,
    rowsLabel,
    sourceLabel,
    sourceRefs,
    moreLabel,
}: {
    columns: DataTableColumn[];
    rows: Record<string, unknown>[];
    columnsLabel: string;
    rowsLabel: string;
    sourceLabel: string;
    sourceRefs?: string[];
    moreLabel: string;
}) {
    const displayRows = rows.slice(0, 3);
    const displayCols = columns.slice(0, 4);
    const sourceCount = sourceRefs?.length ?? 0;

    return (
        <div className="overflow-hidden rounded-lg border border-white/10">
            <div className="flex items-center justify-between bg-white/5 px-2 py-1 text-[10px] text-slate-500">
                <span>
                    {columns.length} {columnsLabel} · {rows.length} {rowsLabel}
                </span>
                {sourceCount > 0 && (
                    <span>
                        {sourceLabel} · {sourceCount}
                    </span>
                )}
            </div>
            <DataTableGrid
                columns={displayCols}
                rows={displayRows}
                tableClassName="w-full text-xs"
                headerClassName="bg-slate-900/40"
                headerCellClassName="px-2 py-1.5 font-medium"
                cellClassName="px-2 py-1.5 max-w-[120px] truncate"
            />
            {rows.length > 3 && (
                <div className="bg-white/5 px-2 py-1 text-center text-[10px] text-slate-500">
                    +{rows.length - 3} {moreLabel}
                </div>
            )}
        </div>
    );
}

/**
 * DataTableDetail - Full table with CSV export
 */
function DataTableDetail({
    columns,
    rows,
    sourceRefs,
    downloadLabel,
    loadMoreLabel,
    filename,
    columnsLabel,
    rowsLabel,
    sourceLabel,
}: {
    columns: DataTableColumn[];
    rows: Record<string, unknown>[];
    sourceRefs?: string[];
    downloadLabel: string;
    loadMoreLabel: string;
    filename: string;
    columnsLabel: string;
    rowsLabel: string;
    sourceLabel: string;
}) {
    const [visibleCount, setVisibleCount] = useState(() =>
        Math.min(rows.length, TABLE_PAGE_SIZE)
    );

    useEffect(() => {
        setVisibleCount(Math.min(rows.length, TABLE_PAGE_SIZE));
    }, [rows]);

    const visibleRows = rows.slice(0, visibleCount);
    const remaining = rows.length - visibleCount;

    const handleDownload = () => {
        if (!rows.length) return;
        downloadCsvFromRecords(filename, rows, columns);
    };

    return (
        <div className="space-y-3">
            <div className="flex flex-wrap items-center justify-between gap-2 text-xs text-slate-400">
                <span>
                    {columns.length} {columnsLabel} · {rows.length} {rowsLabel}
                </span>
                <button
                    type="button"
                    onClick={handleDownload}
                    disabled={!rows.length}
                    className="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-[11px] text-slate-200 hover:border-white/20 hover:bg-white/10 disabled:cursor-not-allowed disabled:opacity-40"
                >
                    {downloadLabel}
                </button>
            </div>
            {sourceRefs && sourceRefs.length > 0 && (
                <div className="rounded-lg border border-white/10 bg-slate-950/40 px-3 py-2">
                    <div className="text-[10px] uppercase tracking-[0.2em] text-slate-500">
                        {sourceLabel}
                    </div>
                    <div className="mt-2 flex flex-wrap gap-2">
                        {sourceRefs.map((ref, index) => (
                            <span
                                key={`${ref}-${index}`}
                                className="rounded-full border border-white/10 bg-white/5 px-2 py-1 text-[10px] text-slate-300"
                            >
                                {ref}
                            </span>
                        ))}
                    </div>
                </div>
            )}
            <div className="max-h-[420px] overflow-auto rounded-lg border border-white/10">
                <DataTableGrid
                    columns={columns}
                    rows={visibleRows}
                    tableClassName="min-w-[720px] w-full text-xs"
                    headerClassName="sticky top-0 bg-slate-950/80"
                    headerCellClassName="px-2 py-2 font-medium"
                    cellClassName="px-2 py-1.5 max-w-[240px] truncate"
                />
            </div>
            {remaining > 0 && (
                <button
                    type="button"
                    onClick={() =>
                        setVisibleCount((prev) => Math.min(rows.length, prev + TABLE_PAGE_SIZE))
                    }
                    className="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-[11px] text-slate-200 hover:border-white/20 hover:bg-white/10"
                >
                    {loadMoreLabel} ({remaining})
                </button>
            )}
        </div>
    );
}

/**
 * VideoSummaryPreview - Summary card for video summary artifacts
 */
function VideoSummaryPreview({
    synopsis,
    themes,
    sceneCount,
    style,
    scenesLabel,
}: {
    synopsis?: string;
    themes?: string[];
    sceneCount?: number;
    style?: string;
    scenesLabel: string;
}) {
    return (
        <div className="space-y-2">
            {synopsis && (
                <p className="text-sm text-slate-200 line-clamp-3">{synopsis}</p>
            )}
            <div className="flex flex-wrap gap-2">
                {themes?.slice(0, 3).map((theme) => (
                    <span
                        key={theme}
                        className="rounded-full border border-white/10 bg-white/5 px-2 py-0.5 text-[10px] text-slate-300"
                    >
                        {theme}
                    </span>
                ))}
            </div>
            <div className="flex items-center gap-4 text-xs text-slate-400">
                {sceneCount && (
                    <span>
                        {sceneCount} {scenesLabel}
                    </span>
                )}
                {style && <span>{style}</span>}
            </div>
        </div>
    );
}

/**
 * VideoSummaryDetail - Full summary view
 */
function VideoSummaryDetail({
    synopsis,
    themes,
    sceneCount,
    style,
    scenesLabel,
}: {
    synopsis?: string;
    themes?: string[];
    sceneCount?: number;
    style?: string;
    scenesLabel: string;
}) {
    return (
        <div className="space-y-3">
            {synopsis && (
                <p className="whitespace-pre-wrap text-sm text-slate-200">{synopsis}</p>
            )}
            <div className="flex flex-wrap gap-2">
                {themes?.map((theme) => (
                    <span
                        key={theme}
                        className="rounded-full border border-white/10 bg-white/5 px-2 py-0.5 text-[10px] text-slate-300"
                    >
                        {theme}
                    </span>
                ))}
            </div>
            <div className="flex items-center gap-4 text-xs text-slate-400">
                {sceneCount !== undefined && (
                    <span>
                        {sceneCount} {scenesLabel}
                    </span>
                )}
                {style && <span>{style}</span>}
            </div>
        </div>
    );
}

/**
 * AudioOverviewPreview - Compact audio overview status
 */
function AudioOverviewPreview({
    status,
    focus,
    languageCode,
    readyLabel,
    generatingLabel,
    overviewLabel,
}: {
    status?: string;
    focus?: string;
    languageCode?: string;
    readyLabel: string;
    generatingLabel: string;
    overviewLabel: string;
}) {
    const isReady = isAudioReadyStatus(status);
    return (
        <div className="flex items-center gap-3">
            <div className={`h-3 w-3 rounded-full ${isReady ? "bg-green-500" : "animate-pulse bg-amber-500"}`} />
            <div className="flex-1">
                <p className="text-xs text-slate-300 line-clamp-1">{focus || overviewLabel}</p>
                <p className="text-[10px] text-slate-500">{languageCode?.toUpperCase() || "KO"}</p>
            </div>
            <span className={`rounded-full px-2 py-0.5 text-[10px] ${isReady ? "bg-green-500/20 text-green-300" : "bg-amber-500/20 text-amber-300"}`}>
                {isReady ? readyLabel : generatingLabel}
            </span>
        </div>
    );
}

/**
 * AudioOverviewDetail - Full audio overview info
 */
function AudioOverviewDetail({
    status,
    focus,
    languageCode,
    notebookId,
    audioOverviewId,
    readyLabel,
    generatingLabel,
    focusLabel,
    languageLabel,
    notebookLabel,
    audioLabel,
}: {
    status?: string;
    focus?: string;
    languageCode?: string;
    notebookId?: string;
    audioOverviewId?: string;
    readyLabel: string;
    generatingLabel: string;
    focusLabel: string;
    languageLabel: string;
    notebookLabel: string;
    audioLabel: string;
}) {
    const isReady = isAudioReadyStatus(status);
    return (
        <div className="space-y-3">
            <div className="flex items-center gap-3">
                <div className={`h-4 w-4 rounded-full ${isReady ? "bg-green-500" : "animate-pulse bg-amber-500"}`} />
                <span className={`rounded-full px-3 py-1 text-xs font-medium ${isReady ? "bg-green-500/20 text-green-300" : "bg-amber-500/20 text-amber-300"}`}>
                    {isReady ? readyLabel : generatingLabel}
                </span>
            </div>
            {focus && (
                <div>
                    <p className="text-[10px] uppercase text-slate-500 mb-1">{focusLabel}</p>
                    <p className="text-sm text-slate-200">{focus}</p>
                </div>
            )}
            <div className="flex gap-4 text-xs text-slate-400">
                <span>
                    {languageLabel}: {languageCode?.toUpperCase() || "KO"}
                </span>
                {notebookId && (
                    <span>
                        {notebookLabel}: {notebookId.slice(0, 8)}...
                    </span>
                )}
                {audioOverviewId && (
                    <span>
                        {audioLabel}: {audioOverviewId.slice(0, 8)}...
                    </span>
                )}
            </div>
        </div>
    );
}

/**
 * Main ArtifactPreview component
 */
export default function ArtifactPreview({
    artifact,
    variant = "compact",
    onExpand,
}: ArtifactPreviewProps) {
    const [isExpanded, setIsExpanded] = useState(variant === "expanded");
    const { t } = useLanguage();
    const Icon = ARTIFACT_ICONS[artifact.artifact_type] || Film;
    const label =
        {
            storyboard: t("artifactLabelStoryboard"),
            shot_list: t("artifactLabelShotList"),
            data_table: t("artifactLabelDataTable"),
            scene_card: t("artifactLabelSceneCard"),
            video_summary: t("artifactLabelVideoSummary"),
            audio_overview: t("artifactLabelAudioOverview"),
        }[artifact.artifact_type] || t("artifactLabelDefault");
    const headerTitle = artifact.title || label;
    const shotsLabel = t("artifactShotsLabel");
    const totalLabel = t("artifactTotalLabel");
    const moreLabel = t("artifactMoreLabel");
    const csvFilename = `${toSafeFilename(artifact.title || "data_table", "data_table")}.csv`;
    const sceneLabel = t("artifactSceneLabel");
    const storyboardLabel = t("artifactStoryboardLabel");
    const evidenceLabel = t("artifactEvidenceLabel");
    const secondsSuffix = t("timeSecondsSuffix");
    const untitledScene = t("sceneUntitled");
    const scenesLabel = t("artifactScenesLabel");
    const readyLabel = t("statusReady");
    const generatingLabel = t("generating");
    const focusLabel = t("artifactAudioFocusLabel");
    const languageLabel = t("artifactAudioLanguageLabel");
    const notebookLabel = t("artifactAudioNotebookLabel");
    const audioLabel = t("artifactAudioIdLabel");
    const overviewLabel = t("artifactLabelAudioOverview");
    const shotListColumns = useMemo(
        () =>
            createShotListColumns({
                shot: t("shotListColumnShot"),
                sequence: t("shotListColumnSequence"),
                scene: t("shotListColumnScene"),
                size: t("shotListColumnSize"),
                action: t("shotListColumnAction"),
                dialogue: t("shotListColumnDialogue"),
                duration: t("shotListColumnDuration"),
                notes: t("shotListColumnNotes"),
            }),
        [t],
    );
    const shotListPreviewColumns = useMemo(
        () => shotListColumns.filter((column) => ["shot_id", "shot_size", "action", "duration"].includes(column.id)),
        [shotListColumns],
    );

    const handleToggle = () => {
        setIsExpanded(!isExpanded);
        if (!isExpanded && onExpand) {
            onExpand();
        }
    };

    const renderContent = () => {
        switch (artifact.artifact_type) {
            case "storyboard":
                return artifact.cards ? (
                    isExpanded ? (
                        <StoryboardDetail
                            cards={artifact.cards}
                            totalDuration={artifact.total_duration_sec}
                            capsuleId={artifact.capsule_id}
                            shotsLabel={shotsLabel}
                            totalLabel={totalLabel}
                            secondsSuffix={secondsSuffix}
                        />
                    ) : (
                        <StoryboardPreview
                            cards={artifact.cards}
                            totalDuration={artifact.total_duration_sec}
                            capsuleId={artifact.capsule_id}
                            shotsLabel={shotsLabel}
                            totalLabel={totalLabel}
                            secondsSuffix={secondsSuffix}
                        />
                    )
                ) : null;

            case "shot_list":
                return artifact.shots ? (
                    isExpanded ? (
                        <ShotListDetail
                            shots={artifact.shots}
                            shotsLabel={shotsLabel}
                            columns={shotListColumns}
                        />
                    ) : (
                        <ShotListPreview
                            shots={artifact.shots}
                            moreLabel={moreLabel}
                            shotsLabel={shotsLabel}
                            columns={shotListPreviewColumns}
                        />
                    )
                ) : null;

            case "scene_card":
                return isExpanded ? (
                    <SceneCardDetail
                        sceneNumber={artifact.scene_number}
                        title={artifact.title}
                        description={artifact.description}
                        mood={artifact.mood}
                        colorPalette={artifact.color_palette}
                        durationSec={artifact.duration_sec}
                        evidenceRefs={artifact.evidence_refs}
                        storyboardCardIds={artifact.storyboard_card_ids}
                        sceneLabel={sceneLabel}
                        storyboardLabel={storyboardLabel}
                        evidenceLabel={evidenceLabel}
                        secondsSuffix={secondsSuffix}
                        untitledLabel={untitledScene}
                    />
                ) : (
                    <SceneCardPreview
                        sceneNumber={artifact.scene_number}
                        title={artifact.title}
                        description={artifact.description}
                        mood={artifact.mood}
                        colorPalette={artifact.color_palette}
                        durationSec={artifact.duration_sec}
                        sceneLabel={sceneLabel}
                        secondsSuffix={secondsSuffix}
                        untitledLabel={untitledScene}
                    />
                );

            case "data_table":
                return artifact.columns && artifact.rows ? (
                    isExpanded ? (
                        <DataTableDetail
                            columns={artifact.columns}
                            rows={artifact.rows}
                            sourceRefs={artifact.source_refs}
                            downloadLabel={t("downloadCsv")}
                            loadMoreLabel={t("tableLoadMore")}
                            filename={csvFilename}
                            columnsLabel={t("tableCols")}
                            rowsLabel={t("tableRows")}
                            sourceLabel={t("tableSources")}
                        />
                    ) : (
                        <DataTablePreview
                            columns={artifact.columns}
                            rows={artifact.rows}
                            columnsLabel={t("tableCols")}
                            rowsLabel={t("tableRows")}
                            sourceLabel={t("tableSources")}
                            sourceRefs={artifact.source_refs}
                            moreLabel={t("tableMoreLabel")}
                        />
                    )
                ) : null;

            case "video_summary":
                return isExpanded ? (
                    <VideoSummaryDetail
                        synopsis={artifact.synopsis}
                        themes={artifact.key_themes}
                        sceneCount={artifact.scene_count}
                        style={artifact.visual_style}
                        scenesLabel={scenesLabel}
                    />
                ) : (
                    <VideoSummaryPreview
                        synopsis={artifact.synopsis}
                        themes={artifact.key_themes}
                        sceneCount={artifact.scene_count}
                        style={artifact.visual_style}
                        scenesLabel={scenesLabel}
                    />
                );

            case "audio_overview":
                return isExpanded ? (
                    <AudioOverviewDetail
                        status={artifact.status as string}
                        focus={artifact.focus as string}
                        languageCode={artifact.language_code as string}
                        notebookId={artifact.notebook_id as string}
                        audioOverviewId={artifact.audio_overview_id as string}
                        readyLabel={readyLabel}
                        generatingLabel={generatingLabel}
                        focusLabel={focusLabel}
                        languageLabel={languageLabel}
                        notebookLabel={notebookLabel}
                        audioLabel={audioLabel}
                    />
                ) : (
                    <AudioOverviewPreview
                        status={artifact.status as string}
                        focus={artifact.focus as string}
                        languageCode={artifact.language_code as string}
                        readyLabel={readyLabel}
                        generatingLabel={generatingLabel}
                        overviewLabel={overviewLabel}
                    />
                );

            default:
                return (
                    <div className="text-xs text-slate-400">
                        Artifact type: {artifact.artifact_type}
                    </div>
                );
        }
    };

    return (
        <div className="rounded-xl border border-white/10 bg-gradient-to-br from-slate-900/80 to-slate-800/60 backdrop-blur-sm">
            {/* Header */}
            <button
                type="button"
                onClick={handleToggle}
                className="flex w-full items-center justify-between px-4 py-3 text-left transition-colors hover:bg-white/5"
            >
                <div className="flex items-center gap-2">
                    <Icon className="h-4 w-4 text-sky-400" />
                    <span className="text-sm font-medium text-slate-100">{headerTitle}</span>
                    <span className="rounded-full bg-white/10 px-2 py-0.5 text-[10px] text-slate-400">
                        {label}
                    </span>
                </div>
                {isExpanded ? (
                    <ChevronUp className="h-4 w-4 text-slate-400" />
                ) : (
                    <ChevronDown className="h-4 w-4 text-slate-400" />
                )}
            </button>

            {/* Content */}
            <div className="border-t border-white/5 px-4 py-3">{renderContent()}</div>
        </div>
    );
}
