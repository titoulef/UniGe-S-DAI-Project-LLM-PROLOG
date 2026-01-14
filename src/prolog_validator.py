from pyswip import Prolog

class PrologValidator:
    def __init__(self):
        self.prolog = Prolog()

    def validate_and_assert(self, prolog_code):
        """
        Tries to assert the generated code into the Prolog Knowledge Base.
        Returns (True, message) if valid, (False, error) if invalid.
        """
        try:
            # pyswip assertz expects a string without the trailing dot for direct assertion,
            # but for loading complex rules, it's often safer to write to a temp file or consult.
            # Here is a simple syntax check by attempting to assert.
            
            # Clean string to ensure format matches pyswip expectations
            clean_code = prolog_code.strip()
            
            # If it is a rule (contains :-), handling in pyswip can be tricky dynamically.
            # We will use the consult approach: write to file -> load file.
            
            with open("temp_kb.pl", "w") as f:
                f.write(clean_code)
                
            self.prolog.consult("temp_kb.pl")
            return True, "Syntax Valid. Loaded into Knowledge Base."
            
        except Exception as e:
            return False, f"Prolog Syntax Error: {e}"