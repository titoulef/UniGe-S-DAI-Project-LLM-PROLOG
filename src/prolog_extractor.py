import ollama
import re
import numpy as np
from sentence_transformers import SentenceTransformer, util

class PrologExtractor:
    def __init__(self, model_name="qwen2.5-coder:14b", kb_path="src/knowledge_base.pl"):
        self.model = model_name
        self.embedder = SentenceTransformer('all-MiniLM-L6-v2')
        self.known_predicates = self._load_kb_predicates(kb_path)

    def _load_kb_predicates(self, path):
        """Extrait les noms des prédicats du fichier .pl"""
        predicates = set()
        try:
            with open(path, "r") as f:
                content = f.read()
                found = re.findall(r'([a-z_]+)\s*\(', content)
                predicates.update(found)
        except FileNotFoundError:
            print("KB file not found, starting empty.")
        print("List des predicats", list(predicates))
        return list(predicates)

    def _find_best_predicate(self, nl_input):
        """Trouve si un prédicat existant match avec le texte via embedding"""
        if not self.known_predicates:
            return None

        input_embedding = self.embedder.encode(nl_input, convert_to_tensor=True)
        kb_embeddings = self.embedder.encode(self.known_predicates, convert_to_tensor=True)

        # compute similarity scores
        hits = util.semantic_search(input_embedding, kb_embeddings, top_k=3)
        print("Semantic Search Hits:", hits)
        
        # keep all those > 0.3
        valid_predicates = [
            self.known_predicates[hit['corpus_id']] 
            for hit in hits[0] 
            if hit['score'] > 0.25
        ]

        return valid_predicates
    
    def get_system_prompt(self, suggested_predicates=None):
        hint = ""
        if suggested_predicates and len(suggested_predicates) > 0:
            formatted_preds = ", ".join([f"`{p}`" for p in suggested_predicates])
            hint = f"CONTEXT: The Knowledge Base already contains these predicates: {formatted_preds}. YOU MUST USE THEM if they match the meaning."

        return f"""
        You are an expert in Prolog Logic. Convert Natural Language into valid Prolog syntax.
        
        {hint}

        ### GUIDELINES:
        1. **ATOMS vs VARIABLES**: 
           - Specific objects/names (Socrates, Paris, Santa, John) MUST be lowercase atoms (e.g., `socrates`, `santa`).
           - Generic placeholders (someone, a child, anything) MUST be Uppercase variables (e.g., `X`, `Y`, `Child`).
           - For abstract rules, prefer standard variables `X`, `Y`, `Z`.

        2. **PREDICATE NAMING**:
           - Keep predicates simple: use `loves(john, mary)` instead of `is_loving` or `love_relation`.
           - Avoid constructing composite names: for "Whales are mammals", use `mammal(X) :- whale(X).` (NOT `whale_mammal(X).`).
           - Avoid suffixes like `_of` unless explicitly strictly necessary (e.g., prefer `parent(X,Y)` over `parent_of(X,Y)` unless the CONTEXT says otherwise).

        3. **LOGICAL STRUCTURE**:
           - **Facts**: "Garfield eats lasagna" -> `eats(garfield, lasagna).`
           - **Class/Type Rules**: "All [SubCategory] are [Category]" -> `category(X) :- subcategory(X).`
             Example: "Whales are mammals" -> `mammal(X) :- whale(X).`
           - **Conditional Rules**: "A is B if C" -> `b(A) :- c(A).`
        
        4. **OUTPUT FORMAT**:
           - Output ONLY the Prolog code. No explanations. No Markdown.
           - Ensure every statement ends with a period `.`.
        """

    def extract_formula(self, natural_language_text):
        suggested = self._find_best_predicate(natural_language_text)
        print(f"Suggested Predicate: {suggested}")
        
        try:
            response = ollama.chat(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.get_system_prompt(suggested)},
                    {"role": "user", "content": f"Input: \"{natural_language_text}\"\nOutput:"}
                ]
            )
            return self._clean_output(response['message']['content'])
        except Exception as e:
            return f"Error: {e}"

    def _clean_output(self, text):
        clean = re.sub(r'```(prolog)?', '', text, flags=re.IGNORECASE)
        return clean.replace('```', '').strip()