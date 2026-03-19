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

BG       = "#1e1e1e"           # Fond principal sombre (VS Code)
BG2      = "#252526"           # Fond de panneau / secondaire
BG3      = "#333333"           # Fond d'input / item
ACCENT   = "#007acc"           # Accent bleu professionnel
ACCENT2  = "#0e639c"           # Accent secondaire
SUCCESS  = "#89d185"           # Vert doux (Succès)
WARNING  = "#d7ba7d"           # Jaune doux (Avertissement)
DANGER   = "#f48771"           # Rouge doux (Erreur)
FG       = "#cccccc"           # Texte principal gris clair
FG2      = "#858585"           # Texte secondaire
BORDER   = "#3e3e42"           # Bordure subtile

FONT_MONO  = ("Consolas", 10)
FONT_BODY  = ("Segoe UI", 10)
FONT_BOLD  = ("Segoe UI", 10, "bold")
FONT_TITLE = ("Segoe UI", 12, "bold")
FONT_SMALL = ("Segoe UI", 9)

METHOD_COLORS = {
    "GET":    "#34a853",       # Vert
    "POST":   "#1a73e8",       # Bleu
    "PUT":    "#fbbc04",       # Jaune
    "PATCH":  "#8764d1",       # Violet
    "DELETE": "#d33b27",       # Rouge
}

# ══════════════════════════════════════════════════════════════════
#  HELPERS UI
# ══════════════════════════════════════════════════════════════════

def styled_button(parent, text, command=None, color=ACCENT, width=12, **kw):
    btn = tk.Button(
        parent, text=text, command=command,
        bg=color, fg="white", relief="flat",
        font=FONT_BOLD, padx=12, pady=8,
        activebackground=_lighten(color), activeforeground="white",
        cursor="hand2", bd=0, width=width, highlightthickness=0, **kw
    )
    btn.bind("<Enter>", lambda e: btn.config(bg=_lighten(color), relief="flat"))
    btn.bind("<Leave>", lambda e: btn.config(bg=color, relief="flat"))
    return btn

def _lighten(hex_color):
    """Éclaircit légèrement une couleur hex."""
    hex_color = hex_color.lstrip("#")
    r, g, b = (int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    r = min(255, r + 30)
    g = min(255, g + 30)
    b = min(255, b + 30)
    return f"#{r:02x}{g:02x}{b:02x}"

def label(parent, text, font=FONT_BODY, fg=FG, **kw):
    return tk.Label(parent, text=text, font=font, fg=fg, bg=BG, **kw)

def separator(parent, orient="horizontal"):
    return ttk.Separator(parent, orient=orient)

def scrolled_text(parent, **kw):
    frame = tk.Frame(parent, bg=BG, bd=0, relief="flat",
                     highlightbackground=BORDER, highlightthickness=1)
    sb_v = tk.Scrollbar(frame, orient="vertical", bg=BG2,
                         troughcolor=BG, activebackground=ACCENT)
    sb_h = tk.Scrollbar(frame, orient="horizontal", bg=BG2,
                         troughcolor=BG, activebackground=ACCENT)
    txt = tk.Text(
        frame,
        yscrollcommand=sb_v.set,
        xscrollcommand=sb_h.set,
        wrap="none",
        bg=BG, fg=FG,
        insertbackground=ACCENT,
        selectbackground=ACCENT,
        selectforeground="white",
        font=FONT_MONO,
        relief="flat", bd=0,
        padx=10, pady=8,
        **kw
    )
    sb_v.config(command=txt.yview)
    sb_h.config(command=txt.xview)
    sb_v.pack(side="right", fill="y")
    sb_h.pack(side="bottom", fill="x")
    txt.pack(fill="both", expand=True)
    return frame, txt

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
            relief="flat", bd=0, padx=8, pady=5,
            activebackground=BG3, activeforeground=FG,
            highlightthickness=0, cursor="hand2"
        )
        method_menu["menu"].config(bg=BG3, fg=FG, font=FONT_BODY,
                                   activebackground=ACCENT)
        self.method_btn = method_menu
        method_menu.pack(side="left", padx=(4, 8))

        self.url_var = tk.StringVar(value="https://jsonplaceholder.typicode.com/posts/1")
        url_entry = tk.Entry(
            top, textvariable=self.url_var,
            bg=BG2, fg=FG, insertbackground=ACCENT,
            font=FONT_MONO, relief="solid", bd=1
        )
        url_entry.pack(side="left", fill="x", expand=True, ipady=8,
                       padx=(0, 8))

        self.send_btn = styled_button(top, "▶  Envoyer",
                                      command=self._send, width=14,
                                      color=ACCENT)
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
        btn_row = tk.Frame(right, bg=BG2, pady=6)
        btn_row.pack(fill="x")
        styled_button(btn_row, "📋 Copier", command=self._copy_response,
                      color=BG3, width=10).pack(side="left", padx=(0, 6))
        styled_button(btn_row, "💾 Sauver", command=self._save_response,
                      color=BG3, width=10).pack(side="left")
        styled_button(btn_row, "🗑 Effacer", command=self._clear,
                      color=BG3, width=10).pack(side="right")

    # ── Headers Tab ───────────────────────────────────────────────
    def _build_headers_tab(self, parent):
        self.header_rows = []
        header_list = tk.Frame(parent, bg=BG)
        header_list.pack(fill="both", expand=True, pady=6)

        # Colonnes
        cols = tk.Frame(header_list, bg=BG)
        cols.pack(fill="x")
        tk.Label(cols, text="Clé", fg=FG2, font=FONT_SMALL,
                 bg=BG, width=22, anchor="w").pack(side="left", padx=(0, 4))
        tk.Label(cols, text="Valeur", fg=FG2, font=FONT_SMALL,
                 bg=BG, anchor="w").pack(side="left")

        self.headers_container = tk.Frame(header_list, bg=BG)
        self.headers_container.pack(fill="both", expand=True)

        # Headers par défaut
        defaults = [
            ("Content-Type", "application/json"),
            ("Accept", "application/json"),
        ]
        for k, v in defaults:
            self._add_header_row(k, v)

        styled_button(parent, "+ Ajouter header",
                      command=self._add_header_row,
                      color=BG3, width=18).pack(anchor="w", pady=4)

    def _add_header_row(self, key="", value=""):
        row = tk.Frame(self.headers_container, bg=BG)
        row.pack(fill="x", pady=2)

        key_var = tk.StringVar(value=key)
        val_var = tk.StringVar(value=value)

        k_entry = tk.Entry(row, textvariable=key_var, bg=BG2, fg=FG,
                           font=FONT_MONO, relief="solid", width=22, bd=1,
                           insertbackground=ACCENT)
        k_entry.pack(side="left", ipady=5, padx=(0, 4))

        v_entry = tk.Entry(row, textvariable=val_var, bg=BG2, fg=FG,
                           font=FONT_MONO, relief="solid", bd=1,
                           insertbackground=ACCENT)
        v_entry.pack(side="left", fill="x", expand=True, ipady=5)

        def remove():
            row.destroy()
            self.header_rows.remove((key_var, val_var))

        tk.Button(row, text="✕", bg=BG2, fg=DANGER, font=FONT_SMALL,
                  relief="flat", bd=0, cursor="hand2",
                  command=remove).pack(side="left", padx=4)

        self.header_rows.append((key_var, val_var))

    # ── Auth Tab ──────────────────────────────────────────────────
    def _build_auth_tab(self, parent):
        self.auth_type = tk.StringVar(value="None")
        types = ["None", "Bearer Token", "Basic Auth", "API Key"]

        for t in types:
            tk.Radiobutton(
                parent, text=t, variable=self.auth_type,
                value=t, bg=BG2, fg=FG, selectcolor=BG3,
                activebackground=BG2, activeforeground=FG,
                font=FONT_BODY, command=self._update_auth_ui
            ).pack(anchor="w", padx=12, pady=2)

        self.auth_frame = tk.Frame(parent, bg=BG)
        self.auth_frame.pack(fill="x", padx=12, pady=8)
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
            tk.Label(self.auth_frame, text=lbl, fg=FG2, font=FONT_SMALL,
                     bg=BG2).pack(anchor="w")
            var = tk.StringVar()
            tk.Entry(self.auth_frame, textvariable=var, bg=BG3, fg=FG,
                     font=FONT_MONO, relief="flat",
                     insertbackground=ACCENT,
                     show="*" if key == "pass" else "").pack(
                fill="x", ipady=5, pady=(0, 6))
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
        self.time_label.config(
            text=f"{elapsed*1000:.0f} ms  •  {len(resp.content)/1024:.1f} Ko")

        # Body
        self.response_text.config(state="normal")
        self.response_text.delete("1.0", "end")
        try:
            body = json.dumps(resp.json(), indent=2, ensure_ascii=False)
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
        style = ttk.Style()
        style.theme_use("default")
        style.configure("TNotebook",
                         background=BG2, borderwidth=0, tabmargins=0)
        style.configure("TNotebook.Tab",
                         background=BG3, foreground=FG2,
                         padding=[12, 6], font=FONT_BODY, borderwidth=0)
        style.map("TNotebook.Tab",
                  background=[("selected", BG2)],
                  foreground=[("selected", ACCENT)])


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
                      command=self._open, color=ACCENT, width=14).pack(
            side="left", padx=(0, 6))
        styled_button(bar, "💾 Sauver CSV",
                      command=self._save, color=BG3, width=14).pack(
            side="left", padx=(0, 16))

        label(bar, "Recherche :", fg=FG2, font=FONT_SMALL).pack(
            side="left", padx=(0, 4))
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *_: self._apply_filter())
        tk.Entry(bar, textvariable=self.search_var,
                 bg=BG3, fg=FG, font=FONT_MONO,
                 insertbackground=ACCENT, relief="flat", width=24).pack(
            side="left", ipady=6, padx=(0, 12))

        label(bar, "Colonne :", fg=FG2, font=FONT_SMALL).pack(
            side="left", padx=(0, 4))
        self.filter_col_var = tk.StringVar(value="— Toutes —")
        self.col_menu = tk.OptionMenu(bar, self.filter_col_var,
                                      "— Toutes —")
        self.col_menu.config(bg=BG3, fg=FG, relief="flat", bd=0,
                              font=FONT_BODY, activebackground=ACCENT2,
                              highlightthickness=0, cursor="hand2")
        self.col_menu["menu"].config(bg=BG3, fg=FG, font=FONT_BODY)
        self.col_menu.pack(side="left", padx=(0, 12))

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
                         background=BG3, foreground=FG,
                         rowheight=26, fieldbackground=BG3,
                         borderwidth=0, font=FONT_MONO)
        style.configure("CSV.Treeview.Heading",
                         background=BG2, foreground=ACCENT,
                         font=FONT_BOLD, relief="flat", borderwidth=0)
        style.map("CSV.Treeview",
                  background=[("selected", ACCENT2)],
                  foreground=[("selected", FG)])

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
        bot = tk.Frame(self, bg=BG2, pady=8, padx=12)
        bot.pack(fill="x")

        styled_button(bot, "🗑 Suppr. ligne",
                      command=self._delete_rows, color=DANGER,
                      width=16).pack(side="left", padx=(0, 6))
        styled_button(bot, "🧹 Suppr. doublons",
                      command=self._remove_duplicates, color=WARNING,
                      width=18).pack(side="left", padx=(0, 6))
        styled_button(bot, "↕ Trier ↑↓",
                      command=self._toggle_sort, color=BG3,
                      width=12).pack(side="left")

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
            self.tree.column(col, width=120, stretch=True, anchor="w")
        for i, row in enumerate(self._filtered):
            tag = "odd" if i % 2 else "even"
            self.tree.insert("", "end",
                              values=[row.get(c, "") for c in self._cols],
                              tags=(tag,))
        self.tree.tag_configure("odd",  background=BG3)
        self.tree.tag_configure("even", background=BG2)

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
        bar = tk.Frame(self, bg=BG, pady=10, padx=12)
        bar.pack(fill="x")

        styled_button(bar, "✨ Beautify",
                      command=self._beautify, color=ACCENT,
                      width=12).pack(side="left", padx=(0, 6))
        styled_button(bar, "📦 Minify",
                      command=self._minify, color=ACCENT2,
                      width=12).pack(side="left", padx=(0, 6))
        styled_button(bar, "✅ Valider",
                      command=self._validate, color=SUCCESS,
                      width=12).pack(side="left", padx=(0, 16))

        styled_button(bar, "📂 Ouvrir",
                      command=self._open, color=BG3,
                      width=10).pack(side="left", padx=(0, 6))
        styled_button(bar, "💾 Sauver",
                      command=self._save, color=BG3,
                      width=10).pack(side="left", padx=(0, 16))

        label(bar, "Indent :", fg=FG2, font=FONT_SMALL).pack(
            side="left", padx=(0, 4))
        self.indent_var = tk.IntVar(value=2)
        for n in [2, 4]:
            tk.Radiobutton(
                bar, text=str(n), variable=self.indent_var, value=n,
                bg=BG2, fg=FG, selectcolor=BG3,
                activebackground=BG2, font=FONT_BODY
            ).pack(side="left")

        # ── Panneau splitté input / output ───────────────────────
        tk.Frame(self, bg=BORDER, height=1).pack(fill="x")

        paned = tk.PanedWindow(self, orient="horizontal",
                               bg=BORDER, sashwidth=3, bd=0)
        paned.pack(fill="both", expand=True, padx=12, pady=12)

        # Input
        left = tk.Frame(paned, bg=BG2)
        paned.add(left, minsize=300)

        tk.Label(left, text="Entrée", fg=FG2, font=FONT_BOLD,
                 bg=BG2).pack(anchor="w", pady=(0, 4))
        frame_in, self.input_text = scrolled_text(left)
        frame_in.pack(fill="both", expand=True)

        btn_row_in = tk.Frame(left, bg=BG2, pady=6)
        btn_row_in.pack(fill="x")
        styled_button(btn_row_in, "📋 Coller",
                      command=self._paste, color=BG3,
                      width=10).pack(side="left", padx=(0, 6))
        styled_button(btn_row_in, "🗑 Vider",
                      command=lambda: self.input_text.delete("1.0", "end"),
                      color=BG3, width=10).pack(side="left")

        # Output
        right = tk.Frame(paned, bg=BG2)
        paned.add(right, minsize=300)

        tk.Label(right, text="Sortie", fg=FG2, font=FONT_BOLD,
                 bg=BG2).pack(anchor="w", pady=(0, 4))
        frame_out, self.output_text = scrolled_text(right)
        frame_out.pack(fill="both", expand=True)

        btn_row_out = tk.Frame(right, bg=BG2, pady=6)
        btn_row_out.pack(fill="x")
        styled_button(btn_row_out, "📋 Copier",
                      command=self._copy_output, color=BG3,
                      width=10).pack(side="left", padx=(0, 6))
        styled_button(btn_row_out, "→ Input",
                      command=self._to_input, color=BG3,
                      width=10).pack(side="left")

        # Status
        self.status = tk.Label(self, text="", fg=SUCCESS,
                               font=FONT_SMALL, bg=BG2, pady=4)
        self.status.pack(fill="x", padx=12)

        # Exemple par défaut
        sample = '{"name":"NdarMarket","type":"marketplace","active":true,"tags":["senegal","tech"]}'
        self.input_text.insert("1.0", sample)

    # ── Actions ───────────────────────────────────────────────────
    def _get_input(self):
        return self.input_text.get("1.0", "end").strip()

    def _set_output(self, text):
        self.output_text.delete("1.0", "end")
        self.output_text.insert("1.0", text)

    def _beautify(self):
        try:
            data = json.loads(self._get_input())
            result = json.dumps(data, indent=self.indent_var.get(),
                                ensure_ascii=False)
            self._set_output(result)
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
        # ── Header ────────────────────────────────────────────────
        header = tk.Frame(self, bg=ACCENT, pady=0)
        header.pack(fill="x")

        title_frame = tk.Frame(header, bg=ACCENT, padx=16, pady=14)
        title_frame.pack(side="left", fill="x", expand=True)

        tk.Label(title_frame, text="DevKit Pro",
                 font=("Segoe UI", 18, "bold"),
                 fg="white", bg=ACCENT).pack(side="left")
        tk.Label(title_frame,
                 text="  API Tester  •  CSV Cleaner  •  JSON Formatter",
                 font=FONT_BODY, fg="white", bg=ACCENT).pack(side="left", padx=12)

        # Version badge
        tk.Label(header, text="v1.0", font=FONT_SMALL,
                 fg="white", bg=ACCENT, padx=12).pack(side="right", padx=12)

        tk.Frame(self, bg=BORDER, height=1).pack(fill="x")

        # ── Notebook principal ────────────────────────────────────
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Main.TNotebook",
                         background=BG, borderwidth=0, tabmargins=[0, 0, 0, 0])
        style.configure("Main.TNotebook.Tab",
                         background=BG2, foreground=FG2,
                         padding=[20, 10], font=FONT_BOLD, borderwidth=0)
        style.map("Main.TNotebook.Tab",
                  background=[("selected", BG)],
                  foreground=[("selected", ACCENT)],
                  expand=[("selected", [0, 0, 0, 0])])

        nb = ttk.Notebook(self, style="Main.TNotebook")
        nb.pack(fill="both", expand=True)

        self.api_tab  = ApiTesterTab(nb)
        self.csv_tab  = CsvTab(nb)
        self.json_tab = JsonTab(nb)

        nb.add(self.api_tab,  text="  🌐  API Tester  ")
        nb.add(self.csv_tab,  text="  📊  CSV Cleaner  ")
        nb.add(self.json_tab, text="  { }  JSON Formatter  ")

        # ── Status bar ────────────────────────────────────────────
        status_bar = tk.Frame(self, bg=BG2, pady=4)
        status_bar.pack(fill="x", side="bottom")
        tk.Label(status_bar,
                 text="DevKit Pro  •  Python + Tkinter",
                 fg=FG2, font=FONT_SMALL, bg=BG2, padx=12).pack(side="left")
        req_status = "✅ requests OK" if HAS_REQUESTS else "⚠️  pip install requests"
        tk.Label(status_bar, text=req_status,
                 fg=SUCCESS if HAS_REQUESTS else WARNING,
                 font=FONT_SMALL, bg=BG2, padx=12).pack(side="right")


# ══════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    app = DevKitPro()
    app.mainloop()
