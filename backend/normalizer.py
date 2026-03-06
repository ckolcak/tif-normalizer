import time
import base64
import numpy as np
import cv2
from PIL import Image
import tifffile
from io import BytesIO
from scipy.signal import savgol_filter

def detect_line_color_hex(img_bgr: np.ndarray, line_mask: np.ndarray) -> str:
    """Çizgi piksellerinin median rengini hex olarak döndürür."""
    line_pixels_y, line_pixels_x = np.where(line_mask > 0)
    if len(line_pixels_y) == 0:
        return "#000000"
    colors = img_bgr[line_pixels_y, line_pixels_x]
    median_color = np.median(colors, axis=0).astype(int)
    b, g, r = int(median_color[0]), int(median_color[1]), int(median_color[2])
    return f"#{r:02x}{g:02x}{b:02x}"

def find_line_top_edge(line_mask: np.ndarray) -> np.ndarray:
    """
    Her x sütununda çizginin en üst pikselini bulur.
    Döndürür: shape (width,) array, her sütun için y koordinatı (bulunamazsa -1)
    """
    height, width = line_mask.shape
    top_edge = np.full(width, -1, dtype=np.float64)
    for x in range(width):
        col = line_mask[:, x]
        ys = np.where(col > 0)[0]
        if len(ys) > 0:
            top_edge[x] = float(ys[0])
    return top_edge

def smooth_top_edge(top_edge: np.ndarray, window_length: int = 51, polyorder: int = 3) -> np.ndarray:
    """
    Savitzky-Golay filtresi ile üst kenar eğrisini düzleştirir.
    Sadece geçerli (>= 0) noktaları kullanır, boşlukları interpolasyon ile doldurur.
    """
    width = len(top_edge)
    valid = top_edge >= 0
    if np.sum(valid) < window_length:
        return top_edge.copy()

    xs = np.arange(width)
    # Boşlukları lineer interpolasyon ile doldur
    filled = top_edge.copy()
    filled[~valid] = np.interp(xs[~valid], xs[valid], top_edge[valid])

    # Pencere boyutu tek sayı olmalı
    wl = min(window_length, width)
    if wl % 2 == 0:
        wl -= 1
    if wl < polyorder + 2:
        return filled

    smoothed = savgol_filter(filled, window_length=wl, polyorder=polyorder)
    return smoothed

def normalize_line_color(img_bgr: np.ndarray):
    """
    Rolling window ile çizgi renklerini normalize eder ve
    çizginin üst kenarına düzgün bir kırmızı çizgi çizer.

    Döndürdükleri:
        normalized_bgr: normalize edilmiş görüntü (kırmızı üst kenar çizgisi dahil)
        detected_color: tespit edilen çizgi rengi (hex)
        normalized_color: normalize edilmiş renk (hex)
        line_pixel_count: çizgi piksel sayısı
        processing_time: saniye cinsinden işlem süresi
    """
    start_time = time.time()

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

    # Tespit edilen rengi hesapla (normalleştirme öncesi)
    detected_color = detect_line_color_hex(img_bgr, line_mask)

    # Toplam çizgi piksel sayısı
    line_pixel_count = int(np.sum(line_mask > 0))

    # Çıktı görüntüsünü oluştur
    output = img_bgr.copy()

    # Hedef renk: koyu lacivert (BGR: 110, 26, 26) → #1a1a6e
    target_color_bgr = (110, 26, 26)

    # Rolling window ile normalize et
    height, width = img_bgr.shape[:2]
    window_size = max(50, min(100, width // 20))

    for x_start in range(0, width, window_size):
        x_end = min(x_start + window_size, width)
        window_mask = line_mask[:, x_start:x_end]

        if np.sum(window_mask) > 0:
            line_pixels_y, line_pixels_x = np.where(window_mask > 0)
            if len(line_pixels_y) > 0:
                output[line_pixels_y, line_pixels_x + x_start] = target_color_bgr

    # Çizginin üst kenarını bul ve kırmızı çizgi çiz
    top_edge = find_line_top_edge(line_mask)
    smoothed_edge = smooth_top_edge(top_edge, window_length=101, polyorder=3)

    # Kırmızı çizgiyi çiz (BGR: 0, 0, 255)
    red_color = (0, 0, 255)
    line_thickness = max(2, height // 200)  # Görüntü boyutuna göre kalınlık

    for x in range(width):
        y = smoothed_edge[x]
        if y >= 0:
            y_int = int(round(y))
            y_start = max(0, y_int - line_thickness // 2)
            y_end = min(height, y_int + line_thickness // 2 + 1)
            output[y_start:y_end, x] = red_color

    normalized_color = "#1a1a6e"
    processing_time = time.time() - start_time

    return output, detected_color, normalized_color, line_pixel_count, processing_time

def load_image_as_bgr(file_bytes: bytes) -> np.ndarray:
    """Dosya byte'larından BGR numpy dizisi yükler."""
    try:
        img_array = tifffile.imread(BytesIO(file_bytes))
    except Exception:
        pil_img = Image.open(BytesIO(file_bytes))
        img_array = np.array(pil_img)

    if img_array.dtype != np.uint8:
        # 16-bit veya float görüntüleri uint8'e dönüştür
        img_min, img_max = img_array.min(), img_array.max()
        if img_max > img_min:
            img_array = ((img_array - img_min) / (img_max - img_min) * 255).astype(np.uint8)
        else:
            img_array = img_array.astype(np.uint8)

    if len(img_array.shape) == 2:
        img_bgr = cv2.cvtColor(img_array, cv2.COLOR_GRAY2BGR)
    elif img_array.shape[2] == 4:
        img_bgr = cv2.cvtColor(img_array, cv2.COLOR_RGBA2BGR)
    elif img_array.shape[2] == 3:
        img_bgr = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
    else:
        img_bgr = img_array

    return img_bgr

def bgr_to_base64_png(img_bgr: np.ndarray) -> str:
    """BGR numpy dizisini base64 PNG string'e çevirir."""
    img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
    pil_img = Image.fromarray(img_rgb)
    buffer = BytesIO()
    pil_img.save(buffer, format="PNG")
    buffer.seek(0)
    return base64.b64encode(buffer.read()).decode("utf-8")
