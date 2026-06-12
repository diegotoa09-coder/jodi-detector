"""
Detector de Texto Generado por IA - v2.0
Proyecto de Bachillerato - Análisis Lingüístico Avanzado
Requiere: pip install python-docx pymupdf nltk spacy
          py -m spacy download es_core_news_sm
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import re
import math
import time
import os
from collections import Counter

# ── Dependencias opcionales ─────────────────────────────────────────────────
try:
    import docx
    DOCX_OK = True
except ImportError:
    DOCX_OK = False

try:
    import fitz
    PDF_OK = True
except ImportError:
    PDF_OK = False

try:
    import nltk
    from nltk.corpus import stopwords
    from nltk.tokenize import sent_tokenize, word_tokenize
    NLTK_OK = True
except ImportError:
    NLTK_OK = False

try:
    import spacy
    try:
        NLP = spacy.load("es_core_news_sm")
    except OSError:
        NLP = None
    SPACY_OK = NLP is not None
except ImportError:
    SPACY_OK = False
    NLP = None

# ═══════════════════════════════════════════════════════════════════════════
#  SEÑALES Y PATRONES
# ═══════════════════════════════════════════════════════════════════════════

AI_PHRASES = [
    "en primer lugar", "en segundo lugar", "en conclusión", "en resumen",
    "es importante destacar", "cabe mencionar", "cabe señalar",
    "a modo de conclusión", "en definitiva", "por otro lado",
    "por una parte", "por otra parte", "en este sentido",
    "a lo largo de", "en el ámbito de", "it is worth noting",
    "it is important to", "in conclusion", "furthermore", "additionally",
    "moreover", "in summary", "to summarize", "first and foremost",
    "last but not least", "delve into", "it is crucial",
    "plays a crucial role", "it is essential", "it is worth mentioning",
    "needless to say", "it goes without saying", "as previously mentioned",
    "as mentioned above", "in light of", "with regard to",
    "with respect to", "in terms of", "it should be noted",
    "it can be observed", "it is evident", "it is clear that",
    "it is important to note", "one must consider", "one can argue",
    "taking into account", "bearing in mind", "in the context of",
    "desde esta perspectiva", "en el marco de", "a partir de lo anterior",
    "en virtud de lo expuesto", "de acuerdo con lo anterior",
    "resulta fundamental", "es preciso señalar", "conviene destacar",
    "vale la pena mencionar", "no cabe duda", "sin lugar a dudas",
    "es necesario recalcar", "hay que tener en cuenta",
]

TRANSITION_WORDS = (
    r"\b(sin embargo|aunque|no obstante|por lo tanto|debido a|"
    r"a pesar de|con respecto a|en cuanto a|however|although|therefore|"
    r"consequently|nevertheless|nonetheless|regarding|concerning|"
    r"asimismo|igualmente|de igual manera|de igual forma|"
    r"por consiguiente|en consecuencia|dado que|puesto que|"
    r"ya que|debido a que|a causa de|por ende|así pues|"
    r"en efecto|ciertamente|efectivamente|indudablemente)\b"
)

PASSIVE_PATTERNS = (
    r"\b(fue|fueron|es|son|era|eran|sido|ha sido|han sido|"
    r"se puede|se debe|se considera|se observa|se evidencia|"
    r"se destaca|se menciona|se establece|se determina|"
    r"was|were|is being|are being|has been|have been|"
    r"it was found|it was noted|it was observed)\b"
)

FORMAL_OVERUSED = [
    "fundamental", "esencial", "crucial", "vital", "primordial",
    "indispensable", "imprescindible", "relevante", "significativo",
    "considerable", "substantial", "significant", "important",
    "notable", "remarkable", "comprehensive", "extensive",
    "various", "numerous", "several", "diverse", "múltiple",
    "diversos", "numerosos", "variados", "distintos",
]

HEDGING_WORDS = [
    "podría", "puede", "quizás", "tal vez", "posiblemente",
    "probablemente", "generalmente", "típicamente", "usualmente",
    "normalmente", "frecuentemente", "a menudo", "en general",
    "por lo general", "could", "may", "might", "perhaps",
    "possibly", "probably", "generally", "typically", "usually",
    "often", "in general", "tends to", "suele",
]


# ═══════════════════════════════════════════════════════════════════════════
#  MOTOR DE ANÁLISIS
# ═══════════════════════════════════════════════════════════════════════════

def tokenize_sentences(text):
    if NLTK_OK:
        try:
            return sent_tokenize(text, language="spanish")
        except Exception:
            pass
    return [s.strip() for s in re.split(r"[.!?]+", text) if len(s.strip()) > 10]


def tokenize_words(text):
    if NLTK_OK:
        try:
            return word_tokenize(text.lower(), language="spanish")
        except Exception:
            pass
    return re.findall(r"\b[a-záéíóúñA-ZÁÉÍÓÚÑA-Za-z]{2,}\b", text.lower())


def get_stopwords():
    if NLTK_OK:
        try:
            return set(stopwords.words("spanish")) | set(stopwords.words("english"))
        except Exception:
            pass
    return set()


def analyze_ngrams(words, n=2):
    """Detecta n-gramas repetidos — señal fuerte de IA."""
    ngrams = [tuple(words[i:i+n]) for i in range(len(words) - n + 1)]
    counts = Counter(ngrams)
    repeated = sum(1 for c in counts.values() if c > 1)
    return repeated / max(len(ngrams), 1)


def flesch_kincaid_es(text, words, sentences):
    """
    Índice de legibilidad adaptado al español (Fernández Huerta).
    Valores altos = texto más fácil = más probable IA (escribe claro y uniforme).
    """
    syllables = sum(count_syllables_es(w) for w in words)
    n_words = max(len(words), 1)
    n_sents = max(len(sentences), 1)
    score = 206.835 - 0.60 * (syllables / n_words) * 100 - 1.02 * (n_words / n_sents)
    return max(0, min(score, 100))


def count_syllables_es(word):
    """Conteo aproximado de sílabas en español."""
    word = word.lower()
    vowels = "aeiouáéíóúü"
    count = 0
    prev_vowel = False
    for ch in word:
        is_vowel = ch in vowels
        if is_vowel and not prev_vowel:
            count += 1
        prev_vowel = is_vowel
    return max(count, 1)


def analyze_pos_spacy(text):
    """Análisis morfológico con spaCy: detecta patrones de verbos y sustantivos."""
    if not SPACY_OK:
        return 0, 0, 0
    doc = NLP(text[:5000])
    tokens = [t for t in doc if not t.is_space]
    total = max(len(tokens), 1)

    noun_ratio = sum(1 for t in tokens if t.pos_ in ("NOUN", "PROPN")) / total
    verb_ratio = sum(1 for t in tokens if t.pos_ == "VERB") / total
    adj_ratio  = sum(1 for t in tokens if t.pos_ == "ADJ") / total

    return noun_ratio, verb_ratio, adj_ratio


def analyze_text(text: str) -> dict:
    sentences = tokenize_sentences(text)
    all_words  = tokenize_words(text)
    stop_words = get_stopwords()

    content_words = [w for w in all_words if w not in stop_words and len(w) > 2]
    word_count    = max(len(all_words), 1)
    sent_count    = max(len(sentences), 1)

    # ── Diversidad léxica ──────────────────────────────────────────────────
    unique_content = set(content_words)
    lexical_diversity = len(unique_content) / max(len(content_words), 1)

    # ── Varianza de oraciones ──────────────────────────────────────────────
    sent_lens = [len(s.split()) for s in sentences]
    avg_len   = sum(sent_lens) / max(len(sent_lens), 1)
    variance  = sum((l - avg_len) ** 2 for l in sent_lens) / max(len(sent_lens), 1)
    sent_variance = math.sqrt(variance)
    uniformity = 1 - min(sent_variance / 15, 1)

    # ── Frases de IA ───────────────────────────────────────────────────────
    text_lower = text.lower()
    ai_phrase_count = sum(len(re.findall(p, text_lower)) for p in AI_PHRASES)
    phrase_density  = min(ai_phrase_count / sent_count, 1.0)

    # ── Voz pasiva ─────────────────────────────────────────────────────────
    passive_count = len(re.findall(PASSIVE_PATTERNS, text, re.IGNORECASE))
    passive_ratio = passive_count / sent_count

    # ── Conectores ─────────────────────────────────────────────────────────
    transition_count   = len(re.findall(TRANSITION_WORDS, text, re.IGNORECASE))
    transition_density = transition_count / sent_count

    # ── Repetición estructural ─────────────────────────────────────────────
    structures = [" ".join(s.lower().split()[:3]) for s in sentences]
    repetition_score = 1 - (len(set(structures)) / max(len(structures), 1))

    # ── N-gramas repetidos (NUEVO) ─────────────────────────────────────────
    ngram_repetition = analyze_ngrams(content_words, n=3)

    # ── Palabras formales sobreusadas (NUEVO) ──────────────────────────────
    formal_count   = sum(text_lower.count(w) for w in FORMAL_OVERUSED)
    formal_density = min(formal_count / word_count * 10, 1.0)

    # ── Hedging / incertidumbre artificial (NUEVO) ─────────────────────────
    hedging_count   = sum(text_lower.count(w) for w in HEDGING_WORDS)
    hedging_density = min(hedging_count / sent_count, 1.0)

    # ── Legibilidad Flesch-Kincaid (NUEVO) ─────────────────────────────────
    fk_score       = flesch_kincaid_es(text, all_words, sentences)
    readability_ai = fk_score / 100

    # ── Análisis morfológico spaCy (NUEVO) ─────────────────────────────────
    noun_ratio, verb_ratio, adj_ratio = analyze_pos_spacy(text)
    # IA tiende a muchos sustantivos y adjetivos, pocos verbos activos
    pos_ai_signal = min((noun_ratio * 0.5 + adj_ratio * 0.8 - verb_ratio * 0.3), 1.0)
    pos_ai_signal = max(pos_ai_signal, 0)

    # ── Puntuación de comas y punto y coma (NUEVO) ─────────────────────────
    punct_density = (text.count(",") + text.count(";")) / word_count
    punct_ai      = min(punct_density * 8, 1.0)

    # ══════════════════════════════════════════════════════════════════════
    #  SCORE FINAL PONDERADO
    # ══════════════════════════════════════════════════════════════════════
    ai_score = 0
    ai_score += phrase_density       * 22   # frases de IA
    ai_score += uniformity           * 14   # oraciones uniformes
    ai_score += min(passive_ratio * 10, 10) # voz pasiva
    ai_score += min(transition_density * 7, 10) # conectores
    ai_score += repetition_score     * 8    # repetición estructural
    ai_score += ngram_repetition     * 10   # n-gramas repetidos
    ai_score += formal_density       * 8    # palabras formales
    ai_score += hedging_density      * 6    # hedging artificial
    ai_score += readability_ai       * 6    # legibilidad uniforme
    ai_score += pos_ai_signal        * 10   # morfología spaCy
    ai_score += punct_ai             * 6    # puntuación excesiva

    ai_score = max(2, min(97, ai_score))
    confidence = min(72 + min(len(content_words) / 40, 25), 97)
    if SPACY_OK:
        confidence = min(confidence + 5, 97)

    avg_wps = round(word_count / sent_count, 1)

    signals = [
        ("Frases típicas de IA",        min(phrase_density * 100, 100)),
        ("Uniformidad sintáctica",       uniformity * 100),
        ("Voz pasiva / impersonal",      min(passive_ratio * 60, 100)),
        ("Conectores discursivos",       min(transition_density * 70, 100)),
        ("N-gramas repetidos",           min(ngram_repetition * 300, 100)),
        ("Vocabulario formal sobreusado",min(formal_density * 100, 100)),
        ("Hedging / incertidumbre",      min(hedging_density * 80, 100)),
        ("Morfología (sustantivos/adj)", min(pos_ai_signal * 100, 100)),
        ("Puntuación excesiva",          min(punct_ai * 100, 100)),
        ("Legibilidad uniforme",         min(readability_ai * 100, 100)),
    ]

    return {
        "ai_score":               round(ai_score),
        "confidence":             round(confidence),
        "word_count":             len(all_words),
        "sentence_count":         sent_count,
        "avg_words_per_sentence": avg_wps,
        "lexical_diversity":      round(lexical_diversity * 100, 1),
        "spacy_active":           SPACY_OK,
        "nltk_active":            NLTK_OK,
        "signals":                [(n, round(v)) for n, v in signals],
    }


# ═══════════════════════════════════════════════════════════════════════════
#  EXTRACCIÓN DE TEXTO
# ═══════════════════════════════════════════════════════════════════════════

def extract_txt(path):
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()

def extract_docx(path):
    if not DOCX_OK:
        raise ImportError("Instala python-docx: py -m pip install python-docx")
    doc = docx.Document(path)
    return "\n".join(p.text for p in doc.paragraphs)

def extract_pdf(path):
    if not PDF_OK:
        raise ImportError("Instala pymupdf: py -m pip install pymupdf")
    text = ""
    with fitz.open(path) as doc:
        for page in doc:
            text += page.get_text()
    return text

def extract_file(path):
    ext = os.path.splitext(path)[1].lower()
    if ext == ".txt":   return extract_txt(path)
    if ext in (".docx", ".doc"): return extract_docx(path)
    if ext == ".pdf":   return extract_pdf(path)
    raise ValueError(f"Formato no soportado: {ext}")


# ═══════════════════════════════════════════════════════════════════════════
#  INTERFAZ GRÁFICA
# ═══════════════════════════════════════════════════════════════════════════

DARK_BG  = "#0f0f11"
PANEL_BG = "#17171a"
CARD_BG  = "#1e1e22"
BORDER   = "#2e2e35"
TEXT_PRI = "#f0f0f4"
TEXT_SEC = "#8a8a99"
TEXT_MUT = "#55555f"
ACCENT   = "#ffffff"
RED      = "#e24b4a"
AMBER    = "#ef9f27"
GREEN    = "#5cca80"
BLUE     = "#4a9eff"

F_TITLE = ("Segoe UI", 20, "bold")
F_HEAD  = ("Segoe UI", 13, "bold")
F_BODY  = ("Segoe UI", 11)
F_MONO  = ("Consolas", 10)
F_SMALL = ("Segoe UI", 9)
F_BIG   = ("Segoe UI", 48, "bold")


class AnimatedBar(tk.Canvas):
    def __init__(self, parent, height=6, fill_color=RED, **kw):
        super().__init__(parent, height=height, bg=CARD_BG,
                         highlightthickness=0, **kw)
        self.fill_color = fill_color
        self._target = 0
        self._current = 0
        self.bind("<Configure>", self._redraw)

    def set_value(self, pct, color=None):
        if color: self.fill_color = color
        self._target = max(0, min(pct, 100))
        self._animate()

    def _animate(self):
        if abs(self._current - self._target) < 0.5:
            self._current = self._target
            self._redraw()
            return
        self._current += (self._target - self._current) * 0.12
        self._redraw()
        self.after(16, self._animate)

    def _redraw(self, *_):
        self.delete("all")
        w, h = self.winfo_width(), self.winfo_height()
        if w < 2: return
        self.create_rectangle(0, 0, w, h, fill=BORDER, outline="")
        fw = int(w * self._current / 100)
        if fw > 0:
            self.create_rectangle(0, 0, fw, h, fill=self.fill_color, outline="")


class DetectorApp(tk.Tk):

    def __init__(self):
        super().__init__()
        self.title("Detector de IA v2.0 — Análisis Lingüístico Avanzado")
        self.geometry("820x720")
        self.minsize(700, 580)
        self.configure(bg=DARK_BG)
        self._extracted_text = ""
        self._build_ui()

    def _build_ui(self):
        outer  = tk.Frame(self, bg=DARK_BG)
        outer.pack(fill="both", expand=True)
        canvas = tk.Canvas(outer, bg=DARK_BG, highlightthickness=0)
        sb     = ttk.Scrollbar(outer, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        self._sf  = tk.Frame(canvas, bg=DARK_BG)
        self._win = canvas.create_window((0, 0), window=self._sf, anchor="nw")
        self._sf.bind("<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>",
            lambda e: canvas.itemconfig(self._win, width=e.width))
        canvas.bind_all("<MouseWheel>",
            lambda e: canvas.yview_scroll(-1*(e.delta//120), "units"))
        self._canvas = canvas
        self._build_content(self._sf)

    def _card(self, parent, pady=(0,0)):
        f = tk.Frame(parent, bg=PANEL_BG,
                     highlightbackground=BORDER, highlightthickness=1)
        f.pack(fill="x", padx=24, pady=pady)
        return f

    def _build_content(self, parent):
        # Header
        hdr = tk.Frame(parent, bg=DARK_BG)
        hdr.pack(fill="x", padx=24, pady=(28, 8))
        dot = tk.Canvas(hdr, width=10, height=10, bg=DARK_BG, highlightthickness=0)
        dot.create_oval(0, 0, 10, 10, fill=GREEN, outline="")
        dot.pack(side="left", padx=(0,10), pady=6)
        tk.Label(hdr, text="Detector de IA", font=F_TITLE,
                 bg=DARK_BG, fg=TEXT_PRI).pack(side="left")
        tk.Label(hdr, text="  análisis lingüístico avanzado · v2.0",
                 font=F_MONO, bg=DARK_BG, fg=TEXT_MUT).pack(side="left", pady=6)

        # Badges de librerías activas
        badge_frame = tk.Frame(parent, bg=DARK_BG)
        badge_frame.pack(fill="x", padx=24, pady=(0, 16))
        for lib, active in [("spaCy", SPACY_OK), ("NLTK", NLTK_OK),
                             ("python-docx", DOCX_OK), ("PyMuPDF", PDF_OK)]:
            color = GREEN if active else RED
            label = "✓ " + lib if active else "✗ " + lib
            tk.Label(badge_frame, text=label, font=F_MONO,
                     bg=DARK_BG, fg=color).pack(side="left", padx=(0, 16))

        # Input card
        self._input_card = self._card(parent, pady=(0, 12))
        self._build_input(self._input_card)

        # Loader
        self._loader_frame = tk.Frame(parent, bg=DARK_BG)
        self._loader_label = tk.Label(self._loader_frame, text="procesando...",
                                      font=F_MONO, bg=DARK_BG, fg=TEXT_SEC)
        self._loader_label.pack(pady=(8, 4))
        self._loader_bar = AnimatedBar(self._loader_frame, height=3,
                                       fill_color=BLUE, width=400)
        self._loader_bar.pack(fill="x", padx=24)

        # Result card
        self._result_card = self._card(parent, pady=(0, 12))
        self._build_result(self._result_card)
        self._result_card.pack_forget()

        # Reset button
        self._reset_btn = tk.Button(parent, text="Analizar otro texto",
                                    font=F_BODY, bg=PANEL_BG, fg=TEXT_SEC,
                                    activebackground=CARD_BG, activeforeground=TEXT_PRI,
                                    relief="flat", bd=0, cursor="hand2",
                                    command=self._reset, pady=10)

    def _build_input(self, parent):
        up_frame = tk.Frame(parent, bg=PANEL_BG)
        up_frame.pack(fill="x", padx=20, pady=(18, 6))
        tk.Button(up_frame, text="📂  Subir archivo (PDF, DOCX, TXT)",
                  font=F_BODY, bg=CARD_BG, fg=TEXT_SEC,
                  activebackground=BORDER, activeforeground=TEXT_PRI,
                  relief="flat", bd=0, cursor="hand2",
                  command=self._load_file, pady=12, padx=16).pack(fill="x")
        self._file_label = tk.Label(up_frame, text="", font=F_MONO,
                                    bg=PANEL_BG, fg=BLUE)
        self._file_label.pack(pady=(4,0))

        div = tk.Frame(parent, bg=PANEL_BG)
        div.pack(fill="x", padx=20, pady=6)
        tk.Frame(div, bg=BORDER, height=1).pack(fill="x", side="left", expand=True, pady=8)
        tk.Label(div, text="  o pegar texto  ", font=F_SMALL,
                 bg=PANEL_BG, fg=TEXT_MUT).pack(side="left")
        tk.Frame(div, bg=BORDER, height=1).pack(fill="x", side="left", expand=True, pady=8)

        ta_frame = tk.Frame(parent, bg=PANEL_BG)
        ta_frame.pack(fill="x", padx=20, pady=(0,4))
        self._textarea = tk.Text(ta_frame, height=8, font=F_MONO,
                                  bg=CARD_BG, fg=TEXT_PRI, insertbackground=TEXT_PRI,
                                  relief="flat", bd=0, padx=12, pady=10,
                                  wrap="word", spacing3=2)
        self._textarea.pack(fill="x")
        self._textarea.insert("1.0", "Pega aquí el texto a analizar...")
        self._textarea.config(fg=TEXT_MUT)
        self._textarea.bind("<FocusIn>",  self._focus_in)
        self._textarea.bind("<FocusOut>", self._focus_out)
        self._textarea.bind("<<Modified>>", self._text_changed)

        self._char_label = tk.Label(parent, text="0 caracteres",
                                     font=F_MONO, bg=PANEL_BG, fg=TEXT_MUT)
        self._char_label.pack(anchor="e", padx=20)

        self._analyze_btn = tk.Button(parent, text="Analizar texto",
                                       font=("Segoe UI", 12, "bold"),
                                       bg=ACCENT, fg=DARK_BG,
                                       activebackground="#cccccc",
                                       relief="flat", bd=0, cursor="hand2",
                                       command=self._start_analysis,
                                       pady=13, state="disabled")
        self._analyze_btn.pack(fill="x", padx=20, pady=(10, 20))

    def _focus_in(self, _):
        if self._textarea.get("1.0", "end-1c") == "Pega aquí el texto a analizar...":
            self._textarea.delete("1.0", "end")
            self._textarea.config(fg=TEXT_PRI)

    def _focus_out(self, _):
        if not self._textarea.get("1.0", "end-1c").strip():
            self._textarea.insert("1.0", "Pega aquí el texto a analizar...")
            self._textarea.config(fg=TEXT_MUT)

    def _text_changed(self, _):
        self._textarea.edit_modified(False)
        text = self._textarea.get("1.0", "end-1c")
        is_ph = text == "Pega aquí el texto a analizar..."
        n = 0 if is_ph else len(text)
        self._char_label.config(text=f"{n} caracteres")
        has = n > 50 or len(self._extracted_text) > 50
        self._analyze_btn.config(state="normal" if has else "disabled")

    def _load_file(self):
        path = filedialog.askopenfilename(
            title="Seleccionar archivo",
            filetypes=[("Archivos soportados", "*.pdf *.docx *.doc *.txt"),
                       ("Todos", "*.*")]
        )
        if not path: return
        try:
            self._extracted_text = extract_file(path)
            preview = self._extracted_text[:600].replace("\n", " ")
            self._textarea.delete("1.0", "end")
            self._textarea.config(fg=TEXT_PRI)
            self._textarea.insert("1.0", preview + ("…" if len(self._extracted_text) > 600 else ""))
            fname = os.path.basename(path)
            self._file_label.config(text=f"✓  {fname}  ({len(self._extracted_text):,} chars)")
            self._char_label.config(text=f"{len(self._extracted_text):,} caracteres")
            self._analyze_btn.config(state="normal")
        except ImportError as e:
            messagebox.showerror("Librería faltante", str(e))
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo leer el archivo:\n{e}")

    def _start_analysis(self):
        text = self._extracted_text or self._textarea.get("1.0", "end-1c")
        if not text or len(text) < 50 or text == "Pega aquí el texto a analizar...":
            messagebox.showwarning("Texto insuficiente",
                                   "Necesitas al menos 50 caracteres.")
            return
        self._input_card.pack_forget()
        self._loader_frame.pack(fill="x", padx=24, pady=20)
        self._loader_bar.set_value(0)

        msgs = [
            "tokenizando con NLTK...",
            "analizando morfología con spaCy...",
            "calculando n-gramas...",
            "midiendo legibilidad Flesch-Kincaid...",
            "evaluando patrones discursivos...",
            "generando resultado...",
        ]

        def run():
            for i, msg in enumerate(msgs):
                self.after(0, lambda m=msg: self._loader_label.config(text=m))
                self.after(0, lambda v=(i+1)*15: self._loader_bar.set_value(v))
                time.sleep(0.5)
            result = analyze_text(text)
            self.after(0, lambda: self._show_result(result))

        threading.Thread(target=run, daemon=True).start()

    def _build_result(self, parent):
        self._rw = {}
        hdr = tk.Frame(parent, bg=PANEL_BG)
        hdr.pack(fill="x", padx=20, pady=(16, 10))
        tk.Label(hdr, text="RESULTADO DEL ANÁLISIS", font=F_MONO,
                 bg=PANEL_BG, fg=TEXT_MUT).pack(side="left")
        self._rw["verdict"] = tk.Label(hdr, text="—", font=F_SMALL,
                                        bg=CARD_BG, fg=TEXT_SEC, padx=10, pady=4)
        self._rw["verdict"].pack(side="right")

        tk.Frame(parent, bg=BORDER, height=1).pack(fill="x", padx=20)

        score_row = tk.Frame(parent, bg=PANEL_BG)
        score_row.pack(fill="x", padx=20, pady=16)
        self._rw["big_score"] = tk.Label(score_row, text="0%",
                                          font=F_BIG, bg=PANEL_BG, fg=TEXT_PRI)
        self._rw["big_score"].pack(side="left", padx=(0, 20))

        bar_col = tk.Frame(score_row, bg=PANEL_BG)
        bar_col.pack(side="left", fill="x", expand=True)
        tk.Label(bar_col, text="PROBABILIDAD DE ORIGEN ARTIFICIAL",
                 font=F_MONO, bg=PANEL_BG, fg=TEXT_MUT).pack(anchor="w")
        self._rw["main_bar"] = AnimatedBar(bar_col, height=6, fill_color=RED, width=300)
        self._rw["main_bar"].pack(fill="x", pady=(4, 10))
        tk.Label(bar_col, text="CONFIANZA DEL ANÁLISIS",
                 font=F_MONO, bg=PANEL_BG, fg=TEXT_MUT).pack(anchor="w")
        self._rw["conf_bar"] = AnimatedBar(bar_col, height=4, fill_color=AMBER, width=300)
        self._rw["conf_bar"].pack(fill="x", pady=(4, 0))

        tk.Frame(parent, bg=BORDER, height=1).pack(fill="x", padx=20, pady=(12,0))
        self._rw["metrics_frame"] = tk.Frame(parent, bg=PANEL_BG)
        self._rw["metrics_frame"].pack(fill="x", padx=20, pady=12)

        tk.Frame(parent, bg=BORDER, height=1).pack(fill="x", padx=20)
        tk.Label(parent, text="SEÑALES DETECTADAS", font=F_MONO,
                 bg=PANEL_BG, fg=TEXT_MUT).pack(anchor="w", padx=20, pady=(12,6))
        self._rw["signals_frame"] = tk.Frame(parent, bg=PANEL_BG)
        self._rw["signals_frame"].pack(fill="x", padx=20, pady=(0, 16))

    def _show_result(self, r):
        self._loader_frame.pack_forget()
        self._result_card.pack(fill="x", padx=24, pady=(0, 12))
        self._reset_btn.pack(fill="x", padx=24, pady=(0, 24))

        score = r["ai_score"]
        if score >= 70:
            verdict, vbg, vfg = "PROBABLEMENTE IA", "#3a1515", RED
        elif score >= 40:
            verdict, vbg, vfg = "MIXTO / INCIERTO", "#3a2a0a", AMBER
        else:
            verdict, vbg, vfg = "PROBABLEMENTE HUMANO", "#0e2a18", GREEN

        bar_color = RED if score >= 70 else AMBER if score >= 40 else GREEN
        self._rw["verdict"].config(text=verdict, bg=vbg, fg=vfg)
        self._rw["big_score"].config(text=f"{score}%", fg=bar_color)
        self._rw["main_bar"].set_value(score, bar_color)
        self._rw["conf_bar"].set_value(r["confidence"])

        mf = self._rw["metrics_frame"]
        for w in mf.winfo_children(): w.destroy()
        metrics = [
            ("Palabras",           str(r["word_count"]),              "en el texto"),
            ("Oraciones",          str(r["sentence_count"]),          "detectadas"),
            ("Prom. por oración",  str(r["avg_words_per_sentence"]),  "palabras"),
            ("Diversidad léxica",  f"{r['lexical_diversity']}%",      "vocab. único"),
            ("Confianza",          f"{r['confidence']}%",             "del análisis"),
        ]
        for i, (label, value, sub) in enumerate(metrics):
            card = tk.Frame(mf, bg=CARD_BG, padx=12, pady=8)
            card.grid(row=0, column=i, padx=(0,8), sticky="ew")
            mf.columnconfigure(i, weight=1)
            tk.Label(card, text=label, font=F_MONO, bg=CARD_BG, fg=TEXT_MUT).pack(anchor="w")
            tk.Label(card, text=value, font=("Segoe UI",16,"bold"),
                     bg=CARD_BG, fg=TEXT_PRI).pack(anchor="w")
            tk.Label(card, text=sub, font=F_SMALL, bg=CARD_BG, fg=TEXT_MUT).pack(anchor="w")

        sf = self._rw["signals_frame"]
        for w in sf.winfo_children(): w.destroy()
        for name, sv in r["signals"]:
            row = tk.Frame(sf, bg=PANEL_BG)
            row.pack(fill="x", pady=3)
            tk.Label(row, text=name, font=F_BODY, bg=PANEL_BG,
                     fg=TEXT_SEC, width=30, anchor="w").pack(side="left")
            bar = AnimatedBar(row, height=3,
                              fill_color=RED if sv>60 else AMBER if sv>30 else GREEN,
                              width=120)
            bar.pack(side="left", padx=(8,8))
            bar.update_idletasks()
            bar.after(100, lambda b=bar, v=sv: b.set_value(v))
            tk.Label(row, text=f"{sv}%", font=F_MONO,
                     bg=PANEL_BG, fg=TEXT_PRI, width=5, anchor="e").pack(side="left")

        # Badge de motores activos
        eng = tk.Frame(sf, bg=PANEL_BG)
        eng.pack(fill="x", pady=(10, 0))
        tk.Label(eng, text="Motores activos: ", font=F_MONO,
                 bg=PANEL_BG, fg=TEXT_MUT).pack(side="left")
        for lib, active in [("spaCy", r["spacy_active"]), ("NLTK", r["nltk_active"])]:
            c = GREEN if active else RED
            tk.Label(eng, text=("✓ " if active else "✗ ") + lib,
                     font=F_MONO, bg=PANEL_BG, fg=c).pack(side="left", padx=(0,12))

    def _reset(self):
        self._extracted_text = ""
        self._result_card.pack_forget()
        self._reset_btn.pack_forget()
        self._textarea.delete("1.0", "end")
        self._textarea.insert("1.0", "Pega aquí el texto a analizar...")
        self._textarea.config(fg=TEXT_MUT)
        self._file_label.config(text="")
        self._char_label.config(text="0 caracteres")
        self._analyze_btn.config(state="disabled")
        self._input_card.pack(fill="x", padx=24, pady=(0, 12))


# ═══════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    app = DetectorApp()
    app.mainloop()