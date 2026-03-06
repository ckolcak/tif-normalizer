from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
import numpy as np
import cv2
from PIL import Image
import tifffile
from io import BytesIO
import base64

app = FastAPI(title="TIF Normalizer API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

def normalize_line_color(image_array: np.ndarray) -> np.ndarray:
    """
    Rolling window ile çizgi renklerini normalize eder.
    Sarı arka planı korur, çizgiyi tek renk yapar.
    """
    # BGR'ye çevir
    if len(image_array.shape) == 2:
        img_bgr = cv2.cvtColor(image_array, cv2.COLOR_GRAY2BGR)
    else:
        img_bgr = image_array.copy()

    img_hsv = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV)

    # Sarı arka plan maskesi (HSV'de sarı aralığı)
    lower_yellow = np.array([15, 50, 150])
    upper_yellow = np.array([40, 255, 255])
    yellow_mask = cv2.inRange(img_hsv, lower_yellow, upper_yellow)

    # Beyaz/açık renk maskesi (grid çizgileri)
    lower_white = np.array([0, 0, 200])
    upper_white = np.array([180, 30, 255])
    white_mask = cv2.inRange(img_hsv, lower_white, upper_white)

    # Arka plan = sarı + beyaz
    background_mask = cv2.bitwise_or(yellow_mask, white_mask)

    # Çizgi maskesi = arka plan olmayan piksel
    line_mask = cv2.bitwise_not(background_mask)

    # Morfolojik işlem ile gürültüyü temizle
    kernel = np.ones((2, 2), np.uint8)
    line_mask = cv2.morphologyEx(line_mask, cv2.MORPH_OPEN, kernel)

    # Çıktı görüntüsünü oluştur
    output = img_bgr.copy()

    # Rolling window ile normalize et
    height, width = img_bgr.shape[:2]
    window_size = max(50, width // 20)
    target_color = (20, 20, 20)  # Koyu siyah (BGR)

    # Her sütun bloğu için çizgi piksellerini normalize et
    for x_start in range(0, width, window_size):
        x_end = min(x_start + window_size, width)
        window_mask = line_mask[:, x_start:x_end]

        if np.sum(window_mask) > 0:
            # Bu penceredeki çizgi piksellerini bul
            line_pixels_y, line_pixels_x = np.where(window_mask > 0)

            if len(line_pixels_y) > 0:
                # Çizgi piksellerinin mevcut renklerini al
                colors = img_bgr[line_pixels_y, line_pixels_x + x_start]
                # Median renk
                median_color = np.median(colors, axis=0).astype(int)

                # Eğer renk yeterince koyu değilse normalize et
                brightness = np.mean(median_color)
                if brightness > 100:
                    # Normalize et - koyu renk yap
                    output[line_pixels_y, line_pixels_x + x_start] = target_color
                else:
                    # Zaten koyu, sadece tek renge normalize et
                    output[line_pixels_y, line_pixels_x + x_start] = target_color

    return output


def array_to_base64(img_array: np.ndarray, format: str = "PNG") -> str:
    """numpy array'i base64 string'e çevirir"""
    img_rgb = cv2.cvtColor(img_array, cv2.COLOR_BGR2RGB)
    pil_img = Image.fromarray(img_rgb)
    buffer = BytesIO()
    pil_img.save(buffer, format=format)
    buffer.seek(0)
    return base64.b64encode(buffer.read()).decode("utf-8")

@app.get("/")
def root():
    return {"message": "TIF Normalizer API is running!"}

@app.post("/normalize/")
async def normalize_image(file: UploadFile = File(...)):
    try:
        contents = await file.read()

        # TIF dosyasını oku
        try:
            img_array = tifffile.imread(BytesIO(contents))
        except Exception:
            # Fallback: PIL ile dene
            pil_img = Image.open(BytesIO(contents))
            img_array = np.array(pil_img)

        # Renk kanallarını düzelt
        if len(img_array.shape) == 2:
            # Grayscale → BGR
            img_bgr = cv2.cvtColor(img_array.astype(np.uint8), cv2.COLOR_GRAY2BGR)
        elif img_array.shape[2] == 4:
            # RGBA → BGR
            img_bgr = cv2.cvtColor(img_array.astype(np.uint8), cv2.COLOR_RGBA2BGR)
        elif img_array.shape[2] == 3:
            img_bgr = cv2.cvtColor(img_array.astype(np.uint8), cv2.COLOR_RGB2BGR)
        else:
            img_bgr = img_array.astype(np.uint8)

        # Normalize et
        normalized = normalize_line_color(img_bgr)

        # Her ikisini base64'e çevir
        original_b64 = array_to_base64(img_bgr)
        normalized_b64 = array_to_base64(normalized)

        return JSONResponse({
            "success": True,
            "original": original_b64,
            "normalized": normalized_b64,
            "width": img_bgr.shape[1],
            "height": img_bgr.shape[0],
            "filename": file.filename
        })

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

@app.post("/download/")
async def download_normalized(file: UploadFile = File(...)):
    """Normalleştirilmiş görüntüyü TIF olarak indir"""
    try:
        contents = await file.read()

        try:
            img_array = tifffile.imread(BytesIO(contents))
        except Exception:
            pil_img = Image.open(BytesIO(contents))
            img_array = np.array(pil_img)

        if len(img_array.shape) == 2:
            img_bgr = cv2.cvtColor(img_array.astype(np.uint8), cv2.COLOR_GRAY2BGR)
        elif img_array.shape[2] == 4:
            img_bgr = cv2.cvtColor(img_array.astype(np.uint8), cv2.COLOR_RGBA2BGR)
        else:
            img_bgr = cv2.cvtColor(img_array.astype(np.uint8), cv2.COLOR_RGB2BGR)

        normalized = normalize_line_color(img_bgr)
        normalized_rgb = cv2.cvtColor(normalized, cv2.COLOR_BGR2RGB)

        buffer = BytesIO()
        tifffile.imwrite(buffer, normalized_rgb)
        buffer.seek(0)

        return StreamingResponse(
            buffer,
            media_type="image/tiff",
            headers={"Content-Disposition": f"attachment; filename=normalized_{file.filename}"}
        )

    except Exception as e:
        return JSONResponse(status_code=500, content={"success": False, "error": str(e)})