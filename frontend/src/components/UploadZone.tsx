import React, { useCallback, useState } from "react";

interface Props {
  onFileSelect: (file: File) => void;
  selectedFile: File | null;
}

const ACCEPTED = ".tif,.tiff,.png,.jpg,.jpeg";
const ACCEPTED_TYPES = new Set([
  "image/tiff",
  "image/png",
  "image/jpeg",
  "image/jpg",
]);

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
}

const UploadZone: React.FC<Props> = ({ onFileSelect, selectedFile }) => {
  const [isDragging, setIsDragging] = useState(false);

  const processFile = useCallback(
    (file: File) => {
      const ext = file.name.split(".").pop()?.toLowerCase() ?? "";
      const validExts = new Set(["tif", "tiff", "png", "jpg", "jpeg"]);
      if (!ACCEPTED_TYPES.has(file.type) && !validExts.has(ext)) return;
      onFileSelect(file);
    },
    [onFileSelect]
  );

  const onDrop = useCallback(
    (e: React.DragEvent<HTMLDivElement>) => {
      e.preventDefault();
      setIsDragging(false);
      const file = e.dataTransfer.files[0];
      if (file) processFile(file);
    },
    [processFile]
  );

  const onInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) processFile(file);
  };

  return (
    <div className="space-y-3">
      <div
        onDragOver={(e) => {
          e.preventDefault();
          setIsDragging(true);
        }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={onDrop}
        className={`relative border-2 border-dashed rounded-xl p-10 text-center cursor-pointer transition-colors duration-200
          ${
            isDragging
              ? "border-violet-400 bg-violet-900/20"
              : "border-slate-600 hover:border-violet-500 hover:bg-slate-700/40"
          }`}
      >
        <input
          type="file"
          accept={ACCEPTED}
          className="absolute inset-0 opacity-0 cursor-pointer w-full h-full"
          onChange={onInputChange}
        />

        {/* Icon */}
        <div className="flex justify-center mb-3">
          <svg
            className="w-12 h-12 text-slate-500"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth={1.5}
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5"
            />
          </svg>
        </div>

        <p className="text-slate-300 font-medium">
          Dosyayı sürükle &amp; bırak
        </p>
        <p className="text-slate-500 text-sm mt-1">
          veya tıklayarak seç
        </p>
        <p className="text-slate-600 text-xs mt-2">
          Desteklenen: .tif, .tiff, .png, .jpg — Maksimum 50 MB
        </p>
      </div>

      {selectedFile && (
        <div className="flex items-center gap-3 bg-slate-700/60 rounded-xl px-4 py-3 text-sm">
          <svg
            className="w-5 h-5 text-violet-400 shrink-0"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth={2}
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M9 12h3.75M9 15h3.75M9 18h3.75m3 .75H18a2.25 2.25 0 002.25-2.25V6.108c0-1.135-.845-2.098-1.976-2.192a48.424 48.424 0 00-1.123-.08m-5.801 0c-.065.21-.1.433-.1.664 0 .414.336.75.75.75h4.5a.75.75 0 00.75-.75 2.25 2.25 0 00-.1-.664m-5.8 0A2.251 2.251 0 0113.5 2.25H15c1.012 0 1.867.668 2.15 1.586m-5.8 0c-.376.023-.75.05-1.124.08C9.095 4.01 8.25 4.973 8.25 6.108V8.25m0 0H4.875c-.621 0-1.125.504-1.125 1.125v11.25c0 .621.504 1.125 1.125 1.125h9.75c.621 0 1.125-.504 1.125-1.125V9.375c0-.621-.504-1.125-1.125-1.125H8.25z"
            />
          </svg>
          <span className="text-slate-200 truncate flex-1">{selectedFile.name}</span>
          <span className="text-slate-400 shrink-0">{formatBytes(selectedFile.size)}</span>
        </div>
      )}
    </div>
  );
};

export default UploadZone;
