"""
╔══════════════════════════════════════════════════════════════╗
║          JoDi  ·  v6.0  ·  Edición Profesional               ║
╚══════════════════════════════════════════════════════════════╝
Motor de análisis: idéntico a v5.0 (200+ señales, 17 métricas).
Novedades v6.0 (capa visual):
- Interfaz tipo dashboard limpio (estética producto, no terminal)
- Medidor circular animado del score (gauge radial)
- Nitidez DPI nativa en Windows (sin texto borroso)
- Tipografía Segoe UI + Consolas, jerarquía profesional
- Exportación de informe HTML imprimible a PDF (para jurado)
- Microinteracciones: hover en botones, animaciones suaves
- Layout responsivo y centrado en pantalla
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import re
import math
import time
import os
import html
import webbrowser
import tempfile
from collections import Counter

# ── Nitidez DPI en Windows (texto crujiente para la demo) ─────────────────
try:
    from ctypes import windll
    try:
        windll.shcore.SetProcessDpiAwareness(2)   # per-monitor v2
    except Exception:
        windll.user32.SetProcessDPIAware()
except Exception:
    pass

# ── Dependencias opcionales ──────────────────────────────────────────────
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
    try:
        stopwords.words("spanish")
    except LookupError:
        nltk.download("stopwords", quiet=True)
    try:
        sent_tokenize("test.", language="spanish")
    except LookupError:
        nltk.download("punkt", quiet=True)
        nltk.download("punkt_tab", quiet=True)
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
#  BASE DE SEÑALES — 200+ frases  (motor v5.0, sin cambios)
# ═══════════════════════════════════════════════════════════════════════════

OPENING_GPT = [
    r"\ben el presente (trabajo|ensayo|documento|análisis|texto|artículo|escrito)\b",
    r"\bel (siguiente|presente) (ensayo|trabajo|documento|análisis)\b",
    r"\ba continuación (se|abordaremos|analizaremos|presentamos|exploraremos|examinaremos)\b",
    r"\bel objetivo (del presente|de este|principal|central|fundamental) (trabajo|ensayo|análisis|documento)\b",
    r"\bel propósito de (este|la presente|este trabajo|este ensayo)\b",
    r"\ba lo largo de (este|la presente|el siguiente|estas páginas)\b",
    r"\ben las siguientes (líneas|páginas|secciones|páginas)\b",
    r"\bprocederemos a (analizar|explorar|examinar|estudiar|abordar)\b",
    r"\bnos (proponemos|disponemos) a (analizar|explorar|examinar)\b",
    r"\bel presente (análisis|trabajo|documento|ensayo|escrito) (tiene|busca|pretende|tiene como objetivo)\b",
    r"\besta (investigación|reflexión|exposición) (tiene|busca|pretende|tiene como objetivo)\b",
    r"\bin this (essay|paper|work|analysis|study|piece)\b",
    r"\bthis (essay|paper|work|analysis|study) (will|aims to|seeks to|explores|examines|discusses)\b",
    r"\bthe following (essay|paper|analysis|study|work)\b",
    r"\bin the following (sections|pages|lines|paragraphs)\b",
    r"\bthis (paper|study|analysis) (will|aims to) (explore|examine|analyze|discuss|investigate)\b",
    r"\bthe purpose of this\b",
    r"\bthe aim of this\b",
    r"\bthe objective of this\b",
]

CLOSING_GPT = [
    r"\ben conclusión[,\s]",
    r"\ben resumen[,\s]",
    r"\ben definitiva[,\s]",
    r"\ba modo de conclusión\b",
    r"\bpara concluir[,\s]",
    r"\bpara finalizar[,\s]",
    r"\bcomo (hemos visto|se ha visto|se puede observar|hemos podido ver|hemos analizado)\b",
    r"\bde todo lo anterior (se puede|podemos|cabe|se desprende)\b",
    r"\ba partir de lo expuesto\b",
    r"\bpor todo lo (anterior|expuesto|mencionado|analizado)\b",
    r"\blos aspectos (analizados|expuestos|mencionados|desarrollados) (permiten|nos permiten|muestran)\b",
    r"\blo expuesto (anteriormente|hasta aquí|en este|a lo largo)\b",
    r"\bqueda (claro|demostrado|evidenciado|patente) que\b",
    r"\bpodemos (concluir|afirmar|sostener|señalar) que\b",
    r"\bin conclusion[,\s]",
    r"\bto (conclude|summarize|sum up)[,\s]",
    r"\bin summary[,\s]",
    r"\bto sum (up|things up)[,\s]",
    r"\bas (we have|we've) (seen|discussed|explored|examined|analyzed)\b",
    r"\boverall[,\s]",
    r"\ball in all[,\s]",
    r"\btaking everything into account\b",
    r"\bbringing (it|everything|this) together\b",
]

TRANSITION_GPT = [
    r"\ben primer lugar\b", r"\ben segundo lugar\b", r"\ben tercer lugar\b",
    r"\ben cuarto lugar\b", r"\bfinalmente[,\s]",
    r"\bpor otro lado\b", r"\bpor una parte\b", r"\bpor otra parte\b",
    r"\ben este sentido\b", r"\ben el ámbito de\b",
    r"\bdesde esta perspectiva\b", r"\ben el marco de\b",
    r"\ba partir de lo anterior\b", r"\ben virtud de lo expuesto\b",
    r"\bde acuerdo con lo anterior\b", r"\ben tal sentido\b",
    r"\bpor lo expuesto\b", r"\blo anteriormente mencionado\b",
    r"\bcomo se mencionó (anteriormente|antes|previamente)\b",
    r"\btal como se indicó\b", r"\btal y como (se|hemos)\b",
    r"\bes por ello que\b", r"\bes por esto que\b", r"\bes por eso que\b",
    r"\ben este (contexto|escenario|marco|orden de ideas)\b",
    r"\bante (este|esta|estos|estas) (panorama|situación|contexto|realidad|escenario)\b",
    r"\bdesde este (punto de vista|enfoque|ángulo|perspectiva)\b",
    r"\btomando en cuenta (lo anterior|lo expuesto|esto)\b",
    r"\ba raíz de (lo anterior|esto|ello|lo expuesto)\b",
    r"(^|\.\s+)asimismo[,\s]", r"(^|\.\s+)igualmente[,\s]",
    r"(^|\.\s+)de igual (manera|forma|modo)[,\s]",
    r"(^|\.\s+)por su parte[,\s]", r"(^|\.\s+)por consiguiente[,\s]",
    r"(^|\.\s+)en consecuencia[,\s]", r"(^|\.\s+)dicho esto[,\s]",
    r"\ben última instancia\b", r"\ben este orden de ideas\b",
    r"\bcada vez más (popular|relevante|importante|frecuente|común|presente)\b",
    r"\bfurthermore[,\s]", r"\bmoreover[,\s]", r"\badditionally[,\s]",
    r"\bin addition[,\s]", r"\bnevertheless[,\s]", r"\bnonetheless[,\s]",
    r"\bin light of\b", r"\bwith regard to\b", r"\bwith respect to\b",
    r"\bon the other hand\b", r"\bon one hand\b",
    r"\bby the same token\b", r"\bin this regard\b", r"\bin this context\b",
    r"\bbuilding on (this|that|these)\b",
    r"\bwith this in mind\b", r"\bbearing this in mind\b",
]

EMPHASIS_GPT = [
    r"\bes importante (destacar|señalar|mencionar|tener en cuenta|recalcar|subrayar|notar)\b",
    r"\bcabe (mencionar|señalar|destacar|preguntarse|reflexionar|aclarar|precisar)\b",
    r"\bresulta (fundamental|esencial|crucial|importante|relevante|necesario|pertinente)\b",
    r"\bes (preciso|necesario|indispensable|imprescindible|menester) (señalar|mencionar|destacar|considerar|tener|recordar)\b",
    r"\bconviene (destacar|mencionar|señalar|recordar|aclarar|precisar)\b",
    r"\bvale la pena (mencionar|destacar|señalar|recordar|considerar|aclarar)\b",
    r"\bno cabe duda\b", r"\bsin lugar a dudas\b", r"\bno hay duda de que\b",
    r"\bes (indudable|innegable|evidente|claro|obvio|patente|manifiesto) que\b",
    r"\bhay que tener en cuenta\b", r"\bes importante tener en cuenta\b",
    r"\bes necesario tener en cuenta\b",
    r"\bse puede (observar|concluir|afirmar|notar|apreciar|ver)\b",
    r"\bpodemos (observar|destacar|concluir|afirmar|señalar|notar|ver|apreciar)\b",
    r"\bse hace (necesario|evidente|imprescindible|patente|urgente)\b",
    r"\bes (por tanto|por ello|por ende) (fundamental|necesario|importante|crucial)\b",
    r"\bjuega(n)? un papel (fundamental|crucial|importante|clave|determinante|esencial|central|preponderante)\b",
    r"\bdesempeña(n)? un papel (fundamental|crucial|importante|clave|central)\b",
    r"\btiene(n)? un (papel|rol|impacto|efecto) (fundamental|crucial|importante|clave|significativo)\b",
    r"\bes de (suma|vital|capital) importancia\b",
    r"\bno se puede (ignorar|negar|desconocer|pasar por alto)\b",
    r"\bsería (un error|incorrecto|inadecuado) (ignorar|negar|desconocer)\b",
    r"\bit is (worth noting|important to|crucial|essential|vital|necessary to|imperative to)\b",
    r"\bit (should|must) be (noted|mentioned|highlighted|emphasized|stressed|acknowledged)\b",
    r"\bit is (clear|evident|obvious|undeniable|worth emphasizing) that\b",
    r"\bone (must|should|can|cannot) (consider|ignore|overlook|deny|underestimate)\b",
    r"\bplays a (crucial|key|vital|important|central|fundamental|pivotal|significant) role\b",
    r"\bit goes without saying\b", r"\bneedless to say\b",
    r"\bit is (no coincidence|no surprise|not surprising) that\b",
    r"\bit would be (remiss|wrong|incorrect) to (ignore|overlook|neglect)\b",
    r"\bwe (cannot|can't|must not) (ignore|overlook|underestimate)\b",
    r"\bof (particular|special|great|utmost|paramount) importance\b",
    r"\bit bears (mentioning|repeating|emphasizing)\b",
]

GENERIC_GPT = [
    r"\bhoy (en día|día)\b",
    r"\ben la actualidad\b",
    r"\ben el mundo actual\b",
    r"\bdesde (tiempos inmemoriales|siempre|antaño)\b",
    r"\ba nivel (global|mundial|nacional|social|local|internacional)\b",
    r"\bel ser humano\b", r"\blos seres humanos\b",
    r"\bla sociedad (actual|moderna|contemporánea|de hoy|globalizada)\b",
    r"\bel mundo (actual|moderno|contemporáneo|globalizado|de hoy|digital)\b",
    r"\blo largo de la historia\b",
    r"\ba través del tiempo\b", r"\ba lo largo del tiempo\b",
    r"\ben todos los ámbitos\b", r"\ben diversos ámbitos\b",
    r"\bun papel (fundamental|crucial|importante|clave) en la sociedad\b",
    r"\bnuevo paradigma\b", r"\bnuevos paradigmas\b", r"\bcambio de paradigma\b",
    r"\bun sinfín de\b",
    r"\bun amplio (abanico|espectro|rango|conjunto) de\b",
    r"\bpermite(n)? (comprender|analizar|observar|identificar|abordar|entender)\b",
    r"\bgenera(n)? un (impacto|cambio|beneficio|efecto) (positivo|negativo|significativo)?\b",
    r"\bthroughout history\b",
    r"\bin today's (world|society|era|age|digital age|fast-paced world)\b",
    r"\bin the modern (world|era|age|society|landscape)\b",
    r"\bhas become (increasingly|ever more|more and more)\b",
    r"\bin recent (years|decades|times|history)\b",
    r"\bwith the (advent|rise|emergence|dawn|proliferation) of\b",
    r"\bthe importance of (this|these|such)\b",
    r"\bdelve into\b", r"\bunpack (this|the|these)\b",
    r"\bnavigate (the|this|these|complex|ever-changing)\b",
    r"\bthe (rapidly|ever|constantly) (changing|evolving|shifting) (world|landscape|environment)\b",
    r"\bin an (increasingly|ever more) (connected|globalized|digital|complex) world\b",
    r"\bmore than ever (before)?\b",
    r"\bthe (digital|information|technological) (age|era|revolution)\b",
    r"\bstand the test of time\b",
    r"\bseparate the wheat from the chaff\b",
    r"\bat the forefront of\b",
    r"\ba (double-edged|two-edged) sword\b",
    r"\bthe elephant in the room\b",
    r"\ba (game[- ]changer|paradigm shift)\b",
]

ALL_AI_PHRASES = OPENING_GPT + CLOSING_GPT + TRANSITION_GPT + EMPHASIS_GPT + GENERIC_GPT

# -- Vocabulario GPT sobreusado (extendido) --------------------------------
GPT_VOCAB_ES = [
    "fundamental", "esencial", "crucial", "vital", "primordial",
    "indispensable", "imprescindible", "relevante", "significativo",
    "considerable", "innegable", "indudable", "evidente", "notable",
    "sustancial", "determinante", "trascendental", "preponderante",
    "paradigma", "sinergia", "complejidad", "perspectiva", "panorama",
    "ámbito", "entorno", "contexto", "marco", "tejido", "ecosistema",
    "dinámica", "dimensión", "eje", "pilar", "vector", "desafío",
    "abordar", "abordará", "abordaremos", "ahondar", "profundizar",
    "implementar", "implementación", "optimizar", "potenciar",
    "enfatizar", "destacar", "resaltar", "subrayar", "visibilizar",
    "promover", "fomentar", "impulsar", "fortalecer",
    "evidentemente", "claramente", "ciertamente", "innegablemente",
    "indudablemente", "inevitablemente", "necesariamente",
    "holístico", "integral", "transversal", "multidimensional",
    "multifacético", "articulado", "cohesionado", "robusto",
    "diverso", "variado", "numeroso", "múltiple",
]

GPT_VOCAB_EN = [
    "substantial", "significant", "notable", "remarkable", "profound",
    "comprehensive", "extensive", "nuanced", "intricate", "complex",
    "pivotal", "paramount", "imperative", "leverage", "synergy",
    "underscore", "emphasize", "highlight", "facilitate", "streamline",
    "utilize", "implement", "optimize", "navigate", "foster",
    "multifaceted", "robust", "transformative", "innovative", "dynamic",
    "ecosystem", "landscape", "framework", "paradigm", "dimension",
    "delve", "unpack", "unravel", "elucidate", "illuminate",
    "crucial", "vital", "essential", "fundamental", "cornerstone",
    "holistic", "comprehensive", "integral", "overarching",
]

GPT_VOCAB = GPT_VOCAB_ES + GPT_VOCAB_EN

EVAL_ADJECTIVES = [
    "fundamental", "esencial", "crucial", "vital", "importante",
    "significativo", "relevante", "notable", "considerable",
    "determinante", "trascendental", "innegable", "indudable",
    "evidente", "claro", "obvio", "necesario", "indispensable",
    "imprescindible", "sustancial", "primordial", "preponderante",
    "important", "significant", "crucial", "essential", "vital",
    "notable", "substantial", "considerable", "evident", "clear",
    "necessary", "fundamental", "critical", "key", "central",
]

HUMAN_MARKERS = [
    r"\.{3}",
    r"[!¡]{1,3}",
    r"[?¿]{2,}",
    r"\b(bueno|pues|o sea|o sea que|la verdad|en fin|igual|type)\b",
    r"\b(creo que|me parece|no sé|no estoy seguro|supongo)\b",
    r"\b(jaja|je|haha|lol|xd)\b",
    r"—",
    r"\b(también|aunque sea|al menos|por lo menos|más o menos)\b",
    r"\b(eso sí|eso no|claro que|desde luego|por supuesto)\b",
    r"\b(anyway|tbh|tbf|ngl|imo|imho|afaik)\b",
    r"[,]{2,}",
]

IMPLICIT_LIST = re.compile(
    r"(también es|también (resulta|representa|constituye|puede)|"
    r"igualmente (es|resulta|representa)|"
    r"de igual (manera|forma|modo)[, ].{5,60}(es|resulta|representa|constituye)|"
    r"asimismo[, ].{5,60}(es|resulta|permite|contribuye))",
    re.IGNORECASE,
)

BALANCED_SYNTAX = [
    r"\b(por un lado).{5,80}(por otro lado)\b",
    r"\b(tanto).{3,50}(como)\b.{3,40}(son|representan|constituyen|permiten)\b",
    r"\bnot only.{5,80}but also\b",
    r"\bon the one hand.{5,100}on the other hand\b",
    r"\bno solo.{5,80}sino (también|además)\b",
    r"\bsi bien.{5,80}(también|igualmente|asimismo)\b",
    r"\b(aunque|a pesar de que).{5,60}(sin embargo|no obstante|pero)\b",
    r"\b(a medida que|conforme).{5,60}(también|igualmente|a su vez)\b",
    r"\b(X|Y)\b.{2,20}(juega un papel|desempeña un papel|tiene un papel).{5,40}(también|igualmente|asimismo)\b",
]

PASSIVE_RE = re.compile(
    r"\b(fue|fueron|es|son|era|eran|ha sido|han sido|"
    r"se puede|se debe|se considera|se observa|se evidencia|"
    r"se destaca|se menciona|se establece|se determina|se presenta|"
    r"se utiliza|se emplea|se aplica|se realiza|se lleva a cabo|"
    r"se ha (demostrado|señalado|indicado|establecido)|"
    r"was|were|is being|are being|has been|have been|"
    r"it was (found|noted|observed|established|shown|demonstrated))\b",
    re.IGNORECASE,
)

CONNECTOR_RE = re.compile(
    r"\b(sin embargo|aunque|no obstante|por lo tanto|debido a|"
    r"a pesar de|con respecto a|en cuanto a|asimismo|igualmente|"
    r"de igual manera|por consiguiente|en consecuencia|"
    r"dado que|puesto que|ya que|debido a que|por ende|"
    r"así pues|en efecto|ciertamente|efectivamente|"
    r"however|although|therefore|consequently|nevertheless|"
    r"furthermore|additionally|moreover|in addition)\b",
    re.IGNORECASE,
)

PARA_STARTER_RE = re.compile(
    r"^(Además|Por otro lado|Por otra parte|Sin embargo|No obstante|"
    r"En conclusión|En resumen|En definitiva|Por lo tanto|Por consiguiente|"
    r"Asimismo|De igual manera|De este modo|De esta manera|Cabe destacar|"
    r"Es importante|Resulta fundamental|En este sentido|En este contexto|"
    r"A su vez|Del mismo modo|De igual forma|Por su parte|"
    r"Furthermore|Moreover|Additionally|However|In conclusion|"
    r"In summary|Therefore|Nevertheless|Consequently|It is important|"
    r"It should be noted|It is worth|Building on|With this in mind),?\s",
    re.IGNORECASE | re.MULTILINE,
)

FALLBACK_STOPWORDS = {
    "de","la","el","en","y","a","los","del","se","las","por","un","para",
    "con","no","una","su","al","es","lo","como","más","pero","sus","le",
    "ya","o","fue","este","ha","si","the","of","and","in","is","it",
    "to","that","was","for","on","are","with","as","at","be","by","from",
    "this","are","were","they","them","their","there","been","have","has",
    "had","would","could","should","will","what","when","where","who",
    "which","that","than","then","than","also","about","into","over",
}


# ═══════════════════════════════════════════════════════════════════════════
#  TOKENIZACIÓN
# ═══════════════════════════════════════════════════════════════════════════

def tokenize_sentences(text: str) -> list:
    if NLTK_OK:
        try:
            return sent_tokenize(text, language="spanish")
        except Exception:
            pass
    return [s.strip() for s in re.split(r"[.!?]+", text) if len(s.strip()) > 10]


def tokenize_words(text: str) -> list:
    if NLTK_OK:
        try:
            return word_tokenize(text.lower(), language="spanish")
        except Exception:
            pass
    return re.findall(r"\b[a-záéíóúñA-ZÁÉÍÓÚÑA-Za-z]{2,}\b", text.lower())


def get_stopwords() -> set:
    if NLTK_OK:
        try:
            return set(stopwords.words("spanish")) | set(stopwords.words("english"))
        except Exception:
            pass
    return FALLBACK_STOPWORDS


# ═══════════════════════════════════════════════════════════════════════════
#  MÉTRICAS INDIVIDUALES
# ═══════════════════════════════════════════════════════════════════════════

def count_syllables_es(word: str) -> int:
    vowels = "aeiouáéíóúü"
    count, prev_v = 0, False
    for ch in word.lower():
        is_v = ch in vowels
        if is_v and not prev_v:
            count += 1
        prev_v = is_v
    return max(count, 1)


def readability_fernandez_huerta(words: list, sentences: list) -> float:
    if not words or not sentences:
        return 50.0
    sylls = sum(count_syllables_es(w) for w in words)
    n_w, n_s = max(len(words), 1), max(len(sentences), 1)
    score = 206.835 - 0.60 * (sylls / n_w) * 100 - 1.02 * (n_w / n_s)
    return max(0.0, min(score, 100.0))


def sentence_uniformity(sentences: list) -> tuple:
    lengths = [len(s.split()) for s in sentences if len(s.split()) > 1]
    if len(lengths) < 2:
        return 0.5, (lengths[0] if lengths else 0)
    avg = sum(lengths) / len(lengths)
    std = math.sqrt(sum((l - avg) ** 2 for l in lengths) / len(lengths))
    cv = std / max(avg, 1)
    signal = max(0.0, 1.0 - min(cv / 0.35, 1.0))
    return signal, avg


def burstiness_index(sentences: list) -> float:
    lengths = [len(s.split()) for s in sentences if len(s.split()) > 1]
    if len(lengths) < 5:
        return 0.5
    mean = sum(lengths) / len(lengths)
    std = math.sqrt(sum((l - mean) ** 2 for l in lengths) / len(lengths))
    b = (std - mean) / (std + mean + 1e-9)
    return max(0.0, min(1.0, (-b + 1.0) / 2.0))


def lexical_entropy(words: list) -> float:
    if not words:
        return 0.0
    counts = Counter(words)
    total = len(words)
    ent = -sum((c / total) * math.log2(c / total) for c in counts.values())
    max_e = math.log2(total) if total > 1 else 1.0
    return ent / max_e


def repetitive_ngrams(words: list, n: int = 3) -> float:
    if len(words) < n:
        return 0.0
    ngrams = [tuple(words[i:i+n]) for i in range(len(words) - n + 1)]
    counts = Counter(ngrams)
    repeated = sum(1 for c in counts.values() if c > 1)
    return min(repeated / max(len(ngrams), 1) * 12, 1.0)


def paragraph_analysis(text: str) -> tuple:
    paragraphs = [p.strip() for p in text.split("\n") if len(p.strip()) > 20]
    if not paragraphs:
        return 0.0, 0.0, 0.0

    gpt_starts = sum(1 for p in paragraphs if PARA_STARTER_RE.match(p))
    start_ratio = gpt_starts / len(paragraphs)

    if len(paragraphs) > 1:
        para_lens = [len(p.split()) for p in paragraphs]
        avg = sum(para_lens) / len(para_lens)
        std = math.sqrt(sum((l - avg) ** 2 for l in para_lens) / len(para_lens))
        para_uniform = max(0.0, 1.0 - min(std / max(avg, 1), 1.0))
    else:
        para_uniform = 0.0

    implicit_hits = len(IMPLICIT_LIST.findall(text))
    implicit_signal = min(implicit_hits / max(len(paragraphs), 1) * 2, 1.0)

    return start_ratio, para_uniform, implicit_signal


def balanced_syntax_score(text: str) -> float:
    hits = sum(1 for p in BALANCED_SYNTAX if re.search(p, text, re.IGNORECASE | re.DOTALL))
    return min(hits / 3.0, 1.0)


def eval_adjective_ratio(text_lower: str, words: list) -> float:
    eval_hits = sum(
        1 for w in EVAL_ADJECTIVES
        if re.search(r"\b" + re.escape(w) + r"\b", text_lower)
    )
    action_verbs = re.findall(
        r"\b(fui|fue|hice|hizo|llegué|llegó|compré|compró|dije|dijo|"
        r"vi|vio|salí|salió|entré|entró|encontré|encontró|"
        r"went|came|said|told|saw|bought|found|got|took|made|"
        r"called|walked|ran|looked|tried|thought|felt)\b",
        text_lower
    )
    ratio = eval_hits / max(len(action_verbs) + 1, 1)
    return min(ratio / 4.0, 1.0)


def human_markers_score(text: str) -> float:
    hits = sum(1 for p in HUMAN_MARKERS if re.search(p, text, re.IGNORECASE))
    return min(hits / 4.0, 1.0)


def informal_punctuation_score(text: str) -> float:
    informal_count = (
        text.count("...") * 2 +
        text.count("!") +
        text.count("¡") +
        text.count("—") +
        len(re.findall(r"\?{2,}", text)) +
        len(re.findall(r"!{2,}", text)) * 2
    )
    density = informal_count / max(len(text) / 100, 1)
    return min(density / 3.0, 1.0)


def semantic_redundancy(sentences: list) -> float:
    if len(sentences) < 3:
        return 0.0

    stop = FALLBACK_STOPWORDS
    overlaps = []
    for i in range(len(sentences) - 1):
        s1 = set(re.findall(r"\b[a-záéíóúñ]{4,}\b", sentences[i].lower())) - stop
        s2 = set(re.findall(r"\b[a-záéíóúñ]{4,}\b", sentences[i+1].lower())) - stop
        if s1 and s2:
            jaccard = len(s1 & s2) / len(s1 | s2)
            overlaps.append(jaccard)

    if not overlaps:
        return 0.0
    avg_overlap = sum(overlaps) / len(overlaps)
    if 0.12 <= avg_overlap <= 0.45:
        return min(avg_overlap * 3, 1.0)
    return 0.0


def zone_analysis(text: str, sentences: list) -> dict:
    n = len(sentences)
    if n < 4:
        return {"intro": 0.0, "body": 0.0, "closing": 0.0}

    intro_end   = max(1, n // 4)
    closing_start = max(intro_end + 1, n - n // 4)

    intro_sents   = sentences[:intro_end]
    closing_sents = sentences[closing_start:]

    intro_text   = " ".join(intro_sents).lower()
    closing_text = " ".join(closing_sents).lower()

    intro_hits = sum(1 for p in OPENING_GPT if re.search(p, intro_text, re.IGNORECASE))
    closing_hits = sum(1 for p in CLOSING_GPT if re.search(p, closing_text, re.IGNORECASE))
    body_sents = sentences[intro_end:closing_start]
    body_text  = " ".join(body_sents).lower()
    body_hits  = sum(1 for p in EMPHASIS_GPT if re.search(p, body_text, re.IGNORECASE))

    return {
        "intro":   min(intro_hits / 2.0, 1.0),
        "body":    min(body_hits / max(len(body_sents), 1) * 2, 1.0),
        "closing": min(closing_hits / 2.0, 1.0),
    }


def spacy_pos_analysis(text: str) -> tuple:
    if not SPACY_OK:
        return 0.0, 0.0, 0.0
    doc = NLP(text[:6000])
    tokens = [t for t in doc if not t.is_space and not t.is_punct]
    total = max(len(tokens), 1)
    noun_r = sum(1 for t in tokens if t.pos_ in ("NOUN", "PROPN")) / total
    verb_r = sum(1 for t in tokens if t.pos_ == "VERB") / total
    adj_r  = sum(1 for t in tokens if t.pos_ == "ADJ") / total
    return noun_r, verb_r, adj_r


# ═══════════════════════════════════════════════════════════════════════════
#  MOTOR PRINCIPAL  (idéntico a v5.0)
# ═══════════════════════════════════════════════════════════════════════════

def analyze_text(text: str) -> dict:
    sentences   = tokenize_sentences(text)
    all_words   = tokenize_words(text)
    stop_words  = get_stopwords()
    text_lower  = text.lower()

    content_words = [w for w in all_words if w not in stop_words and len(w) > 2]
    word_count    = max(len(all_words), 1)
    sent_count    = max(len(sentences), 1)

    opening_hits    = sum(1 for p in OPENING_GPT    if re.search(p, text_lower, re.IGNORECASE))
    closing_hits    = sum(1 for p in CLOSING_GPT    if re.search(p, text_lower, re.IGNORECASE))
    transition_hits = sum(1 for p in TRANSITION_GPT if re.search(p, text_lower, re.IGNORECASE))
    emphasis_hits   = sum(1 for p in EMPHASIS_GPT   if re.search(p, text_lower, re.IGNORECASE))
    generic_hits    = sum(1 for p in GENERIC_GPT    if re.search(p, text_lower, re.IGNORECASE))
    total_hits      = opening_hits + closing_hits + transition_hits + emphasis_hits + generic_hits

    phrase_threshold = max(2.5, word_count / 65)
    phrase_density   = min(total_hits / phrase_threshold, 1.0)

    categories_firing = sum(1 for h in
        (opening_hits, closing_hits, transition_hits, emphasis_hits, generic_hits) if h > 0)
    cooccur_signal = min(max(categories_firing - 1, 0) / 3.0, 1.0)

    gpt_vocab_hits = sum(
        1 for w in GPT_VOCAB
        if re.search(r"\b" + re.escape(w) + r"\b", text_lower)
    )
    vocab_threshold = max(4.0, word_count / 75)
    vocab_signal    = min(gpt_vocab_hits / vocab_threshold, 1.0)

    uniformity, avg_sent_len = sentence_uniformity(sentences)

    para_start, para_uniform, implicit_list = paragraph_analysis(text)
    para_signal = para_start * 0.55 + para_uniform * 0.30 + implicit_list * 0.15

    burst_signal = burstiness_index(sentences)

    connector_count   = len(CONNECTOR_RE.findall(text))
    connector_density = min(connector_count / sent_count / 0.40, 1.0)

    ngram_signal = repetitive_ngrams(content_words, n=3)

    passive_count = len(PASSIVE_RE.findall(text))
    passive_ratio = min(passive_count / sent_count / 0.75, 1.0)

    redundancy_signal = semantic_redundancy(sentences)

    syntax_signal = balanced_syntax_score(text)

    eval_adj_signal = eval_adjective_ratio(text_lower, all_words)

    entropy = lexical_entropy(content_words)
    if 0.68 <= entropy <= 0.93:
        entropy_signal = 0.65
    elif entropy > 0.93:
        entropy_signal = 0.35
    else:
        entropy_signal = 0.30

    zones = zone_analysis(text, sentences)
    zone_signal = zones["intro"] * 0.40 + zones["body"] * 0.30 + zones["closing"] * 0.30

    noun_r, verb_r, adj_r = spacy_pos_analysis(text)
    pos_signal = min(max(noun_r * 0.45 + adj_r * 0.65 - verb_r * 0.20, 0.0), 1.0)

    fk = readability_fernandez_huerta(all_words, sentences)
    fk_signal = 0.60 if 48 <= fk <= 80 else (0.40 if fk > 80 else 0.20)

    ttr = len(set(content_words)) / max(len(content_words), 1)
    ttr_signal = 0.55 if 0.36 <= ttr <= 0.70 else (0.30 if ttr < 0.36 else 0.35)

    human_signal   = human_markers_score(text)
    informal_punct = informal_punctuation_score(text)
    human_penalty  = (human_signal * 0.60 + informal_punct * 0.40)

    weights = {
        "phrase_density":    27,
        "cooccur_signal":    11,
        "vocab_signal":      12,
        "uniformity":        9,
        "para_signal":       8,
        "zone_signal":       7,
        "connector_density": 6,
        "burst_signal":      5,
        "eval_adj_signal":   4,
        "redundancy_signal": 4,
        "syntax_signal":     4,
        "ngram_signal":      3,
        "entropy_signal":    3,
        "passive_ratio":     2,
        "pos_signal":        2,
        "fk_signal":         1,
        "ttr_signal":        0,
    }

    values = {
        "phrase_density":    phrase_density,
        "cooccur_signal":    cooccur_signal,
        "vocab_signal":      vocab_signal,
        "uniformity":        uniformity,
        "para_signal":       para_signal,
        "zone_signal":       zone_signal,
        "connector_density": connector_density,
        "burst_signal":      burst_signal,
        "eval_adj_signal":   eval_adj_signal,
        "redundancy_signal": redundancy_signal,
        "syntax_signal":     syntax_signal,
        "ngram_signal":      ngram_signal,
        "entropy_signal":    entropy_signal,
        "passive_ratio":     passive_ratio,
        "pos_signal":        pos_signal,
        "fk_signal":         fk_signal,
        "ttr_signal":        ttr_signal,
    }

    total_w   = sum(weights.values())
    raw_score = sum(values[k] * weights[k] for k in weights) / total_w * 100

    gpt_evidence = min(
        (total_hits / 6.0) * 0.40 +
        cooccur_signal * 0.35 +
        vocab_signal * 0.25,
        1.0,
    )
    penalty_factor = (1.0 - gpt_evidence) * 0.26
    raw_score = raw_score * (1.0 - human_penalty * penalty_factor)

    if total_hits >= 8 and categories_firing >= 3:
        raw_score = raw_score + (100 - raw_score) * 0.18

    length_factor  = min(len(content_words) / 60, 1.0)
    phrase_boost   = min(total_hits / 4.0, 1.0) * 0.30
    evidence_boost = gpt_evidence * 0.20
    eff_length     = min(length_factor + phrase_boost + evidence_boost, 1.0)
    ai_score       = raw_score * eff_length + 50.0 * (1.0 - eff_length)
    ai_score       = max(2, min(97, ai_score))

    confidence = 48.0
    confidence += min(len(content_words) / 5.5, 32)
    if SPACY_OK:  confidence += 6
    if NLTK_OK:   confidence += 5
    if len(sentences) >= 5:   confidence += 3
    if total_hits >= 3:       confidence += 5
    if total_hits >= 8:       confidence += 3
    confidence = min(confidence, 95)

    signals = [
        ("Frases de apertura/cierre GPT",   _pct(max(opening_hits, closing_hits), 3)),
        ("Frases de énfasis IA",            _pct(emphasis_hits, 5)),
        ("Conectores/transiciones GPT",     _pct(transition_hits, 6)),
        ("Frases genéricas/cliché",         _pct(generic_hits, 6)),
        ("Vocabulario GPT sobreusado",      round(vocab_signal * 100)),
        ("Uniformidad de oraciones",        round(uniformity * 100)),
        ("Estructura de párrafos",          round(para_signal * 100)),
        ("Patrón por zonas (intro/cierre)", round(zone_signal * 100)),
        ("Burstiness (variación ritmo)",    round(burst_signal * 100)),
        ("Adjetivos evaluativos",           round(eval_adj_signal * 100)),
        ("Redundancia semántica",           round(redundancy_signal * 100)),
        ("Sintaxis balanceada/formulaica",  round(syntax_signal * 100)),
        ("N-gramas repetidos",              round(ngram_signal * 100)),
        ("Entropía léxica",                 round(entropy_signal * 100)),
        ("Voz pasiva / impersonal",         round(passive_ratio * 100)),
        ("Rasgos humanos detectados ↓",     round(human_penalty * 100)),
    ]
    if SPACY_OK:
        signals.append(("Morfología spaCy", round(pos_signal * 100)))

    phrase_categories = {
        "apertura":   opening_hits,
        "cierre":     closing_hits,
        "transición": transition_hits,
        "énfasis":    emphasis_hits,
        "clichés":    generic_hits,
    }

    return {
        "ai_score":               round(ai_score),
        "confidence":             round(confidence),
        "word_count":             len(all_words),
        "sentence_count":         sent_count,
        "avg_words_per_sentence": round(avg_sent_len, 1),
        "lexical_diversity":      round(ttr * 100, 1),
        "lexical_entropy":        round(entropy * 100, 1),
        "ai_phrases_total":       total_hits,
        "phrase_categories":      phrase_categories,
        "gpt_vocab_found":        gpt_vocab_hits,
        "readability":            round(fk, 1),
        "human_signal":           round(human_penalty * 100),
        "zones":                  zones,
        "spacy_active":           SPACY_OK,
        "nltk_active":            NLTK_OK,
        "signals":                signals,
    }


def _pct(hits: int, threshold: int) -> int:
    return round(min(hits / threshold, 1.0) * 100)


# ═══════════════════════════════════════════════════════════════════════════
#  EXTRACCIÓN DE TEXTO
# ═══════════════════════════════════════════════════════════════════════════

def extract_txt(path):
    for enc in ["utf-8", "latin-1", "cp1252"]:
        try:
            with open(path, "r", encoding=enc) as f:
                return f.read()
        except UnicodeDecodeError:
            continue
    raise ValueError("No se pudo leer el archivo")

def extract_docx(path):
    if not DOCX_OK:
        raise ImportError("Instala python-docx:  pip install python-docx")
    doc = docx.Document(path)
    return "\n".join(p.text for p in doc.paragraphs if p.text.strip())

def extract_pdf(path):
    if not PDF_OK:
        raise ImportError("Instala PyMuPDF:  pip install pymupdf")
    text = ""
    with fitz.open(path) as doc:
        for page in doc:
            text += page.get_text()
    return text

def extract_file(path):
    ext = os.path.splitext(path)[1].lower()
    if ext == ".txt":            return extract_txt(path)
    if ext in (".docx", ".doc"): return extract_docx(path)
    if ext == ".pdf":            return extract_pdf(path)
    raise ValueError(f"Formato no soportado: {ext}")


# ═══════════════════════════════════════════════════════════════════════════
#  PALETA Y FUENTES  —  Dashboard limpio v6.0
# ═══════════════════════════════════════════════════════════════════════════

# Superficies (oscuro elegante, profundidad por capas)
BG       = "#0a0e16"   # fondo app
SURFACE  = "#111722"   # tarjeta
SURFACE2 = "#161e2c"   # tarjeta interior / chips
SURFACE3 = "#1d2738"   # hover / track
BORDER   = "#222c3c"   # borde sutil
BORDER2  = "#2c3a4f"   # borde resaltado

# Texto
TX  = "#e9eef5"        # principal
TX2 = "#9aa8ba"        # secundario
TX3 = "#5d6b7e"        # terciario / labels

# Acentos
ACCENT    = "#4f9cff"  # azul producto (primario)
ACCENT_DK = "#2f6fd6"
ACCENT_HV = "#6aabff"

GREEN    = "#34d399"; GREEN_BG = "#0f2e24"
AMBER    = "#fbbf24"; AMBER_BG = "#33280f"
RED      = "#f87171"; RED_BG   = "#341a1d"
CYAN     = "#38d9e6"

# Fuentes
F_LOGO   = ("Segoe UI Semibold", 22)
F_LOGO2  = ("Segoe UI Light", 22)
F_H1     = ("Segoe UI Semibold", 15)
F_H2     = ("Segoe UI Semibold", 11)
F_SECT   = ("Segoe UI Semibold", 9)
F_BODY   = ("Segoe UI", 10)
F_SMALL  = ("Segoe UI", 9)
F_TINY   = ("Segoe UI", 8)
F_MONO   = ("Consolas", 9)
F_NUM    = ("Segoe UI Semibold", 17)
F_GAUGE  = ("Segoe UI Semibold", 46)
F_BTN    = ("Segoe UI Semibold", 10)


def lerp_color(c1, c2, t):
    """Interpola entre dos colores hex. t en [0,1]."""
    c1 = c1.lstrip("#"); c2 = c2.lstrip("#")
    r = int(int(c1[0:2], 16) + (int(c2[0:2], 16) - int(c1[0:2], 16)) * t)
    g = int(int(c1[2:4], 16) + (int(c2[2:4], 16) - int(c1[2:4], 16)) * t)
    b = int(int(c1[4:6], 16) + (int(c2[4:6], 16) - int(c1[4:6], 16)) * t)
    return f"#{r:02x}{g:02x}{b:02x}"


def verdict_for(score):
    """Devuelve (texto, color, fondo) según el score."""
    if score >= 70:
        return "PROBABLE ORIGEN ARTIFICIAL", RED, RED_BG
    if score >= 45:
        return "RESULTADO MIXTO / INCIERTO", AMBER, AMBER_BG
    return "PROBABLE ORIGEN HUMANO", GREEN, GREEN_BG


# ═══════════════════════════════════════════════════════════════════════════
#  WIDGETS PERSONALIZADOS
# ═══════════════════════════════════════════════════════════════════════════

class RadialGauge(tk.Canvas):
    """Medidor circular animado con caps redondeados."""
    def __init__(self, parent, size=210, thickness=16, **kw):
        super().__init__(parent, width=size, height=size,
                         bg=parent.cget("bg"), highlightthickness=0, **kw)
        self.size = size
        self.th   = thickness
        self._target = 0.0
        self._cur    = 0.0
        self._color  = ACCENT
        self._anim   = False
        self._label  = "PROBABILIDAD IA"

    def set_value(self, pct, color):
        self._color  = color
        self._target = max(0.0, min(float(pct), 100.0))
        if not self._anim:
            self._anim = True
            self._step()

    def _step(self):
        diff = self._target - self._cur
        if abs(diff) < 0.4:
            self._cur = self._target
            self._anim = False
            self._draw()
            return
        self._cur += diff * 0.12
        self._draw()
        self.after(14, self._step)

    def _arc_points(self, frac, steps=80):
        # de 225° a -45° (270° de barrido), pasando por arriba
        cx = cy = self.size / 2
        r = (self.size - self.th) / 2 - 4
        a0, sweep = 225.0, -270.0
        pts = []
        for i in range(steps + 1):
            a = math.radians(a0 + sweep * frac * (i / steps))
            x = cx + r * math.cos(a)
            y = cy - r * math.sin(a)
            pts.append((x, y))
        return pts

    def _draw(self):
        self.delete("all")
        # track
        tpts = self._arc_points(1.0)
        flat = [c for p in tpts for c in p]
        self.create_line(*flat, fill=SURFACE3, width=self.th,
                         capstyle="round", joinstyle="round", smooth=True)
        # progreso
        frac = self._cur / 100.0
        if frac > 0.001:
            ppts = self._arc_points(frac)
            pflat = [c for p in ppts for c in p]
            self.create_line(*pflat, fill=self._color, width=self.th,
                             capstyle="round", joinstyle="round", smooth=True)
        # número central
        cx = cy = self.size / 2
        self.create_text(cx, cy - 6, text=f"{round(self._cur)}",
                         font=F_GAUGE, fill=TX)
        self.create_text(cx + self._num_offset(), cy - 6, text="",
                         font=F_GAUGE, fill=TX)
        self.create_text(cx, cy + 30, text="% PROB. IA",
                         font=("Segoe UI", 9), fill=TX3)

    def _num_offset(self):
        return 0


class SmoothBar(tk.Canvas):
    """Barra de progreso redondeada y animada."""
    def __init__(self, parent, height=6, color=ACCENT, track=SURFACE3, **kw):
        super().__init__(parent, height=height,
                         bg=parent.cget("bg"), highlightthickness=0, **kw)
        self.color   = color
        self.track   = track
        self._target = 0.0
        self._cur    = 0.0
        self._anim   = False
        self.bind("<Configure>", self._draw)

    def set_value(self, pct, color=None):
        if color:
            self.color = color
        self._target = max(0.0, min(float(pct), 100.0))
        if not self._anim:
            self._anim = True
            self._step()

    def _step(self):
        diff = self._target - self._cur
        if abs(diff) < 0.3:
            self._cur = self._target
            self._anim = False
            self._draw()
            return
        self._cur += diff * 0.15
        self._draw()
        self.after(14, self._step)

    def _draw(self, *_):
        self.delete("all")
        w, h = self.winfo_width(), self.winfo_height()
        if w < 4:
            return
        r = h // 2
        self._rr(0, 0, w, h, r, self.track)
        fw = max(0, int(w * self._cur / 100))
        if fw >= h:
            self._rr(0, 0, fw, h, r, self.color)

    def _rr(self, x0, y0, x1, y1, r, fill):
        self.create_arc(x0, y0, x0+2*r, y0+2*r, start=90,  extent=90,  fill=fill, outline="")
        self.create_arc(x1-2*r, y0, x1, y0+2*r, start=0,   extent=90,  fill=fill, outline="")
        self.create_arc(x0, y1-2*r, x0+2*r, y1, start=180, extent=90,  fill=fill, outline="")
        self.create_arc(x1-2*r, y1-2*r, x1, y1, start=270, extent=90,  fill=fill, outline="")
        self.create_rectangle(x0+r, y0, x1-r, y1, fill=fill, outline="")
        self.create_rectangle(x0, y0+r, x1, y1-r, fill=fill, outline="")


class HoverButton(tk.Button):
    """Botón con cambio de color suave al pasar el cursor."""
    def __init__(self, parent, bg, hover_bg, fg, hover_fg=None, **kw):
        self._bg, self._hbg = bg, hover_bg
        self._fg, self._hfg = fg, (hover_fg or fg)
        super().__init__(parent, bg=bg, fg=fg, activebackground=hover_bg,
                         activeforeground=self._hfg, relief="flat", bd=0,
                         cursor="hand2", **kw)
        self.bind("<Enter>", self._on)
        self.bind("<Leave>", self._off)

    def _on(self, _):
        if self["state"] != "disabled":
            self.config(bg=self._hbg, fg=self._hfg)

    def _off(self, _):
        if self["state"] != "disabled":
            self.config(bg=self._bg, fg=self._fg)

    def set_palette(self, bg, hover_bg, fg, hover_fg=None):
        self._bg, self._hbg, self._fg = bg, hover_bg, fg
        self._hfg = hover_fg or fg
        self.config(bg=bg, fg=fg, activebackground=hover_bg,
                    activeforeground=self._hfg)


class Tooltip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text   = text
        self.tip    = None
        widget.bind("<Enter>", self.show)
        widget.bind("<Leave>", self.hide)

    def show(self, _=None):
        x = self.widget.winfo_rootx() + 18
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 4
        self.tip = tk.Toplevel(self.widget)
        self.tip.wm_overrideredirect(True)
        self.tip.wm_geometry(f"+{x}+{y}")
        f = tk.Frame(self.tip, bg=BORDER2, padx=1, pady=1)
        f.pack()
        tk.Label(f, text=self.text, font=F_TINY,
                 bg=SURFACE3, fg=TX, padx=10, pady=6,
                 wraplength=240, justify="left").pack()

    def hide(self, _=None):
        if self.tip:
            self.tip.destroy()
            self.tip = None


# ═══════════════════════════════════════════════════════════════════════════
#  PASOS DEL LOADER
# ═══════════════════════════════════════════════════════════════════════════

STEPS = [
    "Tokenizando el corpus de entrada",
    "Construyendo el índice de frases",
    "Analizando patrones léxicos",
    "Calculando entropía y burstiness",
    "Evaluando la estructura sintáctica",
    "Detectando frases GPT por categoría",
    "Analizando las zonas del texto",
    "Midiendo la redundancia semántica",
    "Calculando adjetivos evaluativos",
    "Detectando rasgos humanos",
    "Calibrando el score final",
]


# ═══════════════════════════════════════════════════════════════════════════
#  INFORME HTML  (imprimible a PDF para el jurado)
# ═══════════════════════════════════════════════════════════════════════════

def build_html_report(r: dict) -> str:
    score = r["ai_score"]
    verdict, vcol, _ = verdict_for(score)
    ts = time.strftime("%d/%m/%Y · %H:%M:%S")

    def bar_rows(items, human=False):
        rows = ""
        for name, val in items:
            clean = html.escape(name.replace(" ↓", ""))
            col = GREEN if human else (RED if val > 65 else (AMBER if val > 35 else GREEN))
            rows += f"""
            <tr>
              <td class="sig">{clean}</td>
              <td class="track"><span style="width:{val}%;background:{col}"></span></td>
              <td class="pct">{val}%</td>
            </tr>"""
        return rows

    ia_sig  = [(n, v) for n, v in r["signals"] if "↓" not in n]
    hum_sig = [(n, v) for n, v in r["signals"] if "↓" in n]

    metrics = [
        ("Palabras", r["word_count"]), ("Oraciones", r["sentence_count"]),
        ("Prom. palabras/oración", r["avg_words_per_sentence"]),
        ("Diversidad léxica (TTR)", f'{r["lexical_diversity"]}%'),
        ("Entropía léxica", f'{r["lexical_entropy"]}%'),
        ("Frases IA detectadas", r["ai_phrases_total"]),
        ("Vocabulario GPT", r["gpt_vocab_found"]),
        ("Legibilidad (F-Huerta)", r["readability"]),
        ("Señal de humanidad", f'{r["human_signal"]}%'),
        ("Confianza del análisis", f'{r["confidence"]}%'),
    ]
    metric_cells = "".join(
        f'<div class="m"><span class="ml">{html.escape(str(l))}</span>'
        f'<span class="mv">{html.escape(str(v))}</span></div>'
        for l, v in metrics)

    cats = r["phrase_categories"]
    cat_cells = "".join(
        f'<div class="c"><span class="cl">{html.escape(k.upper())}</span>'
        f'<span class="cv">{v}</span></div>'
        for k, v in cats.items())

    return f"""<!DOCTYPE html><html lang="es"><head><meta charset="utf-8">
<title>Informe JoDi — Análisis de texto</title>
<style>
  * {{ box-sizing:border-box; }}
  body {{ font-family:'Segoe UI',Arial,sans-serif; color:#1c2530;
         background:#f4f6f9; margin:0; padding:40px; }}
  .sheet {{ max-width:820px; margin:0 auto; background:#fff; border-radius:14px;
            box-shadow:0 8px 40px rgba(20,30,50,.10); overflow:hidden; }}
  header {{ background:linear-gradient(135deg,#0f1a2e,#1b2c4a); color:#fff;
            padding:28px 36px; display:flex; justify-content:space-between; align-items:center; }}
  header h1 {{ margin:0; font-size:24px; letter-spacing:.5px; }}
  header h1 span {{ color:#4f9cff; }}
  header .sub {{ font-size:12px; opacity:.7; margin-top:4px; }}
  .ts {{ font-size:11px; opacity:.6; text-align:right; }}
  .hero {{ display:flex; gap:32px; padding:34px 36px; align-items:center;
           border-bottom:1px solid #e7ebf0; }}
  .score {{ font-size:74px; font-weight:700; line-height:1; color:{vcol}; }}
  .score small {{ font-size:24px; }}
  .verdict {{ display:inline-block; padding:8px 16px; border-radius:8px; font-weight:600;
              font-size:14px; color:{vcol}; background:{vcol}1a; margin-bottom:10px; }}
  .conf {{ font-size:13px; color:#5d6b7e; }}
  h2 {{ font-size:12px; letter-spacing:1.5px; text-transform:uppercase; color:#8595a8;
        margin:30px 36px 14px; }}
  .grid {{ display:grid; grid-template-columns:repeat(2,1fr); gap:10px; margin:0 36px; }}
  .m {{ display:flex; justify-content:space-between; padding:12px 14px; background:#f7f9fc;
        border:1px solid #eaeef4; border-radius:8px; }}
  .ml {{ color:#5d6b7e; font-size:13px; }} .mv {{ font-weight:700; font-size:15px; }}
  .cats {{ display:grid; grid-template-columns:repeat(5,1fr); gap:8px; margin:0 36px; }}
  .c {{ text-align:center; padding:12px 6px; background:#f7f9fc; border:1px solid #eaeef4;
        border-radius:8px; }}
  .cl {{ display:block; font-size:10px; color:#8595a8; letter-spacing:.5px; }}
  .cv {{ display:block; font-size:22px; font-weight:700; margin-top:4px; }}
  table {{ width:calc(100% - 72px); margin:0 36px; border-collapse:collapse; }}
  td {{ padding:6px 4px; font-size:13px; vertical-align:middle; }}
  td.sig {{ color:#3a4658; width:48%; }}
  td.track {{ width:42%; }}
  td.track span {{ display:block; height:7px; border-radius:4px; }}
  td.track {{ background:#eaeef4; border-radius:4px; }}
  td.pct {{ text-align:right; font-weight:600; color:#5d6b7e; width:10%; }}
  footer {{ margin-top:34px; padding:18px 36px; background:#f7f9fc; border-top:1px solid #e7ebf0;
            font-size:11px; color:#8595a8; display:flex; justify-content:space-between; }}
  .note {{ margin:24px 36px; padding:14px 16px; background:#fff8e6; border:1px solid #f3e3b3;
           border-radius:8px; font-size:12px; color:#7a6a30; }}
  @media print {{ body {{ background:#fff; padding:0; }} .sheet {{ box-shadow:none; }} }}
</style></head><body>
<div class="sheet">
  <header>
    <div><h1>Jo<span>Di</span> · Informe de análisis</h1>
      <div class="sub">Detector de contenido generado por inteligencia artificial · v6.0</div></div>
    <div class="ts">Generado<br>{ts}</div>
  </header>
  <div class="hero">
    <div class="score">{score}<small>%</small></div>
    <div>
      <div class="verdict">{html.escape(verdict)}</div>
      <div class="conf">Confianza del análisis: <b>{r["confidence"]}%</b> ·
        {r["word_count"]:,} palabras · {r["sentence_count"]} oraciones</div>
    </div>
  </div>
  <h2>Métricas del documento</h2>
  <div class="grid">{metric_cells}</div>
  <h2>Frases detectadas por categoría</h2>
  <div class="cats">{cat_cells}</div>
  <h2>Señales que sugieren origen artificial</h2>
  <table>{bar_rows(ia_sig)}</table>
  <h2>Rasgos humanos (reducen el score)</h2>
  <table>{bar_rows(hum_sig, human=True)}</table>
  <div class="note"><b>Nota metodológica.</b> Este informe es una estimación estadística
  basada en patrones léxicos y estructurales. No constituye prueba concluyente de autoría;
  debe interpretarse junto con el juicio del evaluador.</div>
  <footer><span>JoDi v6.0 — Motor de análisis lingüístico</span>
    <span>spaCy: {"activo" if r["spacy_active"] else "inactivo"} ·
          NLTK: {"activo" if r["nltk_active"] else "inactivo"}</span></footer>
</div></body></html>"""


# ═══════════════════════════════════════════════════════════════════════════
#  APP PRINCIPAL
# ═══════════════════════════════════════════════════════════════════════════

class DetectorApp(tk.Tk):

    def __init__(self):
        super().__init__()
        self.title("JoDi · Detector de Texto Artificial · v6.0")
        self.configure(bg=BG)
        self._center(1020, 880)
        self.minsize(880, 680)
        self._extracted = ""
        self._last_result = None
        self._setup_ttk()
        self._build_ui()

    def _center(self, w, h):
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        x, y = (sw - w) // 2, max(0, (sh - h) // 2 - 20)
        self.geometry(f"{w}x{h}+{x}+{y}")

    def _setup_ttk(self):
        s = ttk.Style(self)
        s.theme_use("clam")
        s.configure("Vertical.TScrollbar", background=SURFACE2, troughcolor=BG,
                    bordercolor=BG, arrowcolor=TX3, width=9, relief="flat")
        s.map("Vertical.TScrollbar", background=[("active", SURFACE3)])

    # ── Contenedor con scroll ─────────────────────────────────────────────
    def _build_ui(self):
        outer = tk.Frame(self, bg=BG)
        outer.pack(fill="both", expand=True)
        self._cv = tk.Canvas(outer, bg=BG, highlightthickness=0)
        sb = ttk.Scrollbar(outer, orient="vertical",
                           command=self._cv.yview, style="Vertical.TScrollbar")
        self._cv.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self._cv.pack(side="left", fill="both", expand=True)
        self._sf = tk.Frame(self._cv, bg=BG)
        self._win = self._cv.create_window((0, 0), window=self._sf, anchor="nw")
        self._sf.bind("<Configure>",
            lambda e: self._cv.configure(scrollregion=self._cv.bbox("all")))
        self._cv.bind("<Configure>",
            lambda e: self._cv.itemconfig(self._win, width=e.width))
        self._cv.bind_all("<MouseWheel>",
            lambda e: self._cv.yview_scroll(-1 * (e.delta // 120), "units"))

        self._build_header(self._sf)
        self._build_input(self._sf)
        self._build_loader(self._sf)
        self._build_result(self._sf)

    # ── Helpers de layout ─────────────────────────────────────────────────
    def _card(self, parent, pady=(0, 16)):
        shell = tk.Frame(parent, bg=BG)
        shell.pack(fill="x", padx=32, pady=pady)
        border = tk.Frame(shell, bg=BORDER)
        border.pack(fill="x")
        inner = tk.Frame(border, bg=SURFACE)
        inner.pack(fill="both", expand=True, padx=1, pady=1)
        return inner

    def _section(self, parent, text, pady=(0, 12)):
        row = tk.Frame(parent, bg=parent.cget("bg"))
        row.pack(fill="x", pady=pady)
        tk.Frame(row, bg=ACCENT, width=3, height=14).pack(side="left", padx=(0, 9))
        tk.Label(row, text=text.upper(), font=F_SECT, fg=TX2,
                 bg=parent.cget("bg")).pack(side="left")
        return row

    # ── Header ────────────────────────────────────────────────────────────
    def _build_header(self, parent):
        hdr = tk.Frame(parent, bg=BG)
        hdr.pack(fill="x", padx=32, pady=(26, 8))

        left = tk.Frame(hdr, bg=BG)
        left.pack(side="left")

        logo_row = tk.Frame(left, bg=BG)
        logo_row.pack(anchor="w")

        mark = tk.Canvas(logo_row, width=38, height=38, bg=BG, highlightthickness=0)
        mark.pack(side="left", padx=(0, 12))
        self._draw_logo_mark(mark)

        wm = tk.Frame(logo_row, bg=BG)
        wm.pack(side="left")
        name = tk.Frame(wm, bg=BG)
        name.pack(anchor="w")
        tk.Label(name, text="Jo", font=F_LOGO, fg=TX, bg=BG).pack(side="left")
        tk.Label(name, text="Di", font=F_LOGO, fg=ACCENT, bg=BG).pack(side="left")
        tk.Label(wm, text="Detector de contenido generado por IA",
                 font=F_SMALL, fg=TX3, bg=BG).pack(anchor="w")

        # Badges de motores
        badges = tk.Frame(hdr, bg=BG)
        badges.pack(side="right", anchor="ne")
        tk.Label(badges, text="MOTORES", font=F_TINY, fg=TX3, bg=BG).pack(anchor="e")
        chips = tk.Frame(badges, bg=BG)
        chips.pack(anchor="e", pady=(5, 0))
        for lib, ok in [("spaCy", SPACY_OK), ("NLTK", NLTK_OK),
                        ("DOCX", DOCX_OK), ("PDF", PDF_OK)]:
            col = GREEN if ok else TX3
            dot = "●" if ok else "○"
            chip = tk.Frame(chips, bg=SURFACE2, padx=9, pady=4)
            chip.pack(side="left", padx=(0, 6))
            tk.Label(chip, text=dot, font=("Segoe UI", 7), fg=col, bg=SURFACE2).pack(side="left", padx=(0, 4))
            tk.Label(chip, text=lib, font=F_TINY, fg=TX2, bg=SURFACE2).pack(side="left")

        tk.Frame(parent, bg=BORDER, height=1).pack(fill="x", padx=32, pady=(14, 18))

    def _draw_logo_mark(self, cv):
        # hexágono con acento — marca limpia
        cx, cy, r = 19, 19, 16
        pts = []
        for i in range(6):
            a = math.radians(60 * i - 30)
            pts += [cx + r * math.cos(a), cy + r * math.sin(a)]
        cv.create_polygon(*pts, fill=SURFACE2, outline=ACCENT, width=2)
        cv.create_text(cx, cy, text="J", font=("Segoe UI Semibold", 15), fill=ACCENT)

    # ── Entrada ───────────────────────────────────────────────────────────
    def _build_input(self, parent):
        self._input_outer = tk.Frame(parent, bg=BG)
        self._input_outer.pack(fill="x")
        card = self._card(self._input_outer)

        pad = tk.Frame(card, bg=SURFACE, padx=24, pady=22)
        pad.pack(fill="x")

        head = tk.Frame(pad, bg=SURFACE)
        head.pack(fill="x")
        tk.Label(head, text="Analizar texto", font=F_H1, fg=TX, bg=SURFACE).pack(side="left")
        tk.Label(head, text="PDF · DOCX · TXT · texto pegado",
                 font=F_SMALL, fg=TX3, bg=SURFACE).pack(side="right")

        # Botón de carga
        upload = HoverButton(
            pad, bg=SURFACE2, hover_bg=SURFACE3, fg=ACCENT,
            text="⭱   Cargar archivo", font=F_BTN,
            command=self._load_file, pady=12,
        )
        upload.pack(fill="x", pady=(16, 0))
        upload.config(highlightbackground=BORDER2, highlightthickness=1)
        Tooltip(upload, "Acepta archivos PDF, DOCX, DOC y TXT")

        self._file_lbl = tk.Label(pad, text="", font=F_SMALL, fg=ACCENT, bg=SURFACE)
        self._file_lbl.pack(anchor="w", pady=(8, 0))

        # Separador OR
        orr = tk.Frame(pad, bg=SURFACE)
        orr.pack(fill="x", pady=14)
        tk.Frame(orr, bg=BORDER, height=1).pack(side="left", fill="x", expand=True, pady=8)
        tk.Label(orr, text="  o pega el texto  ", font=F_SMALL, fg=TX3, bg=SURFACE).pack(side="left")
        tk.Frame(orr, bg=BORDER, height=1).pack(side="left", fill="x", expand=True, pady=8)

        # Textarea
        ta_border = tk.Frame(pad, bg=BORDER)
        ta_border.pack(fill="x")
        ta_in = tk.Frame(ta_border, bg=SURFACE2)
        ta_in.pack(fill="both", padx=1, pady=1)
        self._ta = tk.Text(
            ta_in, height=9, font=("Segoe UI", 10),
            bg=SURFACE2, fg=TX, insertbackground=ACCENT,
            relief="flat", bd=0, padx=14, pady=12, wrap="word", spacing3=4,
            selectbackground=ACCENT_DK, selectforeground="#ffffff",
        )
        self._ta.pack(fill="both")
        self._ph = "Pega aquí el texto que quieres analizar…"
        self._ta.insert("1.0", self._ph)
        self._ta.config(fg=TX3)
        self._ta.bind("<FocusIn>",    self._ta_in)
        self._ta.bind("<FocusOut>",   self._ta_out)
        self._ta.bind("<<Modified>>", self._ta_mod)
        self._ta.bind("<FocusIn>", self._ta_border_on(ta_border), add="+")
        self._ta.bind("<FocusOut>", self._ta_border_off(ta_border), add="+")

        footer = tk.Frame(pad, bg=SURFACE)
        footer.pack(fill="x", pady=(8, 0))
        self._char_lbl = tk.Label(footer, text="0 caracteres", font=F_SMALL, fg=TX3, bg=SURFACE)
        self._char_lbl.pack(side="left")
        tk.Label(footer, text="mínimo 80 caracteres", font=F_SMALL, fg=TX3, bg=SURFACE).pack(side="right")

        # CTA
        self._analyze_btn = HoverButton(
            pad, bg=SURFACE3, hover_bg=SURFACE3, fg=TX3,
            text="Analizar texto", font=("Segoe UI Semibold", 11),
            command=self._start, pady=13, state="disabled",
        )
        self._analyze_btn.pack(fill="x", pady=(16, 2))

    def _ta_border_on(self, border):
        return lambda e: border.config(bg=ACCENT_DK)

    def _ta_border_off(self, border):
        return lambda e: border.config(bg=BORDER)

    # ── Loader ────────────────────────────────────────────────────────────
    def _build_loader(self, parent):
        self._loader_outer = tk.Frame(parent, bg=BG)
        card = self._card(self._loader_outer)
        pad = tk.Frame(card, bg=SURFACE, padx=24, pady=22)
        pad.pack(fill="x")

        head = tk.Frame(pad, bg=SURFACE)
        head.pack(fill="x")
        tk.Label(head, text="Procesando", font=F_H1, fg=TX, bg=SURFACE).pack(side="left")
        self._load_pct = tk.Label(head, text="0%", font=F_H1, fg=ACCENT, bg=SURFACE)
        self._load_pct.pack(side="right")

        self._load_bar = SmoothBar(pad, height=6, color=ACCENT)
        self._load_bar.pack(fill="x", pady=(16, 12))

        self._load_msg = tk.Label(pad, text="", font=F_BODY, fg=TX2, bg=SURFACE, anchor="w")
        self._load_msg.pack(fill="x")

        self._log_frame = tk.Frame(pad, bg=SURFACE)
        self._log_frame.pack(fill="x", pady=(10, 0))
        self._log_lbls = []
        for _ in range(6):
            l = tk.Label(self._log_frame, text="", font=F_MONO, fg=TX3, bg=SURFACE, anchor="w")
            l.pack(fill="x", pady=1)
            self._log_lbls.append(l)
        self._log_i = 0

    # ── Resultado ─────────────────────────────────────────────────────────
    def _build_result(self, parent):
        self._result_outer = tk.Frame(parent, bg=BG)
        rw = {}
        self._rw = rw

        # --- Tarjeta principal: gauge + veredicto ---
        card = self._card(self._result_outer)
        pad = tk.Frame(card, bg=SURFACE, padx=24, pady=22)
        pad.pack(fill="x")

        top = tk.Frame(pad, bg=SURFACE)
        top.pack(fill="x")
        tk.Label(top, text="Resultado del análisis", font=F_H1, fg=TX, bg=SURFACE).pack(side="left")
        rw["ts"] = tk.Label(top, text="", font=F_SMALL, fg=TX3, bg=SURFACE)
        rw["ts"].pack(side="right")

        hero = tk.Frame(pad, bg=SURFACE)
        hero.pack(fill="x", pady=(18, 4))

        rw["gauge"] = RadialGauge(hero, size=200)
        rw["gauge"].pack(side="left", padx=(0, 28))

        right = tk.Frame(hero, bg=SURFACE)
        right.pack(side="left", fill="both", expand=True)

        rw["verdict"] = tk.Label(right, text="—", font=("Segoe UI Semibold", 13),
                                  fg=TX, bg=SURFACE2, padx=16, pady=10)
        rw["verdict"].pack(anchor="w", pady=(14, 16))

        tk.Label(right, text="CONFIANZA DEL ANÁLISIS", font=F_TINY, fg=TX3, bg=SURFACE).pack(anchor="w")
        rw["conf_bar"] = SmoothBar(right, height=6, color=ACCENT)
        rw["conf_bar"].pack(fill="x", pady=(5, 4))
        rw["conf_lbl"] = tk.Label(right, text="", font=F_SMALL, fg=TX2, bg=SURFACE)
        rw["conf_lbl"].pack(anchor="w")

        # --- Zonas ---
        zcard = self._card(self._result_outer)
        zpad = tk.Frame(zcard, bg=SURFACE, padx=24, pady=20)
        zpad.pack(fill="x")
        self._section(zpad, "Análisis por zonas del texto")
        rw["zones"] = tk.Frame(zpad, bg=SURFACE)
        rw["zones"].pack(fill="x")

        # --- Métricas ---
        mcard = self._card(self._result_outer)
        mpad = tk.Frame(mcard, bg=SURFACE, padx=24, pady=20)
        mpad.pack(fill="x")
        self._section(mpad, "Métricas del documento")
        rw["metrics"] = tk.Frame(mpad, bg=SURFACE)
        rw["metrics"].pack(fill="x")

        # --- Categorías ---
        ccard = self._card(self._result_outer)
        cpad = tk.Frame(ccard, bg=SURFACE, padx=24, pady=20)
        cpad.pack(fill="x")
        self._section(cpad, "Frases detectadas por categoría")
        rw["cats"] = tk.Frame(cpad, bg=SURFACE)
        rw["cats"].pack(fill="x")

        # --- Señales ---
        scard = self._card(self._result_outer)
        spad = tk.Frame(scard, bg=SURFACE, padx=24, pady=20)
        spad.pack(fill="x")
        sec = self._section(spad, "Señales detectadas", pady=(0, 6))
        tk.Label(sec, text="↑ más alto = más probable IA", font=F_TINY,
                 fg=TX3, bg=SURFACE).pack(side="right")
        rw["signals"] = tk.Frame(spad, bg=SURFACE)
        rw["signals"].pack(fill="x", pady=(8, 0))

        # --- Acciones ---
        actions = tk.Frame(self._result_outer, bg=BG)
        actions.pack(fill="x", padx=32, pady=(2, 30))
        actions.columnconfigure(0, weight=1)
        actions.columnconfigure(1, weight=1)

        rw["export_btn"] = HoverButton(
            actions, bg=ACCENT, hover_bg=ACCENT_HV, fg="#06101f", hover_fg="#06101f",
            text="⬓   Exportar informe (PDF)", font=F_BTN,
            command=self._export_report, pady=12,
        )
        rw["export_btn"].grid(row=0, column=0, sticky="ew", padx=(0, 6))

        reset = HoverButton(
            actions, bg=SURFACE, hover_bg=SURFACE2, fg=TX2,
            text="↺   Analizar otro texto", font=F_BTN,
            command=self._reset, pady=12,
        )
        reset.config(highlightbackground=BORDER, highlightthickness=1)
        reset.grid(row=0, column=1, sticky="ew", padx=(6, 0))

    # ── Eventos del textarea ──────────────────────────────────────────────
    def _ta_in(self, _):
        if self._ta.get("1.0", "end-1c") == self._ph:
            self._ta.delete("1.0", "end")
            self._ta.config(fg=TX)

    def _ta_out(self, _):
        if not self._ta.get("1.0", "end-1c").strip():
            self._ta.insert("1.0", self._ph)
            self._ta.config(fg=TX3)

    def _ta_mod(self, _):
        self._ta.edit_modified(False)
        text = self._ta.get("1.0", "end-1c")
        is_ph = text == self._ph
        n = 0 if is_ph else len(text)
        self._char_lbl.config(
            text=f"{n:,} caracteres",
            fg=ACCENT if n >= 80 else TX3,
        )
        self._set_cta_enabled(n >= 80 or len(self._extracted) >= 80)

    def _set_cta_enabled(self, ok):
        if ok:
            self._analyze_btn.config(state="normal")
            self._analyze_btn.set_palette(ACCENT, ACCENT_HV, "#06101f", "#06101f")
        else:
            self._analyze_btn.config(state="disabled")
            self._analyze_btn.set_palette(SURFACE3, SURFACE3, TX3, TX3)

    # ── Carga de archivo ──────────────────────────────────────────────────
    def _load_file(self):
        path = filedialog.askopenfilename(
            title="Seleccionar archivo",
            filetypes=[("Soportados", "*.pdf *.docx *.doc *.txt"), ("Todos", "*.*")],
        )
        if not path:
            return
        try:
            self._extracted = extract_file(path)
            preview = self._extracted[:900].replace("\n", " ")
            self._ta.delete("1.0", "end")
            self._ta.config(fg=TX)
            self._ta.insert("1.0", preview + ("…" if len(self._extracted) > 900 else ""))
            n = len(self._extracted)
            self._file_lbl.config(text=f"✓ {os.path.basename(path)}  ·  {n:,} caracteres")
            self._char_lbl.config(text=f"{n:,} caracteres", fg=ACCENT)
            self._set_cta_enabled(True)
        except ImportError as e:
            messagebox.showerror("Librería faltante", str(e))
        except Exception as e:
            messagebox.showerror("Error al leer archivo", str(e))

    # ── Análisis ──────────────────────────────────────────────────────────
    def _start(self):
        text = self._extracted or self._ta.get("1.0", "end-1c")
        if not text or len(text) < 80 or text == self._ph:
            messagebox.showwarning("Texto insuficiente",
                                   "Se necesitan al menos 80 caracteres.")
            return
        self._input_outer.pack_forget()
        self._result_outer.pack_forget()
        self._loader_outer.pack(fill="x")
        self._log_i = 0
        for l in self._log_lbls:
            l.config(text="")
        self._load_bar.set_value(0)
        self._load_pct.config(text="0%")

        def run():
            total = len(STEPS)
            for i, msg in enumerate(STEPS):
                pct = int((i + 1) / total * 85)
                self.after(0, lambda m=msg, p=pct: self._upd_loader(m, p))
                time.sleep(0.28)
            result = analyze_text(text)
            self.after(0, lambda: self._load_bar.set_value(100))
            self.after(0, lambda: self._load_pct.config(text="100%"))
            self.after(350, lambda: self._show_result(result))

        threading.Thread(target=run, daemon=True).start()

    def _upd_loader(self, msg, pct):
        self._load_msg.config(text=f"{msg}…")
        self._load_bar.set_value(pct)
        self._load_pct.config(text=f"{pct}%")
        idx = self._log_i % len(self._log_lbls)
        fade = [TX, TX2, TX3, SURFACE3, SURFACE2, SURFACE2]
        for j, l in enumerate(self._log_lbls):
            age = (self._log_i - j) % len(self._log_lbls)
            l.config(fg=fade[min(age, len(fade) - 1)])
        self._log_lbls[idx].config(text=f"   ✓  {msg}", fg=ACCENT)
        self._log_i += 1

    # ── Mostrar resultado ─────────────────────────────────────────────────
    def _show_result(self, r):
        self._last_result = r
        self._loader_outer.pack_forget()
        self._result_outer.pack(fill="x")
        rw = self._rw
        score = r["ai_score"]
        verdict, vcol, vbg = verdict_for(score)

        rw["ts"].config(text=f"{time.strftime('%H:%M:%S')}  ·  {r['word_count']:,} palabras")
        rw["gauge"].set_value(score, vcol)
        rw["verdict"].config(text=verdict, fg=vcol, bg=vbg)
        rw["conf_bar"].set_value(r["confidence"], ACCENT)
        rw["conf_lbl"].config(text=f"{r['confidence']}%  ·  {r['sentence_count']} oraciones analizadas")

        # Zonas
        zf = rw["zones"]
        for w in zf.winfo_children():
            w.destroy()
        zones = r.get("zones", {})
        zlist = [("INTRODUCCIÓN", zones.get("intro", 0), "apertura y encuadre"),
                 ("CUERPO", zones.get("body", 0), "desarrollo central"),
                 ("CIERRE", zones.get("closing", 0), "conclusión")]
        for i, (name, val, tip) in enumerate(zlist):
            pct = round(val * 100)
            col = RED if pct > 60 else AMBER if pct > 30 else GREEN
            cell = tk.Frame(zf, bg=SURFACE2, padx=14, pady=12)
            cell.grid(row=0, column=i, padx=(0, 8) if i < 2 else 0, sticky="ew")
            zf.columnconfigure(i, weight=1)
            tk.Label(cell, text=name, font=F_TINY, fg=TX3, bg=SURFACE2).pack(anchor="w")
            tk.Label(cell, text=f"{pct}%", font=("Segoe UI Semibold", 22),
                     fg=col, bg=SURFACE2).pack(anchor="w", pady=(2, 2))
            bar = SmoothBar(cell, height=4, color=col)
            bar.pack(fill="x", pady=(0, 6))
            bar.after(60, lambda b=bar, v=pct, c=col: b.set_value(v, c))
            tk.Label(cell, text=tip, font=F_TINY, fg=TX3, bg=SURFACE2).pack(anchor="w")

        # Métricas
        mf = rw["metrics"]
        for w in mf.winfo_children():
            w.destroy()
        metrics = [
            ("PALABRAS", str(r["word_count"]), None),
            ("ORACIONES", str(r["sentence_count"]), None),
            ("PROM/ORACIÓN", str(r["avg_words_per_sentence"]), "palabras"),
            ("DIVERSIDAD", f"{r['lexical_diversity']}%", "TTR léxico"),
            ("ENTROPÍA", f"{r['lexical_entropy']}%", "normalizada"),
            ("FRASES IA", str(r["ai_phrases_total"]), "detectadas"),
            ("VOCAB GPT", str(r["gpt_vocab_found"]), "palabras"),
            ("HUMANIDAD", f"{r['human_signal']}%", "señal humana"),
        ]
        cols = 4
        for i, (lbl, val, sub) in enumerate(metrics):
            ri, ci = i // cols, i % cols
            cell = tk.Frame(mf, bg=SURFACE2, padx=14, pady=11)
            cell.grid(row=ri, column=ci, padx=(0, 8) if ci < cols - 1 else 0,
                      pady=(0, 8), sticky="ew")
            mf.columnconfigure(ci, weight=1)
            tk.Label(cell, text=lbl, font=F_TINY, fg=TX3, bg=SURFACE2).pack(anchor="w")
            tk.Label(cell, text=val, font=F_NUM, fg=TX, bg=SURFACE2).pack(anchor="w")
            if sub:
                tk.Label(cell, text=sub, font=F_TINY, fg=TX3, bg=SURFACE2).pack(anchor="w")

        # Categorías
        cf = rw["cats"]
        for w in cf.winfo_children():
            w.destroy()
        CAT = {
            "apertura":   ("APERTURA", "Frases de inicio típicas de ensayos GPT"),
            "cierre":     ("CIERRE", "Frases de conclusión formulaicas"),
            "transición": ("TRANSICIÓN", "Conectores y transiciones abusados"),
            "énfasis":    ("ÉNFASIS", "Frases de énfasis y evaluación"),
            "clichés":    ("CLICHÉS", "Expresiones genéricas y tópicos"),
        }
        for i, (key, (short, tip)) in enumerate(CAT.items()):
            hits = r["phrase_categories"].get(key, 0)
            col = RED if hits >= 3 else AMBER if hits >= 1 else TX3
            cell = tk.Frame(cf, bg=SURFACE2, padx=10, pady=12)
            cell.grid(row=0, column=i, padx=(0, 8) if i < 4 else 0, sticky="ew")
            cf.columnconfigure(i, weight=1)
            tk.Label(cell, text=short, font=F_TINY, fg=TX3, bg=SURFACE2).pack(anchor="w")
            tk.Label(cell, text=str(hits), font=("Segoe UI Semibold", 24),
                     fg=col, bg=SURFACE2).pack(anchor="w")
            tk.Label(cell, text="coincidencias", font=F_TINY, fg=TX3, bg=SURFACE2).pack(anchor="w")
            Tooltip(cell, tip)

        # Señales
        sf = rw["signals"]
        for w in sf.winfo_children():
            w.destroy()
        ia_signals  = [(n, v) for n, v in r["signals"] if "↓" not in n]
        hum_signals = [(n, v) for n, v in r["signals"] if "↓" in n]

        for name, sv in ia_signals:
            self._signal_row(sf, name, sv, human=False)

        if hum_signals:
            sep = tk.Frame(sf, bg=SURFACE)
            sep.pack(fill="x", pady=(10, 6))
            tk.Frame(sep, bg=BORDER, height=1).pack(side="left", fill="x", expand=True, pady=7)
            tk.Label(sep, text="  PENALIZACIONES — REDUCEN EL SCORE  ",
                     font=F_TINY, fg=TX3, bg=SURFACE).pack(side="left")
            tk.Frame(sep, bg=BORDER, height=1).pack(side="left", fill="x", expand=True, pady=7)
            for name, sv in hum_signals:
                self._signal_row(sf, name.replace(" ↓", ""), sv, human=True)

        self._cv.yview_moveto(0)

    def _signal_row(self, parent, name, sv, human):
        col = GREEN if human else (RED if sv > 65 else AMBER if sv > 35 else GREEN)
        row = tk.Frame(parent, bg=SURFACE)
        row.pack(fill="x", pady=3)
        tk.Label(row, text=name, font=F_SMALL, fg=GREEN if human else TX2,
                 bg=SURFACE, width=34, anchor="w").pack(side="left")
        bar = SmoothBar(row, height=6, color=col, width=200)
        bar.pack(side="left", padx=(8, 10), fill="x", expand=True)
        bar.after(70, lambda b=bar, v=sv, c=col: b.set_value(v, c))
        tk.Label(row, text=f"{sv:>3}%", font=F_MONO,
                 fg=col if (sv > 50 or human) else TX2, bg=SURFACE,
                 width=5, anchor="e").pack(side="left")

    # ── Exportar informe ──────────────────────────────────────────────────
    def _export_report(self):
        if not self._last_result:
            return
        html_str = build_html_report(self._last_result)
        default = f"informe_jodi_{time.strftime('%Y%m%d_%H%M%S')}.html"
        path = filedialog.asksaveasfilename(
            title="Guardar informe",
            defaultextension=".html",
            initialfile=default,
            filetypes=[("Página HTML (imprimible a PDF)", "*.html")],
        )
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(html_str)
            webbrowser.open("file://" + os.path.abspath(path))
            messagebox.showinfo(
                "Informe generado",
                "El informe se abrió en tu navegador.\n\n"
                "Para obtener el PDF:  Ctrl+P  →  Destino: «Guardar como PDF».",
            )
        except Exception as e:
            messagebox.showerror("Error al exportar", str(e))

    # ── Reset ─────────────────────────────────────────────────────────────
    def _reset(self):
        self._extracted = ""
        self._last_result = None
        self._result_outer.pack_forget()
        self._loader_outer.pack_forget()
        self._ta.delete("1.0", "end")
        self._ta.insert("1.0", self._ph)
        self._ta.config(fg=TX3)
        self._file_lbl.config(text="")
        self._char_lbl.config(text="0 caracteres", fg=TX3)
        self._set_cta_enabled(False)
        self._log_i = 0
        for l in self._log_lbls:
            l.config(text="")
        self._input_outer.pack(fill="x")
        self._cv.yview_moveto(0)


# ═══════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    app = DetectorApp()
    app.mainloop()
