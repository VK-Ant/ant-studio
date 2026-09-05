"""Ant Studio CLI."""
import click, json
from pathlib import Path

MODEL_HELP = """Model to use. Supports provider/model format:
  ollama/llama3.2 (local Ollama)
  openai/gpt-4o (OpenAI API)
  azure/gpt-4o (Azure OpenAI)
  anthropic/claude-sonnet-4-20250514 (Anthropic)
  huggingface/mistralai/Mistral-7B-v0.1 (HuggingFace)
  groq/llama-3.1-70b (Groq)
  deepseek/deepseek-chat (DeepSeek)
  local:/path/to/model.gguf (local GGUF file)
  Or just a model name to auto-detect provider."""

@click.group()
@click.version_option("0.2.0", prog_name="antstudio")
def cli():
    """Ant Studio -- Build. Run. Control."""
    pass

@cli.group()
def doc():
    """Document intelligence (DocQWise)."""
    pass

@doc.command()
@click.argument("source")
@click.option("--fields", "-f", default="vendor,date,amount,invoice_number")
@click.option("--output", "-o", default="")
@click.option("--output-db", default="", help="Database connection string")
@click.option("--table", default="results")
@click.option("--ocr", is_flag=True)
@click.option("--engine", default="tesseract")
@click.option("--model", default="default", help=MODEL_HELP)
@click.option("--threshold", default=0.7, type=float)
@click.option("--extensions", default=".pdf,.docx,.txt,.xlsx,.csv,.png,.jpg,.jpeg")
def extract(source, fields, output, output_db, table, ocr, engine, model, threshold, extensions):
    """Extract fields from documents (PDF, DOCX, Excel, images, TXT)."""
    from antstudio.doc.extract import run
    run(source=source, fields=[f.strip() for f in fields.split(",")], model=model,
        ocr=ocr, engine=engine, output=output, output_db=output_db, table=table,
        threshold=threshold, extensions=extensions)

@doc.command()
@click.argument("source")
@click.argument("question")
@click.option("--rag", default="auto", type=click.Choice(["simple","graph","multimodal","auto"]))
@click.option("--model", default="", help=MODEL_HELP)
@click.option("--system-prompt", default="")
def ask(source, question, rag, model, system_prompt):
    """Ask questions about documents."""
    from antstudio.doc.ask import run
    run(source=source, question=question, rag=rag, model=model, system_prompt=system_prompt)

@cli.group()
def ts():
    """Temporal intelligence (WavQWise)."""
    pass

@ts.command()
@click.argument("source")
@click.option("--target", "-t", default="value")
@click.option("--horizon", "-h", default=30, type=int)
@click.option("--model", "-m", default="auto")
@click.option("--output", "-o", default="")
@click.option("--chart", default="")
def forecast(source, target, horizon, model, output, chart):
    """Forecast time-series data. Saves chart + quality/audit reports alongside output."""
    from antstudio.ts.forecast import run
    run(source=source, target=target, horizon=horizon, model=model, output=output, chart=chart)

@ts.command()
@click.argument("source")
@click.option("--target", "-t", default="value")
@click.option("--method", "-m", default="zscore")
@click.option("--threshold", default=2.0, type=float)
@click.option("--output", "-o", default="")
def anomaly(source, target, method, threshold, output):
    """Detect anomalies in time-series. Saves quality/audit reports alongside output."""
    from antstudio.ts.anomaly import run
    run(source=source, target=target, method=method, threshold=threshold, output=output)

@cli.command()
@click.option("--limit", default=20, type=int)
def runs(limit):
    """List past pipeline runs (Kubeflow-style)."""
    from antstudio.pipeline import list_runs
    all_runs = list_runs(limit)
    if not all_runs:
        print("\n  No pipeline runs yet.\n"); return
    print(f"\n  {'ID':<10} {'Pipeline':<40} {'Steps':<12} {'Status':<10} {'Time':<8}")
    print(f"  {'---'*10} {'---'*40} {'---'*12} {'---'*10} {'---'*8}")
    for r in all_runs:
        s = r.get("summary", {})
        print(f"  {r['run_id']:<10} {r['name'][:39]:<40} {s.get('success',0)}/{s.get('total',0)} passed  {r['status']:<10} {r['duration_seconds']:.1f}s")
    print()

@cli.command()
@click.argument("run_id")
def run_detail(run_id):
    """Show detailed pipeline run (Kubeflow-style)."""
    from antstudio.pipeline import get_run
    data = get_run(run_id)
    if not data:
        print(f"\n  Run '{run_id}' not found.\n"); return
    icons = {"success":"+","failed":"x","skipped":"-","pending":"."}
    print(f"\n  Pipeline: {data['name']} [{data['run_id']}]")
    print(f"  Status: {data['status'].upper()} | {data['duration_seconds']}s | {data['timestamp']}")
    print(f"  {'='*60}")
    for i, step in enumerate(data.get("steps", [])):
        ic = icons.get(step["status"], "?")
        dur = f"{step['duration_ms']}ms" if step.get("duration_ms") else ""
        err = f" ({step['error'][:40]})" if step.get("error") else ""
        print(f"  [{ic}] {step['name']:<30} {dur:>8}{err}")
        if i < len(data["steps"]) - 1:
            print(f"      |"); print(f"      v")
    print(f"  {'='*60}")
    s = data.get("summary", {})
    print(f"  {s.get('success',0)}/{s.get('total',0)} steps passed\n")

@cli.command()
def history():
    """Show execution history."""
    hist_file = Path.home() / ".antstudio" / "history.json"
    if not hist_file.exists():
        print("  No runs yet."); return
    runs = json.loads(hist_file.read_text())
    print(f"\n  {'ID':<5} {'Command':<45} {'Quality':<10} {'Privacy':<12} {'Time':<8}")
    print(f"  {'---'*5} {'---'*45} {'---'*10} {'---'*12} {'---'*8}")
    for r in runs[-20:]:
        qp = "PASS" if r.get("passed") else "FAIL"
        dl = "LOCAL" if not r["privacy"]["data_left_system"] else "ALERT"
        print(f"  {r['id']:<5} {r['command'][:44]:<45} {qp:<10} {dl:<12} {r['duration_seconds']:.1f}s")
    print()

@cli.command()
def models():
    """List available models (Ollama + configured providers)."""
    from antstudio.llm.engine import LLMEngine, _ollama_models

    # Ollama
    mods = _ollama_models()
    if mods:
        print(f"\n  Ollama models ({len(mods)}):")
        for m in mods: print(f"    - ollama/{m}")
    else:
        print("\n  Ollama: not running (start with: ollama serve)")

    # Configured API providers
    import os
    providers = {
        "OPENAI_API_KEY": "openai",
        "AZURE_API_KEY": "azure",
        "ANTHROPIC_API_KEY": "anthropic",
        "HUGGINGFACE_API_KEY": "huggingface",
        "GROQ_API_KEY": "groq",
        "MISTRAL_API_KEY": "mistral",
        "TOGETHER_API_KEY": "together_ai",
        "DEEPSEEK_API_KEY": "deepseek",
    }
    configured = []
    for key, name in providers.items():
        if os.environ.get(key):
            configured.append(name)

    if configured:
        print(f"\n  API providers configured:")
        for p in configured:
            print(f"    - {p} (set via env)")
    else:
        print(f"\n  API providers: none configured")
        print(f"    Set env vars: OPENAI_API_KEY, AZURE_API_KEY, ANTHROPIC_API_KEY, etc.")

    print(f"\n  Usage: antstudio doc ask ./doc.pdf 'question' --model openai/gpt-4o")
    print(f"         antstudio doc ask ./doc.pdf 'question' --model ollama/llama3.2")
    print()

@cli.command()
def status():
    """System status."""
    print(f"\n  Ant Studio v0.2.0")
    libs = {"docqwise":0,"wavqwise":0,"sightrag":0,"sonarwise":0,
            "adaptive_intelligence":0,"llmevalkit":0,"antguard":0,"litellm":0}
    for lib in libs:
        try: __import__(lib); libs[lib] = 1
        except ImportError: pass
    print(f"\n  Ecosystem libraries:")
    for lib, ok in libs.items():
        print(f"    [{'+'if ok else '-'}] {lib}")
    from antstudio.llm.engine import _ollama_models
    mods = _ollama_models()
    print(f"\n  Ollama: {'connected ('+str(len(mods))+' models)' if mods else 'not running'}")
    print(f"\n  LLM providers: Ollama | OpenAI | Azure | Anthropic | HuggingFace | Groq | Mistral | DeepSeek | Local GGUF")
    print()

def main():
    cli()

if __name__ == "__main__":
    main()
