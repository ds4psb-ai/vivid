"use client";

import { useState } from "react";

export interface CharacterProfile {
  facialFeatures?: string;   // "oval face, sharp jawline"
  skinTone?: string;         // "warm beige"
  hairColor?: string;        // "dark brown"
  emotion?: string;          // "neutral"
  lighting?: string;         // "soft front light"
  clarity?: number;          // 0-100 얼굴 선명도
}

export interface Scene {
  id: string;
  name: string;
  thumbnail?: string;
  description?: string;
  shotType?: string;
  characterProfile?: CharacterProfile;
}

interface AnchorSelectionGateProps {
  scenes: Scene[];
  selectedAnchorId?: string;
  onSelect: (sceneId: string) => void;
  onConfirm?: () => void;
}

/**
 * AnchorSelectionGate - ANCHOR 씬 선택 게이트
 *
 * Stage 2 (IMAGE) 진입 전 캐릭터 레퍼런스로 사용할 씬 선택
 * 얼굴이 가장 선명하게 보이는 컷을 선택하도록 안내
 */
export function AnchorSelectionGate({
  scenes,
  selectedAnchorId,
  onSelect,
  onConfirm,
}: AnchorSelectionGateProps) {
  const [hoveredId, setHoveredId] = useState<string | null>(null);

  const selectedScene = scenes.find((s) => s.id === selectedAnchorId);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="rounded-xl border border-border bg-card p-6">
        <div className="flex items-center gap-4 mb-4">
          <div className="w-14 h-14 rounded-xl bg-yellow-500/10 text-yellow-500 flex items-center justify-center text-2xl">
            Target
          </div>
          <div>
            <h2 className="text-2xl font-bold">ANCHOR Selection</h2>
            <p className="text-muted-foreground">
              Select a reference scene for character consistency
            </p>
          </div>
        </div>

        <div className="p-4 bg-yellow-500/5 border border-yellow-500/20 rounded-lg">
          <p className="text-sm">
            <span className="font-semibold">Tip:</span> Select a scene with the clearest face shot.
            This will be used as the reference for all character images.
          </p>
        </div>
      </div>

      {/* Scene Grid */}
      <div className="rounded-xl border border-border bg-card p-6">
        <h3 className="font-semibold mb-4">Available Scenes ({scenes.length})</h3>

        {scenes.length === 0 ? (
          <div className="text-center py-12 text-muted-foreground">
            <p>No scenes available.</p>
            <p className="text-sm mt-2">Complete the ANALYZE stage first to extract scenes.</p>
          </div>
        ) : (
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
            {scenes.map((scene) => {
              const isSelected = scene.id === selectedAnchorId;
              const isHovered = scene.id === hoveredId;

              return (
                <button
                  key={scene.id}
                  onClick={() => onSelect(scene.id)}
                  onMouseEnter={() => setHoveredId(scene.id)}
                  onMouseLeave={() => setHoveredId(null)}
                  className={`
                    relative rounded-lg border-2 overflow-hidden transition-all
                    ${isSelected ? "border-primary ring-2 ring-primary/30" : "border-border"}
                    ${isHovered && !isSelected ? "border-primary/50" : ""}
                  `}
                >
                  {/* Thumbnail */}
                  <div className="aspect-video bg-muted flex items-center justify-center">
                    {scene.thumbnail ? (
                      <img
                        src={scene.thumbnail}
                        alt={scene.name}
                        className="w-full h-full object-cover"
                      />
                    ) : (
                      <span className="text-4xl text-muted-foreground">
                        {scene.name.charAt(0).toUpperCase()}
                      </span>
                    )}
                  </div>

                  {/* Info */}
                  <div className="p-3">
                    <div className="flex items-center justify-between">
                      <span className="font-medium text-sm truncate">{scene.name}</span>
                      {isSelected && (
                        <span className="w-5 h-5 rounded-full bg-primary text-primary-foreground flex items-center justify-center text-xs">
                          Check
                        </span>
                      )}
                    </div>
                    {scene.shotType && (
                      <span className="text-xs text-muted-foreground">{scene.shotType}</span>
                    )}
                  </div>

                  {/* Selection Radio */}
                  <div className="absolute top-2 right-2">
                    <div
                      className={`
                        w-6 h-6 rounded-full border-2 flex items-center justify-center
                        ${isSelected ? "border-primary bg-primary" : "border-white/50 bg-black/30"}
                      `}
                    >
                      {isSelected && (
                        <div className="w-2 h-2 rounded-full bg-white" />
                      )}
                    </div>
                  </div>
                </button>
              );
            })}
          </div>
        )}
      </div>

      {/* Selection Confirmation */}
      {selectedScene && (
        <div className="rounded-xl border border-primary/30 bg-primary/5 p-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="w-16 h-16 rounded-lg bg-muted overflow-hidden">
                {selectedScene.thumbnail ? (
                  <img
                    src={selectedScene.thumbnail}
                    alt={selectedScene.name}
                    className="w-full h-full object-cover"
                  />
                ) : (
                  <div className="w-full h-full flex items-center justify-center text-2xl text-muted-foreground">
                    {selectedScene.name.charAt(0).toUpperCase()}
                  </div>
                )}
              </div>
              <div>
                <p className="font-semibold">{selectedScene.name} selected as ANCHOR</p>
                <p className="text-sm text-muted-foreground">
                  This scene will be used as the character reference for all generated images.
                </p>
              </div>
            </div>

            {onConfirm && (
              <button
                onClick={onConfirm}
                className="px-6 py-3 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition font-medium"
              >
                Confirm
              </button>
            )}
          </div>
        </div>
      )}

      {/* Character Profile (Phase 6) */}
      {selectedScene?.characterProfile && (
        <div className="rounded-xl border border-border bg-card p-6">
          <h3 className="font-semibold mb-4">Character Profile</h3>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-4 text-sm">
            {selectedScene.characterProfile.facialFeatures && (
              <div>
                <p className="text-muted-foreground">Features</p>
                <p className="font-medium">{selectedScene.characterProfile.facialFeatures}</p>
              </div>
            )}
            {selectedScene.characterProfile.skinTone && (
              <div>
                <p className="text-muted-foreground">Skin Tone</p>
                <p className="font-medium">{selectedScene.characterProfile.skinTone}</p>
              </div>
            )}
            {selectedScene.characterProfile.hairColor && (
              <div>
                <p className="text-muted-foreground">Hair Color</p>
                <p className="font-medium">{selectedScene.characterProfile.hairColor}</p>
              </div>
            )}
            {selectedScene.characterProfile.emotion && (
              <div>
                <p className="text-muted-foreground">Emotion</p>
                <p className="font-medium">{selectedScene.characterProfile.emotion}</p>
              </div>
            )}
            {selectedScene.characterProfile.lighting && (
              <div>
                <p className="text-muted-foreground">Lighting</p>
                <p className="font-medium">{selectedScene.characterProfile.lighting}</p>
              </div>
            )}
            {selectedScene.characterProfile.clarity !== undefined && (
              <div>
                <p className="text-muted-foreground">Clarity</p>
                <div className="flex items-center gap-2">
                  <div className="w-16 h-2 bg-muted rounded-full overflow-hidden">
                    <div
                      className={`h-full rounded-full ${
                        selectedScene.characterProfile.clarity >= 80 ? "bg-green-500" :
                        selectedScene.characterProfile.clarity >= 60 ? "bg-yellow-500" :
                        "bg-red-500"
                      }`}
                      style={{ width: `${selectedScene.characterProfile.clarity}%` }}
                    />
                  </div>
                  <span className="font-medium">{selectedScene.characterProfile.clarity}%</span>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Help Text */}
      <div className="rounded-xl border border-border bg-card p-6">
        <h3 className="font-semibold mb-3">What is ANCHOR?</h3>
        <div className="space-y-2 text-sm text-muted-foreground">
          <p>
            <strong>ANCHOR</strong> is the reference scene used to maintain character consistency
            across all generated images.
          </p>
          <ul className="list-disc list-inside space-y-1 ml-2">
            <li>Choose a close-up with clear facial features</li>
            <li>Good lighting helps AI understand skin tone and details</li>
            <li>Neutral expression works best for versatility</li>
            <li>Avoid scenes with multiple people or busy backgrounds</li>
          </ul>
        </div>
      </div>
    </div>
  );
}

export default AnchorSelectionGate;
