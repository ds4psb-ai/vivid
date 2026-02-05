import React, { useRef, useState } from 'react';
import { Upload, FileJson, MessageSquare, Sparkles, CheckCircle, AlertCircle, X } from 'lucide-react';
import { VariationData, VariationOption } from '../types';

interface VariationPanelProps {
  variationData: VariationData;
  onVariationDataChange: (data: VariationData) => void;
  onGenerateVariation: () => void;
  onSkipVariation: () => void;
}

const VARIATION_OPTIONS: { key: VariationOption; emoji: string; label: string; percent: string; desc: string }[] = [
  { key: 'A', emoji: '🅰️', label: '안정형', percent: '8%', desc: '소품 디테일만 변경' },
  { key: 'B', emoji: '🅱️', label: '밸런스형', percent: '15%', desc: '의상/소품 + 조명 톤' },
  { key: 'AB', emoji: '🆎', label: '과감형', percent: '18%', desc: '문화권/스타일 전환' },
];

export const VariationPanel: React.FC<VariationPanelProps> = ({
  variationData,
  onVariationDataChange,
  onGenerateVariation,
  onSkipVariation,
}) => {
  const inputRef = useRef<HTMLInputElement>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [parseError, setParseError] = useState<string | null>(null);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      validateAndParseJson(e.dataTransfer.files[0]);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      validateAndParseJson(e.target.files[0]);
    }
  };

  const validateAndParseJson = async (file: File) => {
    setParseError(null);

    if (!file.name.endsWith('.json')) {
      setParseError('JSON 파일만 업로드 가능합니다.');
      return;
    }

    try {
      const text = await file.text();
      const parsed = JSON.parse(text);
      onVariationDataChange({
        ...variationData,
        personaJson: file,
        personaContent: parsed,
      });
    } catch {
      setParseError('JSON 파싱 실패: 올바른 JSON 형식인지 확인하세요.');
    }
  };

  const handleRemoveFile = () => {
    onVariationDataChange({
      ...variationData,
      personaJson: null,
      personaContent: null,
    });
    setParseError(null);
    if (inputRef.current) {
      inputRef.current.value = '';
    }
  };

  const handleOptionSelect = (option: VariationOption) => {
    onVariationDataChange({
      ...variationData,
      variationOption: option,
    });
  };

  const handleCommentChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    onVariationDataChange({
      ...variationData,
      bestComment: e.target.value,
    });
  };

  const isGenerateEnabled = variationData.variationOption !== null;

  return (
    <div className="mt-6 p-6 bg-gray-900/80 border border-gray-700 rounded-xl space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
      {/* Header */}
      <div className="flex items-center gap-2 text-accent-purple">
        <Sparkles className="w-5 h-5" />
        <h3 className="font-bold text-lg">변주 생성 (선택)</h3>
      </div>

      {/* persona.json Upload */}
      <div className="space-y-2">
        <label className="flex items-center gap-2 text-sm font-medium text-gray-300">
          <FileJson className="w-4 h-4 text-accent-cyan" />
          persona.json (선택)
        </label>

        {variationData.personaJson ? (
          <div className="flex items-center gap-3 p-3 bg-green-500/10 border border-green-500/30 rounded-lg">
            <CheckCircle className="w-5 h-5 text-green-500" />
            <span className="text-sm text-green-400 flex-1">{variationData.personaJson.name}</span>
            <button
              onClick={handleRemoveFile}
              className="p-1 hover:bg-gray-700 rounded transition-colors"
            >
              <X className="w-4 h-4 text-gray-400 hover:text-white" />
            </button>
          </div>
        ) : (
          <div
            className={`relative w-full h-24 border-2 border-dashed rounded-lg transition-all duration-300 ease-in-out cursor-pointer
              ${isDragging
                ? 'border-accent-cyan bg-accent-cyan/10'
                : 'border-gray-600 hover:border-gray-500 hover:bg-gray-800/50'
              }`}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            onClick={() => inputRef.current?.click()}
          >
            <input
              type="file"
              ref={inputRef}
              className="hidden"
              accept=".json,application/json"
              onChange={handleChange}
            />
            <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
              <Upload className={`w-6 h-6 mb-2 ${isDragging ? 'text-accent-cyan' : 'text-gray-500'}`} />
              <p className="text-xs text-gray-500">드래그 앤 드롭 또는 클릭하여 JSON 파일 업로드</p>
            </div>
          </div>
        )}

        {parseError && (
          <div className="flex items-center gap-2 text-red-400 text-xs">
            <AlertCircle className="w-4 h-4" />
            {parseError}
          </div>
        )}
      </div>

      {/* Best Comment */}
      <div className="space-y-2">
        <label className="flex items-center gap-2 text-sm font-medium text-gray-300">
          <MessageSquare className="w-4 h-4 text-accent-cyan" />
          베스트 댓글 (선택)
        </label>
        <textarea
          value={variationData.bestComment}
          onChange={handleCommentChange}
          placeholder="바이럴 포인트를 강화할 댓글을 입력하세요..."
          className="w-full h-20 px-4 py-3 bg-gray-800 border border-gray-700 rounded-lg text-sm text-gray-200 placeholder-gray-500 focus:outline-none focus:border-accent-cyan focus:ring-1 focus:ring-accent-cyan/50 resize-none"
        />
      </div>

      {/* Variation Options */}
      <div className="space-y-3">
        <label className="flex items-center gap-2 text-sm font-medium text-gray-300">
          🎯 변주 옵션 선택
        </label>
        <div className="grid grid-cols-3 gap-3">
          {VARIATION_OPTIONS.map((opt) => (
            <button
              key={opt.key}
              onClick={() => handleOptionSelect(opt.key)}
              className={`p-4 rounded-xl border-2 transition-all duration-200 text-center
                ${variationData.variationOption === opt.key
                  ? 'border-accent-purple bg-accent-purple/20 shadow-[0_0_15px_rgba(168,85,247,0.3)]'
                  : 'border-gray-700 bg-gray-800/50 hover:border-gray-600 hover:bg-gray-800'
                }`}
            >
              <div className="text-2xl mb-1">{opt.emoji}</div>
              <div className="font-bold text-white text-sm">{opt.label}</div>
              <div className="text-accent-purple text-xs font-medium">({opt.percent})</div>
              <div className="text-gray-400 text-xs mt-1">{opt.desc}</div>
            </button>
          ))}
        </div>
      </div>

      {/* Action Buttons */}
      <div className="space-y-3 pt-2">
        <button
          onClick={onGenerateVariation}
          disabled={!isGenerateEnabled}
          className={`w-full py-4 rounded-xl font-bold text-lg flex items-center justify-center gap-2 transition-all
            ${isGenerateEnabled
              ? 'bg-gradient-to-r from-accent-purple to-accent-blue text-white hover:shadow-[0_0_20px_rgba(168,85,247,0.5)] active:scale-95'
              : 'bg-gray-800 text-gray-500 cursor-not-allowed'
            }`}
        >
          <Sparkles className="w-5 h-5" />
          변주 워크플로우 생성
        </button>

        <button
          onClick={onSkipVariation}
          className="w-full py-3 rounded-xl font-medium text-sm bg-gray-800 border border-gray-700 text-gray-400 hover:text-white hover:border-gray-600 transition-all"
        >
          변주 없이 완료 (오마주 워크플로우만 사용)
        </button>
      </div>
    </div>
  );
};
