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

import { useState, useCallback, useTransition, useRef, useMemo, useEffect } from "react";
import Image from "next/image";
import { DimensionPanel, useDimensionPanel } from "./panel";
import { useCreditContextOptional } from "@/contexts/CreditContext";
import { useLanguage } from "@/contexts/LanguageContext";
import { getPreviousStepResult } from "@/lib/workflow-state";
import InsufficientCreditsModal from "./InsufficientCreditsModal";
import { Upload, X, Music } from "lucide-react";

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
// PRESETS (Dynamic based on language)
// =============================================================================

const getModels = (isKo: boolean) => [
  { value: "V5", label: isKo ? "Suno V5 (최신)" : "Suno V5 (Latest)", credits: 20 },
  { value: "V4_5PLUS", label: "V4.5 Plus", credits: 15 },
  { value: "V4_5ALL", label: "V4.5 All", credits: 15 },
  { value: "V4_5", label: "V4.5", credits: 12 },
  { value: "V4", label: isKo ? "V4 (경제적)" : "V4 (Economic)", credits: 10 },
];

const getGenres = (isKo: boolean) => [
  { value: "pop", label: isKo ? "팝" : "Pop", hint: "Catchy pop melody, upbeat rhythm, modern production" },
  { value: "kpop", label: "K-Pop", hint: "K-pop, electronic dance pop, catchy hooks, powerful vocals" },
  { value: "cinematic", label: isKo ? "시네마틱" : "Cinematic", hint: "Epic cinematic orchestral, dramatic, emotional" },
  { value: "lofi", label: "Lo-Fi", hint: "Lo-fi hip hop, chill beats, relaxing, nostalgic" },
  { value: "edm", label: "EDM", hint: "Electronic dance music, energetic drops, synth heavy" },
  { value: "rock", label: isKo ? "록" : "Rock", hint: "Rock, electric guitar, powerful drums, energetic" },
  { value: "acoustic", label: isKo ? "어쿠스틱" : "Acoustic", hint: "Acoustic, gentle guitar, warm vocals, intimate" },
  { value: "rnb", label: "R&B", hint: "R&B, smooth vocals, soulful, groovy" },
  { value: "hiphop", label: isKo ? "힙합" : "Hip-Hop", hint: "Hip hop, rhythmic flow, bass heavy, urban" },
  { value: "jazz", label: isKo ? "재즈" : "Jazz", hint: "Jazz, smooth, sophisticated, brass and piano" },
  { value: "ambient", label: isKo ? "앰비언트" : "Ambient", hint: "Ambient, atmospheric, ethereal, meditative" },
];

const getMoods = (isKo: boolean) => [
  { value: "happy", label: isKo ? "행복" : "Happy", keywords: "upbeat, joyful, bright, energetic" },
  { value: "sad", label: isKo ? "슬픔" : "Sad", keywords: "melancholy, emotional, touching, heartfelt" },
  { value: "epic", label: isKo ? "웅장" : "Epic", keywords: "grand, powerful, dramatic, heroic" },
  { value: "romantic", label: isKo ? "로맨틱" : "Romantic", keywords: "love, tender, sweet, intimate" },
  { value: "mysterious", label: isKo ? "미스터리" : "Mysterious", keywords: "dark, suspenseful, enigmatic, haunting" },
  { value: "relaxing", label: isKo ? "편안" : "Relaxing", keywords: "calm, peaceful, soothing, gentle" },
  { value: "energetic", label: isKo ? "에너제틱" : "Energetic", keywords: "high-energy, driving, intense, pumping" },
];

const getComposerStyles = (isKo: boolean) => [
  { value: "", label: isKo ? "기본 스타일" : "Default Style" },
  { value: "hans_zimmer", label: isKo ? "한스 짐머" : "Hans Zimmer", hint: "Epic cinematic orchestral, Hans Zimmer style, dramatic brass, layered synths" },
  { value: "joe_hisaishi", label: isKo ? "조 히사이시" : "Joe Hisaishi", hint: "Minimalist piano, Joe Hisaishi style, Ghibli-inspired, gentle strings, nostalgic" },
  { value: "ennio_morricone", label: isKo ? "엔니오 모리코네" : "Ennio Morricone", hint: "Western epic, Ennio Morricone style, trumpet, dramatic orchestration" },
  { value: "john_williams", label: isKo ? "존 윌리엄스" : "John Williams", hint: "Grand orchestral, John Williams style, heroic brass, sweeping strings" },
];

// =============================================================================
// COMPONENT
// =============================================================================

function SunoContent() {
  const { language } = useLanguage();
  const isKo = language === "ko";
  const { setResult: setContextResult } = useDimensionPanel();

  // Memoized presets based on language
  const MODELS = useMemo(() => getModels(isKo), [isKo]);
  const GENRES = useMemo(() => getGenres(isKo), [isKo]);
  const MOODS = useMemo(() => getMoods(isKo), [isKo]);
  const COMPOSER_STYLES = useMemo(() => getComposerStyles(isKo), [isKo]);

  // i18n labels
  const labels = useMemo(() => ({
    title: isKo ? "Suno Music" : "Suno Music",
    subtitle: isKo ? "AI로 고품질 음악과 BGM을 생성합니다 (생성당 2곡)" : "Generate high-quality music and BGM with AI (2 songs per generation)",
    songTitle: isKo ? "곡 제목 *" : "Song Title *",
    songTitlePlaceholder: isKo ? "예: Midnight Dreams" : "e.g., Midnight Dreams",
    genre: isKo ? "장르" : "Genre",
    mood: isKo ? "분위기" : "Mood",
    lyricsOrDesc: isKo ? "가사 / 설명 *" : "Lyrics / Description *",
    musicDesc: isKo ? "음악 설명 *" : "Music Description *",
    lyricsPlaceholder: isKo ? "가사를 입력하세요. 예:\n[Verse]\nWalking through the city lights...\n\n[Chorus]\nWe are the dreamers..." : "Enter lyrics. e.g.:\n[Verse]\nWalking through the city lights...\n\n[Chorus]\nWe are the dreamers...",
    musicDescPlaceholder: isKo ? "어떤 분위기의 음악을 원하시나요? 예: A peaceful morning soundtrack with gentle piano and soft strings" : "What kind of music do you want? e.g., A peaceful morning soundtrack with gentle piano and soft strings",
    reference: isKo ? "레퍼런스 (선택)" : "Reference (Optional)",
    dragOrClick: isKo ? "참고 파일을 드래그하거나 클릭하여 업로드" : "Drag files or click to upload",
    allFormats: isKo ? "모든 파일 형식 지원 (최대 100MB)" : "All file formats supported (max 100MB)",
    addFile: isKo ? "+ 파일 추가" : "+ Add File",
    instrumental: isKo ? "인스트루멘탈 (보컬 없음)" : "Instrumental (no vocals)",
    advancedOptions: isKo ? "고급 옵션" : "Advanced Options",
    modelLabel: isKo ? "모델" : "Model",
    composerStyle: isKo ? "작곡가 스타일" : "Composer Style",
    additionalStyleHint: isKo ? "추가 스타일 힌트" : "Additional Style Hint",
    styleHintPlaceholder: isKo ? "예: with heavy bass drops and catchy synth riffs" : "e.g., with heavy bass drops and catchy synth riffs",
    generatedMusic: (count: number) => isKo ? `생성된 음악 (${count}곡)` : `Generated Music (${count} songs)`,
    download: isKo ? "다운로드" : "Download",
    generating: isKo ? "음악 생성 중... (1-3분 소요)" : "Generating music... (1-3 min)",
    generate: (credits: number) => isKo ? `음악 생성 (${credits} 크레딧)` : `Generate Music (${credits} credits)`,
    twoSongsNote: isKo ? "생성당 2곡이 만들어집니다" : "2 songs will be created per generation",
    errorTitlePrompt: isKo ? "제목과 프롬프트를 입력해주세요." : "Please enter a title and prompt.",
    errorGeneration: isKo ? "음악 생성에 실패했습니다." : "Music generation failed.",
    errorUnknown: isKo ? "알 수 없는 오류가 발생했습니다." : "An unknown error occurred.",
    credits: isKo ? "크레딧" : "credits",
  }), [isKo]);

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
  const [referenceFiles, setReferenceFiles] = useState<File[]>([]);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // UI state
  const [isPending, startTransition] = useTransition();
  const [localResult, setLocalResult] = useState<SunoGenerateResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [showCreditsModal, setShowCreditsModal] = useState(false);

  // ==========================================================================
  // Session Context Inheritance (2026 Best Practice)
  // Inject mood/tempo from previous step (AestheticDirector → Suno)
  // ==========================================================================
  useEffect(() => {
    if (typeof window === "undefined") return;

    const params = new URLSearchParams(window.location.search);
    const ipSlug = params.get("ip");
    const stepParam = params.get("step");
    const currentStep = stepParam ? parseInt(stepParam, 10) : null;

    if (!ipSlug || !currentStep || currentStep <= 1) return;

    const prevResult = getPreviousStepResult(ipSlug, currentStep);
    if (!prevResult?.outputData) return;

    const data = prevResult.outputData;

    // Auto-set mood from previous step
    if (data.mood && !selectedMood) {
      const moodMatch = MOODS.find((m) =>
        m.value.toLowerCase().includes((data.mood as string).toLowerCase()) ||
        (data.mood as string).toLowerCase().includes(m.value.toLowerCase())
      );
      if (moodMatch) {
        setSelectedMood(moodMatch.value);
      }
    }

    // Auto-set genre if style hints available
    if (data.style_guide && typeof data.style_guide === "object" && !selectedGenre) {
      const styleGuide = data.style_guide as Record<string, unknown>;
      // Example: if style is "epic", suggest "orchestral"
      if (styleGuide.composition?.toString().toLowerCase().includes("epic")) {
        setSelectedGenre("orchestral");
      } else if (styleGuide.composition?.toString().toLowerCase().includes("intimate")) {
        setSelectedGenre("ambient");
      }
    }
  }, [selectedMood, selectedGenre, MOODS]);

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
  }, [selectedGenre, selectedMood, selectedComposer, style, GENRES, MOODS, COMPOSER_STYLES]);

  // Handle generate
  const handleGenerate = useCallback(async () => {
    if (!title.trim() || !prompt.trim()) {
      setError(labels.errorTitlePrompt);
      return;
    }

    setError(null);
    setLocalResult(null);

    startTransition(async () => {
      try {
        const finalStyle = buildStyleString();

        const response = await fetch(`${API_BASE}/api/dimension/suno/generate`, {
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
          throw new Error(data.detail || labels.errorGeneration);
        }

        setLocalResult(data);
        setContextResult(data);  // Enable NextNav in workflow mode

        // Refresh credits
        if (creditContext?.refresh) {
          creditContext.refresh();
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : labels.errorUnknown);
      }
    });
  }, [title, prompt, model, instrumental, buildStyleString, creditContext, labels]);

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
          <span>{labels.title}</span>
        </h2>
        <p className="text-sm text-gray-400 mt-1">
          {labels.subtitle}
        </p>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {/* Title Input */}
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-2">
            {labels.songTitle}
          </label>
          <input
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder={labels.songTitlePlaceholder}
            maxLength={100}
            className="w-full px-3 py-2 bg-gray-800 border border-gray-600 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-purple-500"
          />
        </div>

        {/* Genre Selection */}
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-2">
            {labels.genre}
          </label>
          <div className="flex flex-wrap gap-2">
            {GENRES.map((genre) => (
              <button
                key={genre.value}
                onClick={() => handleGenreSelect(genre.value)}
                className={`px-3 py-1.5 rounded-full text-sm transition-colors ${selectedGenre === genre.value
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
            {labels.mood}
          </label>
          <div className="flex flex-wrap gap-2">
            {MOODS.map((mood) => (
              <button
                key={mood.value}
                onClick={() => handleMoodSelect(mood.value)}
                className={`px-3 py-1.5 rounded-full text-sm transition-colors ${selectedMood === mood.value
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
            {instrumental ? labels.musicDesc : labels.lyricsOrDesc}
          </label>
          <textarea
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder={
              instrumental
                ? labels.musicDescPlaceholder
                : labels.lyricsPlaceholder
            }
            rows={6}
            maxLength={2000}
            className="w-full px-3 py-2 bg-gray-800 border border-gray-600 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-purple-500 resize-none"
          />
          <p className="text-xs text-gray-500 mt-1">
            {prompt.length}/2000
          </p>
        </div>

        {/* Reference File Upload */}
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-2">
            {labels.reference}
          </label>
          <div
            className={`border-2 border-dashed rounded-lg p-4 transition-colors ${referenceFiles.length > 0
              ? "border-purple-500 bg-purple-500/10"
              : "border-gray-600 hover:border-gray-500"
              }`}
            onDragOver={(e) => {
              e.preventDefault();
              e.stopPropagation();
            }}
            onDrop={(e) => {
              e.preventDefault();
              e.stopPropagation();
              const files = Array.from(e.dataTransfer.files);
              if (files.length > 0) {
                setReferenceFiles((prev) => [...prev, ...files].slice(0, 10));
              }
            }}
          >
            {referenceFiles.length === 0 ? (
              <div
                className="flex flex-col items-center gap-2 cursor-pointer"
                onClick={() => fileInputRef.current?.click()}
              >
                <Upload className="w-6 h-6 text-gray-400" />
                <p className="text-sm text-gray-500 text-center">
                  {labels.dragOrClick}
                </p>
                <p className="text-xs text-gray-600">{labels.allFormats}</p>
              </div>
            ) : (
              <div className="space-y-2">
                {referenceFiles.map((file, idx) => (
                  <div
                    key={idx}
                    className="flex items-center justify-between bg-gray-800 rounded-lg px-3 py-2"
                  >
                    <div className="flex items-center gap-2 min-w-0">
                      <Music className="w-4 h-4 text-purple-400 flex-shrink-0" />
                      <span className="text-sm text-gray-300 truncate">{file.name}</span>
                      <span className="text-xs text-gray-500 flex-shrink-0">
                        {(file.size / 1024 / 1024).toFixed(1)}MB
                      </span>
                    </div>
                    <button
                      onClick={() =>
                        setReferenceFiles((prev) => prev.filter((_, i) => i !== idx))
                      }
                      className="p-1 hover:bg-gray-700 rounded"
                    >
                      <X className="w-4 h-4 text-gray-400" />
                    </button>
                  </div>
                ))}
                <button
                  onClick={() => fileInputRef.current?.click()}
                  className="w-full py-2 text-sm text-purple-400 hover:text-purple-300"
                >
                  {labels.addFile}
                </button>
              </div>
            )}
            <input
              ref={fileInputRef}
              type="file"
              accept="*"
              multiple
              className="hidden"
              onChange={(e) => {
                const files = Array.from(e.target.files || []);
                setReferenceFiles((prev) => [...prev, ...files].slice(0, 10));
                e.target.value = "";
              }}
            />
          </div>
        </div>

        {/* Instrumental Toggle */}
        <div className="flex items-center gap-3">
          <button
            onClick={() => setInstrumental(!instrumental)}
            className={`relative w-12 h-6 rounded-full transition-colors ${instrumental ? "bg-purple-600" : "bg-gray-600"
              }`}
          >
            <span
              className={`absolute top-1 w-4 h-4 bg-white rounded-full transition-transform ${instrumental ? "left-7" : "left-1"
                }`}
            />
          </button>
          <span className="text-sm text-gray-300">
            {labels.instrumental}
          </span>
        </div>

        {/* Advanced Options */}
        <div>
          <button
            onClick={() => setShowAdvanced(!showAdvanced)}
            className="text-sm text-purple-400 hover:text-purple-300 flex items-center gap-1"
          >
            <span>{showAdvanced ? "▼" : "▶"}</span>
            <span>{labels.advancedOptions}</span>
          </button>

          {showAdvanced && (
            <div className="mt-3 space-y-4 p-3 bg-gray-800/50 rounded-lg">
              {/* Model Selection */}
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  {labels.modelLabel}
                </label>
                <select
                  value={model}
                  onChange={(e) => setModel(e.target.value)}
                  className="w-full px-3 py-2 bg-gray-800 border border-gray-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                >
                  {MODELS.map((m) => (
                    <option key={m.value} value={m.value}>
                      {m.label} ({m.credits} {labels.credits})
                    </option>
                  ))}
                </select>
              </div>

              {/* Composer Style */}
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  {labels.composerStyle}
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
                  {labels.additionalStyleHint}
                </label>
                <input
                  type="text"
                  value={style}
                  onChange={(e) => setStyle(e.target.value)}
                  placeholder={labels.styleHintPlaceholder}
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
        {localResult?.success && localResult.songs.length > 0 && (
          <div className="space-y-3">
            <h3 className="text-sm font-medium text-gray-300">
              {labels.generatedMusic(localResult.songs.length)}
            </h3>
            {localResult.songs.map((song, index) => (
              <div
                key={song.id || index}
                className="p-4 bg-gray-800 rounded-lg space-y-3"
              >
                <div className="flex items-start gap-3">
                  {song.image_url && (
                    <Image
                      src={song.image_url}
                      alt={song.title}
                      width={64}
                      height={64}
                      className="rounded object-cover"
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
                    <span>{labels.download}</span>
                  </a>
                )}
              </div>
            ))}
          </div>
        )}

        {/* Workflow Navigation */}
        {localResult?.success && (
          <div className="mt-4">
            <DimensionPanel.NextNav currentDimension="suno" />
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="p-4 border-t border-gray-700">
        <button
          onClick={handleGenerate}
          disabled={isPending || !title.trim() || !prompt.trim()}
          className={`w-full py-3 rounded-lg font-medium transition-colors ${isPending || !title.trim() || !prompt.trim()
            ? "bg-gray-600 text-gray-400 cursor-not-allowed"
            : "bg-gradient-to-r from-purple-600 to-indigo-600 text-white hover:from-purple-500 hover:to-indigo-500"
            }`}
        >
          {isPending ? (
            <span className="flex items-center justify-center gap-2">
              <span className="animate-spin">⏳</span>
              <span>{labels.generating}</span>
            </span>
          ) : (
            <span className="flex items-center justify-center gap-2">
              <span>🎵</span>
              <span>{labels.generate(creditCost)}</span>
            </span>
          )}
        </button>

        <p className="text-xs text-gray-500 text-center mt-2">
          {labels.twoSongsNote}
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
