#!/usr/bin/env python3
"""
DevKit Pro — API Tester · CSV Cleaner · JSON Formatter
Un outil de développeur tout-en-un avec interface graphique Tkinter.

Dépendances :
    pip install requests
"""

import json
import csv
import io
import os
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from datetime import datetime

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

# ══════════════════════════════════════════════════════════════════
#  PALETTE & CONSTANTES - Design Pro & Sombre (Dark Mode)
# ══════════════════════════════════════════════════════════════════

BG       = "#0d1117"           # Fond principal très sombre (GitHub Dark)
BG2      = "#161b22"           # Fond de panneau / secondaire
BG3      = "#21262d"           # Fond d'input / item
BG4      = "#30363d"           # Fond hover / accent
ACCENT   = "#58a6ff"           # Accent bleu vif (GitHub Blue)
ACCENT2  = "#1f6feb"           # Accent secondaire
SUCCESS  = "#3fb950"           # Vert vif (Succès)
WARNING  = "#d29922"           # Jaune/Orange (Avertissement)
DANGER   = "#f85149"           # Rouge vif (Erreur)
INFO     = "#a371f7"           # Violet (Info)
FG       = "#c9d1d9"           # Texte principal gris clair
FG2      = "#8b949e"           # Texte secondaire
FG3      = "#6e7681"           # Texte tertiaire
BORDER   = "#30363d"           # Bordure subtile
BORDER2  = "#21262d"           # Bordure secondaire

# Font avec fallback pour garantir la disponibilité
try:
    import tkinter.font as tkfont
    available_fonts = tkfont.families()
    MONO_FONT = "JetBrains Mono" if "JetBrains Mono" in available_fonts else \
                "Consolas" if "Consolas" in available_fonts else \
                "Courier New" if "Courier New" in available_fonts else "monospace"
except:
    MONO_FONT = "Consolas"

FONT_MONO  = (MONO_FONT, 10)
FONT_BODY  = ("Segoe UI", 10)
FONT_BOLD  = ("Segoe UI", 10, "bold")
FONT_TITLE = ("Segoe UI", 14, "bold")
FONT_HEADER = ("Segoe UI", 12, "bold")
FONT_SMALL = ("Segoe UI", 9)

METHOD_COLORS = {
    "GET":    "#3fb950",       # Vert
    "POST":   "#58a6ff",       # Bleu
    "PUT":    "#d29922",       # Jaune/Orange
    "PATCH":  "#a371f7",       # Violet
    "DELETE": "#f85149",       # Rouge
}

JSON_COLORS = {
    "key": "#7ee787",          # Vert clair pour les clés
    "string": "#a5d6ff",       # Bleu clair pour strings
    "number": "#79c0ff",       # Bleu pour nombres
    "boolean": "#ff7b72",      # Rouge pour true/false
    "null": "#ff7b72",         # Rouge pour null
}

# ══════════════════════════════════════════════════════════════════
#  HELPERS UI
# ══════════════════════════════════════════════════════════════════

def styled_button(parent, text, command=None, color=ACCENT, width=12, tooltip=None, **kw):
    """Bouton stylisé avec effets hover modernes."""
    btn = tk.Button(
        parent, text=text, command=command,
        bg=color, fg="white", relief="flat",
        font=FONT_BOLD, padx=14, pady=8,
        activebackground=_lighten(color, 20), activeforeground="white",
        cursor="hand2", bd=0, width=width, highlightthickness=0,
        highlightbackground=BORDER, highlightcolor=color, **kw
    )

    def on_enter(e):
        btn.config(bg=_lighten(color, 15))

    def on_leave(e):
        btn.config(bg=color)

    btn.bind("<Enter>", on_enter)
    btn.bind("<Leave>", on_leave)

    if tooltip:
        ToolTip(btn, tooltip)

    return btn


def icon_button(parent, text, command=None, tooltip=None):
    """Bouton icône compact sans fond."""
    btn = tk.Label(parent, text=text, font=("Segoe UI", 12),
                   fg=FG2, bg=BG2, cursor="hand2", padx=6, pady=4)
    if command:
        btn.bind("<Button-1>", lambda e: command())

    def on_enter(e):
        btn.config(fg=ACCENT, bg=BG3)

    def on_leave(e):
        btn.config(fg=FG2, bg=BG2)

    btn.bind("<Enter>", on_enter)
    btn.bind("<Leave>", on_leave)

    if tooltip:
        ToolTip(btn, tooltip, delay=400)

    return btn

def _lighten(hex_color, amount=30):
    """Éclaircit légèrement une couleur hex."""
    hex_color = hex_color.lstrip("#")
    r, g, b = (int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    r = min(255, r + amount)
    g = min(255, g + amount)
    b = min(255, b + amount)
    return f"#{r:02x}{g:02x}{b:02x}"

def _darken(hex_color, amount=20):
    """Assombrit légèrement une couleur hex."""
    hex_color = hex_color.lstrip("#")
    r, g, b = (int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    r = max(0, r - amount)
    g = max(0, g - amount)
    b = max(0, b - amount)
    return f"#{r:02x}{g:02x}{b:02x}"

def label(parent, text, font=FONT_BODY, fg=FG, **kw):
    return tk.Label(parent, text=text, font=font, fg=fg, bg=BG, **kw)


class ToolTip:
    """Tooltip moderne avec délai et style cohérent."""
    def __init__(self, widget, text, delay=500):
        self.widget = widget
        self.text = text
        self.delay = delay
        self.tip_window = None
        self.id = None
        self.widget.bind("<Enter>", self._on_enter)
        self.widget.bind("<Leave>", self._on_leave)
        self.widget.bind("<ButtonPress>", self._on_leave)

    def _on_enter(self, event=None):
        self._schedule()

    def _on_leave(self, event=None):
        self._unschedule()
        self._hide()

    def _schedule(self):
        self.id = self.widget.after(self.delay, self._show)

    def _unschedule(self):
        if self.id:
            self.widget.after_cancel(self.id)
            self.id = None

    def _show(self):
        if self.tip_window:
            return
        x = self.widget.winfo_rootx() + self.widget.winfo_width() // 2
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 5
        self.tip_window = tk.Toplevel(self.widget)
        self.tip_window.wm_overrideredirect(True)
        self.tip_window.wm_geometry(f"+{x}+{y}")
        self.tip_window.configure(bg=BORDER)

        # Conteneur avec padding
        frame = tk.Frame(self.tip_window, bg=BG3, padx=1, pady=1)
        frame.pack()

        label = tk.Label(frame, text=self.text, font=FONT_SMALL,
                        fg=FG, bg=BG3, padx=8, pady=5)
        label.pack()

    def _hide(self):
        if self.tip_window:
            self.tip_window.destroy()
            self.tip_window = None

def separator(parent, orient="horizontal"):
    return ttk.Separator(parent, orient=orient)

def scrolled_text(parent, **kw):
    """Text widget avec scrollbars modernes."""
    frame = tk.Frame(parent, bg=BG3, bd=0, relief="flat",
                     highlightbackground=BORDER, highlightthickness=1,
                     padx=1, pady=1)

    # Scrollbar style
    sb_style = {
        "bg": BG4,
        "troughcolor": BG2,
        "activebackground": ACCENT,
        "relief": "flat",
        "bd": 0,
        "width": 10,
        "highlightthickness": 0
    }

    sb_v = tk.Scrollbar(frame, orient="vertical", **sb_style)
    sb_h = tk.Scrollbar(frame, orient="horizontal", **sb_style)

    txt = tk.Text(
        frame,
        yscrollcommand=sb_v.set,
        xscrollcommand=sb_h.set,
        wrap="none",
        bg=BG2, fg=FG,
        insertbackground=ACCENT,
        insertwidth=2,
        selectbackground=ACCENT2,
        selectforeground="white",
        font=FONT_MONO,
        relief="flat", bd=0,
        padx=12, pady=10,
        **kw
    )
    sb_v.config(command=txt.yview)
    sb_h.config(command=txt.xview)
    sb_v.pack(side="right", fill="y", padx=(0, 1), pady=(1, 0))
    sb_h.pack(side="bottom", fill="x", padx=1, pady=(0, 1))
    txt.pack(fill="both", expand=True)

    # Effet de focus
    def on_focus_in(e):
        frame.config(highlightbackground=ACCENT, highlightthickness=1)

    def on_focus_out(e):
        frame.config(highlightbackground=BORDER, highlightthickness=1)

    txt.bind("<FocusIn>", on_focus_in)
    txt.bind("<FocusOut>", on_focus_out)

    return frame, txt


def syntax_highlight_json(text_widget, content):
    """Applique la coloration syntaxique JSON."""
    text_widget.delete("1.0", "end")
    text_widget.insert("1.0", content)

    # Configuration des tags
    text_widget.tag_configure("key", foreground=JSON_COLORS["key"])
    text_widget.tag_configure("string", foreground=JSON_COLORS["string"])
    text_widget.tag_configure("number", foreground=JSON_COLORS["number"])
    text_widget.tag_configure("boolean", foreground=JSON_COLORS["boolean"])
    text_widget.tag_configure("null", foreground=JSON_COLORS["null"])

    import re

    # Patterns pour la coloration syntaxique
    patterns = [
        (r'"[^"]*"\s*:', "key"),           # Clés JSON
        (r'"[^"]*"(?=\s*[,}\]])', "string"), # Strings (pas clés)
        (r'\b-?\d+\.?\d*\b', "number"),     # Nombres
        (r'\b(true|false)\b', "boolean"),    # Booléens
        (r'\bnull\b', "null"),               # Null
    ]

    for pattern, tag in patterns:
        for match in re.finditer(pattern, content):
            start = f"1.0+{match.start()}c"
            end = f"1.0+{match.end()}c"
            text_widget.tag_add(tag, start, end)

# ══════════════════════════════════════════════════════════════════
#  TAB 1 — API TESTER
# ══════════════════════════════════════════════════════════════════

class ApiTesterTab(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=BG)
        self._history = []
        self._build()

    def _build(self):
        # ── Top bar (method + URL + send) ─────────────────────────
        top = tk.Frame(self, bg=BG, pady=12, padx=12)
        top.pack(fill="x")

        label(top, "Méthode", fg=FG2, font=FONT_SMALL).pack(side="left")

        self.method_var = tk.StringVar(value="GET")
        method_menu = tk.OptionMenu(top, self.method_var, "GET", "POST",
                                    "PUT", "PATCH", "DELETE",
                                    command=self._update_method_color)
        method_menu.config(
            bg=METHOD_COLORS["GET"], fg="white", font=FONT_BOLD,
            relief="flat", bd=0, padx=12, pady=8,
            activebackground=_lighten(METHOD_COLORS["GET"], 20), activeforeground="white",
            highlightthickness=0, cursor="hand2"
        )
        method_menu["menu"].config(bg=BG3, fg=FG, font=FONT_BODY,
                                   activebackground=ACCENT, activeforeground="white",
                                   relief="flat", bd=0)
        self.method_btn = method_menu
        method_menu.pack(side="left", padx=(8, 12))

        self.url_var = tk.StringVar(value="https://jsonplaceholder.typicode.com/posts/1")
        url_entry = tk.Entry(
            top, textvariable=self.url_var,
            bg=BG3, fg=FG, insertbackground=ACCENT,
            font=FONT_MONO, relief="flat",
            highlightthickness=1, highlightbackground=BORDER, highlightcolor=ACCENT
        )
        url_entry.pack(side="left", fill="x", expand=True, ipady=10, padx=(0, 12))

        self.send_btn = styled_button(top, "▶  Envoyer",
                                      command=self._send, width=14,
                                      color=ACCENT, tooltip="Envoyer la requête HTTP")
        self.send_btn.pack(side="left")

        # ── Séparateur ────────────────────────────────────────────
        tk.Frame(self, bg=BORDER, height=1).pack(fill="x")

        # ── Panneau principal (gauche : requête / droite : réponse)
        paned = tk.PanedWindow(self, orient="horizontal",
                               bg=BORDER, sashwidth=3,
                               sashrelief="flat", bd=0)
        paned.pack(fill="both", expand=True, padx=12, pady=12)

        # ── Gauche : Paramètres de la requête ─────────────────────
        left = tk.Frame(paned, bg=BG)
        paned.add(left, minsize=350)

        nb = ttk.Notebook(left)
        nb.pack(fill="both", expand=True)
        self._style_notebook(nb)

        # Tab Headers
        headers_frame = tk.Frame(nb, bg=BG)
        nb.add(headers_frame, text=" Headers ")
        self._build_headers_tab(headers_frame)

        # Tab Body
        body_frame = tk.Frame(nb, bg=BG)
        nb.add(body_frame, text=" Body (JSON) ")
        _, self.body_text = scrolled_text(body_frame,
                                          height=12)
        self.body_text.master.pack(fill="both", expand=True, pady=(8, 0))
        self.body_text.insert("1.0", '{\n  "key": "value"\n}')

        # Tab Auth
        auth_frame = tk.Frame(nb, bg=BG)
        nb.add(auth_frame, text=" Auth ")
        self._build_auth_tab(auth_frame)

        # ── Droite : Réponse ──────────────────────────────────────
        right = tk.Frame(paned, bg=BG)
        paned.add(right, minsize=400)

        # Status bar
        status_bar = tk.Frame(right, bg=BG3, pady=6, padx=10)
        status_bar.pack(fill="x")

        self.status_label = tk.Label(
            status_bar, text="— Aucune requête", font=FONT_BOLD,
            fg=FG2, bg=BG3
        )
        self.status_label.pack(side="left")

        self.time_label = tk.Label(
            status_bar, text="", font=FONT_SMALL, fg=FG2, bg=BG3
        )
        self.time_label.pack(side="right")

        # Response tabs
        resp_nb = ttk.Notebook(right)
        resp_nb.pack(fill="both", expand=True, pady=(8, 0))
        self._style_notebook(resp_nb)

        body_resp = tk.Frame(resp_nb, bg=BG2)
        resp_nb.add(body_resp, text=" Réponse ")
        frame, self.response_text = scrolled_text(body_resp)
        frame.pack(fill="both", expand=True)

        headers_resp = tk.Frame(resp_nb, bg=BG2)
        resp_nb.add(headers_resp, text=" Headers reçus ")
        frame2, self.resp_headers_text = scrolled_text(headers_resp)
        frame2.pack(fill="both", expand=True)

        history_frame = tk.Frame(resp_nb, bg=BG2)
        resp_nb.add(history_frame, text=" Historique ")
        self._build_history_tab(history_frame)

        # Boutons de réponse
        btn_row = tk.Frame(right, bg=BG2, pady=8, padx=10)
        btn_row.pack(fill="x")
        styled_button(btn_row, "📋 Copier", command=self._copy_response,
                      color=BG3, width=10, tooltip="Copier la réponse dans le presse-papiers").pack(side="left", padx=(0, 6))
        styled_button(btn_row, "💾 Sauver", command=self._save_response,
                      color=BG3, width=10, tooltip="Sauvegarder la réponse dans un fichier").pack(side="left", padx=(0, 6))
        styled_button(btn_row, "🗑 Effacer", command=self._clear,
                      color=DANGER, width=10, tooltip="Effacer la réponse").pack(side="right")

    # ── Headers Tab ───────────────────────────────────────────────
    def _build_headers_tab(self, parent):
        self.header_rows = []
        header_list = tk.Frame(parent, bg=BG)
        header_list.pack(fill="both", expand=True, pady=6)

        # Colonnes avec style moderne
        cols = tk.Frame(header_list, bg=BG)
        cols.pack(fill="x", pady=(0, 8))

        tk.Label(cols, text="Clé", fg=FG, font=FONT_BOLD,
                 bg=BG, width=22, anchor="w").pack(side="left", padx=(0, 4))
        tk.Label(cols, text="Valeur", fg=FG, font=FONT_BOLD,
                 bg=BG, anchor="w").pack(side="left", expand=True, fill="x")

        self.headers_container = tk.Frame(header_list, bg=BG)
        self.headers_container.pack(fill="both", expand=True)

        # Headers par défaut
        defaults = [
            ("Content-Type", "application/json"),
            ("Accept", "application/json"),
        ]
        for k, v in defaults:
            self._add_header_row(k, v)

        add_btn = styled_button(parent, "+ Ajouter header",
                      command=self._add_header_row,
                      color=BG3, width=18, tooltip="Ajouter un nouveau header HTTP")
        add_btn.pack(anchor="w", pady=(8, 0))

    def _add_header_row(self, key="", value=""):
        row = tk.Frame(self.headers_container, bg=BG)
        row.pack(fill="x", pady=3)

        key_var = tk.StringVar(value=key)
        val_var = tk.StringVar(value=value)

        k_entry = tk.Entry(row, textvariable=key_var, bg=BG3, fg=FG,
                           font=FONT_MONO, relief="flat", width=22, bd=0,
                           insertbackground=ACCENT, highlightthickness=1,
                           highlightbackground=BORDER, highlightcolor=ACCENT)
        k_entry.pack(side="left", ipady=6, padx=(0, 8))

        v_entry = tk.Entry(row, textvariable=val_var, bg=BG3, fg=FG,
                           font=FONT_MONO, relief="flat", bd=0,
                           insertbackground=ACCENT, highlightthickness=1,
                           highlightbackground=BORDER, highlightcolor=ACCENT)
        v_entry.pack(side="left", fill="x", expand=True, ipady=6)

        def remove():
            row.destroy()
            self.header_rows.remove((key_var, val_var))

        del_btn = tk.Label(row, text="✕", bg=BG, fg=FG3, font=FONT_SMALL,
                  cursor="hand2")
        del_btn.pack(side="left", padx=8)
        del_btn.bind("<Button-1>", lambda e: remove())
        del_btn.bind("<Enter>", lambda e: del_btn.config(fg=DANGER))
        del_btn.bind("<Leave>", lambda e: del_btn.config(fg=FG3))

        self.header_rows.append((key_var, val_var))

    # ── Auth Tab ──────────────────────────────────────────────────
    def _build_auth_tab(self, parent):
        self.auth_type = tk.StringVar(value="None")
        types = ["None", "Bearer Token", "Basic Auth", "API Key"]

        auth_container = tk.Frame(parent, bg=BG, pady=8)
        auth_container.pack(fill="x")

        for t in types:
            rb = tk.Radiobutton(
                auth_container, text=t, variable=self.auth_type,
                value=t, bg=BG, fg=FG, selectcolor=ACCENT,
                activebackground=BG2, activeforeground=ACCENT,
                font=FONT_BODY, command=self._update_auth_ui,
                indicatoron=0,  # Bouton style "pill"
                width=16, padx=8, pady=6
            )
            rb.pack(fill="x", pady=3)

        self.auth_frame = tk.Frame(parent, bg=BG)
        self.auth_frame.pack(fill="x", pady=8)
        self.auth_entries = {}

    def _update_auth_ui(self):
        for w in self.auth_frame.winfo_children():
            w.destroy()
        t = self.auth_type.get()
        fields = {
            "Bearer Token": [("Token", "token")],
            "Basic Auth":   [("Username", "user"), ("Password", "pass")],
            "API Key":      [("Header", "header"), ("Valeur", "value")],
        }
        for lbl, key in fields.get(t, []):
            tk.Label(self.auth_frame, text=lbl, fg=FG, font=FONT_BOLD,
                     bg=BG, pady=(8, 4)).pack(anchor="w")
            var = tk.StringVar()
            entry = tk.Entry(self.auth_frame, textvariable=var, bg=BG3, fg=FG,
                     font=FONT_MONO, relief="flat",
                     insertbackground=ACCENT, highlightthickness=1,
                     highlightbackground=BORDER, highlightcolor=ACCENT)
            entry.pack(fill="x", ipady=6, pady=(0, 8))
            if key == "pass":
                entry.config(show="•")
            self.auth_entries[key] = var

    # ── History Tab ───────────────────────────────────────────────
    def _build_history_tab(self, parent):
        self.history_box = tk.Listbox(
            parent, bg=BG3, fg=FG, font=FONT_MONO,
            selectbackground=ACCENT2, relief="flat",
            borderwidth=0, activestyle="none"
        )
        self.history_box.pack(fill="both", expand=True)
        self.history_box.bind("<Double-Button-1>", self._load_history)

    def _update_method_color(self, method):
        color = METHOD_COLORS.get(method, ACCENT)
        self.method_btn.config(bg=color, activebackground=color)

    # ── Envoi de requête ──────────────────────────────────────────
    def _send(self):
        if not HAS_REQUESTS:
            messagebox.showerror("Erreur",
                "requests n'est pas installé.\n\npip install requests")
            return

        url = self.url_var.get().strip()
        if not url:
            messagebox.showwarning("URL manquante", "Entrez une URL.")
            return

        self.send_btn.config(text="⏳ Envoi…", state="disabled")
        self.status_label.config(text="Chargement…", fg=FG2)
        threading.Thread(target=self._do_request, args=(url,),
                         daemon=True).start()

    def _do_request(self, url):
        method  = self.method_var.get()
        headers = {k.get(): v.get()
                   for k, v in self.header_rows
                   if k.get().strip()}

        # Auth
        auth_type = self.auth_type.get()
        if auth_type == "Bearer Token" and "token" in self.auth_entries:
            headers["Authorization"] = (
                f"Bearer {self.auth_entries['token'].get()}")
        elif auth_type == "Basic Auth":
            import base64
            u = self.auth_entries.get("user", tk.StringVar()).get()
            p = self.auth_entries.get("pass", tk.StringVar()).get()
            creds = base64.b64encode(f"{u}:{p}".encode()).decode()
            headers["Authorization"] = f"Basic {creds}"
        elif auth_type == "API Key":
            h = self.auth_entries.get("header", tk.StringVar()).get()
            v = self.auth_entries.get("value", tk.StringVar()).get()
            if h:
                headers[h] = v

        body = None
        if method in ("POST", "PUT", "PATCH"):
            body = self.body_text.get("1.0", "end").strip() or None

        t0 = datetime.now()
        try:
            resp = requests.request(
                method, url, headers=headers,
                data=body.encode() if body else None,
                timeout=15
            )
            elapsed = (datetime.now() - t0).total_seconds()
            self.after(0, self._show_response, resp, elapsed)
        except Exception as e:
            self.after(0, self._show_error, str(e))

    def _show_response(self, resp, elapsed):
        self.send_btn.config(text="▶  Envoyer", state="normal")
        code   = resp.status_code
        color  = SUCCESS if code < 300 else (WARNING if code < 500 else DANGER)
        reason = resp.reason or ""

        self.status_label.config(
            text=f"  {code}  {reason}", fg=color)

        # Formatage amélioré du temps et taille
        time_str = f"{elapsed*1000:.0f} ms" if elapsed < 1 else f"{elapsed:.2f} s"
        size_kb = len(resp.content) / 1024
        size_str = f"{size_kb:.1f} Ko" if size_kb >= 1 else f"{len(resp.content)} o"
        self.time_label.config(text=f"⏱ {time_str}  •  📦 {size_str}")

        # Body avec syntax highlighting
        self.response_text.config(state="normal")
        self.response_text.delete("1.0", "end")
        try:
            body_json = resp.json()
            body = json.dumps(body_json, indent=2, ensure_ascii=False)
            syntax_highlight_json(self.response_text, body)
        except Exception:
            body = resp.text
            self.response_text.insert("1.0", body)
        self.response_text.config(state="disabled")

        # Response headers
        self.resp_headers_text.config(state="normal")
        self.resp_headers_text.delete("1.0", "end")
        hdrs = "\n".join(f"{k}: {v}" for k, v in resp.headers.items())
        self.resp_headers_text.insert("1.0", hdrs)
        self.resp_headers_text.config(state="disabled")

        # History
        entry = f"[{self.method_var.get():6}] {code}  {self.url_var.get()}"
        self._history.append(entry)
        self.history_box.insert("end", entry)
        self.history_box.see("end")

    def _show_error(self, msg):
        self.send_btn.config(text="▶  Envoyer", state="normal")
        self.status_label.config(text=f"Erreur : {msg}", fg=DANGER)
        self.response_text.config(state="normal")
        self.response_text.delete("1.0", "end")
        self.response_text.insert("1.0", msg)
        self.response_text.config(state="disabled")

    def _load_history(self, event):
        sel = self.history_box.curselection()
        if sel:
            entry = self._history[sel[0]]
            # Extraire l'URL
            parts = entry.split("  ", 2)
            if len(parts) >= 3:
                self.url_var.set(parts[2])

    def _copy_response(self):
        text = self.response_text.get("1.0", "end")
        self.clipboard_clear()
        self.clipboard_append(text)

    def _save_response(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON", "*.json"), ("Texte", "*.txt"),
                       ("Tous", "*.*")]
        )
        if path:
            with open(path, "w", encoding="utf-8") as f:
                f.write(self.response_text.get("1.0", "end"))

    def _clear(self):
        self.response_text.config(state="normal")
        self.response_text.delete("1.0", "end")
        self.response_text.config(state="disabled")
        self.status_label.config(text="— Aucune requête", fg=FG2)
        self.time_label.config(text="")

    def _style_notebook(self, nb):
        # Le style est maintenant configuré dans DevKitPro._build()
        pass


# ══════════════════════════════════════════════════════════════════
#  TAB 2 — CSV CLEANER / VIEWER
# ══════════════════════════════════════════════════════════════════

class CsvTab(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=BG)
        self._data   = []  # list of rows (dicts)
        self._cols   = []
        self._filtered = []
        self._sort_col = None
        self._sort_asc = True
        self._build()

    def _build(self):
        # ── Toolbar ───────────────────────────────────────────────
        bar = tk.Frame(self, bg=BG, pady=10, padx=12)
        bar.pack(fill="x")

        styled_button(bar, "📂 Ouvrir CSV",
                      command=self._open, color=ACCENT, width=14, tooltip="Ouvrir un fichier CSV").pack(
            side="left", padx=(0, 8))
        styled_button(bar, "💾 Sauver CSV",
                      command=self._save, color=BG3, width=14, tooltip="Sauvegarder le CSV modifié").pack(
            side="left", padx=(0, 20))

        label(bar, "Recherche :", fg=FG, font=FONT_BOLD).pack(
            side="left", padx=(0, 8))
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *_: self._apply_filter())
        tk.Entry(bar, textvariable=self.search_var,
                 bg=BG3, fg=FG, font=FONT_MONO,
                 insertbackground=ACCENT, relief="flat", width=24,
                 highlightthickness=1, highlightbackground=BORDER, highlightcolor=ACCENT).pack(
            side="left", ipady=8, padx=(0, 16))

        label(bar, "Colonne :", fg=FG, font=FONT_BOLD).pack(
            side="left", padx=(0, 8))
        self.filter_col_var = tk.StringVar(value="— Toutes —")
        self.col_menu = tk.OptionMenu(bar, self.filter_col_var,
                                      "— Toutes —")
        self.col_menu.config(bg=BG3, fg=FG, relief="flat", bd=0,
                              font=FONT_BODY, activebackground=ACCENT2,
                              highlightthickness=0, cursor="hand2", padx=10)
        self.col_menu["menu"].config(bg=BG3, fg=FG, font=FONT_BODY,
                                       activebackground=ACCENT, activeforeground="white")
        self.col_menu.pack(side="left", padx=(0, 16))

        # Stats
        self.stats_label = tk.Label(bar, text="",
                                    fg=FG2, font=FONT_SMALL, bg=BG2)
        self.stats_label.pack(side="right")

        # ── Séparateur ────────────────────────────────────────────
        tk.Frame(self, bg=BORDER, height=1).pack(fill="x")

        # ── Treeview ──────────────────────────────────────────────
        tv_frame = tk.Frame(self, bg=BG)
        tv_frame.pack(fill="both", expand=True, padx=12, pady=12)

        style = ttk.Style()
        style.theme_use("default")
        style.configure("CSV.Treeview",
                         background=BG2, foreground=FG,
                         rowheight=28, fieldbackground=BG2,
                         borderwidth=0, font=FONT_MONO)
        style.configure("CSV.Treeview.Heading",
                         background=BG3, foreground=ACCENT,
                         font=FONT_BOLD, relief="flat", borderwidth=0)
        style.map("CSV.Treeview",
                  background=[("selected", ACCENT2), ("!selected", BG2)],
                  foreground=[("selected", "white"), ("!selected", FG)])

        sb_y = tk.Scrollbar(tv_frame, orient="vertical",
                             bg=BG3, troughcolor=BG2)
        sb_x = tk.Scrollbar(tv_frame, orient="horizontal",
                             bg=BG3, troughcolor=BG2)
        sb_y.pack(side="right", fill="y")
        sb_x.pack(side="bottom", fill="x")

        self.tree = ttk.Treeview(tv_frame, style="CSV.Treeview",
                                  yscrollcommand=sb_y.set,
                                  xscrollcommand=sb_x.set,
                                  selectmode="extended")
        self.tree.pack(fill="both", expand=True)
        sb_y.config(command=self.tree.yview)
        sb_x.config(command=self.tree.xview)

        self.tree.bind("<Button-1>", self._on_header_click)

        # ── Bottom bar ────────────────────────────────────────────
        bot = tk.Frame(self, bg=BG2, pady=10, padx=12)
        bot.pack(fill="x")

        styled_button(bot, "🗑 Suppr. ligne",
                      command=self._delete_rows, color=DANGER,
                      width=16, tooltip="Supprimer les lignes sélectionnées").pack(side="left", padx=(0, 8))
        styled_button(bot, "🧹 Suppr. doublons",
                      command=self._remove_duplicates, color=WARNING,
                      width=18, tooltip="Supprimer les lignes en double").pack(side="left", padx=(0, 8))
        styled_button(bot, "↕ Trier ↑↓",
                      command=self._toggle_sort, color=BG3,
                      width=12, tooltip="Trier par la première colonne").pack(side="left")

        self.info_label = tk.Label(
            bot, text="Aucun fichier chargé",
            fg=FG2, font=FONT_SMALL, bg=BG2
        )
        self.info_label.pack(side="right")

    # ── Actions ───────────────────────────────────────────────────
    def _open(self):
        path = filedialog.askopenfilename(
            filetypes=[("CSV", "*.csv"), ("Tous", "*.*")])
        if not path:
            return
        try:
            with open(path, newline="", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                self._cols = reader.fieldnames or []
                self._data = [dict(row) for row in reader]
            self._filtered = list(self._data)
            self._build_tree()
            self._update_col_menu()
            name = os.path.basename(path)
            self.info_label.config(
                text=f"{name}  •  {len(self._data)} lignes")
            self._update_stats()
        except Exception as e:
            messagebox.showerror("Erreur CSV", str(e))

    def _build_tree(self):
        self.tree.delete(*self.tree.get_children())
        self.tree["columns"] = self._cols
        self.tree["show"] = "headings"
        for col in self._cols:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=140, minwidth=80, stretch=True, anchor="w")
        for i, row in enumerate(self._filtered):
            tag = "odd" if i % 2 else "even"
            values = [row.get(c, "") for c in self._cols]
            # Tronquer les valeurs très longues
            values = [str(v)[:100] + "..." if len(str(v)) > 100 else v for v in values]
            self.tree.insert("", "end", values=values, tags=(tag,))
        self.tree.tag_configure("odd",  background=BG2)
        self.tree.tag_configure("even", background=BG4)

    def _update_col_menu(self):
        menu = self.col_menu["menu"]
        menu.delete(0, "end")
        options = ["— Toutes —"] + list(self._cols)
        for opt in options:
            menu.add_command(label=opt,
                             command=lambda o=opt: (
                                 self.filter_col_var.set(o),
                                 self._apply_filter()
                             ))
        self.filter_col_var.set("— Toutes —")

    def _apply_filter(self):
        q   = self.search_var.get().lower()
        col = self.filter_col_var.get()
        if not q:
            self._filtered = list(self._data)
        else:
            cols = self._cols if col == "— Toutes —" else [col]
            self._filtered = [
                row for row in self._data
                if any(q in str(row.get(c, "")).lower() for c in cols)
            ]
        self._build_tree()
        self._update_stats()

    def _update_stats(self):
        total = len(self._data)
        shown = len(self._filtered)
        self.stats_label.config(
            text=f"{shown} / {total} lignes  •  {len(self._cols)} colonnes")

    def _delete_rows(self):
        selected = self.tree.selection()
        if not selected:
            return
        # Identifier les valeurs et les retirer
        to_remove = set()
        for iid in selected:
            vals = self.tree.item(iid, "values")
            for i, row in enumerate(self._filtered):
                if tuple(str(row.get(c, "")) for c in self._cols) == tuple(vals):
                    to_remove.add(i)
        self._filtered = [r for i, r in enumerate(self._filtered)
                          if i not in to_remove]
        self._data = [r for r in self._data if r in self._filtered]
        self._build_tree()
        self._update_stats()

    def _remove_duplicates(self):
        before = len(self._data)
        seen = set()
        unique = []
        for row in self._data:
            key = tuple(row.get(c, "") for c in self._cols)
            if key not in seen:
                seen.add(key)
                unique.append(row)
        self._data = unique
        self._filtered = list(unique)
        self._build_tree()
        self._update_stats()
        removed = before - len(self._data)
        messagebox.showinfo("Doublons supprimés",
                            f"{removed} doublon(s) supprimé(s).")

    def _on_header_click(self, event):
        region = self.tree.identify("region", event.x, event.y)
        if region == "heading":
            col_id = self.tree.identify_column(event.x)
            idx = int(col_id.replace("#", "")) - 1
            if 0 <= idx < len(self._cols):
                col = self._cols[idx]
                if self._sort_col == col:
                    self._sort_asc = not self._sort_asc
                else:
                    self._sort_col = col
                    self._sort_asc = True
                self._filtered.sort(
                    key=lambda r: str(r.get(col, "")),
                    reverse=not self._sort_asc
                )
                self._build_tree()
                arrow = " ↑" if self._sort_asc else " ↓"
                for c in self._cols:
                    lbl = c + (arrow if c == col else "")
                    self.tree.heading(c, text=lbl)

    def _toggle_sort(self):
        if not self._cols:
            return
        col = self._cols[0]
        self._sort_asc = not self._sort_asc
        self._filtered.sort(key=lambda r: str(r.get(col, "")),
                             reverse=not self._sort_asc)
        self._build_tree()

    def _save(self):
        if not self._cols:
            messagebox.showwarning("Aucune donnée", "Chargez un CSV d'abord.")
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV", "*.csv"), ("Tous", "*.*")]
        )
        if path:
            with open(path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=self._cols)
                writer.writeheader()
                writer.writerows(self._filtered)
            messagebox.showinfo("Sauvegardé", f"Fichier sauvegardé : {path}")


# ══════════════════════════════════════════════════════════════════
#  TAB 3 — JSON FORMATTER
# ══════════════════════════════════════════════════════════════════

class JsonTab(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=BG)
        self._build()

    def _build(self):
        # ── Toolbar ───────────────────────────────────────────────
        bar = tk.Frame(self, bg=BG, pady=12, padx=12)
        bar.pack(fill="x")

        # Groupe d'actions principales
        actions = tk.Frame(bar, bg=BG)
        actions.pack(side="left")

        styled_button(actions, "✨ Beautify",
                      command=self._beautify, color=ACCENT,
                      width=12, tooltip="Formater le JSON avec indentation").pack(side="left", padx=(0, 8))
        styled_button(actions, "📦 Minify",
                      command=self._minify, color=ACCENT2,
                      width=12, tooltip="Minifier le JSON (sans espaces)").pack(side="left", padx=(0, 8))
        styled_button(actions, "✅ Valider",
                      command=self._validate, color=SUCCESS,
                      width=12, tooltip="Valider la syntaxe JSON").pack(side="left", padx=(0, 20))

        # Groupe fichier
        file_grp = tk.Frame(bar, bg=BG)
        file_grp.pack(side="left")

        styled_button(file_grp, "📂 Ouvrir",
                      command=self._open, color=BG3,
                      width=10, tooltip="Ouvrir un fichier JSON").pack(side="left", padx=(0, 8))
        styled_button(file_grp, "💾 Sauver",
                      command=self._save, color=BG3,
                      width=10, tooltip="Sauvegarder le résultat").pack(side="left", padx=(0, 24))

        # Options
        opts = tk.Frame(bar, bg=BG)
        opts.pack(side="left")

        label(opts, "Indent :", fg=FG, font=FONT_BOLD).pack(side="left", padx=(0, 8))
        self.indent_var = tk.IntVar(value=2)
        self.indent_var.trace_add("write", self._update_indent_buttons)
        self.indent_frame = tk.Frame(opts, bg=BG3, padx=2, pady=2)
        self.indent_frame.pack(side="left")
        self.indent_buttons = {}
        for n in [2, 4]:
            btn = tk.Radiobutton(
                self.indent_frame, text=str(n), variable=self.indent_var, value=n,
                bg=BG3, fg=FG, selectcolor=ACCENT,
                activebackground=ACCENT, activeforeground="white",
                font=FONT_BODY, indicatoron=0, width=4
            )
            btn.pack(side="left", padx=1)
            self.indent_buttons[n] = btn
        self._update_indent_buttons()

    def _update_indent_buttons(self, *args):
        """Met à jour les styles des boutons d'indentation."""
        current = self.indent_var.get()
        for n, btn in self.indent_buttons.items():
            if n == current:
                btn.config(bg=ACCENT, fg="white", selectcolor=ACCENT)
            else:
                btn.config(bg=BG3, fg=FG, selectcolor=ACCENT)

        # ── Panneau splitté input / output ───────────────────────
        tk.Frame(self, bg=BORDER, height=1).pack(fill="x")

        paned = tk.PanedWindow(self, orient="horizontal",
                               bg=BORDER, sashwidth=3, bd=0)
        paned.pack(fill="both", expand=True, padx=12, pady=12)

        # Input
        left = tk.Frame(paned, bg=BG2)
        paned.add(left, minsize=300)

        input_header = tk.Frame(left, bg=BG2)
        input_header.pack(fill="x", pady=(0, 6))
        tk.Label(input_header, text="📥 Entrée", fg=ACCENT, font=FONT_BOLD,
                 bg=BG2).pack(side="left")
        tk.Label(input_header, text="JSON brut ou minifié", fg=FG3, font=FONT_SMALL,
                 bg=BG2).pack(side="left", padx=(8, 0))

        frame_in, self.input_text = scrolled_text(left)
        frame_in.pack(fill="both", expand=True)

        btn_row_in = tk.Frame(left, bg=BG2, pady=8)
        btn_row_in.pack(fill="x")
        styled_button(btn_row_in, "📋 Coller",
                      command=self._paste, color=BG3,
                      width=10, tooltip="Coller depuis le presse-papiers").pack(side="left", padx=(0, 8))
        styled_button(btn_row_in, "🗑 Vider",
                      command=lambda: self.input_text.delete("1.0", "end"),
                      color=DANGER, width=10, tooltip="Vider le contenu").pack(side="left")

        # Output
        right = tk.Frame(paned, bg=BG2)
        paned.add(right, minsize=300)

        output_header = tk.Frame(right, bg=BG2)
        output_header.pack(fill="x", pady=(0, 6))
        tk.Label(output_header, text="📤 Sortie", fg=SUCCESS, font=FONT_BOLD,
                 bg=BG2).pack(side="left")
        tk.Label(output_header, text="Résultat formaté", fg=FG3, font=FONT_SMALL,
                 bg=BG2).pack(side="left", padx=(8, 0))

        frame_out, self.output_text = scrolled_text(right)
        frame_out.pack(fill="both", expand=True)

        btn_row_out = tk.Frame(right, bg=BG2, pady=8)
        btn_row_out.pack(fill="x")
        styled_button(btn_row_out, "📋 Copier",
                      command=self._copy_output, color=BG3,
                      width=10, tooltip="Copier le résultat").pack(side="left", padx=(0, 8))
        styled_button(btn_row_out, "→ Input",
                      command=self._to_input, color=ACCENT,
                      width=10, tooltip="Copier vers l'entrée").pack(side="left")

        # Status avec style amélioré
        self.status_frame = tk.Frame(self, bg=BG2, pady=8)
        self.status_frame.pack(fill="x", padx=12, pady=(0, 8))

        self.status = tk.Label(self.status_frame, text="Prêt", fg=FG2,
                               font=FONT_SMALL, bg=BG2)
        self.status.pack(side="left")

        # Exemple par défaut avec meilleur format
        sample = '''{
  "name": "NdarMarket",
  "type": "marketplace",
  "active": true,
  "tags": ["senegal", "tech"],
  "stats": {
    "users": 15000,
    "rating": 4.8
  }
}'''
        self.input_text.insert("1.0", sample)

    # ── Actions ───────────────────────────────────────────────────
    def _get_input(self):
        return self.input_text.get("1.0", "end").strip()

    def _set_output(self, text):
        self.output_text.delete("1.0", "end")
        # Tenter d'appliquer la coloration syntaxique si c'est du JSON
        try:
            json.loads(text)
            syntax_highlight_json(self.output_text, text)
        except:
            self.output_text.insert("1.0", text)

    def _beautify(self):
        try:
            data = json.loads(self._get_input())
            result = json.dumps(data, indent=self.indent_var.get(),
                                ensure_ascii=False)
            syntax_highlight_json(self.output_text, result)
            lines = result.count("\n") + 1
            self.status.config(
                text=f"✅ Formaté — {lines} lignes", fg=SUCCESS)
        except json.JSONDecodeError as e:
            self._show_error(str(e))

    def _minify(self):
        try:
            data = json.loads(self._get_input())
            result = json.dumps(data, separators=(",", ":"),
                                ensure_ascii=False)
            self._set_output(result)
            self.status.config(
                text=f"✅ Minifié — {len(result)} caractères", fg=SUCCESS)
        except json.JSONDecodeError as e:
            self._show_error(str(e))

    def _validate(self):
        try:
            data = json.loads(self._get_input())
            keys = self._count_keys(data)
            self.status.config(
                text=f"✅ JSON valide — {keys} clés au total", fg=SUCCESS)
        except json.JSONDecodeError as e:
            self._show_error(str(e))

    def _count_keys(self, obj, count=0):
        if isinstance(obj, dict):
            count += len(obj)
            for v in obj.values():
                count = self._count_keys(v, count)
        elif isinstance(obj, list):
            for item in obj:
                count = self._count_keys(item, count)
        return count

    def _show_error(self, msg):
        self._set_output(f"❌ Erreur JSON :\n{msg}")
        self.status.config(text=f"❌ {msg}", fg=DANGER)

    def _open(self):
        path = filedialog.askopenfilename(
            filetypes=[("JSON", "*.json"), ("Tous", "*.*")])
        if path:
            with open(path, encoding="utf-8") as f:
                self.input_text.delete("1.0", "end")
                self.input_text.insert("1.0", f.read())

    def _save(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON", "*.json"), ("Texte", "*.txt")]
        )
        if path:
            content = self.output_text.get("1.0", "end")
            if not content.strip():
                content = self._get_input()
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)

    def _paste(self):
        try:
            text = self.clipboard_get()
            self.input_text.delete("1.0", "end")
            self.input_text.insert("1.0", text)
        except tk.TclError:
            pass

    def _copy_output(self):
        text = self.output_text.get("1.0", "end")
        self.clipboard_clear()
        self.clipboard_append(text)
        self.status.config(text="📋 Copié dans le presse-papiers",
                           fg=SUCCESS)

    def _to_input(self):
        text = self.output_text.get("1.0", "end")
        self.input_text.delete("1.0", "end")
        self.input_text.insert("1.0", text)
        self.output_text.delete("1.0", "end")


# ══════════════════════════════════════════════════════════════════
#  FENÊTRE PRINCIPALE
# ══════════════════════════════════════════════════════════════════

class DevKitPro(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("DevKit Pro")
        self.geometry("1200x780")
        self.minsize(900, 600)
        self.configure(bg=BG)
        self._build()

    def _build(self):
        # ── Header avec gradient effect ────────────────────────────
        header = tk.Frame(self, bg=ACCENT2, pady=0)
        header.pack(fill="x")

        title_frame = tk.Frame(header, bg=ACCENT2, padx=20, pady=16)
        title_frame.pack(side="left", fill="x", expand=True)

        # Logo + Titre
        logo_frame = tk.Frame(title_frame, bg=ACCENT2)
        logo_frame.pack(side="left")

        tk.Label(logo_frame, text="⚡",
                 font=("Segoe UI", 20),
                 fg=SUCCESS, bg=ACCENT2).pack(side="left")

        title_text = tk.Frame(logo_frame, bg=ACCENT2)
        title_text.pack(side="left", padx=(8, 0))

        tk.Label(title_text, text="DevKit Pro",
                 font=FONT_TITLE,
                 fg="white", bg=ACCENT2).pack(anchor="w")
        tk.Label(title_text,
                 text="API Tester  •  CSV Cleaner  •  JSON Formatter",
                 font=FONT_SMALL, fg=FG, bg=ACCENT2).pack(anchor="w")

        # Version badge modernisé
        version_frame = tk.Frame(header, bg=ACCENT, padx=2, pady=2)
        version_frame.pack(side="right", padx=20)

        tk.Label(version_frame, text="v1.1", font=FONT_SMALL,
                 fg=ACCENT, bg=BG2, padx=8, pady=3).pack()

        tk.Frame(self, bg=BORDER, height=1).pack(fill="x")

        # ── Notebook principal avec style amélioré ────────────────
        style = ttk.Style()
        style.theme_use("default")

        # Configuration du notebook principal
        style.configure("Main.TNotebook",
                         background=BG, borderwidth=0, tabmargins=[0, 0, 0, 0])
        style.configure("Main.TNotebook.Tab",
                         background=BG2, foreground=FG2,
                         padding=[24, 12], font=FONT_BOLD, borderwidth=0)
        style.map("Main.TNotebook.Tab",
                  background=[("selected", BG)],
                  foreground=[("selected", ACCENT)],
                  expand=[("selected", [0, 0, 0, 0])])

        # Configuration du notebook intérieur (sous-onglets)
        style.configure("TNotebook",
                         background=BG2, borderwidth=0, tabmargins=0)
        style.configure("TNotebook.Tab",
                         background=BG3, foreground=FG2,
                         padding=[16, 8], font=FONT_BODY, borderwidth=0)
        style.map("TNotebook.Tab",
                  background=[("selected", BG2)],
                  foreground=[("selected", ACCENT)])

        nb = ttk.Notebook(self, style="Main.TNotebook")
        nb.pack(fill="both", expand=True, padx=1, pady=(1, 0))

        self.api_tab  = ApiTesterTab(nb)
        self.csv_tab  = CsvTab(nb)
        self.json_tab = JsonTab(nb)

        nb.add(self.api_tab,  text="  🌐  API Tester  ")
        nb.add(self.csv_tab,  text="  📊  CSV Cleaner  ")
        nb.add(self.json_tab, text="  { }  JSON Formatter  ")

        # ── Status bar ────────────────────────────────────────────
        status_bar = tk.Frame(self, bg=BG2, pady=6)
        status_bar.pack(fill="x", side="bottom")

        # Section gauche
        left_status = tk.Frame(status_bar, bg=BG2)
        left_status.pack(side="left", padx=16)

        tk.Label(left_status,
                 text="DevKit Pro",
                 fg=ACCENT, font=FONT_BOLD, bg=BG2).pack(side="left")
        tk.Label(left_status,
                 text=" • Python + Tkinter",
                 fg=FG2, font=FONT_SMALL, bg=BG2).pack(side="left")

        # Section droite
        right_status = tk.Frame(status_bar, bg=BG2)
        right_status.pack(side="right", padx=16)

        req_status = "✅ requests OK" if HAS_REQUESTS else "⚠️  pip install requests"
        req_color = SUCCESS if HAS_REQUESTS else WARNING
        tk.Label(right_status, text=req_status,
                 fg=req_color, font=FONT_SMALL, bg=BG2).pack(side="right")


# ══════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    app = DevKitPro()
    app.mainloop()
