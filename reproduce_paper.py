#!/usr/bin/env python3
"""
Paper Reproduction Script

This script reproduces results from scientific papers that don't provide code.
It skips the idea generation phase of the AI Scientist and focuses on:
1. Extracting methods and experiments from a paper
2. Implementing the methods
3. Running experiments
4. Comparing results with the original paper's claims
"""

import argparse
import json
import os
import os.path as osp
import shutil
import sys
import time
import torch
from aider.coders import Coder
from aider.io import InputOutput
from aider.models import Model
from datetime import datetime

from ai_scientist.llm import create_client, AVAILABLE_LLMS
from ai_scientist.perform_experiments import perform_experiments
from ai_scientist.perform_review import perform_review, load_paper
from ai_scientist.perform_writeup import perform_writeup, generate_latex

# Import paper reproduction modules
sys.path.append(osp.join(os.path.dirname(__file__), 'templates', 'paper_reproduction'))
from paper_parser import PaperParser
from code_generator import CodeGenerator
from result_validator import ResultValidator


def print_time():
    print(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))


def parse_arguments():
    parser = argparse.ArgumentParser(description="Reproduce results from scientific papers")
    parser.add_argument(
        "--paper",
        type=str,
        required=True,
        help="Path or URL to the paper PDF",
    )
    parser.add_argument(
        "--model",
        type=str,
        default="claude-3-5-sonnet-20240620",
        choices=AVAILABLE_LLMS,
        help="Model to use for code generation and analysis",
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default="paper_reproductions",
        help="Directory to save reproduction results",
    )
    parser.add_argument(
        "--skip_extraction",
        action="store_true",
        help="Skip paper extraction and use existing extracted_info.json",
    )
    parser.add_argument(
        "--skip_implementation",
        action="store_true",
        help="Skip implementation and use existing code",
    )
    parser.add_argument(
        "--skip_experiments",
        action="store_true",
        help="Skip experiments and use existing results",
    )
    parser.add_argument(
        "--gpu",
        type=str,
        default=None,
        help="GPU ID to use (e.g., '0'). If not specified, all available GPUs will be used.",
    )
    return parser.parse_args()


def setup_environment(gpu_id=None):
    """Set up the environment for experiments"""
    if gpu_id is not None:
        os.environ["CUDA_VISIBLE_DEVICES"] = str(gpu_id)
    
    # Print available GPUs
    if torch.cuda.is_available():
        print(f"Available GPUs: {torch.cuda.device_count()}")
        for i in range(torch.cuda.device_count()):
            print(f"  GPU {i}: {torch.cuda.get_device_name(i)}")
    else:
        print("No GPUs available. Using CPU.")


def extract_paper_info(paper_path, output_dir):
    """Extract information from the paper"""
    print_time()
    print("*Starting Paper Extraction*")
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Extract information from the paper
    parser = PaperParser(paper_path)
    extracted_info = parser.extract_all_info()
    
    # Save extracted information
    extracted_info_path = osp.join(output_dir, "extracted_info.json")
    with open(extracted_info_path, "w") as f:
        json.dump(extracted_info, f, indent=4)
    
    print(f"Paper information extracted and saved to {extracted_info_path}")
    return extracted_info


def implement_methods(extracted_info, output_dir, model, client):
    """Implement methods described in the paper"""
    print_time()
    print("*Starting Method Implementation*")
    
    # Create implementation directory
    implementation_dir = osp.join(output_dir, "implementation")
    os.makedirs(implementation_dir, exist_ok=True)
    
    # Generate code implementations
    generator = CodeGenerator(extracted_info, implementation_dir)
    implementation = generator.generate_all_code()
    
    # Use LLM to improve implementations if needed
    methods_dir = osp.join(output_dir, "methods")
    os.makedirs(methods_dir, exist_ok=True)
    
    # For each method, use the LLM to improve the implementation
    for method_name, method_info in implementation.items():
        method_file = osp.join(implementation_dir, f"{method_name}.py")
        
        if osp.exists(method_file):
            # Set up aider for code improvement
            io = InputOutput(yes=True, chat_history_file=f"{methods_dir}/{method_name}_aider.txt")
            main_model = Model(model)
            coder = Coder.create(
                main_model=main_model,
                fnames=[method_file],
                io=io,
                stream=False,
                use_git=False,
                edit_format="diff",
            )
            
            # Improve the implementation
            prompt = f"""
            I've generated an initial implementation of the '{method_name}' method from the paper.
            Please review and improve this implementation to make it more accurate and efficient.
            Focus on:
            1. Ensuring it correctly implements the method described in the paper
            2. Adding any missing details or optimizations
            3. Fixing any potential bugs or issues
            4. Adding proper documentation
            
            Here's the extracted information about this method from the paper:
            {json.dumps(next((m for m in extracted_info.get('methods', []) if m.get('name', '').lower() in method_name), {}), indent=2)}
            """
            
            try:
                coder.run(prompt)
                print(f"Improved implementation of {method_name}")
            except Exception as e:
                print(f"Error improving {method_name}: {e}")
    
    print(f"Method implementations generated and saved to {implementation_dir}")
    return implementation


def run_experiments(extracted_info, output_dir, model, client):
    """Run experiments using the implemented methods"""
    print_time()
    print("*Starting Experiments*")
    
    # Set up paths
    implementation_dir = osp.join(output_dir, "implementation")
    results_dir = osp.join(output_dir, "results")
    os.makedirs(results_dir, exist_ok=True)
    
    # Run the experiment script
    experiment_script = osp.join(implementation_dir, "run_experiments.py")
    if osp.exists(experiment_script):
        try:
            # Change to implementation directory and run the script
            os.chdir(implementation_dir)
            os.system(f"python run_experiments.py --output_dir={osp.relpath(results_dir)}")
            os.chdir(output_dir)  # Return to original directory
            print(f"Experiments completed. Results saved to {results_dir}")
        except Exception as e:
            print(f"Error running experiments: {e}")
            return None
    else:
        print(f"Experiment script not found at {experiment_script}")
        return None
    
    # Load results
    results_file = osp.join(results_dir, "results.json")
    if osp.exists(results_file):
        with open(results_file, "r") as f:
            results = json.load(f)
        return results
    else:
        print(f"Results file not found at {results_file}")
        return None


def validate_results(extracted_info, reproduced_results, output_dir):
    """Validate reproduced results against original paper claims"""
    print_time()
    print("*Starting Result Validation*")
    
    # Set up paths
    validation_dir = osp.join(output_dir, "validation")
    os.makedirs(validation_dir, exist_ok=True)
    
    # Validate results
    validator = ResultValidator(extracted_info, reproduced_results, validation_dir)
    validator.compare_results()
    validation_summary = validator.validate_reproduction()
    validator.generate_plots()
    report_path = validator.generate_report()
    
    print(f"Validation completed. Report saved to {report_path}")
    return validation_summary


def generate_report(extracted_info, implementation, reproduced_results, validation_summary, output_dir, model, client):
    """Generate a comprehensive report on the reproduction"""
    print_time()
    print("*Starting Report Generation*")
    
    # Set up paths
    report_dir = osp.join(output_dir, "report")
    os.makedirs(report_dir, exist_ok=True)
    
    # Copy LaTeX template
    template_dir = osp.join("templates", "paper_reproduction", "latex")
    shutil.copytree(template_dir, osp.join(report_dir, "latex"), dirs_exist_ok=True)
    
    # Set up aider for report generation
    latex_file = osp.join(report_dir, "latex", "template.tex")
    io = InputOutput(yes=True, chat_history_file=f"{report_dir}/report_aider.txt")
    main_model = Model(model)
    coder = Coder.create(
        main_model=main_model,
        fnames=[latex_file],
        io=io,
        stream=False,
        use_git=False,
        edit_format="diff",
    )
    
    # Generate report content
    prompt = f"""
    I need to generate a comprehensive report on the reproduction of a scientific paper.
    
    Here's the information about the paper:
    {json.dumps(extracted_info, indent=2)}
    
    Here's the validation summary:
    {json.dumps(validation_summary, indent=2)}
    
    Please update the LaTeX template with this information, focusing on:
    1. The paper title, authors, and abstract
    2. The methods we implemented
    3. The experiments we ran
    4. The comparison between our reproduced results and the original paper's claims
    5. Discussion of challenges, limitations, and potential improvements
    
    Make sure to include references to the original paper and any other relevant work.
    """
    
    try:
        coder.run(prompt)
        print(f"Report template updated")
    except Exception as e:
        print(f"Error updating report template: {e}")
    
    # Generate PDF
    try:
        os.chdir(osp.join(report_dir, "latex"))
        os.system("pdflatex template.tex")
        os.system("pdflatex template.tex")  # Run twice for references
        os.chdir(output_dir)  # Return to original directory
        
        # Copy PDF to output directory
        shutil.copy(
            osp.join(report_dir, "latex", "template.pdf"),
            osp.join(output_dir, "reproduction_report.pdf")
        )
        
        print(f"Report generated and saved to {osp.join(output_dir, 'reproduction_report.pdf')}")
    except Exception as e:
        print(f"Error generating PDF report: {e}")


def main():
    """Main function to reproduce paper results"""
    args = parse_arguments()
    
    # Set up environment
    setup_environment(args.gpu)
    
    # Create client
    client, client_model = create_client(args.model)
    
    # Create output directory
    paper_name = osp.splitext(osp.basename(args.paper))[0] if not args.paper.startswith(('http://', 'https://')) else "paper"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = osp.join(args.output_dir, f"{timestamp}_{paper_name}")
    os.makedirs(output_dir, exist_ok=True)
    
    # Extract paper information
    if args.skip_extraction:
        # Load existing extracted information
        extracted_info_path = osp.join(output_dir, "extracted_info.json")
        if osp.exists(extracted_info_path):
            with open(extracted_info_path, "r") as f:
                extracted_info = json.load(f)
        else:
            print("No extracted_info.json found. Running extraction...")
            extracted_info = extract_paper_info(args.paper, output_dir)
    else:
        extracted_info = extract_paper_info(args.paper, output_dir)
    
    # Implement methods
    if args.skip_implementation:
        # Assume implementations exist
        implementation = {}
    else:
        implementation = implement_methods(extracted_info, output_dir, args.model, client)
    
    # Run experiments
    if args.skip_experiments:
        # Load existing results
        results_file = osp.join(output_dir, "results", "results.json")
        if osp.exists(results_file):
            with open(results_file, "r") as f:
                reproduced_results = json.load(f)
        else:
            print("No results.json found. Running experiments...")
            reproduced_results = run_experiments(extracted_info, output_dir, args.model, client)
    else:
        reproduced_results = run_experiments(extracted_info, output_dir, args.model, client)
    
    # Validate results
    if reproduced_results:
        validation_summary = validate_results(extracted_info, reproduced_results, output_dir)
    else:
        print("No results available for validation.")
        validation_summary = {}
    
    # Generate report
    if extracted_info and reproduced_results and validation_summary:
        generate_report(extracted_info, implementation, reproduced_results, validation_summary, output_dir, args.model, client)
    
    print("Paper reproduction completed!")


if __name__ == "__main__":
    main()