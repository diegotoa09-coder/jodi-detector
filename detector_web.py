"""
╔══════════════════════════════════════════════════════════════╗
║          JoDi  ·  v6.5  ·  Edición Cinematográfica (Web)      ║
╚══════════════════════════════════════════════════════════════╝
Interfaz web real (HTML/CSS/JS) dentro de una ventana de escritorio,
servida por pywebview + WebView2.  Reutiliza EXACTAMENTE el mismo
motor de análisis de detector_ia_v6.py (analyze_text, extract_file,
build_html_report).  Sin tocar la lógica de detección.

Ejecutar:   python detector_web.py
Requiere:   pip install pywebview     (+ el motor: spacy, nltk, etc.)
"""

import os
import time
import threading
import webbrowser

import webview

# ── Motor de análisis (idéntico, reutilizado) ─────────────────────────────
from detector_ia_v6 import (
    analyze_text,
    extract_file,
    build_html_report,
    SPACY_OK, NLTK_OK, DOCX_OK, PDF_OK,
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INDEX    = os.path.join(BASE_DIR, "ui", "index.html")


class Api:
    """Puente Python ↔ JavaScript expuesto como window.pywebview.api"""

    def __init__(self):
        self.window = None
        self.last_result = None

    # -- estado de los motores (para los badges) ---------------------------
    def get_status(self):
        return {
            "spacy": SPACY_OK,
            "nltk":  NLTK_OK,
            "docx":  DOCX_OK,
            "pdf":   PDF_OK,
        }

    # -- análisis principal ------------------------------------------------
    def analyze(self, text):
        try:
            r = analyze_text(text or "")
            self.last_result = r
            return {"ok": True, "result": r}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    # -- abrir archivo y extraer texto -------------------------------------
    def open_file(self):
        try:
            file_types = ("Documentos (*.pdf;*.docx;*.doc;*.txt)", "Todos los archivos (*.*)")
            res = self.window.create_file_dialog(
                webview.OPEN_DIALOG, allow_multiple=False, file_types=file_types
            )
            if not res:
                return {"ok": False, "cancelled": True}
            path = res[0] if isinstance(res, (list, tuple)) else res
            text = extract_file(path)
            return {"ok": True, "name": os.path.basename(path), "text": text}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    # -- exportar informe HTML imprimible a PDF ----------------------------
    def export_report(self):
        if not self.last_result:
            return {"ok": False, "error": "No hay análisis para exportar."}
        try:
            html_str = build_html_report(self.last_result)
            default = f"informe_jodi_{time.strftime('%Y%m%d_%H%M%S')}.html"
            res = self.window.create_file_dialog(
                webview.SAVE_DIALOG, save_filename=default,
                file_types=("Página HTML (*.html)",),
            )
            if not res:
                return {"ok": False, "cancelled": True}
            path = res[0] if isinstance(res, (list, tuple)) else res
            if not path.lower().endswith(".html"):
                path += ".html"
            with open(path, "w", encoding="utf-8") as f:
                f.write(html_str)
            webbrowser.open("file://" + os.path.abspath(path))
            return {"ok": True, "path": path}
        except Exception as e:
            return {"ok": False, "error": str(e)}


def main():
    api = Api()
    window = webview.create_window(
        title="JoDi · Detector de Texto Artificial",
        url=INDEX,
        js_api=api,
        width=1180,
        height=900,
        min_size=(960, 700),
        background_color="#06060a",
        text_select=True,
    )
    api.window = window
    # debug=True habilita clic derecho → Inspeccionar (útil para desarrollo)
    webview.start(debug=False)


if __name__ == "__main__":
    main()
