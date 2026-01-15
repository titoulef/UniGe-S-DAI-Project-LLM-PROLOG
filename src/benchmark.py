import ollama
import json

OLLAMA_MODEL = "llama3.1:8b" 

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
        self.model = OLLAMA_MODEL

    def evaluate_with_llm(self, nl, expected, actual):
        """
        ask to a LLM if the two formulas are equivalent.
        """
        
        system_prompt = """You are a Prolog Logic Expert. 
        Compare the Expected Prolog code with the Actual Prolog code generated.
        Determine if they are semantically equivalent logic.
        You MUST answer with a valid JSON object containing:
        - "match": boolean (true/false)
        - "reason": string (short explanation)"""

        user_content = f"""Input Sentence: "{nl}"
        EXPECTED: {expected}
        ACTUAL: {actual}"""

        try:
            response = ollama.chat(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content}
                ],
                format='json'
            )
            
            content = response['message']['content']
            data = json.loads(content)
            
            return data.get("match", False), data.get("reason", "No reason provided")

        except ollama.ResponseError as e:
            return False, f"Ollama API Error: {e.error}"
        except json.JSONDecodeError:
            return False, f"Invalid JSON received: {content}"
        except Exception as e:
            return False, f"Unexpected Error: {e}"

    def run(self, n_samples=5, progress=None):
        results = []
        score = 0
        dataset = TEST_DATASET[:min(n_samples, len(TEST_DATASET))]
        total = len(dataset)
        
        print(f"--- Benchmark on {total} tests with model {self.model} ---")

        for i, item in enumerate(dataset):
            nl = item['nl']
            expected = item['expected']
            
            if progress is not None:
                progress(0.1 + (i / total) * 0.8, desc=f"Test {i+1}/{total}")
            
            actual_code = "Error"
            try:
                actual_code = self.extractor.extract_formula(nl)
                if not actual_code: actual_code = "Empty"
                actual_code = actual_code.strip()
            except Exception as e:
                actual_code = f"Crash: {e}"

            # judgment via Ollama
            is_match, reason = self.evaluate_with_llm(nl, expected, actual_code)

            status = "✅" if is_match else "❌"
            if is_match: score += 1
            
            results.append([nl, expected, actual_code, f"{status} {reason}"])
            print(f"[{i+1}/{total}] {status} Exp: {expected} | Act: {actual_code}")

        accuracy = round((score / total) * 100, 1) if total > 0 else 0
        return results, accuracy