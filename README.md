# 🌳 Imprés de l'Arbre Genealògic (Optimitzat per A4)

Aquesta és una aplicació en Python basada en Streamlit dissenyada per generar arbres genealògics elegants i nets a partir de fitxers GEDCOM. L'objectiu principal és la creació d'arbres optimitzats per a la seva impressió en format A4, fent servir un enrutament ortogonal de "bus perfecte" per a les línies de descendència.

## ✨ Característiques

- **Layout de Bus Perfecte**: Enrutament ortogonal (angles de 90°) matemàticament alineat per a una estètica neta i professional.
- **Mode Compacte**: Optimitza l'espai vertical i horitzontal per encabir el màxim d'informació sense perdre llegibilitat.
- **Visualització Interactiva**: Visor SVG amb funcions de zoom, desplaçament (pan) i ajust automàtic a la finestra.
- **Exportació de Qualitat**: Generació de fitxers SVG (vectorial) i PDF optimitzats per a impressió en A4.
- **Personalització Total**:
  - Tria de la persona arrel amb cerca predictiva.
  - Direccions: Descendents, Avantpassats o ambdós.
  - Temes de colors i diferenciació per gènere.
  - Control de profunditat de generacions.
  - Vores arrodonides o rectes.
  - Amplada de nodes ajustable.

## 🚀 Instal·lació

### 1. Prerequisits
Has de tenir instal·lat **Python 3.8+** i **Graphviz** al teu sistema.

- **Graphviz**: És el motor que dibuixa l'arbre. Descarrega'l a [graphviz.org/download](https://graphviz.org/download/) i assegura't que s'afegeix al PATH del teu sistema.

### 2. Instal·lar dependències
Clona aquest repositori i instal·la els paquets necessaris:

```bash
pip install -r requirements.txt
```

*(El fitxer `requirements.txt` inclou streamlit, graphviz i ged4py)*

## 🛠️ Com fer-ho anar

Executa l'aplicació amb Streamlit des del terminal:

```bash
python -m streamlit run app.py
```

S'obrirà una pestanya al teu navegador on podràs:
1. Pujar el teu fitxer `.ged`.
2. Escollir la persona arrel (comença a escriure el seu nom per filtrar).
3. Ajustar el disseny i els colors segons les teves preferències.
4. Descarregar l'arbre final en format SVG o PDF.

## 📁 Estructura del projecte

- `app.py`: Interfície d'usuari i lògica principal de Streamlit.
- `renderer.py`: Motor de generació de grafs fent servir Graphviz.
- `parser.py`: Lògica d'extracció i processament de dades GEDCOM.
- `tests_and_examples/`: Scripts de prova i exemples generats durant el desenvolupament.

---
Creat amb 💙 per organitzar i imprimir la teva història familiar.
