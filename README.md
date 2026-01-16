# **Project:** Standard Project #1: From natural language sentences to Prolog terms via LLMs  
**Proposer:** Prof. Mascardi  
**Max Points:** 12.5  


This project integrates **Large Language Models (LLMs)** with **Symbolic Logic (Prolog)**. It allows users to convert Natural Language into Prolog rules, execute logical queries, and benchmark the translation quality using an "LLM-as-a-judge" approach.
**Starting Point:** [IOS Press Article 76178](https://ebooks.iospress.nl/volumearticle/76178).
---

## 📋 Prerequisites

Before running the project, ensure you have the following installed on your system:

* **Python 3.10+**
* **[Poetry](https://python-poetry.org/)** (Dependency Manager)
* **[Ollama](https://ollama.com/)** (Local LLM Runner)
* **SWI-Prolog** (Required at the system level for `PySWIP`)
    * *Linux:* `sudo apt-get install swi-prolog`
    * *Mac:* `brew install swi-prolog`
    * *Windows:* Download installer from [swi-prolog.org](https://www.swi-prolog.org/download/stable) and add to PATH.

---

## 🛠️ Installation

**1. Clone the repository**
```bash
git clone [https://github.com/titoulef/UniGe-S-DAI-Project-LLM-PROLOG.git](https://github.com/titoulef/UniGe-S-DAI-Project-LLM-PROLOG.git)
cd UniGe-S-DAI-Project-LLM-PROLOG
```

**2. Install dependencies** Initialize the virtual environment and install all required libraries (Gradio, PySWIP, etc.) using Poetry:
```bash
poetry install
```

**3. Prepare LLM models** Start the Ollama server and pull the models used in the prototype. The system is optimized for llama3.1:8b, but you can experiment with other models by changing the configuration in the code.

```bash
ollama pull llama3.1:8b
```


## 🚀 Usage
**1. Start the application** Launch the web interface using the Poetry runner to ensure all dependencies are loaded correctly:
```bash
poetry run python src/app.py
```

**2. Access the Interface**
Open your browser and navigate to: http://127.0.0.1:7860
Note: If the knowledge base file src/temp_kb.pl does not exist, it will be automatically created upon startup.
