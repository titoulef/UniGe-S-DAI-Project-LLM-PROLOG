import ollama
import re
import numpy as np
from sentence_transformers import SentenceTransformer, util

class PrologExtractor:
    def __init__(self, model_name="llama3.1:8b", kb_path="src/temp_kb.pl"):
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
            hint = f"CONTEXT: The Knowledge Base already contains these predicates: {formatted_preds}. Prioritize using them to maintain consistency."

        base_prompt = f"""
        You are an expert in Prolog Logic. Your task is to translate Natural Language into syntactically correct Prolog code. {hint}
        """

        if task_type == "extraction":
            return base_prompt + """
            ### CORE TRANSLATION RULES:

            1. **DISTINCTION: INSTANCE vs CLASS**:
                - **Specific Instance** (John, Paris, Socrates) -> **Atom** (lowercase).
                    - "Socrates is a man" -> `man(socrates).`
                - **General Class** (Men, Whales, Children) -> **Rule with Variable** (Uppercase).
                    - "All clown are funny" -> `funny(X) :- clown(X).` (NOT `funny(clown).`)
                    - "Clown are human" -> `human(X) :- clown(X).` (NOT `human(clown).`)

            2. **LOGICAL PATTERNS**:
                - **"Every A does B"** -> `does(X, b) :- a(X).`
                    - "Every child loves Santa" -> `loves(X, santa) :- child(X).`
                - **"All A are B"** -> `b(X) :- a(X).`
                - **"A if B and C"** -> `a(X) :- b(X), c(X).`
            
            3. **SYNTAX & VARIABLES**:
                - Use standard variables `X`, `Y`, `Z` for general rules.
                - Do NOT use descriptive variables like `Child` or `Person`.
                - End every line with a single period `.`.

            4. **OUTPUT FORMAT**:
                - **STRICTLY CODE ONLY**. No "Note:", no explanations, no Markdown blocks.
                - If the input is a general statement, OUTPUT A RULE (:-), not a simple fact.

            ### FEW-SHOT EXAMPLES:
            Input: "John loves Mary."
            Output: loves(john, mary).

            Input: "All humans are mortal."
            Output: mortal(X) :- human(X).

            Input: "Every bird can fly."
            Output: can_fly(X) :- bird(X).

            Input: "X is a sister of Y if X is female and parents are same."
            Output: sister(X, Y) :- female(X), parent(Z, X), parent(Z, Y).
            """
        
        elif task_type == "query":
            return base_prompt + """
            Convert the Natural Language Question into a Prolog Query.
            - "Is X Y?" -> `predicate(x, y).`
            - "Who is X?" -> `predicate(Variable, x).`
            
            OUTPUT ONLY THE CODE.
            Example: "Who loves Mary?" -> loves(X, mary).
            """
        
            
    def extract_formula(self, natural_language_text):
        # Default extraction logic (Facts/Rules)
        suggested = self._find_best_predicate(natural_language_text)
        prompt = self.get_system_prompt("extraction", suggested)
        #print(f"Extractor Context Predicates: {suggested}")
        #print(f"Extractor System Prompt: {prompt}")
        return self._call_llm(prompt, natural_language_text)

    def generate_query(self, natural_language_query):
        self.refresh_kb_predicates("src/temp_kb.pl")
        
        suggested = self._find_best_predicate(natural_language_query)
        #print(f"Solver Context Predicates: {suggested}")

        if not suggested:
            return None # Solver cannot work if no relevant predicate exists
        
        prompt = self.get_system_prompt("query", suggested)
        #print(f"Suggested Predicates for Query: {suggested}")
        #print(f"Solver System Prompt: {prompt}")
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