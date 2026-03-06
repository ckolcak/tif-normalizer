import React, { useState } from "react";
import axios from "axios";
import "./App.css";
import UploadZone from "./components/UploadZone";
import ImageComparison from "./components/ImageComparison";
import ProgressBar from "./components/ProgressBar";

const API_URL = process.env.REACT_APP_API_URL || "http://localhost:8000";

interface NormalizeResult {
  originalUrl: string;
  normalizedUrl: string;
  processingTime: number;
  detectedColor: string;
  normalizedColor: string;
  linePixelsCount: number;
}

const App: React.FC = () => {
  const [file, setFile] = useState<File | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [progress, setProgress] = useState(0);
  const [result, setResult] = useState<NormalizeResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleFileSelect = (selected: File) => {
    setFile(selected);
    setResult(null);
    setError(null);
  };

  const handleProcess = async () => {
    if (!file) return;

    setIsProcessing(true);
    setError(null);
    setProgress(10);

    const formData = new FormData();
    formData.append("file", file);

    try {
      setProgress(30);
      const response = await axios.post(`${API_URL}/api/normalize`, formData, {
        headers: { "Content-Type": "multipart/form-data" },
        onUploadProgress: (e) => {
          if (e.total) {
            const pct = Math.round((e.loaded / e.total) * 40) + 30;
            setProgress(pct);
          }
        },
      });

      setProgress(90);
      const data = response.data;

      setResult({
        originalUrl: `data:image/png;base64,${data.original_image}`,
        normalizedUrl: `data:image/png;base64,${data.normalized_image}`,
        processingTime: data.processing_time,
        detectedColor: data.detected_color,
        normalizedColor: data.normalized_color,
        linePixelsCount: data.line_pixels_count,
      });

      setProgress(100);
    } catch (err: unknown) {
      if (axios.isAxiosError(err)) {
        const msg =
          err.response?.data?.detail ||
          err.response?.data?.error ||
          err.message ||
          "Bilinmeyen hata";
        setError(`Hata: ${msg}`);
      } else {
        setError("Beklenmedik bir hata oluştu.");
      }
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-900 text-slate-100 flex flex-col">
      {/* Header */}
      <header className="bg-slate-800 border-b border-slate-700 py-6 px-4 shadow-lg">
        <div className="max-w-6xl mx-auto text-center">
          <h1 className="text-3xl font-bold tracking-tight text-violet-400">
            TIF Normalizer
          </h1>
          <p className="mt-1 text-slate-400 text-sm">
            Grafik Çizgi Renk Normalleştirici
          </p>
        </div>
      </header>

      <main className="flex-1 max-w-6xl mx-auto w-full px-4 py-8 space-y-8">
        {/* Upload section */}
        <section className="bg-slate-800 rounded-2xl p-6 shadow-xl border border-slate-700">
          <h2 className="text-lg font-semibold text-slate-200 mb-4">
            Dosya Yükle
          </h2>
          <UploadZone onFileSelect={handleFileSelect} selectedFile={file} />

          {file && (
            <div className="mt-4 flex justify-end">
              <button
                onClick={handleProcess}
                disabled={isProcessing}
                className="flex items-center gap-2 bg-violet-600 hover:bg-violet-500 disabled:bg-violet-900 disabled:cursor-not-allowed text-white font-semibold px-6 py-2.5 rounded-xl transition-colors duration-200"
              >
                {isProcessing ? (
                  <>
                    <span className="spinner" />
                    İşleniyor…
                  </>
                ) : (
                  "Yükle ve İşle"
                )}
              </button>
            </div>
          )}

          {isProcessing && (
            <div className="mt-4">
              <ProgressBar value={progress} />
            </div>
          )}
        </section>

        {/* Error */}
        {error && (
          <div className="bg-red-900/40 border border-red-600 text-red-300 rounded-xl p-4 text-sm">
            {error}
          </div>
        )}

        {/* Result */}
        {result && (
          <section className="bg-slate-800 rounded-2xl p-6 shadow-xl border border-slate-700">
            <h2 className="text-lg font-semibold text-slate-200 mb-1">
              Sonuç
            </h2>

            {/* Metadata */}
            <div className="flex flex-wrap gap-4 text-sm text-slate-400 mb-6">
              <span>
                ⏱ İşlem süresi:{" "}
                <strong className="text-slate-200">
                  {result.processingTime.toFixed(3)} sn
                </strong>
              </span>
              <span className="flex items-center gap-1">
                Tespit edilen renk:
                <span
                  className="inline-block w-4 h-4 rounded-sm border border-slate-600"
                  style={{ background: result.detectedColor }}
                />
                <strong className="text-slate-200">{result.detectedColor}</strong>
              </span>
              <span className="flex items-center gap-1">
                Normalize renk:
                <span
                  className="inline-block w-4 h-4 rounded-sm border border-slate-600"
                  style={{ background: result.normalizedColor }}
                />
                <strong className="text-slate-200">{result.normalizedColor}</strong>
              </span>
              <span>
                Çizgi pikseli:{" "}
                <strong className="text-slate-200">
                  {result.linePixelsCount.toLocaleString()}
                </strong>
              </span>
            </div>

            <ImageComparison
              originalUrl={result.originalUrl}
              normalizedUrl={result.normalizedUrl}
              detectedColor={result.detectedColor}
              normalizedColor={result.normalizedColor}
            />
          </section>
        )}
      </main>

      <footer className="text-center text-slate-600 text-xs py-4">
        TIF Normalizer &mdash; Grafik Çizgi Renk Normalleştirici
      </footer>
    </div>
  );
};

export default App;
