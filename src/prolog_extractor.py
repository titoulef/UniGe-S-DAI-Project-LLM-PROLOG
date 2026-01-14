import ollama
import re

class PrologExtractor:
    def __init__(self, model_name="llama3.1:8b"):
        self.model = model_name

    def get_system_prompt(self):
        return """
        You are an expert in Logic Programming and Prolog. 
        Your task is to convert Natural Language sentences into valid Prolog formulas.

        RULES:
        1. OUTPUT ONLY CODE. No explanations, no markdown, no preamble.
        2. SYNTAX: 
        - Predicates and atoms must start with a lowercase letter (e.g., `man(socrates)`). 
        - Variables must start with an Uppercase letter (e.g., `X`, `Y`).
        
        3. FACTS vs RULES:
        - Specific statements about individuals are FACTS (e.g., "Laura is parent" -> `parent(laura).`).
        - General statements using "All", "Every", "If", or PLURAL NOUNS representing a category (e.g., "Whales are mammals") are RULES.
        - For categories, use variables: "Dogs are animals" -> `animal(X) :- dog(X).` (NOT `animal(dog).`).

        4. LOGICAL IMPLICATION (Crucial):
        - Format: `CONCLUSION :- CONDITION.`
        - "All A are B" means "If X is A, then X is B".
        - Prolog Translation: `b(X) :- a(X).`
        - Example: "Every child loves Santa" -> `loves(X, santa) :- child(X).` (Correct) vs `child(X) :- loves(X, santa).` (WRONG).

        5. ARGUMENT ORDER:
        - Use `predicate(Subject, Object)`.
        - The Subject of the sentence comes FIRST.
        - Example: "Shakespeare wrote Hamlet" -> `wrote(shakespeare, hamlet).`

        6. NO FREE VARIABLES IN FACTS: 
        - Never use a Variable in a fact without a body. `loves(john, X).` is forbidden.

        7. FORMATTING:
        - End every statement with exactly ONE period (.). Do not use double periods (..).

        EXAMPLES:
        Input: "Socrates is a man."
        Output: man(socrates).

        Input: "Whales are mammals."
        Output: mammal(X) :- whale(X).

        Input: "Shakespeare wrote Hamlet."
        Output: wrote(shakespeare, hamlet).

        Input: "Every child loves Santa."
        Output: loves(X, santa) :- child(X).

        Input: "Garfield eats lasagna."
        Output: eats(garfield, lasagna).

        Input: "X is a grandparent of Z if X is parent of Y and Y is parent of Z."
        Output: grandparent_of(X, Z) :- parent_of(X, Y), parent_of(Y, Z).
        """


    def _clean_output(self, text):
        """
        Clean the model's response to retain only the Prolog code.
        Remove Markdown tags (```) and extraneous text.
        """
        # remove markdown code tags
        clean = re.sub(r'```(prolog)?', '', text, flags=re.IGNORECASE)
        clean = clean.replace('```', '')
        
        # remove common introductory phrases from LLMs
        clean = clean.strip()
        
        # If the model output has multiple lines, try to keep the essential part
        # For this project, we assume one formula per line or block
        return clean

    def extract_formula(self, natural_language_text):
        try:
            response = ollama.chat(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.get_system_prompt()},
                    {"role": "user", "content": f"Input: \"{natural_language_text}\"\nOutput:"}
                ]
            )
            
            raw_content = response['message']['content']
            return self._clean_output(raw_content)

        except Exception as e:
            return f"Error connecting to Ollama: {e}"