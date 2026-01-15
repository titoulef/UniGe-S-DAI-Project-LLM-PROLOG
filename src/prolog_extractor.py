import ollama
import re
import numpy as np
from sentence_transformers import SentenceTransformer, util

class PrologExtractor:
    def __init__(self, model_name="qwen2.5-coder:14b", kb_path="src/temp_kb.pl"):
        self.model = model_name
        self.embedder = SentenceTransformer('all-MiniLM-L6-v2')
        # Load initial static KB, but we will often refresh from temp_kb
        self.known_predicates = self._load_kb_predicates(kb_path)

    def _load_kb_predicates(self, path):
        """Extracts predicate names from a .pl file"""
        predicates = set()
        try:
            with open(path, "r") as f:
                content = f.read()
                # Regex to find predicates like 'loves(' or 'man(' at start of line or after whitespace
                found = re.findall(r'(\w+)\s*\(', content)
                predicates.update(found)
        except FileNotFoundError:
            print(f"File {path} not found.")
        return list(predicates)

    def refresh_kb_predicates(self, path="src/temp_kb.pl"):
        """Refreshes the list of known predicates from the current working KB"""
        self.known_predicates = self._load_kb_predicates(path)
        return self.known_predicates

    def _find_best_predicate(self, nl_input):
        """Matches NL input to existing predicates via embeddings"""
        if not self.known_predicates:
            return []

        input_embedding = self.embedder.encode(nl_input, convert_to_tensor=True)
        kb_embeddings = self.embedder.encode(self.known_predicates, convert_to_tensor=True)

        hits = util.semantic_search(input_embedding, kb_embeddings, top_k=5)
        
        # Keep matches with reasonable score
        valid_predicates = [
            self.known_predicates[hit['corpus_id']] 
            for hit in hits[0] 
            if hit['score'] > 0.2
        ]
        return valid_predicates
    
    def get_system_prompt(self, task_type="extraction", suggested_predicates=None):
        hint = ""
        if suggested_predicates and len(suggested_predicates) > 0:
            formatted_preds = ", ".join([f"`{p}`" for p in suggested_predicates])
            hint = f"CONTEXT: The Knowledge Base already contains these predicates: {formatted_preds}. YOU MUST USE THEM if they match the meaning."


        base_prompt = f"""
        You are an expert in Prolog Logic. {hint}
        """

        if task_type == "extraction":
            return base_prompt + """
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
        elif task_type == "query":
            return base_prompt + """
            Convert the Natural Language Question into a Prolog Query.
            - If it asks "Is X Y?", output "predicate(x, y)."
            - If it asks "Who/What...?", use a Variable (Capitalized) like "predicate(X, y)."
            - OUTPUT ONLY THE CODE. NO EXPLANATIONS.
            Example: "Who loves Mary?" -> loves(X, mary).
            Example: "Is Socrates mortal?" -> mortal(socrates).
            """

    def extract_formula(self, natural_language_text):
        # Default extraction logic (Facts/Rules)
        suggested = self._find_best_predicate(natural_language_text)
        prompt = self.get_system_prompt("extraction", suggested)
        print(f"Extractor Context Predicates: {suggested}")
        print(f"Extractor System Prompt: {prompt}")
        return self._call_llm(prompt, natural_language_text)

    def generate_query(self, natural_language_query):
        self.refresh_kb_predicates("src/temp_kb.pl")
        
        suggested = self._find_best_predicate(natural_language_query)
        print(f"Solver Context Predicates: {suggested}")

        if not suggested:
            return None # Solver cannot work if no relevant predicate exists
        
        prompt = self.get_system_prompt("query", suggested)
        print(f"Suggested Predicates for Query: {suggested}")
        print(f"Solver System Prompt: {prompt}")
        return self._call_llm(prompt, natural_language_query)

    def _call_llm(self, system_prompt, user_input):
        try:
            response = ollama.chat(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Input: \"{user_input}\"\nOutput:"}
                ]
            )
            return self._clean_output(response['message']['content'])
        except Exception as e:
            return f"Error: {e}"

    def _clean_output(self, text):
        clean = re.sub(r'```(prolog)?', '', text, flags=re.IGNORECASE)
        # Remove trailing period for PySWIP queries strictly, but usually it handles it.
        # We keep it standard here.
        return clean.replace('```', '').strip()