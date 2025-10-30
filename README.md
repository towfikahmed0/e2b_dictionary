# 🌐 e2b_dictionary

**An English → Bangla Dictionary Generator built with Python, BeautifulSoup, and multi‑source linguistic APIs.**
<br>
Developed by **Towfik Ahmed Razin**

---

## 🧭 Overview

`e2b_dictionary` is a high‑performance, fully automated English‑to‑Bangla dictionary generator.
It crawls webpages, extracts unique English words, retrieves Bangla translations, gathers English definitions, synonyms, and antonyms, and merges everything into a structured JSON database.

The project combines **web scraping, concurrency, linguistic normalization**, and **API‑driven enrichment** to build one of the most comprehensive open‑source bilingual lexicons in Python.

---

## ✨ Key Features

* ⚡ **Multithreaded processing** – handles thousands of words efficiently
* 🧠 **Smart base‑form detection** – identifies roots like `running → run`, `studies → study`
* 🎨 **Color‑coded logging** via `colorama` for clear runtime feedback
* 🔁 **Automatic dictionary merging** – avoids duplicates and preserves previous data
* 🪶 **GitHub sync fallback** – downloads the latest version if local data is missing
* 🌐 **Hybrid data pipeline** – combines web scraping with open dictionary APIs
* 💬 **Bangla meaning extraction** from publicly available bilingual sources

---

## ⚙️ Installation & Setup

### 1️⃣ Clone the repository

```bash
git clone https://github.com/towfikahmed0/e2b_dictionary.git
cd e2b_dictionary
```

### 2️⃣ Install dependencies

```bash
pip install -r requirements.txt
```

### 3️⃣ Run the program

```bash
python word_fetcher.py
```

### 4️⃣ Provide a webpage URL

Enter any valid URL containing English text. The script will automatically:

1. Scrape the page and extract clean English words
2. Filter and normalize them
3. Fetch Bangla meanings, definitions, synonyms, and antonyms
4. Merge everything into your local `dictionary.json`

---

## 🧾 Example Output

```json
[
  {
    "en": "accessibility",
    "bn": ["প্রবেশযোগ্যতা", "সহজপ্রাপ্যতা"],
    "def": ["the quality of being easy to approach or use."],
    "syn": ["convenience"],
    "ant": ["inaccessibility"]
  }
]
```

---

## 🧩 Project Structure

```
e2b_dictionary/
├── word_fetcher.py        # Core engine
├── dictionary.json        # Main generated bilingual dataset
├── requirements.txt       # Python dependencies
└── README.md              # Documentation
```

---

## 📘 Data Usage & Licensing

This dataset was generated **for educational and research purposes** using publicly available dictionary and linguistic sources.
Some entries may contain information derived from web‑based dictionaries or open APIs.

Please respect the terms of use of original data sources. Redistribution should include clear attribution to:

> **Towfik Ahmed Razin – e2b_dictionary Project**

### 🪪 License

This project is licensed under the **MIT License**. You may use, modify, and distribute this software freely, provided that proper credit is given to the author.

---

## 👨‍💻 Author

**Towfik Ahmed Razin** <br>
Student • Developer • Science Enthusiast from Dhaka, Bangladesh<br>
GitHub: [@towfikahmed0](https://github.com/towfikahmed0)

---

> *“Knowledge of languages is the doorway to wisdom.”*
> — **Roger Bacon**
