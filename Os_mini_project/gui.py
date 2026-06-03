"""
==============================================================================
  Virtual Memory Management Simulator — GUI
  File   : gui.py
  Author : (your name)
  Desc   : Advanced CustomTkinter dark-themed GUI that wraps the existing
           FIFO / LRU / Optimal back-end algorithms with animated step-by-
           step simulation, Matplotlib charts, Belady's Anomaly test and
           CSV export.
==============================================================================
"""
 
# ─────────────────────────────────────────────────────────────────────────────
# Standard library
# ─────────────────────────────────────────────────────────────────────────────
import csv
import os
import time
import threading
from collections import OrderedDict
 
# ─────────────────────────────────────────────────────────────────────────────
# Third-party
# ─────────────────────────────────────────────────────────────────────────────
import customtkinter as ctk
from tkinter import messagebox, filedialog
import matplotlib
matplotlib.use("TkAgg")                          # must come before pyplot import
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.ticker as mticker
import pandas as pd
 
# ─────────────────────────────────────────────────────────────────────────────
# Local back-end (your existing algorithm modules)
# ─────────────────────────────────────────────────────────────────────────────
try:
    from fifo     import fifo
    from lru      import lru
    from optimal  import optimal
    BACKEND_LOADED = True
except ImportError:
    BACKEND_LOADED = False
    print("[WARN] Could not import algorithm modules – "
          "built-in fallback implementations will be used.")
 
# ─────────────────────────────────────────────────────────────────────────────
# Global appearance
# ─────────────────────────────────────────────────────────────────────────────
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")
 
# ── Colour palette ────────────────────────────────────────────────────────────
C_BG        = "#0d0f14"   # deepest background
C_SIDEBAR   = "#13151d"   # sidebar panel
C_CARD      = "#1a1d28"   # card / panel background
C_CARD2     = "#1f2235"   # slightly lighter card
C_BORDER    = "#2a2d3e"   # subtle border
C_ACCENT    = "#4f8ef7"   # primary accent (blue)
C_ACCENT2   = "#7c5cbf"   # secondary accent (violet)
C_HIT       = "#2ecc71"   # green  → page hit
C_FAULT     = "#e74c3c"   # red    → page fault
C_TEXT      = "#e8eaf0"   # primary text
C_MUTED     = "#6b7080"   # muted / label text
C_HIGHLIGHT = "#f0c040"   # yellow highlight (Belady)
 
# ── Typography ────────────────────────────────────────────────────────────────
FONT_TITLE   = ("Courier New", 22, "bold")
FONT_SECTION = ("Courier New", 14, "bold")
FONT_LABEL   = ("Consolas",    11)
FONT_MONO    = ("Consolas",    10)
FONT_SMALL   = ("Consolas",     9)
FONT_CARD    = ("Courier New", 26, "bold")
FONT_BTN     = ("Consolas",    12, "bold")
 
# ─────────────────────────────────────────────────────────────────────────────
# ░░  BUILT-IN FALLBACK ALGORITHMS  ░░
# (used only when the original .py files are not found)
# ─────────────────────────────────────────────────────────────────────────────
 
def _fifo_fallback(pages, capacity, show=False):
    """Pure-Python FIFO – returns page_faults count."""
    queue, faults = [], 0
    for p in pages:
        if p not in queue:
            faults += 1
            if len(queue) == capacity:
                queue.pop(0)
            queue.append(p)
    return faults
 
 
def _lru_fallback(pages, capacity, show=False):
    """Pure-Python LRU – returns page_faults count."""
    frames, faults = OrderedDict(), 0
    for p in pages:
        if p in frames:
            frames.move_to_end(p)
        else:
            faults += 1
            if len(frames) == capacity:
                frames.popitem(last=False)
            frames[p] = True
    return faults
 
 
def _optimal_fallback(pages, capacity, show=False):
    """Pure-Python Optimal – returns page_faults count."""
    frames, faults = [], 0
    for i, p in enumerate(pages):
        if p not in frames:
            faults += 1
            if len(frames) == capacity:
                future = []
                for f in frames:
                    try:
                        future.append(pages.index(f, i + 1))
                    except ValueError:
                        future.append(float("inf"))
                frames.pop(future.index(max(future)))
            frames.append(p)
    return faults
 
 
# ── Resolve which back-end to use ────────────────────────────────────────────
_fifo    = fifo    if BACKEND_LOADED else _fifo_fallback
_lru     = lru     if BACKEND_LOADED else _lru_fallback
_optimal = optimal if BACKEND_LOADED else _optimal_fallback
 
 
# ─────────────────────────────────────────────────────────────────────────────
# ░░  STEP-BY-STEP SIMULATION HELPERS  ░░
# These generate the per-step data for the animated table WITHOUT touching
# your original algorithm files.
# ─────────────────────────────────────────────────────────────────────────────
 
def simulate_fifo_steps(pages: list, capacity: int) -> list:
    """
    Returns a list of dicts, one per reference step:
      { 'page', 'frames', 'hit', 'faults_so_far' }
    """
    queue, steps, faults = [], [], 0
    for p in pages:
        hit = p in queue
        if not hit:
            faults += 1
            if len(queue) == capacity:
                queue.pop(0)
            queue.append(p)
        steps.append({
            "page": p,
            "frames": queue[:],
            "hit": hit,
            "faults_so_far": faults
        })
    return steps
 
 
def simulate_lru_steps(pages: list, capacity: int) -> list:
    frames_od, steps, faults = OrderedDict(), [], 0
    for p in pages:
        hit = p in frames_od
        if hit:
            frames_od.move_to_end(p)
        else:
            faults += 1
            if len(frames_od) == capacity:
                frames_od.popitem(last=False)
            frames_od[p] = True
        steps.append({
            "page": p,
            "frames": list(frames_od.keys()),
            "hit": hit,
            "faults_so_far": faults
        })
    return steps
 
 
def simulate_optimal_steps(pages: list, capacity: int) -> list:
    frames, steps, faults = [], [], 0
    for i, p in enumerate(pages):
        hit = p in frames
        if not hit:
            faults += 1
            if len(frames) == capacity:
                future = []
                for f in frames:
                    try:
                        future.append(pages.index(f, i + 1))
                    except ValueError:
                        future.append(float("inf"))
                frames.pop(future.index(max(future)))
            frames.append(p)
        steps.append({
            "page": p,
            "frames": frames[:],
            "hit": hit,
            "faults_so_far": faults
        })
    return steps
 
 
def beladys_test(pages: list, max_frames: int = 8) -> dict:
    """
    Run FIFO for frames 1..max_frames.
    Returns { frames_count: fault_count } and a list of anomaly points.
    """
    results, anomalies = {}, []
    for cap in range(1, max_frames + 1):
        results[cap] = _fifo(pages, cap)
    for cap in range(2, max_frames + 1):
        if results[cap] > results[cap - 1]:
            anomalies.append(cap)
    return results, anomalies
 
 
# ─────────────────────────────────────────────────────────────────────────────
# ░░  TOOLTIP HELPER  ░░
# ─────────────────────────────────────────────────────────────────────────────
 
class ToolTip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text   = text
        self.tip    = None
        widget.bind("<Enter>", self._show)
        widget.bind("<Leave>", self._hide)
 
    def _show(self, _event=None):
        x, y, _, _ = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 20
        self.tip = ctk.CTkToplevel(self.widget)
        self.tip.wm_overrideredirect(True)
        self.tip.wm_geometry(f"+{x}+{y}")
        lbl = ctk.CTkLabel(self.tip, text=self.text, font=FONT_SMALL,
                           fg_color=C_CARD2, corner_radius=6,
                           text_color=C_TEXT, padx=8, pady=4)
        lbl.pack()
 
    def _hide(self, _event=None):
        if self.tip:
            self.tip.destroy()
            self.tip = None
 
 
# ─────────────────────────────────────────────────────────────────────────────
# ░░  MAIN APPLICATION CLASS  ░░
# ─────────────────────────────────────────────────────────────────────────────
 
class VMSimApp(ctk.CTk):
 
    # ── Sidebar navigation items ─────────────────────────────────────────────
    NAV_ITEMS = [
        ("⚡  Simulator",   "simulator"),
        ("📊  Chart",        "chart"),
        ("🔬  Belady Test",  "belady"),
        ("📖  Explanations", "explain"),
        ("ℹ️   About",        "about"),
    ]
 
    ALGO_NAMES = ["FIFO", "LRU", "Optimal", "Compare All"]
 
    EXPLANATIONS = {
        "FIFO": (
            "First-In First-Out (FIFO)\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "The oldest page in memory is the first to be replaced when a\n"
            "new page must be loaded.  The frames act as a circular queue.\n\n"
            "✔ Simple to implement\n"
            "✔ Low overhead\n"
            "✘ Ignores page usage frequency\n"
            "✘ Suffers from Belady's Anomaly\n\n"
            "Time Complexity : O(n)   Space : O(capacity)"
        ),
        "LRU": (
            "Least Recently Used (LRU)\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "Replaces the page that has not been used for the longest\n"
            "period of time.  Based on temporal locality.\n\n"
            "✔ Good approximation of optimal\n"
            "✔ No Belady's Anomaly\n"
            "✘ Requires tracking access order\n"
            "✘ Hardware support needed for full efficiency\n\n"
            "Time Complexity : O(n)   Space : O(capacity)"
        ),
        "Optimal": (
            "Optimal (OPT / Bélády's)\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "Replaces the page that will not be used for the longest\n"
            "future period.  Requires knowledge of future references.\n\n"
            "✔ Theoretically minimum page faults\n"
            "✔ Useful as a benchmark\n"
            "✘ Not implementable in practice\n"
            "✘ Needs complete future reference string\n\n"
            "Time Complexity : O(n·k)  Space : O(capacity)"
        ),
        "Compare All": (
            "Algorithm Comparison\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            "Runs all three algorithms on the same reference string and\n"
            "capacity, then displays a side-by-side fault/hit summary and\n"
            "an embedded bar chart so you can identify the best strategy\n"
            "for your workload.\n\n"
            "General ranking (fewer faults is better):\n"
            "  Optimal ≤ LRU ≤ FIFO  (in most real cases)\n\n"
            "Use the recommendation card on the Simulator tab for an\n"
            "automatic best-algorithm suggestion."
        ),
    }
 
    # ─────────────────────────────────────────────────────────────────────────
    def __init__(self):
        super().__init__()
 
        self.title("Virtual Memory Management Simulator")
        self.geometry("1340x820")
        self.minsize(1100, 700)
        self.configure(fg_color=C_BG)
 
        # ── State variables ───────────────────────────────────────────────
        self._sim_steps        = []      # list of step-dicts for animation
        self._sim_thread       = None
        self._stop_flag        = False
        self._current_page_ref = []
        self._current_capacity = 0
        self._last_results     = {}      # { algo_name: {faults, hits, steps} }
 
        # Build UI
        self._build_layout()
        self._show_page("simulator")
 
    # =========================================================================
    # ░░  LAYOUT BUILDERS  ░░
    # =========================================================================
 
    def _build_layout(self):
        """Top-level two-column grid: sidebar | content."""
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
 
        self._build_sidebar()
        self._build_content_area()
 
    # ── Sidebar ───────────────────────────────────────────────────────────────
    def _build_sidebar(self):
        self.sidebar = ctk.CTkFrame(self, fg_color=C_SIDEBAR,
                                    corner_radius=0, width=220)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)
        self.sidebar.grid_rowconfigure(99, weight=1)  # push items up
 
        # Logo / title
        logo = ctk.CTkLabel(self.sidebar,
                             text="  VM\nSIM",
                             font=("Courier New", 28, "bold"),
                             text_color=C_ACCENT)
        logo.grid(row=0, column=0, padx=20, pady=(28, 4), sticky="w")
 
        sub = ctk.CTkLabel(self.sidebar,
                            text="Memory Simulator v2.0",
                            font=FONT_SMALL, text_color=C_MUTED)
        sub.grid(row=1, column=0, padx=20, pady=(0, 22), sticky="w")
 
        sep = ctk.CTkFrame(self.sidebar, height=1,
                           fg_color=C_BORDER)
        sep.grid(row=2, column=0, padx=14, pady=(0, 18), sticky="ew")
 
        # Nav buttons
        self._nav_buttons = {}
        for idx, (label, key) in enumerate(self.NAV_ITEMS):
            btn = ctk.CTkButton(
                self.sidebar, text=label,
                font=FONT_BTN, anchor="w",
                fg_color="transparent",
                hover_color=C_CARD2,
                text_color=C_MUTED,
                height=42,
                corner_radius=10,
                command=lambda k=key: self._show_page(k)
            )
            btn.grid(row=idx + 3, column=0,
                     padx=12, pady=3, sticky="ew")
            self._nav_buttons[key] = btn
 
        # Version badge at bottom
        ver = ctk.CTkLabel(self.sidebar,
                           text="OS Project  •  CustomTkinter",
                           font=FONT_SMALL, text_color=C_MUTED)
        ver.grid(row=100, column=0, padx=20, pady=20, sticky="sw")
 
    # ── Content area ─────────────────────────────────────────────────────────
    def _build_content_area(self):
        self.content = ctk.CTkFrame(self, fg_color=C_BG, corner_radius=0)
        self.content.grid(row=0, column=1, sticky="nsew")
        self.content.grid_columnconfigure(0, weight=1)
        self.content.grid_rowconfigure(0, weight=1)
 
        self._pages = {}
        for key, builder in [
            ("simulator", self._build_simulator_page),
            ("chart",     self._build_chart_page),
            ("belady",    self._build_belady_page),
            ("explain",   self._build_explain_page),
            ("about",     self._build_about_page),
        ]:
            frame = ctk.CTkFrame(self.content, fg_color=C_BG)
            frame.grid(row=0, column=0, sticky="nsew")
            frame.grid_columnconfigure(0, weight=1)
            frame.grid_rowconfigure(0, weight=1)
            builder(frame)
            self._pages[key] = frame
 
    # =========================================================================
    # ░░  PAGE: SIMULATOR  ░░
    # =========================================================================
 
    def _build_simulator_page(self, parent):
        parent.grid_rowconfigure(1, weight=1)
        parent.grid_columnconfigure(0, weight=1)
 
        # ── Top header ───────────────────────────────────────────────────
        hdr = ctk.CTkFrame(parent, fg_color=C_CARD, corner_radius=0, height=64)
        hdr.grid(row=0, column=0, sticky="ew")
        hdr.grid_propagate(False)
        ctk.CTkLabel(hdr, text="⚡  Simulator Dashboard",
                     font=FONT_TITLE, text_color=C_TEXT
                     ).pack(side="left", padx=24, pady=16)
 
        # ── Main body ────────────────────────────────────────────────────
        body = ctk.CTkScrollableFrame(parent, fg_color=C_BG)
        body.grid(row=1, column=0, sticky="nsew")
        body.grid_columnconfigure((0, 1), weight=1)
 
        # ── Controls card ────────────────────────────────────────────────
        ctrl = self._card(body, "🎛  Input Controls", span=2)
 
        # Page reference string
        ctk.CTkLabel(ctrl, text="Page Reference String  (space-separated):",
                     font=FONT_LABEL, text_color=C_MUTED).grid(
            row=0, column=0, sticky="w", padx=6, pady=(6, 2))
        self.entry_pages = ctk.CTkEntry(
            ctrl, placeholder_text="e.g.  7 0 1 2 0 3 0 4 2 3 0 3 2",
            font=FONT_MONO, height=38, corner_radius=8,
            fg_color=C_BG, border_color=C_BORDER, text_color=C_TEXT)
        self.entry_pages.grid(row=1, column=0, columnspan=3,
                              sticky="ew", padx=6, pady=(0, 10))
        self.entry_pages.insert(0, "7 0 1 2 0 3 0 4 2 3 0 3 2")
 
        # Frames + algo + buttons row
        row_ctrl = ctk.CTkFrame(ctrl, fg_color="transparent")
        row_ctrl.grid(row=2, column=0, columnspan=3,
                      sticky="ew", padx=0, pady=(0, 6))
        row_ctrl.grid_columnconfigure(4, weight=1)
 
        ctk.CTkLabel(row_ctrl, text="Frames:", font=FONT_LABEL,
                     text_color=C_MUTED).grid(row=0, column=0, padx=(6, 4))
        self.entry_frames = ctk.CTkEntry(
            row_ctrl, width=70, placeholder_text="3",
            font=FONT_MONO, height=36, corner_radius=8,
            fg_color=C_BG, border_color=C_BORDER, text_color=C_TEXT)
        self.entry_frames.grid(row=0, column=1, padx=(0, 16))
        self.entry_frames.insert(0, "3")
 
        ctk.CTkLabel(row_ctrl, text="Algorithm:", font=FONT_LABEL,
                     text_color=C_MUTED).grid(row=0, column=2, padx=(0, 4))
        self.algo_var = ctk.StringVar(value="FIFO")
        self.algo_dropdown = ctk.CTkOptionMenu(
            row_ctrl, values=self.ALGO_NAMES,
            variable=self.algo_var,
            font=FONT_MONO, height=36, width=148,
            fg_color=C_CARD2, button_color=C_ACCENT,
            button_hover_color=C_ACCENT2,
            dropdown_fg_color=C_CARD2,
            command=self._on_algo_change)
        self.algo_dropdown.grid(row=0, column=3, padx=(0, 16))
 
        # Speed slider
        ctk.CTkLabel(row_ctrl, text="Speed:", font=FONT_LABEL,
                     text_color=C_MUTED).grid(row=0, column=4, padx=(0, 4))
        self.speed_var = ctk.DoubleVar(value=0.6)
        speed_slider = ctk.CTkSlider(
            row_ctrl, from_=0.05, to=2.0,
            variable=self.speed_var, width=130,
            button_color=C_ACCENT, progress_color=C_ACCENT2)
        speed_slider.grid(row=0, column=5, padx=(0, 4))
        ToolTip(speed_slider, "Drag left = faster  |  Drag right = slower")
 
        self.speed_label = ctk.CTkLabel(row_ctrl, text="0.60s",
                                        font=FONT_SMALL, text_color=C_MUTED)
        self.speed_label.grid(row=0, column=6, padx=(0, 16))
        speed_slider.configure(command=self._update_speed_label)
 
        # Run / Stop / Reset / Export buttons
        btn_frame = ctk.CTkFrame(row_ctrl, fg_color="transparent")
        btn_frame.grid(row=0, column=7, padx=6)
 
        self.run_btn = ctk.CTkButton(
            btn_frame, text="▶  Run", font=FONT_BTN,
            fg_color=C_ACCENT, hover_color=C_ACCENT2,
            corner_radius=10, height=36, width=90,
            command=self._run_simulation)
        self.run_btn.grid(row=0, column=0, padx=4)
 
        self.stop_btn = ctk.CTkButton(
            btn_frame, text="⏹  Stop", font=FONT_BTN,
            fg_color="#c0392b", hover_color="#922b21",
            corner_radius=10, height=36, width=90,
            state="disabled", command=self._stop_simulation)
        self.stop_btn.grid(row=0, column=1, padx=4)
 
        reset_btn = ctk.CTkButton(
            btn_frame, text="↺  Reset", font=FONT_BTN,
            fg_color=C_CARD2, hover_color=C_BORDER,
            corner_radius=10, height=36, width=90,
            command=self._reset)
        reset_btn.grid(row=0, column=2, padx=4)
 
        export_btn = ctk.CTkButton(
            btn_frame, text="⬇  CSV", font=FONT_BTN,
            fg_color="#1e6e40", hover_color="#155230",
            corner_radius=10, height=36, width=90,
            command=self._export_csv)
        export_btn.grid(row=0, column=3, padx=4)
 
        # ── Dashboard KPI cards ──────────────────────────────────────────
        cards_row = ctk.CTkFrame(body, fg_color="transparent")
        cards_row.grid(row=1, column=0, columnspan=2,
                       sticky="ew", padx=20, pady=(12, 0))
        for i in range(5):
            cards_row.grid_columnconfigure(i, weight=1)
 
        labels = ["Page Faults", "Page Hits",
                  "Hit Ratio", "Fault Ratio", "Best Algorithm"]
        defaults = ["—", "—", "—", "—", "—"]
        colors   = [C_FAULT, C_HIT, C_ACCENT, C_ACCENT2, C_HIGHLIGHT]
        self._kpi_vars = []
        for i, (lbl, dflt, clr) in enumerate(zip(labels, defaults, colors)):
            card = ctk.CTkFrame(cards_row, fg_color=C_CARD,
                                corner_radius=14)
            card.grid(row=0, column=i, padx=6, pady=4, sticky="ew")
            card.grid_columnconfigure(0, weight=1)
 
            val_var = ctk.StringVar(value=dflt)
            self._kpi_vars.append(val_var)
 
            ctk.CTkLabel(card, textvariable=val_var,
                         font=FONT_CARD, text_color=clr
                         ).grid(row=0, column=0, pady=(14, 0))
            ctk.CTkLabel(card, text=lbl, font=FONT_SMALL,
                         text_color=C_MUTED
                         ).grid(row=1, column=0, pady=(2, 12))
 
        # ── Step table ───────────────────────────────────────────────────
        tbl_card = self._card(body, "📋  Step-by-Step Frame Table", span=2,
                              row=2)
 
        # Header row
        hdr_row = ctk.CTkFrame(tbl_card, fg_color=C_CARD2, corner_radius=8)
        hdr_row.grid(row=0, column=0, sticky="ew", padx=0, pady=(0, 4))
        for ci, (col, w) in enumerate([
            ("Step", 50), ("Page", 60), ("Frames", 260),
            ("Status", 100), ("Faults So Far", 110)
        ]):
            ctk.CTkLabel(hdr_row, text=col, font=FONT_LABEL,
                         text_color=C_ACCENT, width=w, anchor="center"
                         ).grid(row=0, column=ci, padx=6, pady=6)
 
        # Scrollable table body
        self.table_frame = ctk.CTkScrollableFrame(
            tbl_card, fg_color="transparent", height=240)
        self.table_frame.grid(row=1, column=0, sticky="ew")
        self.table_frame.grid_columnconfigure(0, weight=1)
 
        # ── Frame visualizer ─────────────────────────────────────────────
        viz_card = self._card(body, "🖼  Live Frame Visualizer", span=2, row=3)
        self.frame_viz_row = ctk.CTkFrame(viz_card, fg_color="transparent",
                                          height=80)
        self.frame_viz_row.grid(row=0, column=0, sticky="ew", padx=4, pady=6)
 
    # =========================================================================
    # ░░  PAGE: CHART  ░░
    # =========================================================================
 
    def _build_chart_page(self, parent):
        parent.grid_rowconfigure(1, weight=1)
        parent.grid_columnconfigure(0, weight=1)
 
        hdr = ctk.CTkFrame(parent, fg_color=C_CARD, corner_radius=0, height=64)
        hdr.grid(row=0, column=0, sticky="ew")
        hdr.grid_propagate(False)
        ctk.CTkLabel(hdr, text="📊  Algorithm Comparison Chart",
                     font=FONT_TITLE, text_color=C_TEXT
                     ).pack(side="left", padx=24, pady=16)
 
        self.chart_frame = ctk.CTkFrame(parent, fg_color=C_CARD,
                                         corner_radius=16)
        self.chart_frame.grid(row=1, column=0, sticky="nsew",
                               padx=24, pady=16)
        self.chart_frame.grid_columnconfigure(0, weight=1)
        self.chart_frame.grid_rowconfigure(0, weight=1)
 
        self._fig, self._ax = plt.subplots(figsize=(10, 5))
        self._fig.patch.set_facecolor(C_CARD)
        self._ax.set_facecolor(C_CARD2)
        self._ax.set_title("Run a simulation to see the chart",
                           color=C_MUTED, fontsize=12)
 
        self._canvas = FigureCanvasTkAgg(self._fig, master=self.chart_frame)
        self._canvas.get_tk_widget().grid(row=0, column=0,
                                           sticky="nsew", padx=10, pady=10)
        self._canvas.draw()
 
    # =========================================================================
    # ░░  PAGE: BELADY  ░░
    # =========================================================================
 
    def _build_belady_page(self, parent):
        parent.grid_rowconfigure(1, weight=1)
        parent.grid_columnconfigure(0, weight=1)
 
        hdr = ctk.CTkFrame(parent, fg_color=C_CARD, corner_radius=0, height=64)
        hdr.grid(row=0, column=0, sticky="ew")
        hdr.grid_propagate(False)
        ctk.CTkLabel(hdr, text="🔬  Belady's Anomaly Detector",
                     font=FONT_TITLE, text_color=C_TEXT
                     ).pack(side="left", padx=24, pady=16)
 
        body = ctk.CTkScrollableFrame(parent, fg_color=C_BG)
        body.grid(row=1, column=0, sticky="nsew")
        body.grid_columnconfigure(0, weight=1)
 
        # Controls
        ctrl = self._card(body, "⚙  Test Configuration", span=1, row=0)
        ctk.CTkLabel(ctrl, text="Max Frames to Test (1 → N):",
                     font=FONT_LABEL, text_color=C_MUTED).grid(
            row=0, column=0, sticky="w", padx=6, pady=(6, 2))
 
        inp_row = ctk.CTkFrame(ctrl, fg_color="transparent")
        inp_row.grid(row=1, column=0, sticky="ew", padx=0, pady=(0, 8))
 
        self.belady_max_var = ctk.StringVar(value="8")
        ctk.CTkEntry(inp_row, textvariable=self.belady_max_var,
                     width=80, font=FONT_MONO, height=36,
                     fg_color=C_BG, border_color=C_BORDER,
                     text_color=C_TEXT).grid(row=0, column=0, padx=(6, 12))
 
        ctk.CTkButton(inp_row, text="▶  Run Belady Test",
                      font=FONT_BTN, fg_color=C_ACCENT,
                      hover_color=C_ACCENT2, corner_radius=10,
                      height=36, command=self._run_belady
                      ).grid(row=0, column=1, padx=4)
 
        # Results text
        res_card = self._card(body, "📋  Results", span=1, row=1)
        self.belady_text = ctk.CTkTextbox(
            res_card, font=FONT_MONO, fg_color=C_BG,
            text_color=C_TEXT, height=160, state="disabled")
        self.belady_text.grid(row=0, column=0, sticky="ew",
                               padx=4, pady=(0, 6))
 
        # Embedded chart
        chart_card = self._card(body, "📈  FIFO Fault Curve", span=1, row=2)
        self._bel_fig, self._bel_ax = plt.subplots(figsize=(9, 3.6))
        self._bel_fig.patch.set_facecolor(C_CARD)
        self._bel_ax.set_facecolor(C_CARD2)
        self._bel_ax.set_title("Run the test to populate chart",
                               color=C_MUTED)
        self._bel_canvas = FigureCanvasTkAgg(self._bel_fig,
                                              master=chart_card)
        self._bel_canvas.get_tk_widget().grid(row=0, column=0,
                                               sticky="ew",
                                               padx=8, pady=8)
        self._bel_canvas.draw()
 
    # =========================================================================
    # ░░  PAGE: EXPLANATIONS  ░░
    # =========================================================================
 
    def _build_explain_page(self, parent):
        parent.grid_rowconfigure(1, weight=1)
        parent.grid_columnconfigure(0, weight=1)
 
        hdr = ctk.CTkFrame(parent, fg_color=C_CARD, corner_radius=0, height=64)
        hdr.grid(row=0, column=0, sticky="ew")
        hdr.grid_propagate(False)
        ctk.CTkLabel(hdr, text="📖  Algorithm Explanations",
                     font=FONT_TITLE, text_color=C_TEXT
                     ).pack(side="left", padx=24, pady=16)
 
        body = ctk.CTkScrollableFrame(parent, fg_color=C_BG)
        body.grid(row=1, column=0, sticky="nsew")
        body.grid_columnconfigure(0, weight=1)
 
        for algo, text in self.EXPLANATIONS.items():
            card = self._card(body, f"  {algo}", span=1,
                              row=list(self.EXPLANATIONS).index(algo))
            box = ctk.CTkTextbox(
                card, font=("Consolas", 11),
                fg_color=C_BG, text_color=C_TEXT,
                height=158, state="normal")
            box.insert("0.0", text)
            box.configure(state="disabled")
            box.grid(row=0, column=0, sticky="ew", padx=4, pady=(0, 6))
 
    # =========================================================================
    # ░░  PAGE: ABOUT  ░░
    # =========================================================================
 
    def _build_about_page(self, parent):
        parent.grid_rowconfigure(0, weight=1)
        parent.grid_columnconfigure(0, weight=1)
 
        inner = ctk.CTkFrame(parent, fg_color=C_CARD, corner_radius=18)
        inner.place(relx=0.5, rely=0.5, anchor="center")
 
        lines = [
            ("Virtual Memory Management Simulator", FONT_TITLE,  C_ACCENT),
            ("Advanced OS Project  •  Python GUI",  FONT_SECTION, C_TEXT),
            ("",                                     FONT_LABEL,   C_TEXT),
            ("Algorithms  :  FIFO  •  LRU  •  Optimal", FONT_LABEL, C_MUTED),
            ("Features    :  Animation  •  Belady Test  •  CSV Export",
             FONT_LABEL, C_MUTED),
            ("Built with  :  CustomTkinter  •  Matplotlib  •  Pandas",
             FONT_LABEL, C_MUTED),
            ("",                                     FONT_LABEL,   C_TEXT),
            ("© 2025  •  Operating Systems Course Project",
             FONT_SMALL, C_MUTED),
        ]
        for i, (text, font, color) in enumerate(lines):
            ctk.CTkLabel(inner, text=text, font=font,
                         text_color=color).grid(
                row=i, column=0, padx=60,
                pady=(20 if i == 0 else 4,
                      20 if i == len(lines) - 1 else 0))
 
    # =========================================================================
    # ░░  UTILITY: GENERIC CARD BUILDER  ░░
    # =========================================================================
 
    def _card(self, parent, title: str, span: int = 1, row: int = 0):
        """Creates a titled card frame and returns its inner content frame."""
        outer = ctk.CTkFrame(parent, fg_color=C_CARD, corner_radius=14)
        outer.grid(row=row, column=0, columnspan=span,
                   sticky="ew", padx=20, pady=(14, 0))
        outer.grid_columnconfigure(0, weight=1)
 
        ctk.CTkLabel(outer, text=f"  {title}",
                     font=FONT_SECTION, text_color=C_TEXT,
                     anchor="w").grid(row=0, column=0,
                                      sticky="ew", padx=10, pady=(12, 4))
        sep = ctk.CTkFrame(outer, height=1, fg_color=C_BORDER)
        sep.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 10))
 
        inner = ctk.CTkFrame(outer, fg_color="transparent")
        inner.grid(row=2, column=0, sticky="ew", padx=14, pady=(0, 14))
        inner.grid_columnconfigure(0, weight=1)
        return inner
 
    # =========================================================================
    # ░░  NAVIGATION  ░░
    # =========================================================================
 
    def _show_page(self, key: str):
        for k, btn in self._nav_buttons.items():
            btn.configure(
                fg_color=C_ACCENT if k == key else "transparent",
                text_color=C_TEXT  if k == key else C_MUTED
            )
        self._pages[key].tkraise()
 
    # =========================================================================
    # ░░  HELPERS: INPUT PARSING  ░░
    # =========================================================================
 
    def _parse_inputs(self):
        """Parse and validate the two entry fields. Returns (pages, capacity)
        or raises ValueError with a user-friendly message."""
        raw = self.entry_pages.get().strip()
        if not raw:
            raise ValueError("Page reference string is empty.")
        try:
            pages = [int(x) for x in raw.split()]
        except ValueError:
            raise ValueError("Page reference string must contain "
                             "only integers separated by spaces.")
        if len(pages) < 2:
            raise ValueError("Please enter at least 2 page references.")
 
        try:
            capacity = int(self.entry_frames.get().strip())
        except ValueError:
            raise ValueError("Number of frames must be a positive integer.")
        if capacity < 1:
            raise ValueError("Number of frames must be ≥ 1.")
        if capacity >= len(pages):
            raise ValueError("Number of frames must be less than "
                             "the length of the reference string.")
        return pages, capacity
 
    # =========================================================================
    # ░░  SIMULATION LOGIC  ░░
    # =========================================================================
 
    def _run_simulation(self):
        """Entry point for the Run button."""
        try:
            pages, capacity = self._parse_inputs()
        except ValueError as e:
            messagebox.showerror("Input Error", str(e))
            return
 
        self._current_page_ref = pages
        self._current_capacity = capacity
        self._stop_flag = False
 
        # Disable run, enable stop
        self.run_btn.configure(state="disabled")
        self.stop_btn.configure(state="normal")
 
        algo = self.algo_var.get()
 
        if algo == "Compare All":
            self._run_compare_all(pages, capacity)
        else:
            steps_fn = {
                "FIFO":    simulate_fifo_steps,
                "LRU":     simulate_lru_steps,
                "Optimal": simulate_optimal_steps,
            }[algo]
            self._sim_steps = steps_fn(pages, capacity)
            self._sim_thread = threading.Thread(
                target=self._animate_steps,
                args=(self._sim_steps, capacity),
                daemon=True
            )
            self._sim_thread.start()
 
    def _animate_steps(self, steps: list, capacity: int):
        """Runs in a background thread; populates the table row-by-row."""
        self._clear_table()
        total = len(steps)
        for idx, step in enumerate(steps):
            if self._stop_flag:
                break
            self.after(0, self._add_table_row,
                       idx + 1, step, capacity)
            self.after(0, self._update_frame_visualizer,
                       step["frames"], capacity, step["hit"])
            time.sleep(self.speed_var.get())
 
        # After all steps finished
        final = steps[-1] if steps else {}
        self.after(0, self._finalize_single,
                   final, total, steps)
 
    def _add_table_row(self, idx: int, step: dict, capacity: int):
        """Appends one row to the step table."""
        bg   = "#1c2a1e" if step["hit"] else "#2a1c1c"
        row  = ctk.CTkFrame(self.table_frame, fg_color=bg,
                             corner_radius=6)
        row.grid(row=idx - 1, column=0, sticky="ew",
                 pady=2, padx=2)
 
        cols = [
            (str(idx),                            50),
            (str(step["page"]),                   60),
            (self._frames_str(step["frames"], capacity), 260),
            ("✓ HIT"   if step["hit"] else "✗ FAULT", 100),
            (str(step["faults_so_far"]),           110),
        ]
        colors = [C_TEXT, C_ACCENT,
                  C_TEXT,
                  C_HIT if step["hit"] else C_FAULT,
                  C_FAULT]
 
        for ci, ((text, w), clr) in enumerate(zip(cols, colors)):
            ctk.CTkLabel(row, text=text, font=FONT_MONO,
                         text_color=clr, width=w, anchor="center"
                         ).grid(row=0, column=ci, padx=6, pady=5)
 
    @staticmethod
    def _frames_str(frames: list, capacity: int) -> str:
        filled = [str(f) for f in frames]
        empty  = ["—"] * (capacity - len(filled))
        return "  |  ".join(filled + empty)
 
    def _update_frame_visualizer(self, frames: list,
                                  capacity: int, hit: bool):
        """Redraws the live frame boxes."""
        for widget in self.frame_viz_row.winfo_children():
            widget.destroy()
 
        box_clr = "#1c3a28" if hit else "#3a1c1c"
        for i in range(capacity):
            val  = str(frames[i]) if i < len(frames) else "—"
            clr  = C_HIT if (hit and i < len(frames)) else \
                   (C_FAULT if (not hit and i < len(frames)) else C_MUTED)
            box  = ctk.CTkFrame(self.frame_viz_row,
                                 width=68, height=68,
                                 fg_color=box_clr, corner_radius=10)
            box.pack(side="left", padx=6, pady=4)
            box.pack_propagate(False)
            ctk.CTkLabel(box, text=val, font=("Courier New", 20, "bold"),
                         text_color=clr).place(relx=0.5, rely=0.5,
                                               anchor="center")
 
    def _finalize_single(self, final: dict, total: int, steps: list):
        """Update KPI cards after single-algorithm animation finishes."""
        faults = final.get("faults_so_far", 0)
        hits   = total - faults
        self._kpi_vars[0].set(str(faults))
        self._kpi_vars[1].set(str(hits))
        self._kpi_vars[2].set(f"{hits/total:.1%}" if total else "—")
        self._kpi_vars[3].set(f"{faults/total:.1%}" if total else "—")
        self._kpi_vars[4].set(self.algo_var.get())
 
        # Store for CSV
        self._last_results = {
            self.algo_var.get(): {
                "faults": faults, "hits": hits, "steps": steps
            }
        }
        results = {
            "FIFO": _fifo(self._current_page_ref, self._current_capacity),
            "LRU": _lru(self._current_page_ref, self._current_capacity),
            "Optimal": _optimal(self._current_page_ref, self._current_capacity)
}

        self._plot_chart(results)
        self._re_enable_run()
 
    def _run_compare_all(self, pages: list, capacity: int):
        """Compare all three algorithms instantly (no animation)."""
        results = {}
        for name, fn in [("FIFO", _fifo), ("LRU", _lru),
                          ("Optimal", _optimal)]:
            results[name] = fn(pages, capacity)
 
        total  = len(pages)
        best   = min(results, key=results.get)
        faults = results[best]
        hits   = total - faults
 
        self._kpi_vars[0].set(str(results["FIFO"]))
        self._kpi_vars[1].set(f"F:{results['FIFO']}  "
                               f"L:{results['LRU']}  "
                               f"O:{results['Optimal']}")
        self._kpi_vars[2].set(f"{(total-results[best])/total:.1%}")
        self._kpi_vars[3].set(f"{results[best]/total:.1%}")
        self._kpi_vars[4].set(best)
 
        # Populate table with best algo steps
        steps_fn = {"FIFO": simulate_fifo_steps,
                    "LRU":  simulate_lru_steps,
                    "Optimal": simulate_optimal_steps}[best]
        steps = steps_fn(pages, capacity)
        self._clear_table()
        for idx, step in enumerate(steps):
            self._add_table_row(idx + 1, step, capacity)
 
        self._last_results = {}
        for name in results:
            fn2 = {"FIFO": simulate_fifo_steps,
                   "LRU":  simulate_lru_steps,
                   "Optimal": simulate_optimal_steps}[name]
            s = fn2(pages, capacity)
            self._last_results[name] = {
                "faults": results[name],
                "hits":   total - results[name],
                "steps":  s
            }
        self._plot_chart(results)
        self._re_enable_run()
 
    def _stop_simulation(self):
        self._stop_flag = True
        self._re_enable_run()
 
    def _re_enable_run(self):
        self.run_btn.configure(state="normal")
        self.stop_btn.configure(state="disabled")
 
    def _reset(self):
        self._stop_flag = True
        self._clear_table()
        for var in self._kpi_vars:
            var.set("—")
        for widget in self.frame_viz_row.winfo_children():
            widget.destroy()
        self._last_results = {}
        self._re_enable_run()
 
    def _clear_table(self):
        for widget in self.table_frame.winfo_children():
            widget.destroy()
 
    # =========================================================================
    # ░░  CHART RENDERING  ░░
    # =========================================================================
 
    def _plot_chart(self, results: dict):
        """Draw a styled bar chart inside the Chart page."""
        self._ax.clear()
        algos  = list(results.keys())
        faults = list(results.values())
        colors = [C_FAULT, C_ACCENT, C_HIT,
                  C_ACCENT2][:len(algos)]
 
        bars = self._ax.bar(algos, faults, color=colors,
                             width=0.45, edgecolor=C_BORDER,
                             linewidth=1.2, zorder=3)
        for bar, val in zip(bars, faults):
            self._ax.text(bar.get_x() + bar.get_width() / 2,
                          bar.get_height() + 0.15,
                          str(val), ha="center", va="bottom",
                          color=C_TEXT, fontsize=13,
                          fontfamily="Consolas")
 
        self._ax.set_facecolor(C_CARD2)
        self._fig.patch.set_facecolor(C_CARD)
        self._ax.tick_params(colors=C_TEXT, labelsize=11)
        self._ax.set_ylabel("Page Faults", color=C_MUTED, fontsize=11)
        self._ax.set_title("Page Faults Comparison",
                            color=C_TEXT, fontsize=14, pad=14)
        self._ax.yaxis.set_major_locator(mticker.MaxNLocator(integer=True))
        for spine in self._ax.spines.values():
            spine.set_edgecolor(C_BORDER)
        self._ax.grid(axis="y", color=C_BORDER, linewidth=0.7, zorder=0)
        self._fig.tight_layout()
        self._canvas.draw()
 
    # =========================================================================
    # ░░  BELADY'S ANOMALY TEST  ░░
    # =========================================================================
 
    def _run_belady(self):
        try:
            pages, _ = self._parse_inputs()
        except ValueError as e:
            messagebox.showerror("Input Error", str(e))
            return
 
        try:
            max_f = int(self.belady_max_var.get())
            if max_f < 2:
                raise ValueError
        except ValueError:
            messagebox.showerror("Input Error",
                                 "Max frames must be an integer ≥ 2.")
            return
 
        results, anomalies = beladys_test(pages, max_f)
 
        # ── Text summary ─────────────────────────────────────────────────
        lines = ["  Frames │ Page Faults │ Anomaly?",
                 "  ───────┼─────────────┼─────────"]
        prev = None
        for cap, flt in results.items():
            flag = ""
            if prev is not None and flt > prev:
                flag = "  ← ⚠ ANOMALY"
            lines.append(f"  {cap:^6} │  {flt:^10} │{flag}")
            prev = flt
 
        if anomalies:
            lines.append("")
            lines.append(f"  ⚠  Belady's Anomaly detected at "
                         f"frame counts: {anomalies}")
        else:
            lines.append("")
            lines.append("  ✓  No Belady's Anomaly detected.")
 
        self.belady_text.configure(state="normal")
        self.belady_text.delete("0.0", "end")
        self.belady_text.insert("0.0", "\n".join(lines))
        self.belady_text.configure(state="disabled")
 
        # ── Chart ────────────────────────────────────────────────────────
        self._bel_ax.clear()
        xs = list(results.keys())
        ys = list(results.values())
        # Color bars: red if anomaly point, else blue
        bar_colors = [C_FAULT if x in anomalies else C_ACCENT for x in xs]
        self._bel_ax.bar(xs, ys, color=bar_colors,
                          width=0.6, edgecolor=C_BORDER, zorder=3)
        self._bel_ax.plot(xs, ys, color=C_HIGHLIGHT,
                           marker="o", linewidth=1.8,
                           markersize=5, zorder=4)
        self._bel_ax.set_facecolor(C_CARD2)
        self._bel_fig.patch.set_facecolor(C_CARD)
        self._bel_ax.tick_params(colors=C_TEXT)
        self._bel_ax.set_xlabel("Number of Frames",
                                 color=C_MUTED, fontsize=10)
        self._bel_ax.set_ylabel("Page Faults",
                                 color=C_MUTED, fontsize=10)
        self._bel_ax.set_title("FIFO: Faults vs Frame Count"
                                + ("  ⚠ Anomaly detected!" if anomalies else ""),
                                color=C_HIGHLIGHT if anomalies else C_TEXT,
                                fontsize=12)
        for sp in self._bel_ax.spines.values():
            sp.set_edgecolor(C_BORDER)
        self._bel_ax.grid(axis="y", color=C_BORDER,
                           linewidth=0.7, zorder=0)
        self._bel_ax.yaxis.set_major_locator(
            mticker.MaxNLocator(integer=True))
        self._bel_fig.tight_layout()
        self._bel_canvas.draw()
 
    # =========================================================================
    # ░░  CSV EXPORT  ░░
    # =========================================================================
 
    def _export_csv(self):
        if not self._last_results:
            messagebox.showwarning("No Data",
                                   "Run a simulation first before exporting.")
            return
 
        path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            title="Save Simulation Results"
        )
        if not path:
            return
 
        try:
            rows = []
            for algo, data in self._last_results.items():
                for idx, step in enumerate(data["steps"]):
                    rows.append({
                        "Algorithm": algo,
                        "Step":      idx + 1,
                        "Page":      step["page"],
                        "Frames":    " | ".join(map(str, step["frames"])),
                        "Status":    "HIT" if step["hit"] else "FAULT",
                        "Faults So Far": step["faults_so_far"],
                        "Total Faults":  data["faults"],
                        "Total Hits":    data["hits"],
                        "Hit Ratio":     f"{data['hits']/len(data['steps']):.4f}",
                        "Fault Ratio":   f"{data['faults']/len(data['steps']):.4f}",
                    })
            pd.DataFrame(rows).to_csv(path, index=False)
            messagebox.showinfo("Exported",
                                f"Results saved to:\n{path}")
        except Exception as e:
            messagebox.showerror("Export Error", str(e))
 
    # =========================================================================
    # ░░  MISC CALLBACKS  ░░
    # =========================================================================
 
    def _update_speed_label(self, val):
        self.speed_label.configure(text=f"{float(val):.2f}s")
 
    def _on_algo_change(self, _val):
        pass  # reserved for future live-update logic
 
 
# ─────────────────────────────────────────────────────────────────────────────
# ░░  ENTRY POINT  ░░
# ─────────────────────────────────────────────────────────────────────────────
 
if __name__ == "__main__":
    app = VMSimApp()
    app.mainloop()
