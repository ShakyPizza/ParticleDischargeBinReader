import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageTk
import pytesseract
import re
import cv2
import numpy as np

pytesseract.pytesseract.tesseract_cmd = r"C:\\Users\\benediktop\\AppData\\Local\\Programs\\Tesseract-OCR\\tesseract.exe"

def preprocess_image(pil_img):
    open_cv_image = np.array(pil_img.convert("L"))  # Convert to grayscale
    _, thresh_img = cv2.threshold(open_cv_image, 150, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return Image.fromarray(thresh_img)

def parse_qm_value(text):
    """
    Convert strings like '1,01n' => 1010, '994p' => 994, ignoring the 'p'.
    """
    text = text.strip().lower().replace(',', '.')
    if 'n' in text:
        # e.g. '1.01n' => 1.01 nC => 1.01 * 1000 pC => 1010
        val = float(text.replace('n', '')) * 1000
        return str(int(round(val)))
    if 'p' in text:
        val = float(text.replace('p', ''))
        return str(int(round(val)))
    return text  # fallback

def extract_info_from_bin(filepath):
    """Optimized function to extract Date and Qm values from .bin files efficiently."""
    with open(filepath, "rb") as file:
        full_text = ""
        for line in file:
            try:
                line_text = line.decode(errors="ignore")
            except UnicodeDecodeError:
                continue  # Skip unreadable binary chunks

            if "<Qm" in line_text or "<Time" in line_text or "<Date" in line_text:
                            full_text += line_text
        full_text = file.read().decode(errors="ignore")
    dt_match = re.search(r'(\d{1,2}:\d{2}\s+\d{1,2}\.\d{1,2}\.\d{4})', full_text)
    date_time = dt_match.group(1) if dt_match else "Unknown"
    qm_matches = re.findall(r'<Qm[^>]*>([\d,\.]+)', full_text, re.IGNORECASE)
    qm_values = []
    for val in qm_matches[:3]:
        num = float(val)
        if num < 2:  # If the value is suspiciously low, assume it's in nC and convert to pC
            num *= 1000
        qm_values.append(str(int(num)))
    return date_time, qm_values

def extract_info_from_png(filepath):
    img = Image.open(filepath)
    date_crop = img.crop((20, 18, 120, 35))  
    raw_text_date = pytesseract.image_to_string(date_crop, config="--psm 6")
    dt_match = re.search(r'(\d{1,2}:\d{2}\s+\d{1,2}\.\d{1,2}\.\d{4})', raw_text_date)
    date_time = dt_match.group(1) if dt_match else "Unknown"
    qm1_crop = img.crop((84, 860, 104, 879))
    qm1_crop.show()
    qm2_crop = img.crop((152, 860, 173, 879))
    qm2_crop.show() 
    qm3_crop = img.crop((218, 860, 242, 879))
    qm3_crop.show()
    qm_texts = [pytesseract.image_to_string(crop, config="--psm 7") for crop in [qm1_crop, qm2_crop, qm3_crop]]
    qm_values = [parse_qm_value(val) for val in qm_texts]
    print(f"Raw OCR Output: {qm_texts}")
    qm_values = []
    for val in qm_texts:
        val = val.strip()
        try:
            num = float(val)  # Try converting to float
            qm_values.append(str(int(num)))  # Store as integer string
        except ValueError:
            qm_values.append("Err")  # If conversion fails, mark as Err

    return date_time, qm_values

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("PD Popparinn")
        self.debug_mode = tk.BooleanVar(value=False)
        self.show_date_time = tk.BooleanVar(value=False)
        top_row = tk.Frame(self)
        top_row.pack(fill=tk.X)
        self.upload_button = tk.Button(top_row, text="Hlaða upp Skrám", command=self.upload_files)
        self.upload_button.pack(side=tk.LEFT, padx=10, pady=10)
        self.debug_check = tk.Checkbutton(top_row, text="Debug", variable=self.debug_mode)
        self.debug_check.pack(side=tk.LEFT, padx=5)
        self.date_time_check = tk.Checkbutton(top_row, text="Show Date/Time", variable=self.show_date_time)
        self.date_time_check.pack(side=tk.LEFT, padx=5)
        self.info_box = tk.Text(self, width=100, height=7)
        self.info_box.pack(pady=5)
        self.compare_button = tk.Button(self, text="Samanburður", command=self.compare_two)
        self.compare_button.pack(pady=5)
        self.canvas_left = tk.Label(self)
        self.canvas_left.pack(side=tk.LEFT, padx=5)
        self.canvas_right = tk.Label(self)
        self.canvas_right.pack(side=tk.LEFT, padx=5)
        self.image_refs = []

    def upload_files(self):
        files = filedialog.askopenfilenames(filetypes=[("PNG/BIN Files", "*.png;*.bin")])
        for f in files:
            if f.endswith(".png"):
                date_time, qm_values = extract_info_from_png(f)
            elif f.endswith(".bin"):
                date_time, qm_values = extract_info_from_bin(f)
            else:
                continue
            entry = f"{date_time} | {', '.join(qm_values)}\n" if self.show_date_time.get() else f"{', '.join(qm_values)}\n"
            self.info_box.insert(tk.END, entry)
            
    def compare_two(self):
        files = filedialog.askopenfilenames(filetypes=[("PNG Files","*.png")])
        if len(files) != 2:
            return
        img_left = Image.open(files[0]).resize((796, 800))
        img_right = Image.open(files[1]).resize((796, 800))
        photo_left = ImageTk.PhotoImage(img_left)
        photo_right = ImageTk.PhotoImage(img_right)
        self.canvas_left.config(image=photo_left)
        self.canvas_right.config(image=photo_right)
        self.image_refs = [photo_left, photo_right]
        dt1, qm1 = extract_info_from_png(files[0])
        dt2, qm2 = extract_info_from_png(files[1])
        comparison_str = ""
        if self.show_date_time.get():
            comparison_str += f"Skjal 1: {dt1} | {', '.join(qm1)}\n"
            comparison_str += f"Skjal 2: {dt2} | {', '.join(qm2)}\n"
        else:
            comparison_str += f"{', '.join(qm1)}\n"
            comparison_str += f"{', '.join(qm2)}\n"
        self.info_box.insert(tk.END, comparison_str)

if __name__ == "__main__":
    app = App()
    app.mainloop()
