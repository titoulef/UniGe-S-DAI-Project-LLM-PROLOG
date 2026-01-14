from prolog_extractor import PrologExtractor
from prolog_validator import PrologValidator

def main():
    print("--- Neuro-Symbolic Prolog Extractor ---")
    print("Type 'exit' to quit.\n")
    
    extractor = PrologExtractor()
    validator = PrologValidator()
    

    while True:
        user_input = input("\nEnter Natural Language sentence: ")
        if user_input.lower() == 'exit':
            break

        print("1. Extracting Logic...")
        prolog_code = extractor.extract_formula(user_input)
        print(f"-> Generated Code: {prolog_code}")

        print("2. Validating Syntax...")
        is_valid, message = validator.validate_and_assert(prolog_code)
        
        if is_valid:
            print(f"-> [SUCCESS] {message}")
        else:
            print(f"-> [FAILURE] {message}")

if __name__ == "__main__":
    main()