import argparse
import json
import multiprocessing
import os
import os.path as osp
import shutil
import subprocess
import sys
import time
import torch
from aider.coders import Coder
from aider.io import InputOutput
from aider.models import Model
from datetime import datetime

from ai_scientist.llm import create_client, AVAILABLE_LLMS
from ai_scientist.paper_repro.paper_understanding import extract_paper_info
from ai_scientist.paper_repro.code_generation import generate_implementation
from ai_scientist.paper_repro.experiment_reproduction import run_experiments
from ai_scientist.paper_repro.result_analysis import analyze_results
from ai_scientist.paper_repro.report_generation import generate_report

def print_time():
    print(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))


def parse_arguments():
    parser = argparse.ArgumentParser(description="Run AI scientist paper reproduction")
    parser.add_argument(
        "--pdf_path",
        type=str,
        required=True,
        help="Path to the PDF file of the paper to reproduce",
    )
    parser.add_argument(
        "--skip_paper_extraction",
        action="store_true",
        help="Skip paper information extraction and use existing extracted data",
    )
    parser.add_argument(
        "--skip_code_generation",
        action="store_true",
        help="Skip code generation and use existing implementation",
    )
    parser.add_argument(
        "--skip_experiments",
        action="store_true",
        help="Skip running experiments and use existing results",
    )
    parser.add_argument(
        "--template",
        type=str,
        default=None,
        help="Template to use for reproduction (if applicable)",
    )
    parser.add_argument(
        "--model",
        type=str,
        default="claude-3-5-sonnet-20240620",
        choices=AVAILABLE_LLMS,
        help="Model to use for AI Scientist paper reproduction.",
    )
    parser.add_argument(
        "--report_format",
        type=str,
        default="latex",
        choices=["latex", "markdown"],
        help="What format to use for the reproduction report",
    )
    parser.add_argument(
        "--parallel",
        type=int,
        default=0,
        help="Number of parallel processes to run. 0 for sequential execution.",
    )
    parser.add_argument(
        "--gpus",
        type=str,
        default=None,
        help="Comma-separated list of GPU IDs to use (e.g., '0,1,2'). If not specified, all available GPUs will be used.",
    )
    return parser.parse_args()


def get_available_gpus(gpu_ids=None):
    if gpu_ids is not None:
        return [int(gpu_id) for gpu_id in gpu_ids.split(",")]
    return list(range(torch.cuda.device_count()))


def check_latex_dependencies():
    try:
        subprocess.run(
            ["pdflatex", "--version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
    except FileNotFoundError:
        print(
            "pdflatex not found. Please install texlive-full using: sudo apt-get install texlive-full"
        )
        return False
    return True


def main():
    print_time()
    args = parse_arguments()
    
    if args.report_format == "latex" and not check_latex_dependencies():
        print("LaTeX dependencies missing. Exiting.")
        sys.exit(1)
    
    available_gpus = get_available_gpus(args.gpus)
    if len(available_gpus) == 0:
        print("No GPUs available. Exiting.")
        sys.exit(1)
    
    # Set up directories
    paper_name = osp.splitext(osp.basename(args.pdf_path))[0]
    base_dir = osp.abspath("repro_papers")
    os.makedirs(base_dir, exist_ok=True)
    
    paper_dir = osp.join(base_dir, paper_name)
    os.makedirs(paper_dir, exist_ok=True)
    
    # Create client
    client, client_model = create_client(args.model)
    
    # 1. Extract paper information
    if not args.skip_paper_extraction:
        print(f"Extracting information from paper: {args.pdf_path}")
        paper_info = extract_paper_info(args.pdf_path, client, client_model)
        
        # Save paper info
        with open(osp.join(paper_dir, "paper_info.json"), "w") as f:
            json.dump(paper_info, f, indent=2)
    else:
        # Load existing paper info
        with open(osp.join(paper_dir, "paper_info.json"), "r") as f:
            paper_info = json.load(f)
    
    # 2. Generate implementation
    if not args.skip_code_generation:
        print(f"Generating implementation for paper: {paper_name}")
        implementation_dir = osp.join(paper_dir, "implementation")
        os.makedirs(implementation_dir, exist_ok=True)
        
        # Configure the coder
        inp = InputOutput(no_stream=True, yes=True)
        Model.chat_completions = client_model
        coder = Coder(
            inp,
            fnames=[osp.join(implementation_dir, "README.md")],
            main_model=Model.create(args.model),
            edit_format="full",
            pretty=False,
        )
        
        generate_implementation(paper_info, implementation_dir, coder, client, client_model, template=args.template)
    
    # 3. Run experiments
    if not args.skip_experiments:
        print(f"Running experiments for paper: {paper_name}")
        results_dir = osp.join(paper_dir, "results")
        os.makedirs(results_dir, exist_ok=True)
        
        implementation_dir = osp.join(paper_dir, "implementation")
        results = run_experiments(paper_info, implementation_dir, results_dir, available_gpus, client, client_model)
        
        # Save results
        with open(osp.join(results_dir, "experiment_results.json"), "w") as f:
            json.dump(results, f, indent=2)
    else:
        # Load existing results
        with open(osp.join(paper_dir, "results", "experiment_results.json"), "r") as f:
            results = json.load(f)
    
    # 4. Analyze results
    print(f"Analyzing results for paper: {paper_name}")
    analysis_dir = osp.join(paper_dir, "analysis")
    os.makedirs(analysis_dir, exist_ok=True)
    
    analysis = analyze_results(paper_info, results, analysis_dir, client, client_model)
    
    # Save analysis
    with open(osp.join(analysis_dir, "result_analysis.json"), "w") as f:
        json.dump(analysis, f, indent=2)
    
    # 5. Generate report
    print(f"Generating reproduction report for paper: {paper_name}")
    report_dir = osp.join(paper_dir, "report")
    os.makedirs(report_dir, exist_ok=True)
    
    generate_report(paper_info, results, analysis, report_dir, args.report_format, client, client_model)
    
    print(f"Paper reproduction complete! Results and report available in: {paper_dir}")
    print_time()


if __name__ == "__main__":
    main() 