import ctypes
from ctypes import wintypes
import struct
import os

user32 = ctypes.windll.user32
gdi32 = ctypes.windll.gdi32

def capture_screen(output_path: str):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Attach thread to interactive user desktop
    h_default = user32.OpenDesktopW('default', 0, False, 0x01FF)
    if h_default:
        user32.SetThreadDesktop(h_default)
    
    width = user32.GetSystemMetrics(0)
    height = user32.GetSystemMetrics(1)
    
    hdesktop = user32.GetDesktopWindow()
    hdc_screen = user32.GetDC(hdesktop)
    hdc_mem = gdi32.CreateCompatibleDC(hdc_screen)
    
    hbitmap = gdi32.CreateCompatibleBitmap(hdc_screen, width, height)
    h_old = gdi32.SelectObject(hdc_mem, hbitmap)
    
    SRCCOPY = 0x00CC0020
    success = gdi32.BitBlt(hdc_mem, 0, 0, width, height, hdc_screen, 0, 0, SRCCOPY)
    if not success:
        err = ctypes.GetLastError()
        user32.ReleaseDC(hdesktop, hdc_screen)
        gdi32.DeleteDC(hdc_mem)
        gdi32.DeleteObject(hbitmap)
        raise RuntimeError(f"BitBlt failed with error code: {err}")
        
    class BITMAPINFOHEADER(ctypes.Structure):
        _fields_ = [
            ('biSize', wintypes.DWORD),
            ('biWidth', wintypes.LONG),
            ('biHeight', wintypes.LONG),
            ('biPlanes', wintypes.WORD),
            ('biBitCount', wintypes.WORD),
            ('biCompression', wintypes.DWORD),
            ('biSizeImage', wintypes.DWORD),
            ('biXPelsPerMeter', wintypes.LONG),
            ('biYPelsPerMeter', wintypes.LONG),
            ('biClrUsed', wintypes.DWORD),
            ('biClrImportant', wintypes.DWORD)
        ]
        
    bmi = BITMAPINFOHEADER()
    bmi.biSize = ctypes.sizeof(BITMAPINFOHEADER)
    bmi.biWidth = width
    bmi.biHeight = height
    bmi.biPlanes = 1
    bmi.biBitCount = 24
    bmi.biCompression = 0 # BI_RGB
    
    row_bytes = (width * 3 + 3) & ~3
    image_size = row_bytes * height
    bmi.biSizeImage = image_size
    
    buf = (ctypes.c_char * image_size)()
    DIB_RGB_COLORS = 0
    lines = gdi32.GetDIBits(hdc_mem, hbitmap, 0, height, ctypes.byref(buf), ctypes.byref(bmi), DIB_RGB_COLORS)
    
    # Clean up GDI objects
    gdi32.SelectObject(hdc_mem, h_old)
    gdi32.DeleteObject(hbitmap)
    gdi32.DeleteDC(hdc_mem)
    user32.ReleaseDC(hdesktop, hdc_screen)
    if h_default:
        user32.CloseDesktop(h_default)
    
    if lines != height:
        raise RuntimeError(f"GetDIBits failed: returned {lines} of {height}")
        
    # Write standard BMP
    bfType = b'BM'
    bfOffBits = 14 + ctypes.sizeof(BITMAPINFOHEADER)
    bfSize = bfOffBits + image_size
    header = struct.pack('<2sIHHI', bfType, bfSize, 0, 0, bfOffBits)
    
    with open(output_path, 'wb') as f:
        f.write(header)
        f.write(bytes(bmi))
        f.write(bytes(buf))
        
    return output_path

if __name__ == "__main__":
    out = os.path.join(r"E:\okal llm benschmark\data\screenshots", "screen_test.bmp")
    capture_screen(out)
    print(f"Captured: {out} ({os.path.getsize(out)} bytes)")
