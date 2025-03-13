"""
Code Generation Module

This module is responsible for implementing the methods and algorithms described in a paper,
including setting up the experimental infrastructure to reproduce the results.
"""

import json
import os
import os.path as osp
import shutil
from typing import Dict, List, Any, Optional

def generate_implementation(
    paper_info: Dict[str, Any], 
    output_dir: str, 
    coder, 
    client, 
    client_model: str,
    template: Optional[str] = None
) -> None:
    """
    Generate code implementation based on paper information.
    
    Args:
        paper_info: Extracted information from the paper
        output_dir: Directory to save the implementation
        coder: Aider coder object for code generation
        client: LLM client
        client_model: Name of the LLM model
        template: Optional template directory to use as a starting point
    """
    os.makedirs(output_dir, exist_ok=True)
    
    # If template is provided, copy it to the output directory
    if template and osp.exists(template):
        for item in os.listdir(template):
            s = osp.join(template, item)
            d = osp.join(output_dir, item)
            if osp.isdir(s):
                shutil.copytree(s, d, dirs_exist_ok=True)
            else:
                shutil.copy2(s, d)
    
    # Extract key information needed for implementation
    basic_info = paper_info["basic_info"]
    code_guidance = paper_info["code_guidance"]
    results_tables = paper_info["results_tables"]
    
    # Create a project structure
    generate_project_structure(output_dir, basic_info, code_guidance, client, client_model)
    
    # Generate implementation files
    generate_implementation_files(output_dir, paper_info, coder, client, client_model)
    
    # Generate experiment runner
    generate_experiment_runner(output_dir, paper_info, coder, client, client_model)
    
    # Generate evaluation code
    generate_evaluation_code(output_dir, paper_info, coder, client, client_model)
    
    # Generate README
    generate_readme(output_dir, paper_info, client, client_model)


def generate_project_structure(
    output_dir: str, 
    basic_info: Dict[str, Any], 
    code_guidance: Dict[str, Any],
    client,
    client_model: str
) -> None:
    """
    Generate project structure based on paper information.
    
    Args:
        output_dir: Directory to save the implementation
        basic_info: Basic information about the paper
        code_guidance: Guidance for code implementation
        client: LLM client
        client_model: Name of the LLM model
    """
    # Generate project structure based on paper domain and methods
    prompt = f"""
    You are designing a project structure for implementing a research paper.
    
    Paper title: {basic_info.get('title', '')}
    Paper methods: {json.dumps(basic_info.get('methods', []))}
    
    Implementation guidance:
    {json.dumps(code_guidance, indent=2)}
    
    Please suggest a clean, modular project structure for reproducing this paper.
    Include directories for:
    1. Core implementation (models, algorithms)
    2. Data processing and datasets
    3. Training scripts
    4. Evaluation scripts
    5. Utility functions
    6. Configuration files
    7. Any other necessary components
    
    Format your response as a JSON object with the following structure:
    {{
        "directories": [
            {{
                "path": "relative/path",
                "purpose": "Description of what goes in this directory"
            }}
        ],
        "files": [
            {{
                "path": "relative/path/to/file.py",
                "purpose": "Description of the file's functionality",
                "key_components": ["List", "of", "key", "components", "or", "classes"]
            }}
        ]
    }}
    """
    
    response = client.get(prompt, model=client_model)
    
    # Extract the JSON from the response
    import re
    json_match = re.search(r'```json\n(.*?)\n```', response, re.DOTALL)
    if json_match:
        json_str = json_match.group(1)
    else:
        # Try to find any JSON-like structure in the response
        json_str = response
    
    try:
        structure = json.loads(json_str)
    except json.JSONDecodeError:
        # Default structure if parsing fails
        structure = {
            "directories": [
                {"path": "data", "purpose": "Dataset storage and processing"},
                {"path": "models", "purpose": "Implementation of models from the paper"},
                {"path": "experiments", "purpose": "Training and testing scripts"},
                {"path": "utils", "purpose": "Utility functions"},
                {"path": "configs", "purpose": "Configuration files"}
            ],
            "files": [
                {"path": "requirements.txt", "purpose": "Required packages", "key_components": []},
                {"path": "main.py", "purpose": "Main entry point", "key_components": ["ArgumentParser"]},
                {"path": "train.py", "purpose": "Training script", "key_components": ["train_model"]},
                {"path": "evaluate.py", "purpose": "Evaluation script", "key_components": ["evaluate_model"]}
            ]
        }
    
    # Create the directories
    for directory in structure["directories"]:
        dir_path = osp.join(output_dir, directory["path"])
        os.makedirs(dir_path, exist_ok=True)
        
        # Create an empty __init__.py file in each directory
        with open(osp.join(dir_path, "__init__.py"), "w") as f:
            f.write(f'"""\n{directory["purpose"]}\n"""\n')
    
    # Create empty files (will be filled later)
    for file in structure["files"]:
        file_path = osp.join(output_dir, file["path"])
        os.makedirs(osp.dirname(file_path), exist_ok=True)
        
        # Create an empty file with just a docstring
        with open(file_path, "w") as f:
            f.write(f'"""\n{file["purpose"]}\n"""\n')
    
    # Save the structure for reference
    with open(osp.join(output_dir, "project_structure.json"), "w") as f:
        json.dump(structure, f, indent=2)
    
    return structure


def generate_implementation_files(
    output_dir: str, 
    paper_info: Dict[str, Any], 
    coder, 
    client,
    client_model: str
) -> None:
    """
    Generate implementation files based on paper information.
    
    Args:
        output_dir: Directory to save the implementation
        paper_info: Extracted information from the paper
        coder: Aider coder object for code generation
        client: LLM client
        client_model: Name of the LLM model
    """
    # Load project structure
    with open(osp.join(output_dir, "project_structure.json"), "r") as f:
        structure = json.load(f)
    
    # Get key algorithms and methods to implement
    code_guidance = paper_info["code_guidance"]
    algorithms = code_guidance.get("algorithms", [])
    implementation_details = code_guidance.get("implementation_details", [])
    
    # Prepare model implementations
    model_files = [file for file in structure["files"] 
                  if "model" in file["path"].lower() or 
                     any("model" in component.lower() for component in file.get("key_components", []))]
    
    if model_files:
        for model_file in model_files:
            file_path = osp.join(output_dir, model_file["path"])
            
            # Create model implementation prompt
            prompt = f"""
            You are implementing a research paper.
            
            Paper title: {paper_info["basic_info"].get("title", "")}
            
            Key algorithms to implement:
            {json.dumps(algorithms, indent=2)}
            
            Implementation details:
            {json.dumps(implementation_details, indent=2)}
            
            You need to implement the model in the file: {model_file["path"]}
            Purpose of this file: {model_file["purpose"]}
            
            Implement the necessary classes and functions for this file.
            Use standard Python libraries like NumPy, PyTorch, TensorFlow, etc. as appropriate.
            Include proper documentation and type hints.
            Ensure the implementation is complete and can be imported and used by other files.
            """
            
            # Use coder to implement the file
            coder.fnames = [file_path]
            coder.run_command(prompt)
    
    # Prepare data processing implementations
    data_files = [file for file in structure["files"] 
                 if "data" in file["path"].lower() or 
                    any("data" in component.lower() for component in file.get("key_components", []))]
    
    if data_files:
        for data_file in data_files:
            file_path = osp.join(output_dir, data_file["path"])
            
            # Create data processing implementation prompt
            prompt = f"""
            You are implementing a research paper.
            
            Paper title: {paper_info["basic_info"].get("title", "")}
            
            Datasets needed:
            {json.dumps(code_guidance.get("datasets", []), indent=2)}
            
            Implementation details:
            {json.dumps(implementation_details, indent=2)}
            
            You need to implement the data processing in the file: {data_file["path"]}
            Purpose of this file: {data_file["purpose"]}
            
            Implement the necessary classes and functions for this file.
            Include data loading, preprocessing, augmentation, and dataset classes as needed.
            Use standard libraries like pandas, NumPy, PyTorch, TensorFlow, etc. as appropriate.
            Include proper documentation and type hints.
            """
            
            # Use coder to implement the file
            coder.fnames = [file_path]
            coder.run_command(prompt)
    
    # Generate utility functions
    util_files = [file for file in structure["files"] 
                 if "util" in file["path"].lower() or 
                    any("util" in component.lower() for component in file.get("key_components", []))]
    
    if util_files:
        for util_file in util_files:
            file_path = osp.join(output_dir, util_file["path"])
            
            # Create utility implementation prompt
            prompt = f"""
            You are implementing a research paper.
            
            Paper title: {paper_info["basic_info"].get("title", "")}
            
            Implementation details:
            {json.dumps(implementation_details, indent=2)}
            
            You need to implement utility functions in the file: {util_file["path"]}
            Purpose of this file: {util_file["purpose"]}
            
            Implement helper functions that might be needed for the implementation, such as:
            - Metric calculation functions
            - Data visualization functions
            - File I/O functions
            - Utility functions for experiment logging
            - Any other utilities mentioned in the paper
            
            Include proper documentation and type hints.
            """
            
            # Use coder to implement the file
            coder.fnames = [file_path]
            coder.run_command(prompt)
    
    # Generate requirements.txt
    requirements_path = osp.join(output_dir, "requirements.txt")
    if osp.exists(requirements_path):
        prompt = f"""
        You are implementing a research paper.
        
        Paper title: {paper_info["basic_info"].get("title", "")}
        
        Based on the implementation details, generate a comprehensive requirements.txt file 
        with all necessary libraries and their versions.
        
        Consider what libraries would be needed for:
        - The core algorithms and models
        - Data processing and augmentation
        - Evaluation metrics
        - Visualization
        - Any other tasks mentioned in the paper
        
        Format the requirements in the standard pip requirements.txt format with versions pinned.
        """
        
        # Use coder to implement the file
        coder.fnames = [requirements_path]
        coder.run_command(prompt)


def generate_experiment_runner(
    output_dir: str, 
    paper_info: Dict[str, Any], 
    coder, 
    client,
    client_model: str
) -> None:
    """
    Generate an experiment runner script.
    
    Args:
        output_dir: Directory to save the implementation
        paper_info: Extracted information from the paper
        coder: Aider coder object for code generation
        client: LLM client
        client_model: Name of the LLM model
    """
    # Find main and training files from project structure
    with open(osp.join(output_dir, "project_structure.json"), "r") as f:
        structure = json.load(f)
    
    main_files = [file for file in structure["files"] 
                 if "main" in file["path"].lower() or 
                    "train" in file["path"].lower()]
    
    if main_files:
        for main_file in main_files:
            file_path = osp.join(output_dir, main_file["path"])
            
            # Create experiment runner prompt
            code_guidance = paper_info["code_guidance"]
            implementation_details = code_guidance.get("implementation_details", [])
            prompt = f"""
            You are implementing a research paper.
            
            Paper title: {paper_info["basic_info"].get("title", "")}
            
            Training details:
            {json.dumps(implementation_details, indent=2)}
            
            Experimental setup:
            {json.dumps(code_guidance.get("datasets", []), indent=2)}
            
            Expected results:
            {json.dumps(code_guidance.get("expected_results", []), indent=2)}
            
            You need to implement the experiment runner in the file: {main_file["path"]}
            Purpose of this file: {main_file["purpose"]}
            
            Create a script that:
            1. Parses command-line arguments for all relevant hyperparameters
            2. Sets up the model, dataset, and optimizer
            3. Implements the training loop with appropriate logging
            4. Saves model checkpoints and results
            5. Optionally implements evaluation during training
            
            Ensure the script is robust, well-documented, and includes appropriate error handling.
            """
            
            # Use coder to implement the file
            coder.fnames = [file_path]
            coder.run_command(prompt)


def generate_evaluation_code(
    output_dir: str, 
    paper_info: Dict[str, Any], 
    coder, 
    client,
    client_model: str
) -> None:
    """
    Generate evaluation code based on paper metrics.
    
    Args:
        output_dir: Directory to save the implementation
        paper_info: Extracted information from the paper
        coder: Aider coder object for code generation
        client: LLM client
        client_model: Name of the LLM model
    """
    # Find evaluation files from project structure
    with open(osp.join(output_dir, "project_structure.json"), "r") as f:
        structure = json.load(f)
    
    eval_files = [file for file in structure["files"] 
                 if "eval" in file["path"].lower() or 
                    "test" in file["path"].lower()]
    
    if eval_files:
        for eval_file in eval_files:
            file_path = osp.join(output_dir, eval_file["path"])
            
            # Create evaluation code prompt
            code_guidance = paper_info["code_guidance"]
            results_tables = paper_info["results_tables"]
            
            prompt = f"""
            You are implementing a research paper.
            
            Paper title: {paper_info["basic_info"].get("title", "")}
            
            Evaluation metrics:
            {json.dumps(code_guidance.get("metrics", []), indent=2)}
            
            Expected results:
            {json.dumps(code_guidance.get("expected_results", []), indent=2)}
            
            Results tables from the paper:
            {json.dumps(results_tables, indent=2)}
            
            You need to implement the evaluation code in the file: {eval_file["path"]}
            Purpose of this file: {eval_file["purpose"]}
            
            Create a script that:
            1. Loads a trained model and test dataset
            2. Implements all evaluation metrics mentioned in the paper
            3. Computes the metrics on the test data
            4. Outputs results in a format that can be compared to the paper's results
            5. Optionally creates visualizations of the results
            
            Ensure the implementation matches the evaluation protocol described in the paper.
            """
            
            # Use coder to implement the file
            coder.fnames = [file_path]
            coder.run_command(prompt)


def generate_readme(
    output_dir: str, 
    paper_info: Dict[str, Any], 
    client,
    client_model: str
) -> None:
    """
    Generate a comprehensive README file.
    
    Args:
        output_dir: Directory to save the implementation
        paper_info: Extracted information from the paper
        client: LLM client
        client_model: Name of the LLM model
    """
    readme_path = osp.join(output_dir, "README.md")
    
    basic_info = paper_info["basic_info"]
    code_guidance = paper_info["code_guidance"]
    
    prompt = f"""
    You are creating a README.md file for a code implementation that reproduces a research paper.
    
    Paper title: {basic_info.get("title", "")}
    Authors: {json.dumps(basic_info.get("authors", []))}
    
    Abstract: {basic_info.get("abstract", "")}
    
    Key contributions: {json.dumps(basic_info.get("key_contributions", []))}
    
    Implementation details:
    {json.dumps(code_guidance, indent=2)}
    
    Create a comprehensive README.md that includes:
    1. Title and paper reference
    2. Brief description of the paper and its contributions
    3. Installation instructions (including requirements)
    4. Usage instructions with example commands
    5. Description of the repository structure
    6. Description of the results being reproduced
    7. Troubleshooting tips
    
    Use proper Markdown formatting with headers, code blocks, lists, etc.
    """
    
    response = client.get(prompt, model=client_model)
    
    with open(readme_path, "w") as f:
        f.write(response) 