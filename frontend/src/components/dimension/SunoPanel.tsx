"use client";

/**
 * SunoPanel - Suno AI Music Generation
 *
 * 2026 Golden App: React 19 Best Practices
 *
 * Features:
 * - Custom mode with title, style, lyrics
 * - Instrumental mode (no vocals)
 * - Genre and mood presets
 * - Composer style presets (Hans Zimmer, Joe Hisaishi, etc.)
 * - 2 songs per generation
 *
 * @see docs/research/04_SOUND_CRAFTER_RESEARCH.md
 * @see https://react.dev/blog/2024/12/05/react-19
 */

import { useState, useCallback, useTransition, useOptimistic } from "react";
import { DimensionPanel, useDimensionPanel } from "./panel";
import { useAsyncOperation, useResultExport } from "./DimensionPanelLayout";
import { useCreditContextOptional } from "@/contexts/CreditContext";
import InsufficientCreditsModal from "./InsufficientCreditsModal";

// =============================================================================
// CONSTANTS
// =============================================================================

const DIMENSION_CODE = "sound" as const; // Shares color theme with Sound
const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8100";

// =============================================================================
// TYPES
// =============================================================================

interface SunoSong {
  id: string;
  title: string;
  audio_url?: string;
  stream_url?: string;
  image_url?: string;
  duration?: number;
}

interface SunoGenerateResponse {
  success: boolean;
  task_id: string;
  status: string;
  songs: SunoSong[];
  credits_used: number;
  error?: string;
}

// =============================================================================
// PRESETS
// =============================================================================

const MODELS = [
  { value: "V5", label: "Suno V5 (최신)", credits: 20 },
  { value: "V4_5PLUS", label: "V4.5 Plus", credits: 15 },
  { value: "V4_5ALL", label: "V4.5 All", credits: 15 },
  { value: "V4_5", label: "V4.5", credits: 12 },
  { value: "V4", label: "V4 (경제적)", credits: 10 },
];

const GENRES = [
  { value: "pop", label: "팝", hint: "Catchy pop melody, upbeat rhythm, modern production" },
  { value: "kpop", label: "K-Pop", hint: "K-pop, electronic dance pop, catchy hooks, powerful vocals" },
  { value: "cinematic", label: "시네마틱", hint: "Epic cinematic orchestral, dramatic, emotional" },
  { value: "lofi", label: "Lo-Fi", hint: "Lo-fi hip hop, chill beats, relaxing, nostalgic" },
  { value: "edm", label: "EDM", hint: "Electronic dance music, energetic drops, synth heavy" },
  { value: "rock", label: "록", hint: "Rock, electric guitar, powerful drums, energetic" },
  { value: "acoustic", label: "어쿠스틱", hint: "Acoustic, gentle guitar, warm vocals, intimate" },
  { value: "rnb", label: "R&B", hint: "R&B, smooth vocals, soulful, groovy" },
  { value: "hiphop", label: "힙합", hint: "Hip hop, rhythmic flow, bass heavy, urban" },
  { value: "jazz", label: "재즈", hint: "Jazz, smooth, sophisticated, brass and piano" },
  { value: "ambient", label: "앰비언트", hint: "Ambient, atmospheric, ethereal, meditative" },
];

const MOODS = [
  { value: "happy", label: "행복", keywords: "upbeat, joyful, bright, energetic" },
  { value: "sad", label: "슬픔", keywords: "melancholy, emotional, touching, heartfelt" },
  { value: "epic", label: "웅장", keywords: "grand, powerful, dramatic, heroic" },
  { value: "romantic", label: "로맨틱", keywords: "love, tender, sweet, intimate" },
  { value: "mysterious", label: "미스터리", keywords: "dark, suspenseful, enigmatic, haunting" },
  { value: "relaxing", label: "편안", keywords: "calm, peaceful, soothing, gentle" },
  { value: "energetic", label: "에너제틱", keywords: "high-energy, driving, intense, pumping" },
];

const COMPOSER_STYLES = [
  { value: "", label: "기본 스타일" },
  { value: "hans_zimmer", label: "한스 짐머", hint: "Epic cinematic orchestral, Hans Zimmer style, dramatic brass, layered synths" },
  { value: "joe_hisaishi", label: "조 히사이시", hint: "Minimalist piano, Joe Hisaishi style, Ghibli-inspired, gentle strings, nostalgic" },
  { value: "ennio_morricone", label: "엔니오 모리코네", hint: "Western epic, Ennio Morricone style, trumpet, dramatic orchestration" },
  { value: "john_williams", label: "존 윌리엄스", hint: "Grand orchestral, John Williams style, heroic brass, sweeping strings" },
];

// =============================================================================
// COMPONENT
// =============================================================================

function SunoContent() {
  // Form state
  const [title, setTitle] = useState("");
  const [style, setStyle] = useState("");
  const [prompt, setPrompt] = useState("");
  const [model, setModel] = useState("V5");
  const [instrumental, setInstrumental] = useState(false);
  const [selectedGenre, setSelectedGenre] = useState("");
  const [selectedMood, setSelectedMood] = useState("");
  const [selectedComposer, setSelectedComposer] = useState("");
  const [showAdvanced, setShowAdvanced] = useState(false);

  // UI state
  const [isPending, startTransition] = useTransition();
  const [result, setResult] = useState<SunoGenerateResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [showCreditsModal, setShowCreditsModal] = useState(false);

  const creditContext = useCreditContextOptional();

  // Get current credit cost
  const currentModel = MODELS.find((m) => m.value === model);
  const creditCost = currentModel?.credits || 20;

  // Build style string from presets
  const buildStyleString = useCallback(() => {
    const parts: string[] = [];

    if (selectedGenre) {
      const genre = GENRES.find((g) => g.value === selectedGenre);
      if (genre) parts.push(genre.hint);
    }

    if (selectedMood) {
      const mood = MOODS.find((m) => m.value === selectedMood);
      if (mood) parts.push(mood.keywords);
    }

    if (selectedComposer) {
      const composer = COMPOSER_STYLES.find((c) => c.value === selectedComposer);
      if (composer?.hint) parts.push(composer.hint);
    }

    if (style && !parts.includes(style)) {
      parts.push(style);
    }

    return parts.join(", ") || "Cinematic, modern production";
  }, [selectedGenre, selectedMood, selectedComposer, style]);

  // Handle generate
  const handleGenerate = useCallback(async () => {
    if (!title.trim() || !prompt.trim()) {
      setError("제목과 프롬프트를 입력해주세요.");
      return;
    }

    setError(null);
    setResult(null);

    startTransition(async () => {
      try {
        const finalStyle = buildStyleString();

        const response = await fetch(`${API_BASE}/api/v1/dimension/suno/generate`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "x-user-id": localStorage.getItem("userId") || "demo-user",
          },
          body: JSON.stringify({
            title: title.trim(),
            style: finalStyle,
            prompt: prompt.trim(),
            model,
            instrumental,
          }),
        });

        const data = await response.json();

        if (response.status === 402) {
          setShowCreditsModal(true);
          return;
        }

        if (!response.ok) {
          throw new Error(data.detail || "음악 생성에 실패했습니다.");
        }

        setResult(data);

        // Refresh credits
        if (creditContext?.refresh) {
          creditContext.refresh();
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : "알 수 없는 오류가 발생했습니다.");
      }
    });
  }, [title, prompt, model, instrumental, buildStyleString, creditContext]);

  // Handle genre select
  const handleGenreSelect = (genreValue: string) => {
    setSelectedGenre((prev) => (prev === genreValue ? "" : genreValue));
  };

  // Handle mood select
  const handleMoodSelect = (moodValue: string) => {
    setSelectedMood((prev) => (prev === moodValue ? "" : moodValue));
  };

  // Format duration
  const formatDuration = (seconds?: number) => {
    if (!seconds) return "--:--";
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, "0")}`;
  };

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="p-4 border-b border-gray-700">
        <h2 className="text-xl font-bold text-white flex items-center gap-2">
          <span>🎵</span>
          <span>Suno Music</span>
        </h2>
        <p className="text-sm text-gray-400 mt-1">
          AI로 고품질 음악과 BGM을 생성합니다 (생성당 2곡)
        </p>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {/* Title Input */}
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-2">
            곡 제목 *
          </label>
          <input
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="예: Midnight Dreams"
            maxLength={100}
            className="w-full px-3 py-2 bg-gray-800 border border-gray-600 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-purple-500"
          />
        </div>

        {/* Genre Selection */}
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-2">
            장르
          </label>
          <div className="flex flex-wrap gap-2">
            {GENRES.map((genre) => (
              <button
                key={genre.value}
                onClick={() => handleGenreSelect(genre.value)}
                className={`px-3 py-1.5 rounded-full text-sm transition-colors ${
                  selectedGenre === genre.value
                    ? "bg-purple-600 text-white"
                    : "bg-gray-700 text-gray-300 hover:bg-gray-600"
                }`}
              >
                {genre.label}
              </button>
            ))}
          </div>
        </div>

        {/* Mood Selection */}
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-2">
            분위기
          </label>
          <div className="flex flex-wrap gap-2">
            {MOODS.map((mood) => (
              <button
                key={mood.value}
                onClick={() => handleMoodSelect(mood.value)}
                className={`px-3 py-1.5 rounded-full text-sm transition-colors ${
                  selectedMood === mood.value
                    ? "bg-indigo-600 text-white"
                    : "bg-gray-700 text-gray-300 hover:bg-gray-600"
                }`}
              >
                {mood.label}
              </button>
            ))}
          </div>
        </div>

        {/* Lyrics/Description */}
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-2">
            {instrumental ? "음악 설명 *" : "가사 / 설명 *"}
          </label>
          <textarea
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder={
              instrumental
                ? "어떤 분위기의 음악을 원하시나요? 예: A peaceful morning soundtrack with gentle piano and soft strings"
                : "가사를 입력하세요. 예:\n[Verse]\nWalking through the city lights...\n\n[Chorus]\nWe are the dreamers..."
            }
            rows={6}
            maxLength={2000}
            className="w-full px-3 py-2 bg-gray-800 border border-gray-600 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-purple-500 resize-none"
          />
          <p className="text-xs text-gray-500 mt-1">
            {prompt.length}/2000
          </p>
        </div>

        {/* Instrumental Toggle */}
        <div className="flex items-center gap-3">
          <button
            onClick={() => setInstrumental(!instrumental)}
            className={`relative w-12 h-6 rounded-full transition-colors ${
              instrumental ? "bg-purple-600" : "bg-gray-600"
            }`}
          >
            <span
              className={`absolute top-1 w-4 h-4 bg-white rounded-full transition-transform ${
                instrumental ? "left-7" : "left-1"
              }`}
            />
          </button>
          <span className="text-sm text-gray-300">
            인스트루멘탈 (보컬 없음)
          </span>
        </div>

        {/* Advanced Options */}
        <div>
          <button
            onClick={() => setShowAdvanced(!showAdvanced)}
            className="text-sm text-purple-400 hover:text-purple-300 flex items-center gap-1"
          >
            <span>{showAdvanced ? "▼" : "▶"}</span>
            <span>고급 옵션</span>
          </button>

          {showAdvanced && (
            <div className="mt-3 space-y-4 p-3 bg-gray-800/50 rounded-lg">
              {/* Model Selection */}
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  모델
                </label>
                <select
                  value={model}
                  onChange={(e) => setModel(e.target.value)}
                  className="w-full px-3 py-2 bg-gray-800 border border-gray-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                >
                  {MODELS.map((m) => (
                    <option key={m.value} value={m.value}>
                      {m.label} ({m.credits} 크레딧)
                    </option>
                  ))}
                </select>
              </div>

              {/* Composer Style */}
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  작곡가 스타일
                </label>
                <select
                  value={selectedComposer}
                  onChange={(e) => setSelectedComposer(e.target.value)}
                  className="w-full px-3 py-2 bg-gray-800 border border-gray-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                >
                  {COMPOSER_STYLES.map((c) => (
                    <option key={c.value} value={c.value}>
                      {c.label}
                    </option>
                  ))}
                </select>
              </div>

              {/* Custom Style */}
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  추가 스타일 힌트
                </label>
                <input
                  type="text"
                  value={style}
                  onChange={(e) => setStyle(e.target.value)}
                  placeholder="예: with heavy bass drops and catchy synth riffs"
                  maxLength={500}
                  className="w-full px-3 py-2 bg-gray-800 border border-gray-600 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-purple-500"
                />
              </div>
            </div>
          )}
        </div>

        {/* Error Display */}
        {error && (
          <div className="p-3 bg-red-900/50 border border-red-700 rounded-lg text-red-200 text-sm">
            {error}
          </div>
        )}

        {/* Results */}
        {result?.success && result.songs.length > 0 && (
          <div className="space-y-3">
            <h3 className="text-sm font-medium text-gray-300">
              생성된 음악 ({result.songs.length}곡)
            </h3>
            {result.songs.map((song, index) => (
              <div
                key={song.id || index}
                className="p-4 bg-gray-800 rounded-lg space-y-3"
              >
                <div className="flex items-start gap-3">
                  {song.image_url && (
                    <img
                      src={song.image_url}
                      alt={song.title}
                      className="w-16 h-16 rounded object-cover"
                    />
                  )}
                  <div className="flex-1 min-w-0">
                    <h4 className="text-white font-medium truncate">
                      {song.title || `Track ${index + 1}`}
                    </h4>
                    <p className="text-sm text-gray-400">
                      {formatDuration(song.duration)}
                    </p>
                  </div>
                </div>

                {(song.audio_url || song.stream_url) && (
                  <audio
                    controls
                    className="w-full"
                    src={song.audio_url || song.stream_url}
                  >
                    Your browser does not support the audio element.
                  </audio>
                )}

                {song.audio_url && (
                  <a
                    href={song.audio_url}
                    download
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-2 px-3 py-1.5 bg-purple-600 hover:bg-purple-500 text-white text-sm rounded transition-colors"
                  >
                    <span>⬇</span>
                    <span>다운로드</span>
                  </a>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="p-4 border-t border-gray-700">
        <button
          onClick={handleGenerate}
          disabled={isPending || !title.trim() || !prompt.trim()}
          className={`w-full py-3 rounded-lg font-medium transition-colors ${
            isPending || !title.trim() || !prompt.trim()
              ? "bg-gray-600 text-gray-400 cursor-not-allowed"
              : "bg-gradient-to-r from-purple-600 to-indigo-600 text-white hover:from-purple-500 hover:to-indigo-500"
          }`}
        >
          {isPending ? (
            <span className="flex items-center justify-center gap-2">
              <span className="animate-spin">⏳</span>
              <span>음악 생성 중... (1-3분 소요)</span>
            </span>
          ) : (
            <span className="flex items-center justify-center gap-2">
              <span>🎵</span>
              <span>음악 생성 ({creditCost} 크레딧)</span>
            </span>
          )}
        </button>

        <p className="text-xs text-gray-500 text-center mt-2">
          생성당 2곡이 만들어집니다
        </p>
      </div>

      {/* Credits Modal */}
      <InsufficientCreditsModal
        isOpen={showCreditsModal}
        onClose={() => setShowCreditsModal(false)}
        requiredCredits={creditCost}
        currentBalance={creditContext?.balance ?? 0}
      />
    </div>
  );
}

// =============================================================================
// EXPORT
// =============================================================================

export default function SunoPanel() {
  return (
    <DimensionPanel dimensionCode={DIMENSION_CODE}>
      <SunoContent />
    </DimensionPanel>
  );
}
