from pyswip import Prolog

class PrologValidator:
    def __init__(self):
        self.prolog = Prolog()

    def append_to_kb(self, prolog_code, kb_path="src/knowledge_base.pl"):
        with open(kb_path, "a") as f:
            f.write(f"\n{prolog_code}")

    def validate_and_assert(self, prolog_code):
        """
        Tries to assert the generated code into the Prolog Knowledge Base.
        Returns (True, message) if valid, (False, error) if invalid.
        """
        try:
            clean_code = prolog_code.strip()
                    
            with open("src/temp_kb.pl", "w") as f:
                f.write(clean_code)
                
            self.prolog.consult("src/temp_kb.pl")
            return True, "Syntax Valid. Loaded into Knowledge Base."
            
        except Exception as e:
            return False, f"Prolog Syntax Error: {e}"