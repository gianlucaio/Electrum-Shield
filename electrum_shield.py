#!/usr/bin/env python3
"""
Electrum GPG Verifier
Verifica l'autenticità dell'AppImage di Electrum tramite firme GPG.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import subprocess
import urllib.request
import urllib.error
import os
import sys
import shutil

# ── Configurazione ──────────────────────────────────────────────────────────
VERSION = "4.7.2"
BASE_URL = f"https://download.electrum.org/{VERSION}"
APPIMAGE_NAME = f"electrum-{VERSION}-x86_64.AppImage"
ASC_NAME = f"electrum-{VERSION}-x86_64.AppImage.asc"
APPIMAGE_URL = f"{BASE_URL}/{APPIMAGE_NAME}"
ASC_URL = f"{BASE_URL}/{ASC_NAME}"

# Chiavi GPG degli sviluppatori ufficiali
GPG_KEYS = {
    "ThomasV":     ("6694D8DE7BE8EE5631BED9502BD5824B7F9470E6",
                    "https://raw.githubusercontent.com/spesmilo/electrum/master/pubkeys/ThomasV.asc"),
    "SomberNight": ("0EEDCFD5CAFB459067349B23CA9EEC43DF911DC",
                    "https://raw.githubusercontent.com/spesmilo/electrum/master/pubkeys/sombernight_releasekey.asc"),
    "Emzy":        ("",
                    "https://raw.githubusercontent.com/spesmilo/electrum/master/pubkeys/Emzy.asc"),
    "felixb_f321x":("",
                    "https://raw.githubusercontent.com/spesmilo/electrum/master/pubkeys/felixb_f321x.asc"),
}

# ── Palette colori ───────────────────────────────────────────────────────────
BG       = "#0d1117"
BG2      = "#161b22"
BG3      = "#21262d"
ACCENT   = "#f7931a"   # Bitcoin orange
ACCENT2  = "#ffa94d"
GREEN    = "#3fb950"
RED      = "#f85149"
YELLOW   = "#d29922"
TEXT     = "#e6edf3"
TEXT2    = "#8b949e"
BORDER   = "#30363d"
FONT_MONO = ("Courier New", 10)
FONT_MAIN = ("Segoe UI", 10) if sys.platform == "win32" else ("DejaVu Sans", 10)
FONT_HEAD = ("Segoe UI", 13, "bold") if sys.platform == "win32" else ("DejaVu Sans", 13, "bold")


def gpg_available():
    return shutil.which("gpg") is not None


def http_download(url, dest_path, reporthook=None):
    """Download con User-Agent browser per evitare errori 403."""
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"}
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        total = int(resp.headers.get("Content-Length", 0))
        block = 8192
        count = 0
        with open(dest_path, "wb") as f:
            while True:
                chunk = resp.read(block)
                if not chunk:
                    break
                f.write(chunk)
                count += 1
                if reporthook:
                    reporthook(count, block, total)


class ProgressDialog(tk.Toplevel):
    def __init__(self, parent, title="Download in corso..."):
        super().__init__(parent)
        self.title(title)
        self.configure(bg=BG)
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        w, h = 420, 130
        x = parent.winfo_rootx() + (parent.winfo_width() - w) // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")

        self.label = tk.Label(self, text="Inizializzazione...", fg=TEXT2, bg=BG,
                              font=FONT_MAIN)
        self.label.pack(pady=(18, 6))

        style = ttk.Style(self)
        style.theme_use("default")
        style.configure("Orange.Horizontal.TProgressbar",
                        troughcolor=BG3, background=ACCENT,
                        bordercolor=BORDER, lightcolor=ACCENT, darkcolor=ACCENT)
        self.bar = ttk.Progressbar(self, style="Orange.Horizontal.TProgressbar",
                                   length=360, mode="determinate")
        self.bar.pack(pady=6)

        self.pct = tk.Label(self, text="0%", fg=ACCENT, bg=BG, font=FONT_MONO)
        self.pct.pack()

    def update_progress(self, filename, downloaded, total):
        if total > 0:
            pct = int(downloaded / total * 100)
            self.bar["value"] = pct
            mb_done = downloaded / 1_048_576
            mb_tot = total / 1_048_576
            self.label.config(text=f"Download: {filename}  ({mb_done:.1f} / {mb_tot:.1f} MB)")
            self.pct.config(text=f"{pct}%")
        else:
            self.label.config(text=f"Download: {filename}")
        self.update_idletasks()


class ElectrumVerifier(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Electrum GPG Verifier")
        self.configure(bg=BG)
        self.resizable(True, True)
        self.minsize(720, 600)

        # Stato
        self.appimage_path = tk.StringVar()
        self.asc_path = tk.StringVar()
        self.download_dir = tk.StringVar(value=os.path.expanduser("~/Downloads"))
        self.status_lines = []

        self._build_ui()
        self._center_window(740, 660)
        self._log("🟠 Electrum GPG Verifier avviato.", "accent")
        self._log(f"   Versione target: Electrum {VERSION} (AppImage x86_64)", "dim")
        if not gpg_available():
            self._log("⚠️  gpg non trovato nel PATH. Installalo con: sudo apt install gnupg", "warn")
        else:
            self._log("✅ gpg trovato nel sistema.", "ok")

    # ── Layout ──────────────────────────────────────────────────────────────

    def _build_ui(self):
        # Header
        hdr = tk.Frame(self, bg=BG, pady=0)
        hdr.pack(fill="x", padx=0, pady=0)
        canvas = tk.Canvas(hdr, height=72, bg=BG, highlightthickness=0)
        canvas.pack(fill="x")
        canvas.bind("<Configure>", lambda e: self._draw_header(canvas))

        # Body
        body = tk.Frame(self, bg=BG)
        body.pack(fill="both", expand=True, padx=18, pady=(6, 12))

        # ── Sezione 1: Cartella di download ─────────────────────────────
        self._section(body, "1 · Cartella di salvataggio")
        row = tk.Frame(body, bg=BG)
        row.pack(fill="x", pady=(0, 10))
        self._entry(row, self.download_dir, width=54).pack(side="left", padx=(0, 8))
        self._btn(row, "Sfoglia", self._browse_dir).pack(side="left")

        # ── Sezione 2: Scarica file ──────────────────────────────────────
        self._section(body, "2 · Scarica AppImage + Firma")
        dl_row = tk.Frame(body, bg=BG)
        dl_row.pack(fill="x", pady=(0, 10))
        self._btn(dl_row, "⬇  Scarica AppImage + .asc", self._download_both,
                  accent=True).pack(side="left", padx=(0, 10))
        self._btn(dl_row, "📂 Usa file già presenti", self._pick_existing).pack(side="left")

        # File selezionati
        fi = tk.Frame(body, bg=BG2, bd=0, relief="flat",
                      highlightbackground=BORDER, highlightthickness=1)
        fi.pack(fill="x", pady=(0, 10))
        self._file_row(fi, "AppImage:", self.appimage_path)
        ttk.Separator(fi, orient="horizontal").pack(fill="x", padx=10)
        self._file_row(fi, "Firma .asc:", self.asc_path)

        # ── Sezione 3: Chiavi GPG ────────────────────────────────────────
        self._section(body, "3 · Importa chiavi GPG degli sviluppatori")
        kr = tk.Frame(body, bg=BG)
        kr.pack(fill="x", pady=(0, 10))
        self._btn(kr, "🔑 Importa tutte le chiavi", self._import_keys,
                  accent=True).pack(side="left", padx=(0, 10))

        # Badge sviluppatori
        badges = tk.Frame(body, bg=BG)
        badges.pack(fill="x", pady=(0, 10))
        for dev in GPG_KEYS:
            b = tk.Label(badges, text=f"  {dev}  ", fg=TEXT2, bg=BG3,
                         font=("Courier New", 9), relief="flat",
                         padx=6, pady=3,
                         highlightbackground=BORDER, highlightthickness=1)
            b.pack(side="left", padx=(0, 6))

        # ── Sezione 4: Verifica ──────────────────────────────────────────
        self._section(body, "4 · Verifica firma")
        vr = tk.Frame(body, bg=BG)
        vr.pack(fill="x", pady=(0, 10))
        self._btn(vr, "🔐 Verifica ora", self._verify, accent=True,
                  big=True).pack(side="left")

        # ── Log ─────────────────────────────────────────────────────────
        self._section(body, "Log")
        log_frame = tk.Frame(body, bg=BG2,
                             highlightbackground=BORDER, highlightthickness=1)
        log_frame.pack(fill="both", expand=True)
        self.log_text = tk.Text(log_frame, bg=BG2, fg=TEXT, font=FONT_MONO,
                                relief="flat", bd=0, state="disabled",
                                wrap="word", height=10,
                                selectbackground=BG3, insertbackground=TEXT)
        sb = tk.Scrollbar(log_frame, command=self.log_text.yview, bg=BG3)
        self.log_text.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self.log_text.pack(fill="both", expand=True, padx=8, pady=6)
        # Tag colori
        self.log_text.tag_config("accent", foreground=ACCENT)
        self.log_text.tag_config("ok",     foreground=GREEN)
        self.log_text.tag_config("warn",   foreground=YELLOW)
        self.log_text.tag_config("err",    foreground=RED)
        self.log_text.tag_config("dim",    foreground=TEXT2)
        self.log_text.tag_config("normal", foreground=TEXT)

    def _draw_header(self, canvas):
        canvas.delete("all")
        w = canvas.winfo_width()
        canvas.create_rectangle(0, 0, w, 72, fill=BG2, outline="")
        canvas.create_line(0, 71, w, 71, fill=BORDER)
        # Accent bar
        canvas.create_rectangle(0, 0, 4, 72, fill=ACCENT, outline="")
        canvas.create_text(22, 22, anchor="w", text="⛓  Electrum GPG Verifier",
                           fill=TEXT, font=(FONT_HEAD[0], 15, "bold"))
        canvas.create_text(22, 50, anchor="w",
                           text=f"Verifica l'autenticità dell'AppImage v{VERSION} per Linux",
                           fill=TEXT2, font=FONT_MAIN)

    def _section(self, parent, text):
        f = tk.Frame(parent, bg=BG)
        f.pack(fill="x", pady=(8, 3))
        tk.Label(f, text=text.upper(), fg=ACCENT, bg=BG,
                 font=("Courier New", 9, "bold")).pack(side="left")
        tk.Frame(f, bg=BORDER, height=1).pack(side="left", fill="x",
                                               expand=True, padx=(8, 0), pady=6)

    def _entry(self, parent, var, width=40):
        e = tk.Entry(parent, textvariable=var, width=width,
                     bg=BG3, fg=TEXT, insertbackground=TEXT,
                     relief="flat", font=FONT_MONO,
                     highlightbackground=BORDER, highlightthickness=1,
                     highlightcolor=ACCENT)
        return e

    def _btn(self, parent, text, cmd, accent=False, big=False):
        bg = ACCENT if accent else BG3
        fg = BG if accent else TEXT
        pad = (16, 8) if big else (10, 5)
        b = tk.Button(parent, text=text, command=cmd,
                      bg=bg, fg=fg, activebackground=ACCENT2,
                      activeforeground=BG, relief="flat", cursor="hand2",
                      font=(FONT_MAIN[0], 11 if big else 10, "bold" if accent else "normal"),
                      padx=pad[0], pady=pad[1],
                      highlightthickness=0, bd=0)
        return b

    def _file_row(self, parent, label, var):
        row = tk.Frame(parent, bg=BG2)
        row.pack(fill="x", padx=10, pady=6)
        tk.Label(row, text=label, fg=TEXT2, bg=BG2, width=12,
                 anchor="w", font=FONT_MONO).pack(side="left")
        tk.Label(row, textvariable=var, fg=ACCENT2, bg=BG2,
                 font=FONT_MONO, anchor="w").pack(side="left", fill="x", expand=True)

    def _center_window(self, w, h):
        self.update_idletasks()
        x = (self.winfo_screenwidth() - w) // 2
        y = (self.winfo_screenheight() - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")

    # ── Log helper ───────────────────────────────────────────────────────────

    def _log(self, msg, tag="normal"):
        self.log_text.config(state="normal")
        self.log_text.insert("end", msg + "\n", tag)
        self.log_text.see("end")
        self.log_text.config(state="disabled")

    # ── Azioni ───────────────────────────────────────────────────────────────

    def _browse_dir(self):
        d = filedialog.askdirectory(initialdir=self.download_dir.get())
        if d:
            self.download_dir.set(d)

    def _pick_existing(self):
        path = filedialog.askopenfilename(
            title="Seleziona AppImage",
            initialdir=self.download_dir.get(),
            filetypes=[("AppImage", "*.AppImage"), ("Tutti", "*.*")])
        if not path:
            return
        self.appimage_path.set(path)
        self._log(f"📂 AppImage selezionata: {path}", "dim")

        # Aggiorna download_dir alla cartella dell'AppImage selezionata
        folder = os.path.dirname(path)
        self.download_dir.set(folder)

        # Cerca il .asc nella stessa cartella
        asc = path + ".asc"
        if os.path.exists(asc):
            self.asc_path.set(asc)
            self._log(f"✅ Firma .asc trovata automaticamente nella stessa cartella.", "ok")
        else:
            # Non trovato: offri di scaricarlo nella stessa cartella
            self._log("⚠️  File .asc non trovato nella stessa cartella.", "warn")
            self._log(f"   → Scarico automaticamente il .asc in: {folder}", "dim")
            threading.Thread(target=self._download_asc_only, args=(folder,), daemon=True).start()

    def _download_asc_only(self, dest):
        """Scarica solo il file .asc nella cartella indicata."""
        asc_dest = os.path.join(dest, ASC_NAME)
        try:
            self.after(0, self._log, f"⬇  Download firma .asc...", "dim")
            http_download(ASC_URL, asc_dest)
            self.after(0, self.asc_path.set, asc_dest)
            self.after(0, self._log, f"✅ Firma scaricata in: {asc_dest}", "ok")
        except Exception as e:
            self.after(0, self._log, f"❌ Errore download .asc: {e}", "err")

    def _download_both(self):
        dest = self.download_dir.get()
        if not os.path.isdir(dest):
            messagebox.showerror("Errore", f"Cartella non valida:\n{dest}")
            return
        threading.Thread(target=self._do_download, args=(dest,), daemon=True).start()

    def _do_download(self, dest):
        dlg = ProgressDialog(self)

        def progress_hook(filename):
            def hook(count, block_size, total):
                downloaded = count * block_size
                self.after(0, dlg.update_progress, filename, downloaded, total)
            return hook

        try:
            # Scarica AppImage
            appimage_dest = os.path.join(dest, APPIMAGE_NAME)
            self.after(0, self._log, f"⬇  Download AppImage...", "dim")
            http_download(APPIMAGE_URL, appimage_dest,
                          reporthook=progress_hook(APPIMAGE_NAME))
            self.after(0, self.appimage_path.set, appimage_dest)
            self.after(0, self._log, f"✅ AppImage scaricata: {appimage_dest}", "ok")

            # Scarica .asc nella stessa cartella
            asc_dest = os.path.join(dest, ASC_NAME)
            self.after(0, self._log, f"⬇  Download firma .asc...", "dim")
            http_download(ASC_URL, asc_dest,
                          reporthook=progress_hook(ASC_NAME))
            self.after(0, self.asc_path.set, asc_dest)
            self.after(0, self._log, f"✅ Firma scaricata: {asc_dest}", "ok")
            self.after(0, self._log, "   ✔ Entrambi i file pronti. Ora importa le chiavi GPG.", "dim")

        except urllib.error.URLError as e:
            self.after(0, self._log, f"❌ Errore di rete: {e}", "err")
        except Exception as e:
            self.after(0, self._log, f"❌ Errore: {e}", "err")
        finally:
            self.after(0, dlg.destroy)

    def _import_keys(self):
        if not gpg_available():
            messagebox.showerror("GPG mancante",
                                 "gpg non è installato.\nEsegui: sudo apt install gnupg")
            return
        threading.Thread(target=self._do_import_keys, daemon=True).start()

    def _do_import_keys(self):
        self.after(0, self._log, "🔑 Importazione chiavi GPG in corso...", "accent")
        ok_count = 0
        for dev, (fingerprint, url) in GPG_KEYS.items():
            self.after(0, self._log, f"   → {dev} ...", "dim")
            try:
                req = urllib.request.Request(
                    url,
                    headers={"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"}
                )
                with urllib.request.urlopen(req, timeout=15) as resp:
                    key_data = resp.read()
                result = subprocess.run(
                    ["gpg", "--batch", "--import"],
                    input=key_data,
                    capture_output=True)
                stderr = result.stderr.decode("utf-8", errors="replace")
                if result.returncode == 0 or "imported" in stderr or "not changed" in stderr:
                    self.after(0, self._log, f"   ✅ {dev}: importata nel keyring (~/.gnupg/)", "ok")
                    ok_count += 1
                else:
                    self.after(0, self._log,
                               f"   ⚠️  {dev}: {stderr.strip()[:120]}", "warn")
            except Exception as e:
                self.after(0, self._log, f"   ❌ {dev}: errore - {e}", "err")
        if ok_count == len(GPG_KEYS):
            self.after(0, self._log,
                       f"✅ Tutte e {ok_count} chiavi salvate in ~/.gnupg/ — pronto per la verifica!", "ok")
        else:
            self.after(0, self._log,
                       f"⚠️  {ok_count}/{len(GPG_KEYS)} chiavi importate.", "warn")

    def _verify(self):
        if not gpg_available():
            messagebox.showerror("GPG mancante",
                                 "gpg non è installato.\nEsegui: sudo apt install gnupg")
            return
        appimage = self.appimage_path.get()
        asc = self.asc_path.get()
        if not appimage or not os.path.exists(appimage):
            messagebox.showwarning("File mancante",
                                   "Seleziona o scarica prima il file AppImage.")
            return
        if not asc or not os.path.exists(asc):
            messagebox.showwarning("Firma mancante",
                                   "Seleziona o scarica prima il file firma .asc.")
            return
        threading.Thread(target=self._do_verify, args=(appimage, asc), daemon=True).start()

    def _do_verify(self, appimage, asc):
        self.after(0, self._log, "─" * 56, "dim")
        self.after(0, self._log, "🔐 Avvio verifica GPG...", "accent")
        self.after(0, self._log, f"   File  : {os.path.basename(appimage)}", "dim")
        self.after(0, self._log, f"   Firma : {os.path.basename(asc)}", "dim")
        try:
            result = subprocess.run(
                ["gpg", "--verify", asc, appimage],
                capture_output=True, text=True)
            output = (result.stdout + result.stderr).strip()
            self.after(0, self._log, "", "dim")
            good_sigs = 0
            for line in output.splitlines():
                # Firma valida (IT) / Good signature (EN)
                if "Firma valida" in line or "Good signature" in line:
                    self.after(0, self._log, f"   {line}", "ok")
                    good_sigs += 1
                # Firma NON valida (IT) / BAD signature (EN)
                elif "Firma NON valida" in line or "BAD signature" in line:
                    self.after(0, self._log, f"   {line}", "err")
                # Warning "non certificata" = NORMALE, non è un errore
                elif "ATTENZIONE" in line or "WARNING" in line or \
                     "not certified" in line or "non è certificata" in line or \
                     "Non ci sono indicazioni" in line:
                    self.after(0, self._log, f"   {line}", "warn")
                else:
                    self.after(0, self._log, f"   {line}", "dim")
            self.after(0, self._log, "", "dim")

            # Successo = returncode 0 (gpg ha verificato ok) + almeno una firma valida
            if result.returncode == 0 and good_sigs > 0:
                self.after(0, self._show_result, True,
                           f"✅  FIRMA VALIDA ({good_sigs} firme verificate)\n"
                           f"Il file AppImage è autentico e non è stato manomesso.\n\n"
                           f"Nota: il warning 'chiave non certificata' è normale\n"
                           f"e non indica alcun problema di sicurezza.")
            else:
                self.after(0, self._show_result, False,
                           "❌  FIRMA NON VALIDA\nIl file potrebbe essere corrotto o contraffatto.\n"
                           "NON eseguirlo!")
        except FileNotFoundError:
            self.after(0, self._log, "❌ gpg non trovato.", "err")
        except Exception as e:
            self.after(0, self._log, f"❌ Errore imprevisto: {e}", "err")

    def _show_result(self, ok, message):
        self._log("─" * 56, "dim")
        if ok:
            self._log(message, "ok")
            messagebox.showinfo("✅ Verifica completata", message)
        else:
            self._log(message, "err")
            messagebox.showerror("❌ Verifica fallita", message)


if __name__ == "__main__":
    app = ElectrumVerifier()
    app.mainloop()
