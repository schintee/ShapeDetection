import cv2
import numpy as np
from shape_detector import detect_shapes, draw_shapes, change_shape_color


COLORS = {
    "rosu":       (0,   0,   255),
    "verde":      (0,   200,  0),
    "albastru":   (255, 50,   0),
    "galben":     (0,   230, 230),
    "portocaliu": (0,   140, 255),
    "violet":     (180,  0,  180),
    "roz":        (147, 20,  255),
    "cyan":       (255, 255,  0),
    "alb":        (255, 255, 255),
    "negru":      (0,     0,   0),
    "gri":        (128, 128, 128),
}

COLOR_EN_TO_RO = {
    "red":      "rosu",
    "green":    "verde",
    "blue":     "albastru",
    "yellow":   "galben",
    "orange":   "portocaliu",
    "purple":   "violet",
    "pink":     "roz",
    "cyan":     "cyan",
    "white":    "alb",
    "black":    "negru",
    "gray":     "gri",
    "grey":     "gri",
    "unknown":  "necunoscuta",
}

SHAPE_EN_TO_RO = {
    "circle":    "cerc",
    "triangle":  "triunghi",
    "square":    "patrat",
    "rectangle": "dreptunghi",
    "pentagon":  "pentagon",
    "hexagon":   "hexagon",
}



def ro_color(en):
    return COLOR_EN_TO_RO.get(en, en)

def ro_shape(en):
    s = en.split("(")[0]
    return SHAPE_EN_TO_RO.get(s, en)

def article(shape_ro):
    masculine = {"cerc", "triunghi", "pentagon", "hexagon", "dreptunghi", "patrat"}
    return "ul" if shape_ro in masculine else "ul"

def describe_shapes(shapes):
    if not shapes:
        return "Nu am detectat nicio formă în imagine."
    parts = []
    for s in shapes:
        c = ro_color(s["color"])
        sh = ro_shape(s["shape"])
        parts.append(f"un {sh} {c}")
    if len(parts) == 1:
        return f"Am detectat {parts[0]}."
    return "Am detectat: " + ", ".join(parts[:-1]) + f" și {parts[-1]}."

def ask_color():
    print(f"\n  Culori disponibile: {', '.join(COLORS.keys())}")
    while True:
        c = input("  Ce culoare vrei? ").strip().lower()
        if c in COLORS:
            return c
        print(f" Culoarea '{c}' nu e disponibilă. Încearcă din lista de mai sus.")

def show(title, img):
    cv2.imshow(title, img)
    print("  [apasă orice tastă în fereastra imaginii pentru a continua]")
    cv2.waitKey(0)
    cv2.destroyWindow(title)



def create_test_image():
    img = np.ones((500, 700, 3), dtype=np.uint8) * 240

    cv2.circle(img, (100, 110), 70, (0, 0, 200), -1)
    cv2.rectangle(img, (220, 50), (380, 160), (200, 50, 0), -1)
    pts = np.array([[500, 40], [420, 160], [580, 160]], np.int32)
    cv2.fillPoly(img, [pts], (0, 180, 0))
    cv2.rectangle(img, (50, 300), (170, 420), (0, 220, 220), -1)

    angles5 = np.linspace(-np.pi/2, 3*np.pi/2, 6)[:-1]
    pent = np.array([[int(300+80*np.cos(a)), int(360+80*np.sin(a))] for a in angles5], np.int32)
    cv2.fillPoly(img, [pent], (0, 140, 255))

    angles6 = np.linspace(0, 2*np.pi, 7)[:-1]
    hexag = np.array([[int(530+75*np.cos(a)), int(360+75*np.sin(a))] for a in angles6], np.int32)
    cv2.fillPoly(img, [hexag], (180, 0, 180))

    return img




def process_image(image):

    shapes = detect_shapes(image)


    print(f"\n   {describe_shapes(shapes)}")

    if not shapes:
        show("Imagine", image)
        return


    labeled = draw_shapes(image, shapes)
    show("Forme detectate", labeled)


    current_image = image.copy()

    while True:
        if len(shapes) == 1:
            s = shapes[0]
            print(f"\n  Vrei să schimb culoarea {ro_shape(s['shape'])}-ului {ro_color(s['color'])}? (da/nu)")
            ans = input("  > ").strip().lower()
            if ans != "da":
                break
            target = 0
        else:
            print("\n  Vrei să schimbi culoarea unei forme? (da/nu)")
            ans = input("  > ").strip().lower()
            if ans != "da":
                break

            print("\n  Care formă vrei să o schimbi?")
            for i, s in enumerate(shapes):
                print(f"    [{i}] {ro_shape(s['shape'])} {ro_color(s['color'])}")
            while True:
                try:
                    target = int(input("  Numărul formei: ").strip())
                    if 0 <= target < len(shapes):
                        break
                    print(f" Introdu un număr între 0 și {len(shapes)-1}.")
                except ValueError:
                    print("  Te rog introdu un număr.")


        new_color_ro = ask_color()
        new_bgr = COLORS[new_color_ro]


        current_image = change_shape_color(current_image, shapes, target, new_bgr)


        shapes = detect_shapes(current_image)
        labeled = draw_shapes(current_image, shapes)
        show("Rezultat", labeled)


        filename = "rezultat.png"
        cv2.imwrite(filename, labeled)
        print(f"  Imaginea a fost salvată ca '{filename}'")

        print("\n Vrei să mai schimbi o altă formă? (da/nu)")
        if input("  > ").strip().lower() != "da":
            break



def main():
    print("SHAPE DETECTOR")

    while True:
        print("""
    1. Generează imagine de test   
    2. Încarcă o imagine proprie   
    3. Generează o formă singură   
    0. Ieși                        """)

        choice = input("\n  Alegere: ").strip()


        if choice == "1":
            print("\n  Se generează imaginea de test...")
            image = create_test_image()
            process_image(image)


        elif choice == "2":
            path = input("\n  Calea imaginii (ex: C:/poze/test.jpg): ").strip().strip('"')
            image = cv2.imread(path)
            if image is None:
                print("  Nu am putut deschide imaginea. Verifică calea.")
            else:
                process_image(image)


        elif choice == "3":
            print("""
  Ce formă vrei să generez?
    1. Cerc
    2. Triunghi
    3. Pătrat
    4. Dreptunghi
    5. Pentagon
    6. Hexagon""")
            shape_choice = input("  Alegere: ").strip()

            print(f"\n  Ce culoare? ({', '.join(COLORS.keys())})")
            color_ro = ask_color()
            bgr = COLORS[color_ro]

            img = np.ones((400, 400, 3), dtype=np.uint8) * 240
            cx, cy = 200, 200

            if shape_choice == "1":
                cv2.circle(img, (cx, cy), 120, bgr, -1)
                desc = f"cerc {color_ro}"
            elif shape_choice == "2":
                pts = np.array([[cx, cy-130], [cx-115, cy+100], [cx+115, cy+100]], np.int32)
                cv2.fillPoly(img, [pts], bgr)
                desc = f"triunghi {color_ro}"
            elif shape_choice == "3":
                cv2.rectangle(img, (cx-110, cy-110), (cx+110, cy+110), bgr, -1)
                desc = f"pătrat {color_ro}"
            elif shape_choice == "4":
                cv2.rectangle(img, (cx-150, cy-90), (cx+150, cy+90), bgr, -1)
                desc = f"dreptunghi {color_ro}"
            elif shape_choice == "5":
                a = np.linspace(-np.pi/2, 3*np.pi/2, 6)[:-1]
                pts = np.array([[int(cx+120*np.cos(x)), int(cy+120*np.sin(x))] for x in a], np.int32)
                cv2.fillPoly(img, [pts], bgr)
                desc = f"pentagon {color_ro}"
            elif shape_choice == "6":
                a = np.linspace(0, 2*np.pi, 7)[:-1]
                pts = np.array([[int(cx+120*np.cos(x)), int(cy+120*np.sin(x))] for x in a], np.int32)
                cv2.fillPoly(img, [pts], bgr)
                desc = f"hexagon {color_ro}"
            else:
                print("   Opțiune invalidă.")
                continue

            print(f"\n  Am generat un {desc}.")
            process_image(img)

        # ── Ieșire ────────────────────────────────────
        elif choice == "0":
            print("\n  Pa! \n")
            break

        else:
            print("  Opțiune invalidă. Încearcă din nou.")

    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()