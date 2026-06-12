# JoDi · Detector de Texto Artificial

Aplicación que estima si un texto fue **escrito por una persona** o **generado por inteligencia
artificial** (ChatGPT y similares), mediante análisis lingüístico: **17 métricas** y más de
**200 señales** léxicas y estructurales.

🔗 **Demo en vivo:** _(se completa al activar GitHub Pages — ver más abajo)_

![JoDi](https://img.shields.io/badge/JoDi-v6.5-c46bff) ![web](https://img.shields.io/badge/web-100%25%20navegador-3ee9b0)

---

## ✨ Cómo funciona

El motor combina señales de varias familias y las pondera en un único *score* de probabilidad IA:

- **Frases plantilla de GPT** (apertura, cierre, transiciones, énfasis, clichés)
- **Vocabulario sobreusado** por modelos de lenguaje
- **Uniformidad de oraciones** y **burstiness** (variación del ritmo)
- **Entropía léxica**, **diversidad (TTR)** y **n-gramas repetidos**
- **Voz pasiva/impersonal**, **redundancia semántica** y **sintaxis balanceada**
- **Análisis por zonas** del texto (introducción / cuerpo / cierre)
- **Contrapeso de rasgos humanos** (muletillas, puntuación informal) que reduce el score

> JoDi entrega una **estimación estadística**, no una prueba concluyente de autoría.

## 🗂️ Versiones incluidas

| Versión | Archivo | Descripción |
|---|---|---|
| **Web** (estática) | [`docs/`](docs/) | Sitio en HTML/CSS/JS, motor portado a JavaScript. Se publica en GitHub Pages. **El texto nunca sale del navegador.** |
| **Escritorio (web UI)** | [`detector_web.py`](detector_web.py) | Misma interfaz dentro de una ventana de escritorio (pywebview), motor en Python. |
| **Escritorio (tkinter)** | [`detector_ia_v6.py`](detector_ia_v6.py) | Interfaz nativa tkinter con medidor circular y exportación de informe. |

## 🚀 Publicar la web (GitHub Pages)

1. Sube este repositorio a GitHub.
2. En GitHub: **Settings → Pages**.
3. En *Source* elige **Deploy from a branch**, rama **main**, carpeta **/docs**.
4. Guarda. En 1-2 minutos tu sitio estará en:
   `https://TU-USUARIO.github.io/NOMBRE-DEL-REPO/`

## 💻 Ejecutar las versiones de escritorio

```bash
pip install -r requirements.txt
python -m spacy download es_core_news_sm   # opcional, mejora el análisis

python detector_web.py      # versión con interfaz web en ventana
python detector_ia_v6.py    # versión tkinter
```

## 🔒 Privacidad

La versión web ejecuta **todo el análisis en tu navegador** (JavaScript). Ningún texto se envía
a ningún servidor.

## 📄 Licencia

Proyecto académico. Uso educativo.
