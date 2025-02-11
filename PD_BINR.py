import tkinter as tk
from tkinter import filedialog
import re

# Function to extract data from .bin file
def extract_info_from_bin(filepath):
    with open(filepath, "rb") as file:
        bin_data = file.read().decode(errors="ignore")

    # Extract Date/Time
    time_stamp_match = re.search(r'<Time_Stamp>([\d\-T:,\.\+]+)</Time_Stamp>', bin_data, re.IGNORECASE)
    if time_stamp_match:
        raw_timestamp = time_stamp_match.group(1)
        date_time = raw_timestamp[:10].replace("-", ".") + " " + raw_timestamp[11:19]  # Format YYYY-MM-DD HH:MM:SS
    else:
        date_time = "Unknown"

    # Extract HW-Gain
    hw_gain_match = re.search(r'<HWGain>([\d,\.]+)</HWGain>', bin_data, re.IGNORECASE)
    hw_gain = hw_gain_match.group(1) if hw_gain_match else "Unknown"


    # Extract Qm values
    qm_matches = re.findall(r'<Qm[^>]*>([\d.eE\-]+)</Qm>', bin_data, re.IGNORECASE)
    print("Extracted Qm values before conversion:", qm_matches)
    qm_values = []
    for val in qm_matches[:3]:
        try:
            num = float(val)
            print(f"Converted {val} to float:", num)  # Debug print

            # Convert to pico (p)
            num *= 1e12  # Convert from Farads to picoFarads

            # Format display value
            if num >= 1000:
                final_value = f"{int(num)}"  # Convert to integer if large
            else:
                final_value = f"{num:.0f}".rstrip("0").rstrip(".")  # Keep precision, strip trailing zeros

            qm_values.append(final_value)
        except ValueError:
            print("Failed to convert:", val)
            qm_values.append("Err")


    print(qm_values)
    return date_time, hw_gain, qm_values

# GUI Application class
class BinFileApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Bin File Data Extractor")

        # Upload Button
        self.upload_button = tk.Button(self, text="Upload .bin Files", command=self.upload_file)
        self.upload_button.pack(pady=10)
        
        # Text Display Box
        self.info_box = tk.Text(self, width=40, height=40)
        self.info_box.pack(pady=5)
        
        # Copy Button
        self.copy_button = tk.Button(self, text="Copy Data", command=self.copy_to_clipboard)
        self.copy_button.pack(pady=5)
    
    def upload_file(self):
        file_paths = filedialog.askopenfilenames(filetypes=[("BIN Files", "*.bin")])
        if not file_paths:
            return
        
        output_text = ""
        for file_path in file_paths:
            date_time, hw_gain, qm_values = extract_info_from_bin(file_path)
            output_text += f"Date/Time: {date_time}\n"
            output_text += f"HW-Gain: {hw_gain}\n"
            # Display Qm values as separated
            if len(qm_values) >= 3:
                output_text += f"Qm1: {qm_values[0]}\n"
                output_text += f"Qm2: {qm_values[1]}\n"
                output_text += f"Qm3: {qm_values[2]}\n\n"
            else:
                output_text += f"Qm1: {qm_values[0] if len(qm_values)>0 else 'N/A'}\n"
                output_text += f"Qm2: {qm_values[1] if len(qm_values)>1 else 'N/A'}\n"
                output_text += f"Qm3: {qm_values[2] if len(qm_values)>2 else 'N/A'}\n\n"
        
        self.info_box.delete("1.0", tk.END)
        self.info_box.insert(tk.END, output_text.strip())
        
        self.info_box.delete("1.0", tk.END)
        self.info_box.insert(tk.END, output_text.strip())
    
    def copy_to_clipboard(self):
        text = self.info_box.get("1.0", tk.END)
        self.clipboard_clear()
        self.clipboard_append(text)
        self.update()

# Run Application
if __name__ == "__main__":
    app = BinFileApp()
    app.mainloop()
