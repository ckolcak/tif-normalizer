import os

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from normalizer import load_image_as_bgr, normalize_line_color, bgr_to_base64_png

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB
ALLOWED_EXTENSIONS = {".tif", ".tiff", ".png", ".jpg", ".jpeg"}

app = FastAPI(title="TIF Normalizer API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"message": "TIF Normalizer API is running!"}


@app.post("/api/normalize")
async def normalize_image(file: UploadFile = File(...)):
    """
    TIF/PNG/JPG görüntüsündeki çizgi rengini normalize eder.
    Orijinal ve normalize edilmiş görüntüleri base64 olarak döndürür.
    """
    # Dosya uzantısı kontrolü
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Desteklenmeyen dosya formatı: {ext}. Kabul edilenler: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    contents = await file.read()

    # Boyut kontrolü
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail="Dosya boyutu 50 MB sınırını aşıyor."
        )

    try:
        img_bgr = load_image_as_bgr(contents)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"Görüntü yüklenemedi: {exc}") from exc

    try:
        normalized_bgr, detected_color, normalized_color, line_pixel_count, processing_time = normalize_line_color(img_bgr)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Normalize işlemi başarısız: {exc}") from exc

    original_b64 = bgr_to_base64_png(img_bgr)
    normalized_b64 = bgr_to_base64_png(normalized_bgr)

    return JSONResponse({
        "original_image": original_b64,
        "normalized_image": normalized_b64,
        "processing_time": round(processing_time, 3),
        "detected_color": detected_color,
        "normalized_color": normalized_color,
        "line_pixels_count": line_pixel_count,
    })
