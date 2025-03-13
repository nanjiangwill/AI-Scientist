"""
Experiment Reproduction Module

This module is responsible for running the experiments defined in the implementation
to reproduce the results from the paper.
"""

import json
import os
import os.path as osp
import shutil
import subprocess
import sys
import time
from typing import Dict, List, Any, Optional

def run_experiments(
    paper_info: Dict[str, Any],
    implementation_dir: str,
    results_dir: str,
    available_gpus: List[int],
    client,
    client_model: str
) -> Dict[str, Any]:
    """
    Run experiments to reproduce paper results.
    
    Args:
        paper_info: Extracted information from the paper
        implementation_dir: Directory containing the implementation
        results_dir: Directory to save experiment results
        available_gpus: List of GPU IDs to use for experiments
        client: LLM client
        client_model: Name of the LLM model
        
    Returns:
        Dictionary containing experiment results
    """
    os.makedirs(results_dir, exist_ok=True)
    
    # Check if there's a main entry point
    main_file = identify_main_file(implementation_dir)
    
    # Create an experiment plan
    experiment_plan = create_experiment_plan(paper_info, implementation_dir, client, client_model)
    
    # Save the experiment plan
    with open(osp.join(results_dir, "experiment_plan.json"), "w") as f:
        json.dump(experiment_plan, f, indent=2)
    
    # Run the experiments
    experiment_results = execute_experiment_plan(
        experiment_plan, implementation_dir, results_dir, available_gpus
    )
    
    return experiment_results


def identify_main_file(implementation_dir: str) -> Optional[str]:
    """
    Identify the main entry point for running experiments.
    
    Args:
        implementation_dir: Directory containing the implementation
        
    Returns:
        Path to the main file or None if not found
    """
    # Common main file names
    candidate_names = ["main.py", "train.py", "run.py", "experiment.py"]
    
    for name in candidate_names:
        path = osp.join(implementation_dir, name)
        if osp.exists(path):
            return path
    
    # Check if any python file in the root directory contains a main function or script
    for file in os.listdir(implementation_dir):
        if file.endswith(".py"):
            path = osp.join(implementation_dir, file)
            
            with open(path, "r") as f:
                content = f.read()
                
                if "if __name__ == '__main__':" in content:
                    return path
    
    return None


def create_experiment_plan(
    paper_info: Dict[str, Any],
    implementation_dir: str,
    client,
    client_model: str
) -> Dict[str, Any]:
    """
    Create a plan for running experiments.
    
    Args:
        paper_info: Extracted information from the paper
        implementation_dir: Directory containing the implementation
        client: LLM client
        client_model: Name of the LLM model
        
    Returns:
        Dictionary containing the experiment plan
    """
    code_guidance = paper_info["code_guidance"]
    results_tables = paper_info["results_tables"]
    
    # Check if there's a README with instructions
    readme_path = osp.join(implementation_dir, "README.md")
    readme_content = ""
    if osp.exists(readme_path):
        with open(readme_path, "r") as f:
            readme_content = f.read()
    
    # List all Python files in the implementation directory
    python_files = []
    for root, _, files in os.walk(implementation_dir):
        for file in files:
            if file.endswith(".py"):
                rel_path = osp.relpath(osp.join(root, file), implementation_dir)
                python_files.append(rel_path)
    
    # Create an experiment plan using LLM
    prompt = f"""
    You are planning experiments to reproduce a research paper's results.
    
    Paper title: {paper_info["basic_info"].get("title", "")}
    
    Expected results to reproduce:
    {json.dumps(results_tables, indent=2)}
    
    Implementation guidance:
    {json.dumps(code_guidance, indent=2)}
    
    README content:
    {readme_content}
    
    Python files in the implementation:
    {json.dumps(python_files, indent=2)}
    
    Based on this information, create a comprehensive plan for running experiments to reproduce the paper's results.
    
    The plan should include:
    1. The main command to run each experiment
    2. Required configuration files or parameters for each experiment
    3. Expected output and where results will be saved
    4. Dependencies between experiments (if any)
    5. Estimated runtime for each experiment
    
    Format your response as a JSON object with the following structure:
    {{
        "experiments": [
            {{
                "name": "experiment_name",
                "description": "What this experiment aims to reproduce",
                "command": "python script.py --arg1 value1 --arg2 value2",
                "working_directory": "relative/path/to/working/dir",
                "output_directory": "relative/path/to/output",
                "expected_results": "Description of expected results",
                "estimated_runtime_minutes": 60
            }}
        ],
        "evaluation": {{
            "command": "python evaluate.py --results_dir path/to/results",
            "output_file": "path/to/evaluation/results.json"
        }}
    }}
    """
    
    response = client.get(prompt, model=client_model)
    
    # Extract the JSON from the response
    import re
    json_match = re.search(r'```json\n(.*?)\n```', response, re.DOTALL)
    if json_match:
        experiment_plan_json = json_match.group(1)
    else:
        # Try to find any JSON-like structure in the response
        experiment_plan_json = response
    
    try:
        experiment_plan = json.loads(experiment_plan_json)
    except json.JSONDecodeError:
        # Default experiment plan if parsing fails
        main_file = identify_main_file(implementation_dir)
        if main_file:
            main_file_path = osp.relpath(main_file, implementation_dir)
            experiment_plan = {
                "experiments": [
                    {
                        "name": "default_experiment",
                        "description": "Default experiment to reproduce paper results",
                        "command": f"python {main_file_path}",
                        "working_directory": ".",
                        "output_directory": "results",
                        "expected_results": "Results similar to those reported in the paper",
                        "estimated_runtime_minutes": 60
                    }
                ],
                "evaluation": {
                    "command": "python evaluate.py --results_dir results",
                    "output_file": "evaluation_results.json"
                }
            }
        else:
            experiment_plan = {
                "experiments": [],
                "evaluation": {
                    "command": "",
                    "output_file": ""
                }
            }
    
    return experiment_plan


def execute_experiment_plan(
    experiment_plan: Dict[str, Any],
    implementation_dir: str,
    results_dir: str,
    available_gpus: List[int]
) -> Dict[str, Any]:
    """
    Execute the experiment plan.
    
    Args:
        experiment_plan: Experiment plan to execute
        implementation_dir: Directory containing the implementation
        results_dir: Directory to save experiment results
        available_gpus: List of GPU IDs to use for experiments
        
    Returns:
        Dictionary containing experiment results
    """
    experiments = experiment_plan.get("experiments", [])
    experiment_results = {}
    
    for i, experiment in enumerate(experiments):
        exp_name = experiment.get("name", f"experiment_{i}")
        exp_dir = osp.join(results_dir, exp_name)
        os.makedirs(exp_dir, exist_ok=True)
        
        command = experiment.get("command", "")
        if not command:
            print(f"No command specified for experiment: {exp_name}")
            continue
        
        working_dir = experiment.get("working_directory", ".")
        full_working_dir = osp.join(implementation_dir, working_dir)
        
        # Ensure output directory exists
        output_dir = experiment.get("output_directory", "")
        if output_dir:
            full_output_dir = osp.join(full_working_dir, output_dir)
            os.makedirs(full_output_dir, exist_ok=True)
        
        # Assign a GPU
        gpu_id = available_gpus[i % len(available_gpus)]
        env = os.environ.copy()
        env["CUDA_VISIBLE_DEVICES"] = str(gpu_id)
        
        print(f"Running experiment: {exp_name}")
        print(f"Command: {command}")
        print(f"Working directory: {full_working_dir}")
        print(f"Using GPU: {gpu_id}")
        
        # Save experiment info
        exp_info = {
            "name": exp_name,
            "command": command,
            "working_directory": working_dir,
            "gpu_id": gpu_id,
            "start_time": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        with open(osp.join(exp_dir, "experiment_info.json"), "w") as f:
            json.dump(exp_info, f, indent=2)
        
        # Run the experiment
        try:
            # Split command into args
            cmd_args = command.split()
            
            # Create log files
            stdout_file = open(osp.join(exp_dir, "stdout.log"), "w")
            stderr_file = open(osp.join(exp_dir, "stderr.log"), "w")
            
            # Start the process
            process = subprocess.Popen(
                cmd_args, 
                cwd=full_working_dir, 
                env=env, 
                stdout=stdout_file, 
                stderr=stderr_file
            )
            
            # Wait for completion
            return_code = process.wait()
            
            # Update experiment info
            exp_info["return_code"] = return_code
            exp_info["end_time"] = time.strftime("%Y-%m-%d %H:%M:%S")
            exp_info["success"] = (return_code == 0)
            
            with open(osp.join(exp_dir, "experiment_info.json"), "w") as f:
                json.dump(exp_info, f, indent=2)
            
            # Close log files
            stdout_file.close()
            stderr_file.close()
            
            # Check if the expected output file exists
            expected_output = experiment.get("output_file", "")
            if expected_output:
                expected_output_path = osp.join(full_working_dir, expected_output)
                if osp.exists(expected_output_path):
                    # Copy the output file to the experiment directory
                    shutil.copy2(expected_output_path, osp.join(exp_dir, osp.basename(expected_output)))
            
            # Add results to the dictionary
            experiment_results[exp_name] = {
                "success": (return_code == 0),
                "return_code": return_code,
                "logs_dir": exp_dir
            }
            
            print(f"Experiment {exp_name} completed with return code {return_code}")
            
        except Exception as e:
            # Handle any exceptions
            print(f"Error running experiment {exp_name}: {str(e)}")
            
            exp_info["error"] = str(e)
            exp_info["end_time"] = time.strftime("%Y-%m-%d %H:%M:%S")
            exp_info["success"] = False
            
            with open(osp.join(exp_dir, "experiment_info.json"), "w") as f:
                json.dump(exp_info, f, indent=2)
            
            experiment_results[exp_name] = {
                "success": False,
                "error": str(e),
                "logs_dir": exp_dir
            }
    
    # Run evaluation
    evaluation = experiment_plan.get("evaluation", {})
    eval_command = evaluation.get("command", "")
    
    if eval_command:
        eval_dir = osp.join(results_dir, "evaluation")
        os.makedirs(eval_dir, exist_ok=True)
        
        print(f"Running evaluation: {eval_command}")
        
        try:
            # Split command into args
            cmd_args = eval_command.split()
            
            # Create log files
            stdout_file = open(osp.join(eval_dir, "stdout.log"), "w")
            stderr_file = open(osp.join(eval_dir, "stderr.log"), "w")
            
            # Start the process
            process = subprocess.Popen(
                cmd_args, 
                cwd=implementation_dir, 
                stdout=stdout_file, 
                stderr=stderr_file
            )
            
            # Wait for completion
            return_code = process.wait()
            
            # Close log files
            stdout_file.close()
            stderr_file.close()
            
            # Check if the output file exists
            output_file = evaluation.get("output_file", "")
            if output_file:
                output_file_path = osp.join(implementation_dir, output_file)
                if osp.exists(output_file_path):
                    # Copy the output file to the evaluation directory
                    shutil.copy2(output_file_path, osp.join(eval_dir, osp.basename(output_file)))
                    
                    # Also load and include in results
                    try:
                        with open(output_file_path, "r") as f:
                            eval_results = json.load(f)
                            experiment_results["evaluation"] = eval_results
                    except:
                        experiment_results["evaluation"] = {
                            "success": (return_code == 0),
                            "return_code": return_code,
                            "output_file": output_file
                        }
            
            experiment_results["evaluation_summary"] = {
                "success": (return_code == 0),
                "return_code": return_code,
                "logs_dir": eval_dir
            }
            
            print(f"Evaluation completed with return code {return_code}")
            
        except Exception as e:
            # Handle any exceptions
            print(f"Error running evaluation: {str(e)}")
            
            experiment_results["evaluation_summary"] = {
                "success": False,
                "error": str(e),
                "logs_dir": eval_dir
            }
    
    # Save overall results
    with open(osp.join(results_dir, "experiment_results.json"), "w") as f:
        json.dump(experiment_results, f, indent=2)
    
    return experiment_results 