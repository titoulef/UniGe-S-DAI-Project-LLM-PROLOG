from pyswip import Prolog

class PrologValidator:
    def __init__(self):
        # Do not keep a global Prolog instance for web apps (thread-unsafe)
        pass

    def validate_and_assert(self, prolog_code):
        """
        Validates syntax and asserts into temp_kb for future use.
        """
        prolog = Prolog() # Instantiate local engine
        try:
            clean_code = prolog_code.strip()
            
            # Read existing to check for duplicates (simple persistence)
            existing = ""
            try:
                with open("src/temp_kb.pl", "r") as f:
                    existing = f.read()
            except FileNotFoundError:
                pass

            # Append only if new
            if clean_code not in existing:
                with open("src/temp_kb.pl", "a") as f:
                    f.write(f"\n{clean_code}")
            
            # Load into Prolog Engine to check syntax
            prolog.consult("src/temp_kb.pl")
            return True, "Syntax Valid. Saved to temp_kb.pl."
            
        except Exception as e:
            return False, f"Prolog Syntax Error: {e}"

    def run_query(self, query_code):
        """
        Runs a query against the current temp_kb.pl
        """
        prolog = Prolog() # Instantiate local engine
        try:
            # 1. Clean the query
            # PySWIP often prefers queries WITHOUT the trailing dot in query(), 
            # while the LLM generates one. We strip it to be safe.
            query_clean = query_code.strip().rstrip('.')

            # 2. Reload KB
            prolog.consult("src/temp_kb.pl")
            
            results = list(prolog.query(query_clean))
            # rocess Results
            if len(results) == 0:
                return False, "False"
            
            if len(results) >= 1 and len(results[0]) == 0:
                return True, "True"
            
            # Format variable results (e.g. X = socrates)
            formatted = []
            for res in results:
                # Convert Prolog result dict to string
                # matches: [{'X': 'socrates'}, {'X': 'plato'}]
                formatted.append(str(res))
            
            return True, f"Solutions found: {', '.join(formatted)}"

        except Exception as e:
            return False, f"Execution Error: {e}"