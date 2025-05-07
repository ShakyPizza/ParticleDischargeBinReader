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
    qm_values = []
    for val in qm_matches[:3]:
        try:
            num = float(val)

            # Convert to pico (pF)
            num *= 1e12  # Convert from Farads to picoFarads
            final_value = str(round(num))  # Round and convert to string

            qm_values.append(final_value)
        except ValueError:
            qm_values.append("Err")

    return date_time, hw_gain, qm_values

# GUI Application class
class BinFileApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Bin File Data Extractor (V. 0.5)")
        self.resizable(False, False)
        self.geometry("400x600")
        self.configure(bg="indianred")

        # Upload Button
        self.upload_button = tk.Button(self, text="Upload .bin Files", command=self.upload_file)
        self.upload_button.pack(pady=10)

        # First Text Display Box (Full Info)
        self.info_box = tk.Text(self, width=40, height=20)
        self.info_box.pack(pady=5)

        # Copy Button for Full Info
        self.copy_button = tk.Button(self, text="Copy Data", command=self.copy_to_clipboard)
        self.copy_button.pack(pady=5)

        # Second Text Display Box (Qm values only)
        self.qm_box = tk.Text(self, width=40, height=5)
        self.qm_box.pack(pady=5)

        # Copy Button for Qm values only
        self.qm_copy_button = tk.Button(self, text="Copy Qm Values", command=self.copy_qm_to_clipboard)
        self.qm_copy_button.pack(pady=5)

    def upload_file(self):
        file_paths = filedialog.askopenfilenames(filetypes=[("BIN Files", "*.bin")])
        if not file_paths:
            return

        file_data = []  # List to store file info for sorting
        output_text = ""
        all_qm_values = []  # List to store all Qm values

        for file_path in file_paths:
            date_time, hw_gain, qm_values = extract_info_from_bin(file_path)

            # Convert Date/Time to a sortable format
            try:
                datetime_numeric = int("".join(re.findall(r'\d+', date_time)))  # Convert YYYY.MM.DD HH:MM:SS to int
            except ValueError:
                datetime_numeric = 0  # If parsing fails, push to bottom

            file_data.append((datetime_numeric, file_path, date_time, hw_gain, qm_values))

        # Sort files by Date/Time (newest first)
        file_data.sort(key=lambda x: x[0], reverse=True)

        for datetime_numeric, file_path, date_time, hw_gain, qm_values in file_data:
            output_text += f"File: {file_path.split('/')[-1]}\n"
            output_text += f"Date/Time: {date_time}\n"
            output_text += f"HW-Gain: {hw_gain}\n"

            for i, qm_value in enumerate(qm_values, start=1):
                output_text += f"Qm{i}: {qm_value}\n"
                all_qm_values.append(qm_value)  # Collect Qm values

            output_text += "\n"  # Empty line between different bin files
            all_qm_values.append("")  # Add a blank line in Qm box

        # Update Full Info Box
        self.info_box.delete("1.0", tk.END)
        self.info_box.insert(tk.END, output_text.strip())
        self.configure(bg="lawngreen")

        # Update Qm Values Box (newest Qm values first, with empty lines between files)
        self.qm_box.delete("1.0", tk.END)
        self.qm_box.insert(tk.END, "\n".join(all_qm_values).strip())


        # Update Full Info Box
        self.info_box.delete("1.0", tk.END)
        self.info_box.insert(tk.END, output_text.strip())

        # Update Qm Values Box (all Qm values from all files, each on a new line)
        self.qm_box.delete("1.0", tk.END)
        self.qm_box.insert(tk.END, "\n".join(all_qm_values))

      
    def copy_to_clipboard(self):
        text = self.info_box.get("1.0", tk.END)
        self.clipboard_clear()
        self.clipboard_append(text)
        self.update()

    def copy_qm_to_clipboard(self):
        text = self.qm_box.get("1.0", tk.END)
        self.clipboard_clear()
        self.clipboard_append(text)
        self.update()

# Run Application
if __name__ == "__main__":
    app = BinFileApp()
    app.mainloop()
