import gradio as gr
from prolog_extractor import PrologExtractor 
from prolog_validator import PrologValidator
from benchmark import BenchmarkEngine


extractor = PrologExtractor()
validator = PrologValidator()
benchmark_runner = BenchmarkEngine(extractor)


# logic fonctions
def process_natural_language(text_input):
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

def run_benchmark_ui(progress=gr.Progress()):
    """Runs the benchmark on the hardcoded cases."""
    try:
        # running on 10 samples but in fact my api key allows only 5 per minute
        data, accuracy = benchmark_runner.run(n_samples=10, progress=progress)
        summary = f"### 🎯 Model Accuracy: {accuracy}%"
        return data, summary
    except Exception as e:
        import traceback
        return [], f"🚨 Benchmark Error: {str(e)}\n\n{traceback.format_exc()}"

def get_kb_content():
    """Lit le contenu du fichier de connaissance pour l'affichage."""
    try:
        with open("src/knowledge_base.pl", "r") as f:
            content = f.read()
        return content if content else "La Knowledge Base est vide."
    except FileNotFoundError:
        return "Fichier knowledge_base.pl non trouvé."
    
# gradio 
with gr.Blocks(theme=gr.themes.Soft(), title="LLM to Prolog") as demo:
    
    gr.Markdown("# 🦉 LLM to Prolog Converter")
    
    with gr.Tab("Converter"):
        with gr.Row():
            with gr.Column():
                #inpput NL
                input_text = gr.Textbox(
                    lines=8, 
                    label="Natural Language Text", 
                    placeholder="Ex: Socrates is a man..."
                )
                convert_btn = gr.Button("Generate Prolog Code", variant="primary")
                # some examples
                gr.Examples([["Socrates is a man."], ["Every child loves Santa."]], inputs=input_text)
                #urrent Knowledge Base
                with gr.Accordion("📚 Current Knowledge Base", open=False):
                    kb_display = gr.TextArea(
                        show_label=False, # Le label est déjà sur l'accordéon
                        value=get_kb_content,
                        lines=10, # On peut augmenter les lignes vu que c'est caché par défaut
                        interactive=False
                    )
                    refresh_kb_btn = gr.Button("🔄 Rafraîchir la vue", size="sm")
                refresh_kb_btn.click(get_kb_content, outputs=kb_display)
            
            with gr.Column():
                output_code = gr.Code(language=None, label="Generated Prolog", interactive=False)
                output_status = gr.Markdown(label="Validation Logs")
        
                
        convert_btn.click(process_natural_language, input_text, [output_code, output_status])


        
        
    with gr.Tab("🧪 Benchmark"):
        gr.Markdown("### Performance Test (Fixed Dataset)")
        gr.Markdown("The system will test 10 predefined sentences (Facts, Simple Rules, Complex Rules) and compare the results using an AI Judge.")
        
        bench_btn = gr.Button("Run Benchmark", variant="stop")
        bench_summary = gr.Markdown("### Waiting...")
        
        results_df = gr.Dataframe(
            headers=["NL Input", "Expected", "Generated", "Judge Verdict"],
            datatype=["str", "str", "str", "str"],
            label="Results",
            wrap=True
        )

        bench_btn.click(run_benchmark_ui, None, [results_df, bench_summary])

if __name__ == "__main__":
    demo.launch()