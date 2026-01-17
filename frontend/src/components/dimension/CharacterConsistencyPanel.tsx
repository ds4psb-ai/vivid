"use client";

/**
 * CharacterConsistencyPanel - StoryMem Character Library
 *
 * 2026 Golden App: React 19 Best Practices + Character Consistency
 *
 * Features:
 * - Character library with CRUD operations
 * - StoryMem memory bank visualization
 * - Platform sync (Veo, Kling, Runway)
 * - Similar character search
 *
 * @see https://arxiv.org/abs/2512.19539 - StoryMem Paper
 */

import { useState, useCallback, useTransition, useEffect } from "react";
import Image from "next/image";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Plus,
  Edit,
  Trash2,
  Brain,
  Upload,
  RefreshCw,
  Search,
  X,
  Check,
  Cloud,
  Video,
  Film,
  Layers,
} from "lucide-react";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8100";

// ============================================================================
// Types
// ============================================================================

interface SourceImage {
  url: string;
  timestamp?: string;
  quality_score?: number;
  is_primary: boolean;
}

interface MemoryKeyframe {
  frame_url: string;
  timestamp: number;
  clip_score: number;
  hps_score: number;
  face_confidence: number;
  is_long_term: boolean;
}

interface PlatformRef {
  ref_id?: string;
  last_sync?: string;
  style_strength?: number;
}

interface Character {
  id: string;
  name: string;
  description?: string;
  tags: string[];
  primary_image_url?: string;
  source_images: SourceImage[];
  memory_keyframes: MemoryKeyframe[];
  platform_refs: {
    veo?: PlatformRef;
    kling?: PlatformRef;
    runway?: PlatformRef;
    hailuo?: PlatformRef;
  };
  qdrant_point_id?: string;
  project_id?: string;
  user_id: string;
  created_at: string;
  updated_at?: string;
}

interface CharacterSummary {
  id: string;
  name: string;
  primary_image_url?: string;
  tags: string[];
  keyframe_count: number;
  platforms_synced: string[];
}

type PlatformType = "veo" | "kling" | "runway" | "hailuo";

// ============================================================================
// API Client
// ============================================================================

async function fetchCharacters(token: string): Promise<{ items: CharacterSummary[]; total: number }> {
  const response = await fetch(`${API_BASE}/api/dimension/character`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!response.ok) throw new Error("Failed to fetch characters");
  return response.json();
}

async function fetchCharacter(token: string, characterId: string): Promise<Character> {
  const response = await fetch(`${API_BASE}/api/dimension/character/${characterId}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!response.ok) throw new Error("Failed to fetch character");
  return response.json();
}

async function createCharacter(
  token: string,
  data: { name: string; description?: string; tags?: string[]; reference_image?: string }
): Promise<Character> {
  const response = await fetch(`${API_BASE}/api/dimension/character/create`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify(data),
  });
  if (!response.ok) throw new Error("Failed to create character");
  return response.json();
}

async function deleteCharacter(token: string, characterId: string): Promise<void> {
  const response = await fetch(`${API_BASE}/api/dimension/character/${characterId}`, {
    method: "DELETE",
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!response.ok) throw new Error("Failed to delete character");
}

async function syncToPlatform(
  token: string,
  characterId: string,
  platform: PlatformType
): Promise<{ status: string; platform_ref_id?: string }> {
  const response = await fetch(`${API_BASE}/api/dimension/character/${characterId}/sync-platform`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ platform }),
  });
  if (!response.ok) throw new Error("Failed to sync to platform");
  return response.json();
}

// ============================================================================
// Components
// ============================================================================

interface CharacterCardProps {
  character: CharacterSummary;
  onSelect?: (character: CharacterSummary) => void;
  onEdit?: () => void;
  onDelete?: () => void;
  selected?: boolean;
}

function CharacterCard({ character, onSelect, onEdit, onDelete, selected }: CharacterCardProps) {
  return (
    <div
      className={cn(
        "relative rounded-lg border-2 overflow-hidden cursor-pointer transition-all",
        selected ? "border-blue-500 ring-2 ring-blue-200" : "border-gray-200 hover:border-gray-300"
      )}
      onClick={() => onSelect?.(character)}
    >
      {/* Primary image */}
      <div className="aspect-square relative bg-gray-100">
        {character.primary_image_url ? (
          <Image
            src={character.primary_image_url}
            alt={character.name}
            fill
            className="object-cover"
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center text-gray-400">
            <Layers className="w-12 h-12" />
          </div>
        )}

        {/* Memory bank indicator */}
        {character.keyframe_count > 0 && (
          <div className="absolute top-2 right-2 bg-black/60 text-white text-xs px-2 py-1 rounded">
            <Brain className="w-3 h-3 inline mr-1" />
            {character.keyframe_count}
          </div>
        )}

        {/* Platform sync status */}
        <div className="absolute bottom-2 left-2 flex gap-1">
          {character.platforms_synced.includes("veo") && (
            <Badge variant="outline" className="bg-white/80 text-xs">Veo</Badge>
          )}
          {character.platforms_synced.includes("kling") && (
            <Badge variant="outline" className="bg-white/80 text-xs">Kling</Badge>
          )}
          {character.platforms_synced.includes("runway") && (
            <Badge variant="outline" className="bg-white/80 text-xs">Runway</Badge>
          )}
        </div>
      </div>

      {/* Character info */}
      <div className="p-3">
        <h3 className="font-medium truncate">{character.name}</h3>

        {/* Tags */}
        <div className="flex flex-wrap gap-1 mt-2">
          {character.tags.slice(0, 3).map(tag => (
            <Badge key={tag} variant="secondary" className="text-xs">{tag}</Badge>
          ))}
          {character.tags.length > 3 && (
            <Badge variant="secondary" className="text-xs">+{character.tags.length - 3}</Badge>
          )}
        </div>
      </div>

      {/* Action buttons */}
      <div className="absolute top-2 left-2 flex gap-1">
        <Button
          variant="ghost"
          size="icon"
          className="h-7 w-7 bg-white/80 hover:bg-white"
          onClick={(e) => {
            e.stopPropagation();
            onEdit?.();
          }}
        >
          <Edit className="w-3 h-3" />
        </Button>
        <Button
          variant="ghost"
          size="icon"
          className="h-7 w-7 bg-white/80 hover:bg-white text-red-600"
          onClick={(e) => {
            e.stopPropagation();
            onDelete?.();
          }}
        >
          <Trash2 className="w-3 h-3" />
        </Button>
      </div>
    </div>
  );
}

interface MemoryBankVisualizerProps {
  character: Character;
  onKeyframeSelect?: (keyframe: MemoryKeyframe) => void;
}

function MemoryBankVisualizer({ character, onKeyframeSelect }: MemoryBankVisualizerProps) {
  const longTermKeyframes = character.memory_keyframes.filter(k => k.is_long_term);
  const recentKeyframes = character.memory_keyframes.filter(k => !k.is_long_term);

  return (
    <div className="space-y-4">
      <Tabs defaultValue="long-term">
        <TabsList>
          <TabsTrigger value="long-term">
            Long-term Memory ({longTermKeyframes.length})
          </TabsTrigger>
          <TabsTrigger value="recent">
            Recent ({recentKeyframes.length})
          </TabsTrigger>
        </TabsList>

        <TabsContent value="long-term" className="mt-4">
          <p className="text-sm text-gray-500 mb-3">
            Best keyframes selected by CLIP similarity and aesthetic quality.
          </p>
          {longTermKeyframes.length === 0 ? (
            <div className="text-center py-8 text-gray-400">
              <Brain className="w-12 h-12 mx-auto mb-2 opacity-50" />
              <p>No keyframes yet. Generate videos to build memory.</p>
            </div>
          ) : (
            <div className="grid grid-cols-4 gap-2">
              {longTermKeyframes.map((keyframe, idx) => (
                <KeyframeCard
                  key={idx}
                  keyframe={keyframe}
                  onClick={() => onKeyframeSelect?.(keyframe)}
                />
              ))}
            </div>
          )}
        </TabsContent>

        <TabsContent value="recent" className="mt-4">
          <p className="text-sm text-gray-500 mb-3">
            Sliding window of recent generation keyframes.
          </p>
          {recentKeyframes.length === 0 ? (
            <div className="text-center py-8 text-gray-400">
              <RefreshCw className="w-12 h-12 mx-auto mb-2 opacity-50" />
              <p>No recent keyframes.</p>
            </div>
          ) : (
            <div className="grid grid-cols-4 gap-2">
              {recentKeyframes.map((keyframe, idx) => (
                <KeyframeCard
                  key={idx}
                  keyframe={keyframe}
                  onClick={() => onKeyframeSelect?.(keyframe)}
                />
              ))}
            </div>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}

function KeyframeCard({ keyframe, onClick }: { keyframe: MemoryKeyframe; onClick?: () => void }) {
  return (
    <div
      className="relative aspect-video rounded overflow-hidden cursor-pointer hover:ring-2 hover:ring-blue-400 bg-gray-100"
      onClick={onClick}
    >
      <Image src={keyframe.frame_url} alt="" fill className="object-cover" />

      {/* Quality scores overlay */}
      <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/70 p-2">
        <div className="flex justify-between text-xs text-white">
          <span>CLIP: {(keyframe.clip_score * 100).toFixed(0)}%</span>
          <span>HPS: {(keyframe.hps_score * 100).toFixed(0)}%</span>
        </div>
      </div>

      {/* Long-term indicator */}
      {keyframe.is_long_term && (
        <div className="absolute top-1 right-1">
          <Badge className="bg-purple-600 text-white text-xs">LT</Badge>
        </div>
      )}
    </div>
  );
}

interface PlatformSyncPanelProps {
  character: Character;
  token: string;
  onSyncComplete: () => void;
}

function PlatformSyncPanel({ character, token, onSyncComplete }: PlatformSyncPanelProps) {
  const [syncing, setSyncing] = useState<PlatformType | null>(null);

  const handleSync = async (platform: PlatformType) => {
    setSyncing(platform);
    try {
      await syncToPlatform(token, character.id, platform);
      onSyncComplete();
    } catch (error) {
      console.error("Sync failed:", error);
    } finally {
      setSyncing(null);
    }
  };

  const platforms: { id: PlatformType; name: string; icon: React.ReactNode }[] = [
    { id: "veo", name: "Google Veo", icon: <Video className="w-4 h-4" /> },
    { id: "kling", name: "Kling", icon: <Film className="w-4 h-4" /> },
    { id: "runway", name: "Runway", icon: <Layers className="w-4 h-4" /> },
  ];

  return (
    <div className="space-y-4">
      <h4 className="font-medium">Platform Sync</h4>
      <p className="text-sm text-gray-500">
        Sync this character to video generation platforms for consistent results.
      </p>

      <div className="grid grid-cols-3 gap-3">
        {platforms.map(platform => {
          const ref = character.platform_refs[platform.id];
          const isSynced = !!ref?.ref_id;
          const isSyncing = syncing === platform.id;

          return (
            <Card key={platform.id} className={cn(isSynced && "border-green-200 bg-green-50")}>
              <CardContent className="pt-4">
                <div className="flex items-center gap-2 mb-3">
                  {platform.icon}
                  <span className="font-medium">{platform.name}</span>
                </div>

                {isSynced ? (
                  <div className="space-y-2">
                    <div className="flex items-center gap-1 text-green-600 text-sm">
                      <Check className="w-4 h-4" />
                      Synced
                    </div>
                    <p className="text-xs text-gray-500">
                      {ref.last_sync ? new Date(ref.last_sync).toLocaleDateString() : "N/A"}
                    </p>
                    <Button
                      size="sm"
                      variant="outline"
                      className="w-full"
                      onClick={() => handleSync(platform.id)}
                      disabled={isSyncing}
                    >
                      {isSyncing ? <RefreshCw className="w-4 h-4 animate-spin" /> : "Re-sync"}
                    </Button>
                  </div>
                ) : (
                  <Button
                    size="sm"
                    className="w-full"
                    onClick={() => handleSync(platform.id)}
                    disabled={isSyncing}
                  >
                    {isSyncing ? (
                      <RefreshCw className="w-4 h-4 animate-spin mr-2" />
                    ) : (
                      <Cloud className="w-4 h-4 mr-2" />
                    )}
                    Sync
                  </Button>
                )}
              </CardContent>
            </Card>
          );
        })}
      </div>
    </div>
  );
}

// ============================================================================
// Main Panel
// ============================================================================

interface CharacterConsistencyPanelProps {
  projectId?: string;
  onSelectCharacter?: (character: Character) => void;
}

export default function CharacterConsistencyPanel({
  projectId,
  onSelectCharacter,
}: CharacterConsistencyPanelProps) {
  // State
  const [characters, setCharacters] = useState<CharacterSummary[]>([]);
  const [selectedCharacter, setSelectedCharacter] = useState<Character | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");

  // Form state for create modal
  const [newCharacterName, setNewCharacterName] = useState("");
  const [newCharacterDescription, setNewCharacterDescription] = useState("");
  const [newCharacterTags, setNewCharacterTags] = useState("");
  const [uploadedImage, setUploadedImage] = useState<string | null>(null);

  const [isCreating, startCreating] = useTransition();

  // Get token (in real app, from auth context)
  const token = "demo-token"; // Replace with actual auth

  // Load characters
  const loadCharacters = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await fetchCharacters(token);
      setCharacters(data.items);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load characters");
    } finally {
      setIsLoading(false);
    }
  }, [token]);

  useEffect(() => {
    loadCharacters();
  }, [loadCharacters]);

  // Handle character selection
  const handleSelectCharacter = async (summary: CharacterSummary) => {
    try {
      const fullCharacter = await fetchCharacter(token, summary.id);
      setSelectedCharacter(fullCharacter);
      onSelectCharacter?.(fullCharacter);
    } catch (err) {
      console.error("Failed to load character details:", err);
    }
  };

  // Handle create character
  const handleCreateCharacter = () => {
    startCreating(async () => {
      try {
        const newCharacter = await createCharacter(token, {
          name: newCharacterName,
          description: newCharacterDescription || undefined,
          tags: newCharacterTags ? newCharacterTags.split(",").map(t => t.trim()) : undefined,
          reference_image: uploadedImage || undefined,
        });
        setShowCreateModal(false);
        setNewCharacterName("");
        setNewCharacterDescription("");
        setNewCharacterTags("");
        setUploadedImage(null);
        await loadCharacters();
        setSelectedCharacter(newCharacter);
      } catch (err) {
        console.error("Failed to create character:", err);
      }
    });
  };

  // Handle delete character
  const handleDeleteCharacter = async (characterId: string) => {
    if (!confirm("Are you sure you want to delete this character?")) return;
    try {
      await deleteCharacter(token, characterId);
      if (selectedCharacter?.id === characterId) {
        setSelectedCharacter(null);
      }
      await loadCharacters();
    } catch (err) {
      console.error("Failed to delete character:", err);
    }
  };

  // Handle image upload
  const handleImageUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onloadend = () => {
      setUploadedImage(reader.result as string);
    };
    reader.readAsDataURL(file);
  };

  // Filter characters by search query
  const filteredCharacters = characters.filter(c =>
    c.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    c.tags.some(t => t.toLowerCase().includes(searchQuery.toLowerCase()))
  );

  return (
    <div className="h-full flex">
      {/* Left: Character Library */}
      <div className="w-1/2 border-r p-4 overflow-y-auto">
        {/* Header */}
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-lg font-semibold">Character Library</h2>
          <Button onClick={() => setShowCreateModal(true)}>
            <Plus className="w-4 h-4 mr-2" />
            New Character
          </Button>
        </div>

        {/* Search */}
        <div className="relative mb-4">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <Input
            placeholder="Search characters..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-10"
          />
        </div>

        {/* Error state */}
        {error && (
          <div className="bg-red-50 text-red-600 p-3 rounded-lg mb-4">
            {error}
          </div>
        )}

        {/* Loading state */}
        {isLoading && (
          <div className="text-center py-8 text-gray-400">
            <RefreshCw className="w-8 h-8 animate-spin mx-auto mb-2" />
            Loading characters...
          </div>
        )}

        {/* Empty state */}
        {!isLoading && characters.length === 0 && (
          <div className="text-center py-12 text-gray-400">
            <Layers className="w-16 h-16 mx-auto mb-4 opacity-50" />
            <p className="mb-4">No characters yet</p>
            <Button onClick={() => setShowCreateModal(true)}>
              <Plus className="w-4 h-4 mr-2" />
              Create your first character
            </Button>
          </div>
        )}

        {/* Character grid */}
        {!isLoading && filteredCharacters.length > 0 && (
          <div className="grid grid-cols-2 gap-4">
            {filteredCharacters.map(character => (
              <CharacterCard
                key={character.id}
                character={character}
                selected={selectedCharacter?.id === character.id}
                onSelect={handleSelectCharacter}
                onEdit={() => handleSelectCharacter(character)}
                onDelete={() => handleDeleteCharacter(character.id)}
              />
            ))}
          </div>
        )}
      </div>

      {/* Right: Character Details */}
      <div className="w-1/2 p-4 overflow-y-auto">
        {selectedCharacter ? (
          <div className="space-y-6">
            {/* Character header */}
            <div className="flex gap-4">
              <div className="w-32 h-32 rounded-lg overflow-hidden bg-gray-100 flex-shrink-0">
                {selectedCharacter.primary_image_url ? (
                  <Image
                    src={selectedCharacter.primary_image_url}
                    alt={selectedCharacter.name}
                    width={128}
                    height={128}
                    className="object-cover w-full h-full"
                  />
                ) : (
                  <div className="w-full h-full flex items-center justify-center text-gray-400">
                    <Layers className="w-12 h-12" />
                  </div>
                )}
              </div>
              <div className="flex-1">
                <h2 className="text-xl font-semibold">{selectedCharacter.name}</h2>
                {selectedCharacter.description && (
                  <p className="text-gray-600 mt-1">{selectedCharacter.description}</p>
                )}
                <div className="flex flex-wrap gap-1 mt-2">
                  {selectedCharacter.tags.map(tag => (
                    <Badge key={tag} variant="secondary">{tag}</Badge>
                  ))}
                </div>
                <p className="text-xs text-gray-400 mt-2">
                  Created {new Date(selectedCharacter.created_at).toLocaleDateString()}
                </p>
              </div>
            </div>

            {/* Tabs for different sections */}
            <Tabs defaultValue="memory">
              <TabsList>
                <TabsTrigger value="memory">Memory Bank</TabsTrigger>
                <TabsTrigger value="platforms">Platforms</TabsTrigger>
                <TabsTrigger value="images">Source Images</TabsTrigger>
              </TabsList>

              <TabsContent value="memory" className="mt-4">
                <MemoryBankVisualizer
                  character={selectedCharacter}
                  onKeyframeSelect={(kf) => console.log("Selected keyframe:", kf)}
                />
              </TabsContent>

              <TabsContent value="platforms" className="mt-4">
                <PlatformSyncPanel
                  character={selectedCharacter}
                  token={token}
                  onSyncComplete={async () => {
                    const updated = await fetchCharacter(token, selectedCharacter.id);
                    setSelectedCharacter(updated);
                  }}
                />
              </TabsContent>

              <TabsContent value="images" className="mt-4">
                <div className="space-y-4">
                  <div className="flex justify-between items-center">
                    <h4 className="font-medium">Source Images ({selectedCharacter.source_images.length})</h4>
                    <Button variant="outline" size="sm">
                      <Upload className="w-4 h-4 mr-2" />
                      Add Images
                    </Button>
                  </div>
                  <div className="grid grid-cols-4 gap-2">
                    {selectedCharacter.source_images.map((img, idx) => (
                      <div key={idx} className="relative aspect-square rounded overflow-hidden bg-gray-100">
                        <Image src={img.url} alt="" fill className="object-cover" />
                        {img.is_primary && (
                          <Badge className="absolute top-1 left-1 bg-blue-600 text-xs">Primary</Badge>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              </TabsContent>
            </Tabs>
          </div>
        ) : (
          <div className="h-full flex items-center justify-center text-gray-400">
            <div className="text-center">
              <Layers className="w-16 h-16 mx-auto mb-4 opacity-50" />
              <p>Select a character to view details</p>
            </div>
          </div>
        )}
      </div>

      {/* Create Character Modal */}
      <Dialog open={showCreateModal} onOpenChange={setShowCreateModal}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Create New Character</DialogTitle>
            <DialogDescription>
              Add a character to your library for consistent video generation.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="name">Name</Label>
              <Input
                id="name"
                placeholder="Character name"
                value={newCharacterName}
                onChange={(e) => setNewCharacterName(e.target.value)}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="description">Description</Label>
              <Input
                id="description"
                placeholder="Brief description"
                value={newCharacterDescription}
                onChange={(e) => setNewCharacterDescription(e.target.value)}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="tags">Tags (comma-separated)</Label>
              <Input
                id="tags"
                placeholder="protagonist, human, female"
                value={newCharacterTags}
                onChange={(e) => setNewCharacterTags(e.target.value)}
              />
            </div>

            <div className="space-y-2">
              <Label>Reference Image</Label>
              <div className="border-2 border-dashed rounded-lg p-4 text-center">
                {uploadedImage ? (
                  <div className="relative">
                    <img
                      src={uploadedImage}
                      alt="Preview"
                      className="max-h-48 mx-auto rounded"
                    />
                    <Button
                      variant="ghost"
                      size="icon"
                      className="absolute top-0 right-0"
                      onClick={() => setUploadedImage(null)}
                    >
                      <X className="w-4 h-4" />
                    </Button>
                  </div>
                ) : (
                  <label className="cursor-pointer">
                    <Upload className="w-8 h-8 mx-auto mb-2 text-gray-400" />
                    <p className="text-sm text-gray-500">Click to upload</p>
                    <input
                      type="file"
                      accept="image/*"
                      className="hidden"
                      onChange={handleImageUpload}
                    />
                  </label>
                )}
              </div>
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setShowCreateModal(false)}>
              Cancel
            </Button>
            <Button
              onClick={handleCreateCharacter}
              disabled={!newCharacterName.trim() || isCreating}
            >
              {isCreating ? (
                <RefreshCw className="w-4 h-4 animate-spin mr-2" />
              ) : (
                <Plus className="w-4 h-4 mr-2" />
              )}
              Create
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
