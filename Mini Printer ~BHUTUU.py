import socket
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageDraw, ImageFont, ImageChops, ImageOps, ImageTk
import struct
from time import sleep

# Bluetooth printer configuration
printerMACAddress = 'EB:37:29:F6:7E:D0'
printerWidth = 384
port = 2

def connect_to_printer():
    s = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)
    s.connect((printerMACAddress, port))
    return s

def initilize_printer(soc):
    soc.send(b"\x1b\x40")

def send_start_print_sequence(soc):
    soc.send(b"\x1d\x49\xf0\x19")

def send_end_print_sequence(soc):
    soc.send(b"\x0a\x0a\x0a\x0a")

def print_image(soc, im):
    if im.width > printerWidth:
        height = int(im.height * (printerWidth / im.width))
        im = im.resize((printerWidth, height))
        
    if im.width < printerWidth:
        padded_image = Image.new("1", (printerWidth, im.height), 1)
        padded_image.paste(im)
        im = padded_image
        
    im = im.rotate(180)
    
    if im.mode != '1':
        im = im.convert('1')
        
    if im.size[0] % 8:
        im2 = Image.new('1', (im.size[0] + 8 - im.size[0] % 8, im.size[1]), 'white')
        im2.paste(im, (0, 0))
        im = im2
        
    im = ImageOps.invert(im.convert('L'))
    im = im.convert('1')

    buf = b''.join((bytearray(b'\x1d\x76\x30\x00'), 
                    struct.pack('2B', int(im.size[0] / 8 % 256), int(im.size[0] / 8 / 256)), 
                    struct.pack('2B', int(im.size[1] % 256), int(im.size[1] / 256)), 
                    im.tobytes()))
    initilize_printer(soc)  
    sleep(0.5)    
    send_start_print_sequence(soc)
    sleep(0.5)
    soc.send(buf)
    sleep(0.5)
    send_end_print_sequence(soc)
    sleep(0.5)


def trimImage(im):
    bg = Image.new(im.mode, im.size, (255,255,255))
    diff = ImageChops.difference(im, bg)
    diff = ImageChops.add(diff, diff, 2.0)
    bbox = diff.getbbox()
    if bbox:
        return im.crop((bbox[0],bbox[1],bbox[2],bbox[3]+10))
def print_text(socket_conn, text, font_name="arial.ttf", font_size=12):
    img = Image.new('RGB', (printerWidth, 5000), color = (255, 255, 255))
    font = ImageFont.truetype(font_name, font_size)
    
    d = ImageDraw.Draw(img)
    lines = []
    for line in text.splitlines():
        lines.append(get_wrapped_text(line, font, printerWidth))
    lines = "\n".join(lines)
    d.text((0,0), lines, fill=(0,0,0), font=font)
    imgFromText = trimImage(img)
    print_image(socket_conn, imgFromText)


def get_wrapped_text(text: str, font: ImageFont.ImageFont, line_length: int):
    lines = ['']
    for word in text.split():
        line = f'{lines[-1]} {word}'.strip()
        if font.getlength(line) <= line_length:
            lines[-1] = line
        else:
            lines.append(word)
    return '\n'.join(lines)

def select_image():
    file_path = filedialog.askopenfilename(title="Select Image", filetypes=(("Image files", "*.jpg;*.jpeg;*.png"), ("All files", "*.*")))
    if file_path:
        image = Image.open(file_path)
        print_image(socket_conn, image)

def print_text_window():
    def print_text_from_entry():
        entered_text = text_entry.get("1.0", tk.END)
        font_name = font_var.get()
        font_size = int(font_size_var.get())
        print_text(socket_conn, entered_text, font_name, font_size)
        top_level.destroy()

    top_level = tk.Toplevel(root)
    top_level.title("Print Text")
    
    text_entry = tk.Text(top_level, width=30, height=15)
    text_entry.pack(pady=10)
    
    font_label = tk.Label(top_level, text="Font:")
    font_label.pack()
    
    font_var = tk.StringVar(top_level)
    font_var.set("arial.ttf")
    font_dropdown = tk.OptionMenu(top_level, font_var, "arial.ttf", "times.ttf", "LCALLIG.TTF", "HARLOWSI.TTF")
    font_dropdown.pack(pady=5)
    
    font_size_label = tk.Label(top_level, text="Font Size:")
    font_size_label.pack()
    
    font_size_var = tk.StringVar(top_level)
    font_size_var.set("30")
    font_size_entry = tk.Entry(top_level, textvariable=font_size_var)
    font_size_entry.pack(pady=5)
    
    print_button = tk.Button(top_level, text="Print", command=print_text_from_entry)
    print_button.pack(pady=10)

def print_option_selected(option):
    if option == "Image":
        select_image()
    elif option == "Text":
        print_text_window()
    else:
        messagebox.showerror("Error", "Invalid option selected!")
emoji_text = "👻"
image = Image.new("RGB", (100, 100), "white")
draw = ImageDraw.Draw(image)
font = ImageFont.truetype("seguiemj.ttf", 50)
draw.text((17, 27), emoji_text, fill="black", font=font)
root = tk.Tk()
root.title("Mini Printer ~BHUTUU")
root.geometry("350x200")
root.maxsize(width=350, height=200)
iconImage = ImageTk.PhotoImage(image)
root.iconphoto(True, iconImage)
try:
    socket_conn = connect_to_printer()
except:
    messagebox.showerror("Error", "Could not connect to printer!")
    root.destroy()
    exit(1)

option_label = tk.Label(root, text="Select Print Option:")
option_label.pack(pady=10)

print_image_button = tk.Button(root, text="Print Image", command=lambda: print_option_selected("Image"))
print_image_button.pack()

print_text_button = tk.Button(root, text="Print Text", command=lambda: print_option_selected("Text"))
print_text_button.pack()

root.mainloop()
