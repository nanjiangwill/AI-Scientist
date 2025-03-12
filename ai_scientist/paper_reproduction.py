"""
Paper Reproduction Module for AI-Scientist.

This module extends the AI-Scientist framework to reproduce results from academic papers
that don't provide code. It extracts information from papers, generates implementation code,
runs experiments, and compares results with those reported in the paper.
"""

import os
import os.path as osp
import json
import re
import tempfile
from typing import Dict, List, Optional, Tuple, Any

import pymupdf4llm
from pymupdf4llm import MuPDFExtractor

from ai_scientist.llm import get_response_from_llm


# Paper parsing functions
def extract_paper_content(pdf_path: str) -> str:
    """
    Extract text content from a PDF paper.
    
    Args:
        pdf_path: Path to the PDF file
        
    Returns:
        str: Extracted text content
    """
    extractor = MuPDFExtractor()
    return extractor.extract(pdf_path)


def parse_paper_sections(paper_content: str) -> Dict[str, str]:
    """
    Parse the paper content into sections.
    
    Args:
        paper_content: The extracted text content from the paper
        
    Returns:
        Dict[str, str]: Dictionary mapping section names to their content
    """
    # This is a simplified implementation - in practice, we would need more sophisticated parsing
    sections = {}
    current_section = "Abstract"
    sections[current_section] = ""
    
    for line in paper_content.split('\n'):
        # Check if line is a section header (simplified)
        if re.match(r'^[0-9]+\.\s+[A-Z]', line) or line.isupper():
            current_section = line.strip()
            sections[current_section] = ""
        else:
            sections[current_section] += line + "\n"
    
    return sections


def extract_algorithms(paper_content: str) -> List[str]:
    """
    Extract algorithm descriptions from the paper.
    
    Args:
        paper_content: The extracted text content from the paper
        
    Returns:
        List[str]: List of algorithm descriptions
    """
    # This is a simplified implementation - in practice, we would need more sophisticated parsing
    algorithms = []
    algorithm_pattern = re.compile(r'Algorithm\s+\d+[:\s]+(.*?)(?=Algorithm\s+\d+|$)', re.DOTALL)
    
    matches = algorithm_pattern.findall(paper_content)
    for match in matches:
        algorithms.append(match.strip())
    
    return algorithms


def extract_results(paper_content: str) -> Dict[str, Any]:
    """
    Extract reported results from the paper.
    
    Args:
        paper_content: The extracted text content from the paper
        
    Returns:
        Dict[str, Any]: Dictionary of results
    """
    # This is a placeholder - in practice, we would need more sophisticated parsing
    # Ideally, we would extract tables and figures
    return {"results": "Placeholder for extracted results"}


# Code generation functions
def generate_implementation_code(
    paper_sections: Dict[str, str],
    algorithms: List[str],
    client: Any,
    model: str
) -> Dict[str, str]:
    """
    Generate implementation code based on the paper content.
    
    Args:
        paper_sections: Dictionary of paper sections
        algorithms: List of algorithm descriptions
        client: LLM client
        model: LLM model name
        
    Returns:
        Dict[str, str]: Dictionary mapping file names to generated code
    """
    implementation_files = {}
    
    # Generate main implementation
    method_description = ""
    for section_name, section_content in paper_sections.items():
        if any(keyword in section_name.lower() for keyword in ["method", "approach", "model"]):
            method_description += section_content + "\n"
    
    # Prompt for the main implementation
    prompt = f"""
You are tasked with implementing the method described in an academic paper. 
Below is the method section from the paper:

{method_description}

Please generate Python code that implements this method. 
The code should be well-structured, modular, and follow best practices.
Include detailed comments explaining how each part corresponds to the paper description.
"""
    
    response, _ = get_response_from_llm(prompt, client, model)
    
    # Extract code blocks from the response
    code_blocks = re.findall(r'```python(.*?)```', response, re.DOTALL)
    
    if code_blocks:
        implementation_files["implementation.py"] = code_blocks[0].strip()
    else:
        implementation_files["implementation.py"] = "# Failed to extract code from LLM response"
    
    # Generate experiment code
    experiment_description = ""
    for section_name, section_content in paper_sections.items():
        if any(keyword in section_name.lower() for keyword in ["experiment", "evaluation", "result"]):
            experiment_description += section_content + "\n"
    
    prompt = f"""
You are tasked with implementing the experimental setup described in an academic paper.
Below is the experiment section from the paper:

{experiment_description}

Please generate Python code that reproduces the experiments described in the paper.
The code should:
1. Load or generate the necessary datasets
2. Run the method on these datasets
3. Evaluate the results using the metrics described in the paper
4. Compare the results with those reported in the paper

Assume that the main implementation is available in a module called 'implementation'.
"""
    
    response, _ = get_response_from_llm(prompt, client, model)
    
    # Extract code blocks from the response
    code_blocks = re.findall(r'```python(.*?)```', response, re.DOTALL)
    
    if code_blocks:
        implementation_files["experiment.py"] = code_blocks[0].strip()
    else:
        implementation_files["experiment.py"] = "# Failed to extract code from LLM response"
    
    return implementation_files


# Experiment running functions
def setup_experiment_directory(
    paper_title: str,
    implementation_files: Dict[str, str]
) -> str:
    """
    Set up a directory for the experiment.
    
    Args:
        paper_title: Title of the paper
        implementation_files: Dictionary mapping file names to generated code
        
    Returns:
        str: Path to the experiment directory
    """
    # Create a directory name based on the paper title
    dir_name = re.sub(r'[^\w\s-]', '', paper_title).strip().lower()
    dir_name = re.sub(r'[-\s]+', '-', dir_name)
    
    # Create the directory
    experiment_dir = osp.join("results", "paper_reproduction", dir_name)
    os.makedirs(experiment_dir, exist_ok=True)
    
    # Write the implementation files
    for file_name, file_content in implementation_files.items():
        with open(osp.join(experiment_dir, file_name), "w") as f:
            f.write(file_content)
    
    return experiment_dir


def run_experiment(
    experiment_dir: str,
    coder: Any
) -> Dict[str, Any]:
    """
    Run the experiment using the generated code.
    
    Args:
        experiment_dir: Path to the experiment directory
        coder: OpenHands coder instance
        
    Returns:
        Dict[str, Any]: Dictionary of results
    """
    # First, let the coder review and improve the implementation
    prompt = f"""
Please review the implementation code in {experiment_dir}/implementation.py and the experiment code in {experiment_dir}/experiment.py.
Identify any issues or improvements that could be made to ensure the code correctly implements the method and experiments described in the paper.
Make any necessary changes to fix issues or improve the implementation.
"""
    
    coder.run(prompt)
    
    # Now, run the experiment
    prompt = f"""
Please run the experiment code in {experiment_dir}/experiment.py and report the results.
Compare the results with those reported in the paper and analyze any differences.
"""
    
    response = coder.run(prompt)
    
    # Parse the results from the response
    # This is a simplified implementation - in practice, we would need more sophisticated parsing
    return {"results": response}


# Main function for paper reproduction
def reproduce_paper(
    pdf_path: str,
    client: Any,
    model: str,
    coder: Any
) -> Dict[str, Any]:
    """
    Reproduce the results from a paper.
    
    Args:
        pdf_path: Path to the PDF file
        client: LLM client
        model: LLM model name
        coder: OpenHands coder instance
        
    Returns:
        Dict[str, Any]: Dictionary of reproduction results
    """
    # Extract paper content
    paper_content = extract_paper_content(pdf_path)
    
    # Parse paper sections
    paper_sections = parse_paper_sections(paper_content)
    
    # Extract algorithms
    algorithms = extract_algorithms(paper_content)
    
    # Extract reported results
    reported_results = extract_results(paper_content)
    
    # Generate implementation code
    implementation_files = generate_implementation_code(
        paper_sections,
        algorithms,
        client,
        model
    )
    
    # Extract paper title
    paper_title = "Untitled Paper"
    for line in paper_content.split('\n')[:20]:  # Look in the first 20 lines
        if len(line.strip()) > 10 and not line.startswith("Abstract"):
            paper_title = line.strip()
            break
    
    # Setup experiment directory
    experiment_dir = setup_experiment_directory(paper_title, implementation_files)
    
    # Run experiment
    reproduction_results = run_experiment(experiment_dir, coder)
    
    # Compare results
    comparison = compare_results(reported_results, reproduction_results)
    
    return {
        "paper_title": paper_title,
        "reported_results": reported_results,
        "reproduction_results": reproduction_results,
        "comparison": comparison,
        "experiment_dir": experiment_dir
    }


def compare_results(
    reported_results: Dict[str, Any],
    reproduction_results: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Compare the reported results with the reproduced results.
    
    Args:
        reported_results: Results reported in the paper
        reproduction_results: Results from the reproduction
        
    Returns:
        Dict[str, Any]: Comparison of results
    """
    # This is a placeholder - in practice, we would need more sophisticated comparison
    return {
        "match": "Unknown",
        "differences": "Placeholder for result differences"
    }


if __name__ == "__main__":
    import argparse
    from ai_scientist.llm import create_client
    from ai_scientist.openhands_wrapper import create_openhands_coder
    
    parser = argparse.ArgumentParser(description="Reproduce results from a paper")
    parser.add_argument("--pdf", type=str, required=True, help="Path to the PDF file")
    parser.add_argument("--model", type=str, default="gpt-4o", help="LLM model to use")
    args = parser.parse_args()
    
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
    
    main_model = Model(args.model)
    io = InputOutput(yes=True, chat_history_file="paper_reproduction_chat.txt")
    
    coder = create_openhands_coder(
        main_model=main_model,
        fnames=[],
        io=io,
        stream=False,
        use_git=False,
        edit_format="diff",
    )
    
    # Reproduce paper
    results = reproduce_paper(args.pdf, client, client_model, coder)
    
    # Print results
    print(f"Paper: {results['paper_title']}")
    print(f"Experiment directory: {results['experiment_dir']}")
    print(f"Comparison: {results['comparison']}")