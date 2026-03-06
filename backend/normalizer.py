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

def detect_line_mask(img_bgr: np.ndarray) -> np.ndarray:
    """
    Görüntüdeki mavi/koyu çizgiyi tespit eder.
    Arka plan: beyaz veya bej/krem
    Çizgi: mavi, lacivert, koyu gibi piksel
    """
    img_hsv = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV)

    # --- Mavi çizgi maskesi ---
    lower_blue = np.array([90, 30, 30])
    upper_blue = np.array([160, 255, 255])
    blue_mask = cv2.inRange(img_hsv, lower_blue, upper_blue)

    # --- Koyu çizgi maskesi ---
    lower_dark = np.array([0, 0, 0])
    upper_dark = np.array([180, 255, 120])
    dark_mask = cv2.inRange(img_hsv, lower_dark, upper_dark)

    # Çizgi = mavi VEYA koyu
    line_mask = cv2.bitwise_or(blue_mask, dark_mask)

    # --- Arka plan maskesi ---
    lower_white = np.array([0, 0, 200])
    upper_white = np.array([180, 40, 255])
    white_mask = cv2.inRange(img_hsv, lower_white, upper_white)

    lower_beige = np.array([10, 10, 160])
    upper_beige = np.array([35, 80, 255])
    beige_mask = cv2.inRange(img_hsv, lower_beige, upper_beige)

    # Kırmızı grid çizgileri
    lower_red1 = np.array([0, 40, 100])
    upper_red1 = np.array([10, 255, 255])
    lower_red2 = np.array([170, 40, 100])
    upper_red2 = np.array([180, 255, 255])
    red_mask = cv2.bitwise_or(
        cv2.inRange(img_hsv, lower_red1, upper_red1),
        cv2.inRange(img_hsv, lower_red2, upper_red2)
    )

    background_mask = cv2.bitwise_or(white_mask, beige_mask)
    background_mask = cv2.bitwise_or(background_mask, red_mask)

    # Çizgi maskesinden arka planı çıkar
    line_mask = cv2.bitwise_and(line_mask, cv2.bitwise_not(background_mask))

    kernel = np.ones((2, 2), np.uint8)
    line_mask = cv2.morphologyEx(line_mask, cv2.MORPH_OPEN, kernel)
    line_mask = cv2.morphologyEx(line_mask, cv2.MORPH_CLOSE, kernel)

    return line_mask

def extract_line_points(line_mask: np.ndarray):
    """
    Her x sütununda çizgi piksellerinin median y koordinatını çıkarır.
    Outlier filtrelemesi uygular.
    """
    height, width = line_mask.shape
    points_x = []
    points_y = []

    for x in range(width):
        col = line_mask[:, x]
        y_coords = np.where(col > 0)[0]
        if len(y_coords) > 0:
            y_val = float(np.median(y_coords))
            points_x.append(x)
            points_y.append(y_val)

    if len(points_x) < 10:
        return np.array(points_x), np.array(points_y)

    xs = np.array(points_x)
    ys = np.array(points_y)

    diffs = np.abs(np.diff(ys))
    diffs = np.concatenate([[0], diffs])
    valid = diffs < 30
    xs = xs[valid]
    ys = ys[valid]

    return xs, ys

def smooth_line_points(xs: np.ndarray, ys: np.ndarray, width: int):
    """
    Savitzky-Golay filtresi ile çizgi noktalarını düzleştirir.
    Döndürür: (full_xs, smoothed_ys, error_margin)
    """
    if len(xs) < 10:
        full_xs = np.arange(width)
        return full_xs, np.full(width, -1.0), np.zeros(width)

    wl = min(51, len(xs))
    if wl % 2 == 0:
        wl -= 1
    if wl < 5:
        wl = 5

    try:
        ys_smooth = savgol_filter(ys, window_length=wl, polyorder=3)
    except Exception:
        ys_smooth = ys.copy()

    error_margin = np.abs(ys - ys_smooth)
    window = 20
    error_smooth = np.convolve(error_margin, np.ones(window) / window, mode='same')

    full_xs = np.arange(width)
    full_ys = np.interp(full_xs, xs, ys_smooth, left=-1, right=-1)
    full_err = np.interp(full_xs, xs, error_smooth, left=0, right=0)

    return full_xs, full_ys, full_err

def normalize_line_color(img_bgr: np.ndarray):
    """
    Mavi çizgiyi tespit eder, orijinal görüntü üzerine:
      - Sarı güven bandı (hata payı) çizer
      - Kırmızı ana hat (jilet gibi düzgün) çizer
    Mavi çizgi olduğu gibi kalır, kırmızı onun üstüne çizilir.
    """
    start_time = time.time()

    height, width = img_bgr.shape[:2]

    # 1. Mavi çizgi maskesi
    line_mask = detect_line_mask(img_bgr)

    # 2. Tespit edilen renk
    detected_color = detect_line_color_hex(img_bgr, line_mask)

    # 3. Piksel sayısı
    line_pixel_count = int(np.sum(line_mask > 0))

    # 4. Orijinal görüntüyü koru
    output = img_bgr.copy()

    # 5. Çizgi noktalarını çıkar
    xs, ys = extract_line_points(line_mask)

    if len(xs) >= 10:
        full_xs, smoothed_ys, error_margin = smooth_line_points(xs, ys, width)

        line_thickness = max(3, height // 150)
        band_thickness = max(2, height // 300)

        # 6. Sarı güven bandı
        yellow_color = (0, 200, 255)  # BGR: sarı
        for x in range(width):
            y_center = smoothed_ys[x]
            if y_center < 0:
                continue
            err = max(2, error_margin[x])
            y_upper = int(round(max(0, y_center - err)))
            y_lower = int(round(min(height - 1, y_center + err)))
            output[max(0, y_upper - band_thickness):y_upper + band_thickness + 1, x] = yellow_color
            output[max(0, y_lower - band_thickness):y_lower + band_thickness + 1, x] = yellow_color

        # 7. Kırmızı ana hat (mavi çizginin üstüne)
        red_color = (0, 0, 255)
        for x in range(width):
            y = smoothed_ys[x]
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
