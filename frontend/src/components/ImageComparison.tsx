import React from "react";

interface Props {
  originalUrl: string;
  normalizedUrl: string;
  detectedColor: string;
  normalizedColor: string;
}

const ImageComparison: React.FC<Props> = ({
  originalUrl,
  normalizedUrl,
  detectedColor,
  normalizedColor,
}) => {
  const handleDownload = () => {
    const link = document.createElement("a");
    link.href = normalizedUrl;
    link.download = "normalized.png";
    link.click();
  };

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
      {/* Orijinal */}
      <div className="flex flex-col gap-3">
        <div className="flex items-center justify-between">
          <h3 className="font-semibold text-slate-300">Orijinal</h3>
          <div className="flex items-center gap-2 text-xs text-slate-400">
            <span
              className="inline-block w-4 h-4 rounded-sm border border-slate-600"
              style={{ background: detectedColor }}
            />
            {detectedColor}
          </div>
        </div>
        <div className="bg-slate-900 rounded-xl overflow-hidden border border-slate-700 flex items-center justify-center min-h-48">
          <img
            src={originalUrl}
            alt="Orijinal"
            className="max-w-full max-h-96 object-contain"
          />
        </div>
      </div>

      {/* Normalize Edilmiş */}
      <div className="flex flex-col gap-3">
        <div className="flex items-center justify-between">
          <h3 className="font-semibold text-slate-300">Normalize Edilmiş</h3>
          <div className="flex items-center gap-2 text-xs text-slate-400">
            <span
              className="inline-block w-4 h-4 rounded-sm border border-slate-600"
              style={{ background: normalizedColor }}
            />
            {normalizedColor}
          </div>
        </div>
        <div className="bg-slate-900 rounded-xl overflow-hidden border border-slate-700 flex items-center justify-center min-h-48">
          <img
            src={normalizedUrl}
            alt="Normalize Edilmiş"
            className="max-w-full max-h-96 object-contain"
          />
        </div>
        <button
          onClick={handleDownload}
          className="flex items-center justify-center gap-2 bg-slate-700 hover:bg-slate-600 text-slate-200 text-sm font-medium px-4 py-2.5 rounded-xl transition-colors duration-200 border border-slate-600"
        >
          <svg
            className="w-4 h-4"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth={2}
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5M16.5 12L12 16.5m0 0L7.5 12m4.5 4.5V3"
            />
          </svg>
          İndir (PNG)
        </button>
      </div>
    </div>
  );
};

export default ImageComparison;
