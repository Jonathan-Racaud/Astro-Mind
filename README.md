# Astro Mind

**Astro Mind** is a friendly AI assistant for *Elite Dangerous* commanders, designed to help you explore and understand the capabilities of ships across the galaxy.

Powered by modern **LLMs** and a **RAG (Retrieval-Augmented Generation)** system, Astro Mind combines embedded knowledge with curated data extracted from the [Elite Dangerous Fandom Wiki](https://elite-dangerous.fandom.com/wiki/Elite_Dangerous_Wiki) to provide detailed answers about ships and their specifications.

Future versions will include role-specific outfitting recommendations, real-time data scraping, and integration with community tools such as [EDSY.org](https://edsy.org/) for direct loadout visualization.

Astro Mind aims to be your co-pilot in the outfitting bay, context-aware, and constantly evolving.

---

## ✨ Features

### ✅ Currently Implemented

- 🚀 **LLM-Powered Question Answering (Ships Only)**
  Ask natural-language questions about ships—get detailed descriptions, stats, and comparisons.

- 📚 **RAG-Based Knowledge Retrieval**
  Uses a Retrieval-Augmented Generation system to ground responses in curated, up-to-date wiki data.

- 🧱 **Modular RAG Architecture**
  Built for future extension to equipment, modules, weapons, and third-party integrations.

### 🛠️ Planned Features

- 📡 **Real-Time Web Scraping**
  Automatically fetch the latest data from the Elite Dangerous Fandom Wiki when existing info is outdated or missing.

- 📦 **EDSY.org Integration**  
  Generate `.json` loadout files that can be imported directly into [EDSY.org](https://edsy.org/) for ship build visualization.

- 🧠 **Intention-Based Outfitting Recommendations**  
  Get suggestions tailored to your ship’s role—combat, mining, exploration, trade, or multi-role builds.

- 🤝 **Third-Party API Support**
  Interface with community tools and services for enhanced functionality and shared ecosystem support.

---

## 🧪 Tech Stack

| Layer              | Tools & Frameworks                                      |
|-------------------|----------------------------------------------------------|
| **Language Model** | HuggingFace Transformers, Open Source LLMs              |
| **RAG Framework**  | [LangChain](https://www.langchain.com/)                 |
| **Vector Store**   | [Marqo](https://marqo.ai/)|
| **Data Source**    | Manually scraped from the [Elite Dangerous Fandom Wiki](https://elite-dangerous.fandom.com/wiki/) |
| **Language**       | Python                                                   |

---

## 📚 Acknowledgments

- Elite Dangerous is the sole propriety of Frontier Developments.  
- Data sources extracted and transformed from the [Elite Dangerous Fandom Wiki](https://elite-dangerous.fandom.com/wiki/Elite_Dangerous_Wiki).  

---

## 🛰️ License

This project is currently under development. Licensing terms will be added in a future release.

It is not endorsed by nor reflects the views or opinions of Frontier Developments and no employee of Frontier Developments was involved in the making of it.

---

> *Astro Mind – For the Commander Who Plans Ahead.*

