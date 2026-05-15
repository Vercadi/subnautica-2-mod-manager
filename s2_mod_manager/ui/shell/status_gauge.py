from __future__ import annotations

import math
import tkinter as tk

import customtkinter as ctk

from ..ui_tokens import UiTokens


class OxygenGauge(ctk.CTkFrame):
    def __init__(self, master, *, tokens: UiTokens, value: int = 98):
        super().__init__(master, fg_color="transparent")
        self.tokens = tokens
        self.value = max(0, min(100, int(value)))
        self.canvas = tk.Canvas(
            self,
            width=150,
            height=150,
            highlightthickness=0,
            bg=tokens.colors.glass_black,
            bd=0,
        )
        self.canvas.pack(expand=True)
        self._draw_gauge()

    def _draw_gauge(self) -> None:
        c = self.canvas
        c.delete("all")
        colors = self.tokens.colors
        size = 150
        cx = cy = size // 2
        c.create_oval(6, 6, size - 6, size - 6, outline=colors.shadow, width=5)
        c.create_oval(10, 10, size - 10, size - 10, outline=colors.shell_border_dim, width=2)
        c.create_oval(25, 25, size - 25, size - 25, outline=colors.border_soft, width=1)
        c.create_oval(42, 42, size - 42, size - 42, fill="#04131E", outline=colors.shell_border_dim, width=1)

        extent = int(300 * self.value / 100)
        ring_color = colors.accent_lagoon if self.value >= 80 else colors.warning if self.value >= 50 else colors.danger
        for start in range(110, 410, 24):
            c.create_arc(16, 16, size - 16, size - 16, start=start, extent=14, style="arc", outline="#0A2837", width=9)
        for start in range(110, 110 + extent, 24):
            segment = min(14, 110 + extent - start)
            if segment > 0:
                c.create_arc(16, 16, size - 16, size - 16, start=start, extent=segment, style="arc", outline=ring_color, width=9)

        for angle in range(110, 411, 30):
            rad = angle * math.pi / 180
            x1 = cx + 55 * math.cos(rad)
            y1 = cy - 55 * math.sin(rad)
            x2 = cx + 65 * math.cos(rad)
            y2 = cy - 65 * math.sin(rad)
            c.create_line(x1, y1, x2, y2, fill=colors.border_cold, width=1)

        c.create_text(cx, 45, text="O2", fill=colors.accent_lagoon, font=("Segoe UI", 17, "bold"))
        c.create_text(cx, 77, text=f"{self.value}%", fill=colors.text_primary, font=("Segoe UI", 28, "bold"))
        c.create_text(cx, 108, text="System Health", fill=colors.text_secondary, font=("Segoe UI", 10))
        c.create_line(cx - 24, 120, cx + 24, 120, fill=colors.shell_border_dim, width=1)
