"""
Launch script for paper reproduction.

This script launches the paper reproduction process, which extracts information from
academic papers, generates implementation code, runs experiments, and compares results
with those reported in the paper.
"""

import argparse
import json
import os
import os.path as osp
import sys
from datetime import datetime

from ai_scientist.llm import create_client, AVAILABLE_LLMS
from ai_scientist.openhands_wrapper import create_openhands_coder
from ai_scientist.paper_reproduction import reproduce_paper


def print_time():
    print(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))


def parse_arguments():
    parser = argparse.ArgumentParser(description="Reproduce results from academic papers")
    parser.add_argument(
        "--pdf",
        type=str,
        required=True,
        help="Path to the PDF file of the paper to reproduce",
    )
    parser.add_argument(
        "--model",
        type=str,
        default="gpt-4o",
        choices=AVAILABLE_LLMS,
        help="Model to use for paper reproduction.",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="results/paper_reproduction",
        help="Directory to store reproduction results",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_arguments()
    
    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Create LLM client
    client, client_model = create_client(args.model)
    
    # Create OpenHands coder
    class InputOutput:
        def __init__(self, yes=False, chat_history_file=None):
            self.yes = yes
            self.chat_history_file = chat_history_file
    
    class Model:
        def __init__(self, name):
            self.name = name
    
    # Extract paper filename for chat history
    pdf_filename = osp.basename(args.pdf)
    pdf_name = osp.splitext(pdf_filename)[0]
    chat_history_file = osp.join(args.output_dir, f"{pdf_name}_chat_history.txt")
    
    main_model = Model(args.model)
    io = InputOutput(yes=True, chat_history_file=chat_history_file)
    
    # Create temporary files for the coder to work with
    temp_implementation = osp.join(args.output_dir, "temp_implementation.py")
    temp_experiment = osp.join(args.output_dir, "temp_experiment.py")
    
    with open(temp_implementation, "w") as f:
        f.write("# Temporary implementation file\n")
    
    with open(temp_experiment, "w") as f:
        f.write("# Temporary experiment file\n")
    
    coder = create_openhands_coder(
        main_model=main_model,
        fnames=[temp_implementation, temp_experiment],
        io=io,
        stream=False,
        use_git=False,
        edit_format="diff",
    )
    
    print_time()
    print(f"*Starting paper reproduction for {pdf_filename}*")
    
    try:
        # Reproduce paper
        results = reproduce_paper(args.pdf, client, client_model, coder)
        
        # Save results
        results_file = osp.join(args.output_dir, f"{pdf_name}_results.json")
        with open(results_file, "w") as f:
            json.dump(results, f, indent=4)
        
        print_time()
        print(f"*Paper reproduction completed*")
        print(f"Paper: {results['paper_title']}")
        print(f"Experiment directory: {results['experiment_dir']}")
        print(f"Results saved to: {results_file}")
        
    except Exception as e:
        print(f"Error during paper reproduction: {e}")
        import traceback
        print(traceback.format_exc())
        sys.exit(1)
    
    # Clean up temporary files
    if osp.exists(temp_implementation):
        os.remove(temp_implementation)
    
    if osp.exists(temp_experiment):
        os.remove(temp_experiment)
    
    print("Paper reproduction process completed successfully.")