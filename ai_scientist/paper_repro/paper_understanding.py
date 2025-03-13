"""
Paper Understanding Module

This module is responsible for extracting key information from research papers, including:
- Methods and algorithms
- Experimental setups
- Datasets used
- Evaluation metrics
- Results reported in the paper
- Figures and tables
"""

import json
import os
import os.path as osp
import re
import subprocess
from typing import Dict, List, Any

def extract_pdf_text(pdf_path: str) -> str:
    """
    Extract text from a PDF file using pdftotext.
    
    Args:
        pdf_path: Path to the PDF file
        
    Returns:
        Extracted text from the PDF
    """
    try:
        # Check if pdftotext is installed
        subprocess.run(["which", "pdftotext"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError:
        raise RuntimeError("pdftotext not found. Please install it using: sudo apt-get install poppler-utils")
    
    # Extract text from PDF
    result = subprocess.run(
        ["pdftotext", "-layout", pdf_path, "-"],
        capture_output=True,
        text=True,
        check=True
    )
    
    return result.stdout

def extract_pdf_images(pdf_path: str, output_dir: str) -> List[str]:
    """
    Extract images from a PDF file using pdfimages.
    
    Args:
        pdf_path: Path to the PDF file
        output_dir: Directory to save extracted images
        
    Returns:
        List of paths to extracted images
    """
    os.makedirs(output_dir, exist_ok=True)
    
    try:
        # Check if pdfimages is installed
        subprocess.run(["which", "pdfimages"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError:
        raise RuntimeError("pdfimages not found. Please install it using: sudo apt-get install poppler-utils")
    
    # Extract images from PDF
    output_prefix = osp.join(output_dir, "image")
    subprocess.run(
        ["pdfimages", "-all", pdf_path, output_prefix],
        check=True
    )
    
    # Get list of extracted image files
    image_files = [osp.join(output_dir, f) for f in os.listdir(output_dir) 
                  if osp.isfile(osp.join(output_dir, f)) and f.startswith("image")]
    
    return sorted(image_files)

def process_paper_section(section_text: str, section_name: str, client, client_model: str) -> Dict[str, Any]:
    """
    Process a specific section of the paper using LLM.
    
    Args:
        section_text: Text content of the section
        section_name: Name of the section (e.g., "Introduction", "Methods", etc.)
        client: LLM client
        client_model: Name of the LLM model
        
    Returns:
        Extracted information from the section as a dictionary
    """
    prompt = f"""
    You are analyzing the {section_name} section of a research paper. 
    Extract the key information from this section.
    
    {section_text}
    
    Please extract and structure the following information from this section:
    1. Key concepts and terminology introduced
    2. Main methods, algorithms, or approaches described
    3. Mathematical formulations or equations (if any)
    4. Implementation details that would be needed for reproduction
    5. Any numerical parameters or hyperparameters mentioned
    
    Format your response as a JSON object with the above categories as keys.
    """
    
    response = client.get(prompt, model=client_model)
    
    # Extract the JSON from the response
    json_match = re.search(r'```json\n(.*?)\n```', response, re.DOTALL)
    if json_match:
        json_str = json_match.group(1)
    else:
        # Try to find any JSON-like structure in the response
        json_str = response
        
    try:
        return json.loads(json_str)
    except json.JSONDecodeError:
        # If JSON parsing fails, return a structured dictionary with the raw text
        return {
            "raw_text": response,
            "key_concepts": [],
            "main_methods": [],
            "mathematical_formulations": [],
            "implementation_details": [],
            "parameters": []
        }

def process_results_tables(paper_text: str, client, client_model: str) -> List[Dict[str, Any]]:
    """
    Process results tables from the paper text using LLM.
    
    Args:
        paper_text: Full text of the paper
        client: LLM client
        client_model: Name of the LLM model
        
    Returns:
        List of dictionaries containing structured table data
    """
    prompt = f"""
    You are analyzing a research paper to extract numerical results from tables.
    
    Here is the paper text, focusing on sections that might contain result tables:
    
    {paper_text}
    
    Please identify all results tables in the paper and extract the following for each:
    1. Table number and caption (if available)
    2. The metrics being measured
    3. The methods/models being compared
    4. The numerical results for each method and metric
    5. The best performing method for each metric
    
    Format your response as a JSON array of table objects, where each table has the structure:
    {{
        "table_id": "Table X",
        "caption": "Caption text",
        "metrics": ["metric1", "metric2", ...],
        "methods": ["method1", "method2", ...],
        "results": [
            {{"method": "method1", "metric": "metric1", "value": X.XX}},
            ...
        ],
        "best_performing": {{"metric": "metric1", "method": "methodX"}}
    }}
    """
    
    response = client.get(prompt, model=client_model)
    
    # Extract the JSON from the response
    json_match = re.search(r'```json\n(.*?)\n```', response, re.DOTALL)
    if json_match:
        json_str = json_match.group(1)
    else:
        # Try to find any JSON-like structure in the response
        json_str = response
        
    try:
        return json.loads(json_str)
    except json.JSONDecodeError:
        # If JSON parsing fails, return an empty list
        return []

def extract_paper_info(pdf_path: str, client, client_model: str) -> Dict[str, Any]:
    """
    Extract comprehensive information from a research paper PDF.
    
    Args:
        pdf_path: Path to the PDF file
        client: LLM client
        client_model: Name of the LLM model
        
    Returns:
        Dictionary containing extracted paper information
    """
    # Create output directory based on PDF name
    pdf_name = osp.splitext(osp.basename(pdf_path))[0]
    output_dir = osp.join(osp.dirname(osp.abspath(pdf_path)), f"{pdf_name}_extraction")
    os.makedirs(output_dir, exist_ok=True)
    
    # Extract text and images
    paper_text = extract_pdf_text(pdf_path)
    with open(osp.join(output_dir, "paper_text.txt"), "w") as f:
        f.write(paper_text)
    
    image_dir = osp.join(output_dir, "images")
    image_paths = extract_pdf_images(pdf_path, image_dir)
    
    # Get high-level paper information
    paper_info_prompt = f"""
    You are analyzing a research paper to extract key information.
    
    Here is the paper text:
    
    {paper_text[:20000]}  # Limit text to avoid token issues
    
    Please extract the following information:
    1. Title of the paper
    2. Authors
    3. Abstract
    4. Keywords (if available)
    5. Main research question or objective
    6. Key contributions
    7. Methods or approaches introduced
    
    Format your response as a JSON object with the above categories as keys.
    """
    
    paper_info_response = client.get(paper_info_prompt, model=client_model)
    
    # Extract the JSON from the response
    json_match = re.search(r'```json\n(.*?)\n```', paper_info_response, re.DOTALL)
    if json_match:
        paper_info_json = json_match.group(1)
    else:
        # Try to find any JSON-like structure in the response
        paper_info_json = paper_info_response
        
    try:
        paper_info = json.loads(paper_info_json)
    except json.JSONDecodeError:
        # If JSON parsing fails, create a basic structure
        paper_info = {
            "title": "",
            "authors": [],
            "abstract": "",
            "keywords": [],
            "research_question": "",
            "key_contributions": [],
            "methods": []
        }
    
    # Process sections
    section_markers = [
        "Abstract", "Introduction", "Related Work", "Background", 
        "Methods", "Methodology", "Method", "Approach", "Algorithm",
        "Experiments", "Experimental Setup", "Evaluation", "Results",
        "Discussion", "Conclusion", "Future Work", "References"
    ]
    
    sections = {}
    current_section = "Preamble"
    section_text = ""
    
    for line in paper_text.split("\n"):
        line = line.strip()
        if not line:
            continue
        
        # Check if line is a section header
        is_section_header = False
        for marker in section_markers:
            if re.match(f"^\\s*{re.escape(marker)}\\s*$", line, re.IGNORECASE) or \
               re.match(f"^\\s*\\d+\\.?\\s+{re.escape(marker)}\\s*$", line, re.IGNORECASE):
                if section_text:
                    sections[current_section] = section_text
                current_section = marker
                section_text = ""
                is_section_header = True
                break
        
        if not is_section_header:
            section_text += line + "\n"
    
    # Add the last section
    if section_text:
        sections[current_section] = section_text
    
    # Process key sections using LLM
    processed_sections = {}
    for section_name, section_text in sections.items():
        if section_name in ["Abstract", "Introduction", "Methods", "Methodology", "Method", 
                          "Experiments", "Results", "Conclusion"]:
            processed_sections[section_name] = process_paper_section(
                section_text, section_name, client, client_model
            )
    
    # Process results tables
    results_tables = process_results_tables(paper_text, client, client_model)
    
    # Create code generation guidance
    code_guidance_prompt = f"""
    You are analyzing a research paper to provide guidance for reproducing its results.
    
    Here is key information extracted from the paper:
    
    Title: {paper_info.get('title', '')}
    
    Abstract: {paper_info.get('abstract', '')}
    
    Methods: {json.dumps(paper_info.get('methods', []))}
    
    Key sections:
    {json.dumps(processed_sections, indent=2)}
    
    Results:
    {json.dumps(results_tables, indent=2)}
    
    Based on this information, provide guidance for reproducing the paper's results:
    1. The key algorithms or methods to implement
    2. Required datasets and preprocessing steps
    3. Evaluation metrics to use
    4. Expected results to compare against
    5. Potential challenges in reproduction
    6. Any specific implementations details that are crucial
    
    Format your response as a JSON object with the above categories as keys.
    """
    
    code_guidance_response = client.get(code_guidance_prompt, model=client_model)
    
    # Extract the JSON from the response
    json_match = re.search(r'```json\n(.*?)\n```', code_guidance_response, re.DOTALL)
    if json_match:
        code_guidance_json = json_match.group(1)
    else:
        # Try to find any JSON-like structure in the response
        code_guidance_json = code_guidance_response
        
    try:
        code_guidance = json.loads(code_guidance_json)
    except json.JSONDecodeError:
        # If JSON parsing fails, create a basic structure
        code_guidance = {
            "algorithms": [],
            "datasets": [],
            "metrics": [],
            "expected_results": [],
            "challenges": [],
            "implementation_details": []
        }
    
    # Compile full paper info
    full_paper_info = {
        "basic_info": paper_info,
        "sections": processed_sections,
        "results_tables": results_tables,
        "code_guidance": code_guidance,
        "image_paths": image_paths
    }
    
    # Save the extracted information
    with open(osp.join(output_dir, "paper_info.json"), "w") as f:
        json.dump(full_paper_info, f, indent=2)
    
    return full_paper_info 