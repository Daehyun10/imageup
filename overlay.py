"""화면 위에 이미지를 띄워두는 오버레이 프로그램 (Windows)."""

import ctypes
import os
import sys
import tkinter as tk
from tkinter import filedialog, messagebox

from PIL import Image, ImageGrab, ImageTk

GWL_EXSTYLE = -20
WS_EX_LAYERED = 0x00080000
WS_EX_TRANSPARENT = 0x00000020
WS_EX_TOOLWINDOW = 0x00000080

IS_WINDOWS = sys.platform.startswith("win")

MIN_SIZE = 40
HANDLE = 16


def _hwnd_of(window):
    """Tk 창의 실제 최상위 HWND를 구한다."""
    window.update_idletasks()
    hwnd = window.winfo_id()
    parent = ctypes.windll.user32.GetParent(hwnd)
    return parent if parent else hwnd


def _set_ex_style(window, flag, enabled):
    if not IS_WINDOWS:
        return
    user32 = ctypes.windll.user32
    hwnd = _hwnd_of(window)
    style = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
    style = (style | flag) if enabled else (style & ~flag)
    user32.SetWindowLongW(hwnd, GWL_EXSTYLE, style)


class Overlay(tk.Toplevel):
    """이미지 한 장을 담는 테두리 없는 창."""

    def __init__(self, master, image, on_close):
        super().__init__(master)
        self.source = image.convert("RGBA")
        self.on_close = on_close
        self.photo = None
        self.click_through = False

        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.attributes("-alpha", 0.8)
        self.configure(bg="#101010")

        self.canvas = tk.Canvas(self, highlightthickness=0, bd=0, bg="#101010")
        self.canvas.pack(fill="both", expand=True)

        self.item = self.canvas.create_image(0, 0, anchor="nw")
        self.close_btn = tk.Button(
            self,
            text="X",
            command=self.close,
            bg="#202020",
            fg="white",
            bd=0,
            padx=6,
            pady=0,
            activebackground="#c0392b",
            activeforeground="white",
            font=("Segoe UI", 9, "bold"),
        )
        self.close_btn.place(relx=1.0, x=-2, y=2, anchor="ne")

        w, h = self.source.size
        scale = min(1.0, 600 / max(w, h))
        self.set_size(int(w * scale), int(h * scale))
        self.geometry("+120+120")

        self.canvas.bind("<ButtonPress-1>", self._press)
        self.canvas.bind("<B1-Motion>", self._drag)
        self.canvas.bind("<MouseWheel>", self._wheel)
        self.bind("<MouseWheel>", self._wheel)

        if IS_WINDOWS:
            _set_ex_style(self, WS_EX_TOOLWINDOW, True)

    # --- 크기 / 투명도 ---------------------------------------------------

    def set_size(self, w, h):
        w = max(MIN_SIZE, int(w))
        h = max(MIN_SIZE, int(h))
        resized = self.source.resize((w, h), Image.LANCZOS)
        self.photo = ImageTk.PhotoImage(resized)
        self.canvas.itemconfigure(self.item, image=self.photo)
        self.canvas.configure(width=w, height=h)
        self.geometry(f"{w}x{h}")

    def scale_to(self, percent):
        w, h = self.source.size
        self.set_size(w * percent / 100, h * percent / 100)

    def set_alpha(self, value):
        self.attributes("-alpha", max(0.05, min(1.0, value)))

    def current_percent(self):
        return self.winfo_width() / self.source.size[0] * 100

    # --- 클릭 통과 -------------------------------------------------------

    def set_click_through(self, enabled):
        self.click_through = enabled
        if enabled:
            self.close_btn.place_forget()
        else:
            self.close_btn.place(relx=1.0, x=-2, y=2, anchor="ne")
        _set_ex_style(self, WS_EX_LAYERED | WS_EX_TRANSPARENT, enabled)
        self.attributes("-topmost", True)

    # --- 마우스 조작 -----------------------------------------------------

    def _press(self, event):
        w, h = self.winfo_width(), self.winfo_height()
        self._mode = "resize" if (event.x > w - HANDLE and event.y > h - HANDLE) else "move"
        self._origin = (event.x_root, event.y_root)
        self._start = (self.winfo_x(), self.winfo_y(), w, h)

    def _drag(self, event):
        dx = event.x_root - self._origin[0]
        dy = event.y_root - self._origin[1]
        x, y, w, h = self._start
        if self._mode == "move":
            self.geometry(f"+{x + dx}+{y + dy}")
        else:
            ratio = h / w if w else 1
            new_w = max(MIN_SIZE, w + dx)
            self.set_size(new_w, new_w * ratio)
            self.geometry(f"+{x}+{y}")
        self.event_generate("<<OverlayChanged>>")

    def _wheel(self, event):
        step = 1.1 if event.delta > 0 else 1 / 1.1
        self.set_size(self.winfo_width() * step, self.winfo_height() * step)
        self.event_generate("<<OverlayChanged>>")

    def close(self):
        self.on_close(self)
        self.destroy()


class ControlPanel(tk.Tk):
    """이미지를 불러오고 오버레이를 제어하는 작은 창."""

    def __init__(self):
        super().__init__()
        self.title("Image Overlay")
        self.geometry("320x260")
        self.attributes("-topmost", True)
        self.resizable(False, False)

        self.overlays = []
        self._syncing = False
        self.click_through = tk.BooleanVar(value=False)

        pad = {"padx": 10, "pady": 4}

        row = tk.Frame(self)
        row.pack(fill="x", **pad)
        tk.Button(row, text="파일 열기", command=self.open_file).pack(side="left", expand=True, fill="x")
        tk.Button(row, text="붙여넣기", command=self.paste).pack(side="left", expand=True, fill="x")

        tk.Label(self, text="투명도").pack(anchor="w", padx=10)
        self.alpha = tk.Scale(
            self, from_=5, to=100, orient="horizontal", command=self._alpha_changed
        )
        self.alpha.set(80)
        self.alpha.pack(fill="x", padx=10)

        tk.Label(self, text="크기 (%)").pack(anchor="w", padx=10)
        self.scale = tk.Scale(
            self, from_=5, to=400, orient="horizontal", command=self._scale_changed
        )
        self.scale.set(100)
        self.scale.pack(fill="x", padx=10)

        tk.Checkbutton(
            self,
            text="클릭 통과 (이미지 위에서 그대로 작업)",
            variable=self.click_through,
            command=self._toggle_click_through,
        ).pack(anchor="w", padx=10, pady=(6, 0))

        tk.Button(self, text="모두 닫기", command=self.close_all).pack(fill="x", **pad)

        self.status = tk.Label(self, text="이미지 없음", anchor="w", fg="#555")
        self.status.pack(fill="x", padx=10)

        self.bind_all("<Control-v>", lambda _e: self.paste())
        self.protocol("WM_DELETE_WINDOW", self.quit_all)

        if not IS_WINDOWS:
            self.status.configure(
                text="클릭 통과는 Windows에서만 동작합니다", fg="#b04000"
            )

    # --- 이미지 추가 -----------------------------------------------------

    def open_file(self):
        path = filedialog.askopenfilename(
            title="이미지 선택",
            filetypes=[
                ("이미지", "*.png *.jpg *.jpeg *.gif *.bmp *.webp"),
                ("모든 파일", "*.*"),
            ],
        )
        if not path:
            return
        try:
            image = Image.open(path)
            image.load()
        except Exception as exc:
            messagebox.showerror("열기 실패", str(exc))
            return
        self.add_overlay(image, os.path.basename(path))

    def paste(self):
        data = ImageGrab.grabclipboard()
        if isinstance(data, list):
            paths = [p for p in data if os.path.isfile(p)]
            if not paths:
                self.status.configure(text="클립보드에 이미지가 없음")
                return
            try:
                data = Image.open(paths[0])
                data.load()
            except Exception as exc:
                messagebox.showerror("붙여넣기 실패", str(exc))
                return
        if not isinstance(data, Image.Image):
            self.status.configure(text="클립보드에 이미지가 없음")
            return
        self.add_overlay(data, "클립보드 이미지")

    def add_overlay(self, image, label):
        overlay = Overlay(self, image, self.forget_overlay)
        overlay.set_alpha(self.alpha.get() / 100)
        overlay.set_click_through(self.click_through.get())
        overlay.bind("<<OverlayChanged>>", self._sync_scale)
        self.overlays.append(overlay)
        self._syncing = True
        self.scale.set(int(overlay.current_percent()))
        self._syncing = False
        self.status.configure(text=f"{label} ({len(self.overlays)}장)")

    def forget_overlay(self, overlay):
        if overlay in self.overlays:
            self.overlays.remove(overlay)
        self.status.configure(
            text=f"{len(self.overlays)}장" if self.overlays else "이미지 없음"
        )

    # --- 제어 ------------------------------------------------------------

    def _alpha_changed(self, value):
        for overlay in self.overlays:
            overlay.set_alpha(int(value) / 100)

    def _scale_changed(self, value):
        if self._syncing:
            return
        for overlay in self.overlays:
            overlay.scale_to(int(value))

    def _sync_scale(self, event):
        self._syncing = True
        self.scale.set(int(event.widget.current_percent()))
        self._syncing = False

    def _toggle_click_through(self):
        enabled = self.click_through.get()
        for overlay in self.overlays:
            overlay.set_click_through(enabled)

    def close_all(self):
        for overlay in list(self.overlays):
            overlay.close()

    def quit_all(self):
        self.close_all()
        self.destroy()


if __name__ == "__main__":
    ControlPanel().mainloop()
