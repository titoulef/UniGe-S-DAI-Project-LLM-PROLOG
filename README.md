# Project Roadmap & Timeline
**Project:** Standard Project #1: From natural language sentences to Prolog terms via LLMs  
**Proposer:** Prof. Mascardi  
**Max Points:** 12.5  


### Phase A: The Survey (Theoretical)
You need to write a short survey on approaches connecting Prolog and Large Language Models (LLMs).

* **Starting Point:** Read the paper [IOS Press Article 76178](https://ebooks.iospress.nl/volumearticle/76178).
* **Research Task:** Search for other papers specifically where LLMs are used to extract Prolog logical formulas from Natural Language (NL).
* **Output:** A written overview comparing these different approaches.

### Phase B: The Implementation (Practical)
**Goal:** Design and test a simplified LLM-based formula extractor.

* **Method:** You are not expected to invent a new method from scratch; take inspiration from one of the papers read in Phase A.
* **Tech Stack:** * **Language:** Python
    * **Core:** APIs for LLMs (Ollama).
    * **Interface:** A way to interface with Prolog (e.g., `pyswip` or generating `.pl` files).

