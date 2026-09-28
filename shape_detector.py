import cv2
import numpy as np


def get_color_name(bgr_pixel):
    pixel = np.uint8([[bgr_pixel]])
    hsv = cv2.cvtColor(pixel, cv2.COLOR_BGR2HSV)[0][0]
    h, s, v = int(hsv[0]), int(hsv[1]), int(hsv[2])

    if v < 40:
        return "black"
    if s < 30 and v > 200:
        return "white"
    if s < 50:
        return "gray"

    # Roșu — două intervale în HSV (0-10 și 160-180)
    if h < 10 or h >= 160:
        if s > 150 and v > 150:
            return "red"
        elif s < 150 and v > 180:
            return "pink"
        return "red"

    if 10 <= h < 20:
        return "orange"

    if 20 <= h < 33:
        # Diferențiere galben vs portocaliu după saturație
        if s > 200:
            return "orange"
        return "yellow"

    if 33 <= h < 85:
        return "green"

    if 85 <= h < 100:
        return "cyan"

    if 100 <= h < 130:
        return "blue"

    if 130 <= h < 160:
        return "purple"

    return "unknown"


def get_dominant_color_in_mask(image, mask):

    pixels = image[mask == 255]
    if len(pixels) == 0:
        return "unknown"


    non_white = pixels[~((pixels[:, 0] > 220) & (pixels[:, 1] > 220) & (pixels[:, 2] > 220))]
    if len(non_white) == 0:
        return "white"


    pixels_bgr = non_white.reshape(-1, 1, 3).astype(np.uint8)
    pixels_hsv = cv2.cvtColor(pixels_bgr, cv2.COLOR_BGR2HSV).reshape(-1, 3)

    h_med = int(np.median(pixels_hsv[:, 0]))
    s_med = int(np.median(pixels_hsv[:, 1]))
    v_med = int(np.median(pixels_hsv[:, 2]))


    if v_med < 40:
        return "black"
    if s_med < 30 and v_med > 200:
        return "white"
    if s_med < 50:
        return "gray"

    if h_med < 10 or h_med >= 160:
        if s_med > 150 and v_med > 150:
            return "red"
        elif s_med < 150 and v_med > 180:
            return "pink"
        return "red"

    if 10 <= h_med < 20:
        return "orange"

    if 20 <= h_med < 33:
        if s_med > 200:
            return "orange"
        return "yellow"

    if 33 <= h_med < 85:
        return "green"

    if 85 <= h_med < 100:
        return "cyan"

    if 100 <= h_med < 130:
        return "blue"

    if 130 <= h_med < 160:
        return "purple"

    return "unknown"


def detect_shapes(image):
    """
    Detectează formele dintr-o imagine folosind multiple metode de threshold.
    Returnează lista: [{shape, color, contour, center, area}]
    """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (7, 7), 0)

    all_contours = []


    thresh1 = cv2.adaptiveThreshold(
        blurred, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY_INV, 21, 4
    )
    c1, _ = cv2.findContours(thresh1, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    all_contours.extend(c1)


    edges = cv2.Canny(blurred, 30, 100)
    kernel = np.ones((3, 3), np.uint8)
    edges = cv2.dilate(edges, kernel, iterations=2)
    c2, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    all_contours.extend(c2)


    for channel_combo in [
        cv2.cvtColor(image, cv2.COLOR_BGR2HSV)[:, :, 1],
        cv2.cvtColor(image, cv2.COLOR_BGR2LAB)[:, :, 1],
        cv2.cvtColor(image, cv2.COLOR_BGR2LAB)[:, :, 2],   #
    ]:
        _, thresh_ch = cv2.threshold(channel_combo, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        c_ch, _ = cv2.findContours(thresh_ch, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        all_contours.extend(c_ch)


    min_area = max(500, image.shape[0] * image.shape[1] * 0.002)
    max_area = image.shape[0] * image.shape[1] * 0.95

    shapes = []
    used_centers = []

    for contour in all_contours:
        area = cv2.contourArea(contour)
        if area < min_area or area > max_area:
            continue


        M = cv2.moments(contour)
        if M["m00"] == 0:
            continue
        cx = int(M["m10"] / M["m00"])
        cy = int(M["m01"] / M["m00"])


        too_close = False
        for uc in used_centers:
            if abs(cx - uc[0]) < 30 and abs(cy - uc[1]) < 30:
                too_close = True
                break
        if too_close:
            continue


        perimeter = cv2.arcLength(contour, True)
        if perimeter == 0:
            continue

        approx = cv2.approxPolyDP(contour, 0.03 * perimeter, True)
        vertices = len(approx)

        circularity = 4 * np.pi * area / (perimeter * perimeter)

        if vertices == 3:
            shape_name = "triangle"
        elif vertices == 4:
            x, y, w, h = cv2.boundingRect(approx)
            ratio = w / float(h)
            shape_name = "square" if 0.85 <= ratio <= 1.15 else "rectangle"
        elif vertices == 5:
            shape_name = "pentagon"
        elif vertices == 6:
            shape_name = "hexagon"
        elif vertices > 6:
            if circularity > 0.88:
                shape_name = "circle"
            else:
                shape_name = f"polygon({vertices})"
        else:
            shape_name = "circle" if circularity > 0.75 else f"polygon({vertices})"


        mask = np.zeros(image.shape[:2], dtype=np.uint8)
        cv2.drawContours(mask, [contour], -1, 255, -1)
        color = get_dominant_color_in_mask(image, mask)

        shapes.append({
            "shape":   shape_name,
            "color":   color,
            "contour": contour,
            "center":  (cx, cy),
            "area":    area,
        })
        used_centers.append((cx, cy))


    shapes.sort(key=lambda s: s["area"], reverse=True)
    return shapes




def draw_shapes(image, shapes):
    result = image.copy()
    for s in shapes:
        cx, cy = s["center"]
        label = f"{s['color']} {s['shape']}"

        cv2.drawContours(result, [s["contour"]], -1, (0, 255, 0), 2)

        (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.65, 2)
        cv2.rectangle(result,
                      (cx - tw // 2 - 5, cy - th - 10),
                      (cx + tw // 2 + 5, cy + 6),
                      (0, 0, 0), -1)
        cv2.putText(result, label,
                    (cx - tw // 2, cy),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 255, 255), 2)
    return result



def change_shape_color(image, shapes, target_index, new_bgr_color):
    result = image.copy()
    contour = shapes[target_index]["contour"]

    mask = np.zeros(image.shape[:2], dtype=np.uint8)
    cv2.drawContours(mask, [contour], -1, 255, -1)
    result[mask == 255] = new_bgr_color

    return result