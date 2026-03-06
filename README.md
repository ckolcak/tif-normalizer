# TIF Normalizer

**Grafik Çizgi Renk Normalleştirici** — Seismogram, EKG veya kayıt şeridi gibi TIF grafik görüntülerindeki çizgilerin rengini normalize eden tam yığın web uygulaması.

**Chart Line Color Normalizer** — A full-stack web application that normalizes the plotted line color in TIF chart images (seismograms, EKGs, chart recorder strips).

---

## 🚀 Hızlı Başlangıç / Quick Start (Docker)

```bash
docker-compose up --build
```

- Frontend: http://localhost:3000  
- Backend API: http://localhost:8000

---

## 🛠 Manuel Kurulum / Manual Setup

### Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm start
```

---

## 🏗 Teknoloji Yığını / Tech Stack

![Python](https://img.shields.io/badge/Python-3.11-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.110-green)
![React](https://img.shields.io/badge/React-18-61dafb)
![TypeScript](https://img.shields.io/badge/TypeScript-5.3-3178c6)
![TailwindCSS](https://img.shields.io/badge/TailwindCSS-3.4-38bdf8)
![Docker](https://img.shields.io/badge/Docker-compose-2496ed)

---

## ⚙️ Algoritma / Algorithm

1. **Arka Plan Tespiti** — HSV renk uzayında sarı/krem ızgara arka planı tespit edilir  
2. **Çizgi İzolasyonu** — Arka plan olmayan pikseller çizgi maskesi olarak işaretlenir  
3. **Rolling Window Normalizasyonu** — 100 piksellik pencereler kaydırılarak her penceredeki çizgi piksellerinin median rengi hesaplanır  
4. **Renk Düzeltmesi** — Tüm çizgi pikselleri hedef koyu lacivert `#1a1a6e` rengine dönüştürülür  
5. **Çıktı** — Orijinal ve normalize edilmiş görüntüler base64 PNG olarak döndürülür

---

## 📡 API

`POST /api/normalize` — TIF/PNG/JPG yükle, normalize et

```json
{
  "original_image": "base64_string",
  "normalized_image": "base64_string",
  "processing_time": 1.23,
  "detected_color": "#2b2b8f",
  "normalized_color": "#1a1a6e",
  "line_pixels_count": 45230
}
```

---

## 📁 Proje Yapısı / Project Structure

```
tif-normalizer/
├── frontend/
│   ├── public/index.html
│   ├── src/
│   │   ├── App.tsx
│   │   ├── App.css
│   │   ├── components/
│   │   │   ├── UploadZone.tsx
│   │   │   ├── ImageComparison.tsx
│   │   │   └── ProgressBar.tsx
│   │   ├── index.tsx
│   │   └── index.css
│   ├── package.json
│   ├── tsconfig.json
│   └── tailwind.config.js
├── backend/
│   ├── main.py
│   ├── normalizer.py
│   ├── requirements.txt
│   └── Dockerfile
├── docker-compose.yml
└── README.md
```
