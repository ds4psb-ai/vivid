import React, { useRef, useState } from 'react';
import { Upload, CheckCircle2 } from 'lucide-react';

interface FileUploadProps {
  onFileSelect: (file: File) => void;
  selectedFile: File | null;
}

export const FileUpload: React.FC<FileUploadProps> = ({ onFileSelect, selectedFile }) => {
  const inputRef = useRef<HTMLInputElement>(null);
  const [isDragging, setIsDragging] = useState(false);

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
      validateAndSelect(e.dataTransfer.files[0]);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      validateAndSelect(e.target.files[0]);
    }
  };

  const validateAndSelect = (file: File) => {
    if (file.type.startsWith('video/')) {
      onFileSelect(file);
    } else {
      alert("올바른 동영상 파일을 선택해주세요.");
    }
  };

  return (
    <div 
      className={`relative w-full h-64 border-2 border-dashed rounded-xl transition-all duration-300 ease-in-out cursor-pointer group
        ${isDragging 
          ? 'border-accent-blue bg-accent-blue/10' 
          : selectedFile 
            ? 'border-green-500/50 bg-green-500/5' 
            : 'border-gray-700 hover:border-gray-500 hover:bg-gray-800/50'
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
        accept="video/mp4,video/webm,video/quicktime" 
        onChange={handleChange}
      />
      
      <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
        {selectedFile ? (
          <>
            <div className="w-16 h-16 rounded-full bg-green-500/20 flex items-center justify-center mb-4 animate-bounce">
              <CheckCircle2 className="w-8 h-8 text-green-500" />
            </div>
            <h3 className="text-lg font-medium text-white mb-1">{selectedFile.name}</h3>
            <p className="text-sm text-gray-400">
              {(selectedFile.size / (1024 * 1024)).toFixed(2)} MB • 분석 준비 완료
            </p>
          </>
        ) : (
          <>
            <div className={`w-16 h-16 rounded-full flex items-center justify-center mb-4 transition-colors
              ${isDragging ? 'bg-accent-blue/20' : 'bg-gray-800 group-hover:bg-gray-700'}`}>
              <Upload className={`w-8 h-8 ${isDragging ? 'text-accent-blue' : 'text-gray-400'}`} />
            </div>
            <h3 className="text-lg font-medium text-white mb-2">분석할 영상 업로드</h3>
            <p className="text-sm text-gray-500 text-center max-w-xs">
              클릭하거나 파일을 드래그하세요<br/>
              <span className="text-xs text-gray-600 mt-1 block">MP4, MOV, WEBM (20MB 이하 권장)</span>
            </p>
          </>
        )}
      </div>
    </div>
  );
};
