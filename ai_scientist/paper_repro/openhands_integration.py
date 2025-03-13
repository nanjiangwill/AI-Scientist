"""
OpenHands integration module for paper reproduction.

This module provides functions to generate code and run experiments using OpenHands,
replacing the Aider-based implementation.
"""

import json
import os
import os.path as osp
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

def setup_openhands_config(implementation_dir, paper_info, model_config="llm.eval_sonnet"):
    """
    Set up the OpenHands configuration for code generation.
    
    Args:
        implementation_dir (str): Directory where the implementation will be generated
        paper_info (dict): Dictionary containing information about the paper
        model_config (str): OpenHands model configuration name
        
    Returns:
        dict: Configuration for OpenHands
    """
    # Get the absolute path to the OpenHands directory
    openhands_dir = osp.abspath("../openhands")
    
    # Create a config for OpenHands
    config = {
        "repo_split": implementation_dir,
        "model_config": model_config,
        "agent": "CodeActAgent",
        "eval_limit": 1,  # We're generating for one paper at a time
        "max_iter": 150,  # Allow more iterations for complex papers
        "num_workers": 1,
        "dataset": "wentingzhao/commit0_combined",  # Default dataset
        "dataset_split": "test",
    }
    
    return config

def initialize_runtime(config):
    """
    Initialize the OpenHands runtime.
    
    Args:
        config (dict): Configuration for OpenHands
        
    Returns:
        object: Runtime object for OpenHands
    """
    # This would typically involve running the appropriate OpenHands initialization
    # For now, we'll return the config as a placeholder
    openhands_dir = osp.abspath("../openhands")
    
    # Create a temporary script to initialize the runtime
    with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=False) as temp:
        temp.write("#!/usr/bin/env bash\n")
        temp.write(f"cd {openhands_dir}\n")
        temp.write("poetry run python evaluation/benchmarks/commit0/run_infer.py ")
        temp.write(f"--repo_split={config['repo_split']} ")
        temp.write(f"--model_config={config['model_config']} ")
        temp.write(f"--agent={config['agent']} ")
        temp.write(f"--eval_limit={config['eval_limit']} ")
        temp.write(f"--max_iter={config['max_iter']} ")
        temp.write(f"--num_workers={config['num_workers']} ")
        temp.write(f"--dataset={config['dataset']} ")
        temp.write(f"--dataset_split={config['dataset_split']} ")
        temp.write("--initialize_runtime\n")
    
    temp_script_path = temp.name
    os.chmod(temp_script_path, 0o755)
    
    # Execute the temporary script to initialize the runtime
    try:
        subprocess.run([temp_script_path], check=True)
    finally:
        os.unlink(temp_script_path)
    
    return config

def generate_code_with_openhands(paper_info, output_dir, model_config="llm.eval_sonnet", template=None):
    """
    Generate code implementation using OpenHands.
    
    Args:
        paper_info (dict): Dictionary containing information about the paper
        output_dir (str): Directory where the implementation will be generated
        model_config (str): OpenHands model configuration name
        template (str, optional): Path to a template directory to use as a starting point
        
    Returns:
        bool: True if code generation was successful, False otherwise
    """
    print(f"Generating code with OpenHands using {model_config}...")
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # If a template is provided, copy it to the output directory
    if template and osp.exists(template):
        for item in os.listdir(template):
            s = osp.join(template, item)
            d = osp.join(output_dir, item)
            if osp.isdir(s):
                shutil.copytree(s, d, dirs_exist_ok=True)
            else:
                shutil.copy2(s, d)
    
    # Create a README.md file with basic information about the paper
    with open(osp.join(output_dir, "README.md"), "w") as f:
        f.write(f"# {paper_info['title']}\n\n")
        f.write(f"Implementation of the paper: {paper_info['title']}\n\n")
        f.write(f"Authors: {', '.join(paper_info['authors'])}\n\n")
        f.write(f"Year: {paper_info.get('year', 'N/A')}\n\n")
        f.write("## Implementation Details\n\n")
        f.write("This implementation was generated using OpenHands.\n\n")
    
    # Prepare instruction for OpenHands based on the paper info
    instruction = generate_paper_instruction(paper_info)
    
    # Save the instruction to a file
    with open(osp.join(output_dir, "paper_instruction.txt"), "w") as f:
        f.write(instruction)
    
    # Set up OpenHands configuration
    config = setup_openhands_config(output_dir, paper_info, model_config)
    
    # Initialize OpenHands runtime
    runtime = initialize_runtime(config)
    
    # Run OpenHands to generate the implementation
    openhands_dir = osp.abspath("../openhands")
    
    # Create a temporary script to run OpenHands
    with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=False) as temp:
        temp.write("#!/usr/bin/env bash\n")
        temp.write(f"cd {openhands_dir}\n")
        temp.write(f"export INSTANCE_INSTRUCTION_PATH={osp.join(output_dir, 'paper_instruction.txt')}\n")
        temp.write("bash evaluation/benchmarks/commit0/scripts/run_infer.sh ")
        temp.write(f"REPO_SPLIT={output_dir} ")
        temp.write(f"MODEL_CONFIG={model_config} ")
        temp.write(f"AGENT={config['agent']} ")
        temp.write(f"EVAL_LIMIT={config['eval_limit']} ")
        temp.write(f"MAX_ITER={config['max_iter']} ")
        temp.write(f"NUM_WORKERS={config['num_workers']} ")
        temp.write(f"DATASET={config['dataset']} ")
        temp.write(f"SPLIT={config['dataset_split']}\n")
    
    temp_script_path = temp.name
    os.chmod(temp_script_path, 0o755)
    
    # Execute the temporary script to run OpenHands
    try:
        subprocess.run([temp_script_path], check=True)
    finally:
        os.unlink(temp_script_path)
    
    return True

def generate_paper_instruction(paper_info):
    """
    Generate a structured instruction for OpenHands based on paper information.
    
    Args:
        paper_info (dict): Dictionary containing information about the paper
        
    Returns:
        str: Formatted instruction for OpenHands
    """
    instruction = f"# Paper Reproduction Task\n\n"
    instruction += f"## Paper Information\n\n"
    instruction += f"Title: {paper_info['title']}\n\n"
    instruction += f"Authors: {', '.join(paper_info['authors'])}\n\n"
    instruction += f"Year: {paper_info.get('year', 'N/A')}\n\n"
    
    # Add abstract
    if paper_info.get('abstract'):
        instruction += f"Abstract: {paper_info['abstract']}\n\n"
    
    # Add key findings
    if paper_info.get('key_findings'):
        instruction += f"## Key Findings\n\n"
        if isinstance(paper_info['key_findings'], list):
            for i, finding in enumerate(paper_info['key_findings']):
                instruction += f"{i+1}. {finding}\n"
        else:
            instruction += f"{paper_info['key_findings']}\n\n"
    
    # Add methodology
    if paper_info.get('methodology'):
        instruction += f"## Methodology\n\n"
        instruction += f"{paper_info['methodology']}\n\n"
    
    # Add algorithms
    if paper_info.get('algorithms'):
        instruction += f"## Algorithms\n\n"
        if isinstance(paper_info['algorithms'], list):
            for i, algorithm in enumerate(paper_info['algorithms']):
                instruction += f"### Algorithm {i+1}\n"
                instruction += f"{algorithm}\n\n"
        else:
            instruction += f"{paper_info['algorithms']}\n\n"
    
    # Add experimental setup
    if paper_info.get('experimental_setup'):
        instruction += f"## Experimental Setup\n\n"
        instruction += f"{paper_info['experimental_setup']}\n\n"
    
    # Add task instructions
    instruction += f"## Task\n\n"
    instruction += f"Your task is to implement the key algorithms and methodologies described in this paper. "
    instruction += f"Create a working implementation that can reproduce the main results of the paper. "
    instruction += f"Include code for training, evaluation, and any necessary data processing. "
    instruction += f"Make sure to include clear instructions on how to run the experiments.\n\n"
    
    return instruction

def run_experiments_with_openhands(paper_info, implementation_dir, results_dir, model_config="llm.eval_sonnet"):
    """
    Run experiments using OpenHands-generated code.
    
    Args:
        paper_info (dict): Dictionary containing information about the paper
        implementation_dir (str): Directory containing the implementation
        results_dir (str): Directory where results will be stored
        model_config (str): OpenHands model configuration name
        
    Returns:
        dict: Dictionary containing experiment results
    """
    print(f"Running experiments with OpenHands using {model_config}...")
    
    # Create results directory if it doesn't exist
    os.makedirs(results_dir, exist_ok=True)
    
    # Set up OpenHands configuration
    config = setup_openhands_config(implementation_dir, paper_info, model_config)
    
    # Initialize OpenHands runtime
    runtime = initialize_runtime(config)
    
    # Run OpenHands to execute the experiments
    openhands_dir = osp.abspath("../openhands")
    
    # Prepare an instruction for running experiments
    run_instruction = f"# Run Experiments for Paper: {paper_info['title']}\n\n"
    run_instruction += "Execute the implementation to reproduce the key results of the paper.\n"
    run_instruction += "Save all results, figures, and metrics to the specified output directory.\n"
    
    # Save the instruction to a file
    with open(osp.join(results_dir, "run_experiments_instruction.txt"), "w") as f:
        f.write(run_instruction)
    
    # Create a temporary script to run experiments with OpenHands
    with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=False) as temp:
        temp.write("#!/usr/bin/env bash\n")
        temp.write(f"cd {openhands_dir}\n")
        temp.write(f"export INSTANCE_INSTRUCTION_PATH={osp.join(results_dir, 'run_experiments_instruction.txt')}\n")
        temp.write(f"export RESULTS_OUTPUT_DIR={results_dir}\n")
        temp.write("bash evaluation/benchmarks/commit0/scripts/run_infer.sh ")
        temp.write(f"REPO_SPLIT={implementation_dir} ")
        temp.write(f"MODEL_CONFIG={model_config} ")
        temp.write(f"AGENT={config['agent']} ")
        temp.write(f"EVAL_LIMIT={config['eval_limit']} ")
        temp.write(f"MAX_ITER={config['max_iter']} ")
        temp.write(f"NUM_WORKERS={config['num_workers']} ")
        temp.write(f"DATASET={config['dataset']} ")
        temp.write(f"SPLIT={config['dataset_split']}\n")
    
    temp_script_path = temp.name
    os.chmod(temp_script_path, 0o755)
    
    # Execute the temporary script to run experiments with OpenHands
    try:
        subprocess.run([temp_script_path], check=True)
    finally:
        os.unlink(temp_script_path)
    
    # Collect and process results
    results = {
        "paper_id": paper_info.get("id", "unknown"),
        "paper_title": paper_info["title"],
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "metrics": {},
        "figures": [],
        "tables": [],
        "successful": True,
        "notes": "Experiments run with OpenHands",
    }
    
    # Check for any JSON result files
    for file in os.listdir(results_dir):
        if file.endswith(".json") and file != "experiment_results.json":
            try:
                with open(osp.join(results_dir, file), "r") as f:
                    result_data = json.load(f)
                    if isinstance(result_data, dict) and "metrics" in result_data:
                        results["metrics"].update(result_data["metrics"])
            except Exception as e:
                print(f"Error reading result file {file}: {e}")
    
    # Check for any image files (figures)
    for file in os.listdir(results_dir):
        if file.endswith((".png", ".jpg", ".pdf", ".svg")):
            results["figures"].append({
                "path": osp.join(results_dir, file),
                "name": file,
                "description": f"Figure generated during experiment: {file}"
            })
    
    return results 