import gradio as gr
from prolog_extractor import PrologExtractor 
from prolog_validator import PrologValidator
from benchmark import BenchmarkEngine
import os

extractor = PrologExtractor()
validator = PrologValidator()
benchmark_runner = BenchmarkEngine(extractor)

# --- Logic Functions ---

def process_natural_language(text_input):
    """Generates Facts/Rules from NL"""
    if not text_input or not text_input.strip():
        return "", "⚠️ Please enter text."
    
    try:
        raw_prolog = extractor.extract_formula(text_input)
        is_valid, logs = validator.validate_and_assert(raw_prolog)
        
        status_emoji = "✅ Success" if is_valid else "❌ Error"
        validation_report = f"### Status: {status_emoji}\n\n**Logs:**\n{logs}"
        return raw_prolog, validation_report

    except Exception as e:
        return "", f"### 🚨 System Error: {str(e)}"

def run_solver(nl_query):
    """
    1. Check Embeddings in temp_kb
    2. Generate Prolog Query
    3. Run in PySWIP
    """
    if not nl_query: return "", "⚠️ Enter a question."

    try:
        generated_query = extractor.generate_query(nl_query)
        
        if not generated_query:
            return "No matching predicate found.", "⚠️ The solver could not find any relevant logic in the Knowledge Base for this question."

        success, result = validator.run_query(generated_query)
        
        status = "✅ Answer Found" if success else "❌ False / Error"
        return generated_query, f"### {status}\n**Result:** {result}"
        
    except Exception as e:
        return "Error", f"Solver Crash: {str(e)}"

def run_benchmark_ui(progress=gr.Progress()):
    try:
        data, accuracy = benchmark_runner.run(n_samples=10, progress=progress)
        summary = f"### 🎯 Model Accuracy: {accuracy}%"
        return data, summary
    except Exception as e:
        return [], f"🚨 Error: {str(e)}"

def get_kb_content():
    try:
        if os.path.exists("src/temp_kb.pl"):
            with open("src/temp_kb.pl", "r") as f:
                content = f.read()
            return content
        else:
            return "temp_kb.pl is empty."
    except Exception:
        return "Error reading file."

# --- GUI ---
with gr.Blocks(theme=gr.themes.Soft(), title="Neuro-Symbolic Prolog") as demo:
    
    gr.Markdown("# 🦉 Neuro-Symbolic Prolog System")
    
    with gr.Tabs():
        
        with gr.Tab("📝 Knowledge Extractor"):
            with gr.Row():
                with gr.Column():
                    
                    input_text = gr.Textbox(lines=5, label="Natural Language Fact/Rule", placeholder="Ex: Socrates is a man. All men are mortal.")
                    convert_btn = gr.Button("Add to Knowledge Base", variant="primary")

                    

                with gr.Column():
                    output_code = gr.Code(language=None, label="Generated Logic")
                    output_status = gr.Markdown(label="System Status")
                    
            with gr.Row():
                with gr.Accordion("📚 Current Knowledge Base (temp_kb.pl)", open=False):
                        kb_display = gr.Code(language=None, value=get_kb_content, interactive=False)
                        refresh_kb_btn = gr.Button("🔄 Refresh KB View", size="sm")
                        refresh_kb_btn.click(get_kb_content, outputs=kb_display)
            with gr.Row():
                gr.Examples([["All men are mortal. Socrates is a man."], ["Every child loves Santa. Laura is a child"], ["Paris is the capital of France."]], inputs=input_text, label=None)

            convert_btn.click(process_natural_language, input_text, [output_code, output_status])

        with gr.Tab("🔍 Prolog Solver"):
            gr.Markdown("Ask questions based on the logic you added in the Extractor tab.")
            with gr.Row():
                with gr.Column():
                    solver_input = gr.Textbox(lines=2, label="Ask a Question", placeholder="Ex: Is Socrates mortal? Who is a man?")
                    solve_btn = gr.Button("Solve Query", variant="primary")
                
                with gr.Column():
                    solver_generated_code = gr.Code(language=None, label="Generated Query")
                    solver_result = gr.Markdown(label="Execution Result")

            solve_btn.click(run_solver, solver_input, [solver_generated_code, solver_result])

        with gr.Tab("🧪 Benchmark"):
            bench_btn = gr.Button("Run Benchmark", variant="stop")
            bench_summary = gr.Markdown("### Ready")
            results_df = gr.Dataframe(headers=["NL", "Exp", "Act", "Verdict"], wrap=True)
            bench_btn.click(run_benchmark_ui, None, [results_df, bench_summary])

if __name__ == "__main__":
    # Create temp_kb if not exists
    if not os.path.exists("src/temp_kb.pl"):
        with open("src/temp_kb.pl", "w") as f: f.write("% Temp KB\n")
            
    demo.launch()