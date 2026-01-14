from google import genai
import json
import os

# --- 1. CONFIGURATION GOOGLE ---
# Remplace par ta clé API
API_KEY = "AIzaSyAiUa4m1nuBBEX9uRnzUgkyAvIHqoMJHZA"


try:
    client = genai.Client(api_key="AIzaSyAiUa4m1nuBBEX9uRnzUgkyAvIHqoMJHZA")
except Exception as e:
    print(f"Erreur config Google: {e}")

TEST_DATASET = [
    {"nl": "Socrates is a man.", "expected": "man(socrates)."},
    {"nl": "John loves Mary.", "expected": "loves(john, mary)."},
    {"nl": "Paris is the capital of France.", "expected": "capital(paris, france)."},
    {"nl": "Garfield eats lasagna.", "expected": "eats(garfield, lasagna)."},
    {"nl": "All men are mortal.", "expected": "mortal(X) :- man(X)."},
    {"nl": "Every child loves Santa.", "expected": "loves(X, santa) :- child(X)."},
    {"nl": "Whales are mammals.", "expected": "mammal(X) :- whale(X)."},
    {"nl": "X is grandparent of Z if X is parent of Y and Y is parent of Z.", 
     "expected": "grandparent(X, Z) :- parent(X, Y), parent(Y, Z)."},
    {"nl": "X is a mother of Y if X is parent of Y and X is female.", 
     "expected": "mother(X, Y) :- parent(X, Y), female(X)."},
    {"nl": "X is a sibling of Y if Z is parent of X and Z is parent of Y.", 
     "expected": "sibling(X, Y) :- parent(Z, X), parent(Z, Y)."}
]

class BenchmarkEngine:
    def __init__(self, extractor_instance):
        self.extractor = extractor_instance

      

    def evaluate_with_llm(self, nl, expected, actual):
        """Demande au Juge si c'est équivalent."""
        prompt = f"""
        Act as a Prolog Logic Expert. Compare these snippets for: "{nl}".
        EXPECTED: {expected}
        ACTUAL: {actual}
        Output ONLY JSON: {{"match": true/false, "reason": "short string"}}
        """
        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash", contents=prompt
            )
            text = response.text.replace("```json", "").replace("```", "").strip()
            data = json.loads(text)
            return data.get("match", False), data.get("reason", "No reason")
        except Exception as e:
            return False, f"Juge Error: {str(e)}"

    def run(self, n_samples=5, progress=None):
        results = []
        score = 0
        dataset = TEST_DATASET[:n_samples]
        total = len(dataset)
        
        print(f"--- Benchmark sur {total} tests ---")

        for i, item in enumerate(dataset):
            nl = item['nl']
            expected = item['expected']
            
            # --- CORRECTION ICI ---
            # On utilise 'is not None' pour éviter le crash IndexError de Gradio
            if progress is not None:
                progress(0.1 + (i / total) * 0.8, desc=f"Test {i+1}/{total}")
            
            # 1. Extraction
            actual_code = "Error"
            try:
                actual_code = self.extractor.extract_formula(nl)
                if not actual_code: actual_code = "Vide"
                actual_code = actual_code.strip()
            except Exception as e:
                actual_code = f"Crash: {e}"

            # 2. Jugement
            is_match, reason = self.evaluate_with_llm(nl, expected, actual_code)

            # 3. Résultat
            status = "✅" if is_match else "❌"
            if is_match: score += 1
            
            results.append([nl, expected, actual_code, f"{status} {reason}"])

        accuracy = round((score / total) * 100, 1) if total > 0 else 0
        return results, accuracy