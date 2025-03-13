"""
Report Generation Module

This module is responsible for generating a comprehensive report of the paper reproduction,
including the implementation, experiments, results, and analysis.
"""

import json
import os
import os.path as osp
import subprocess
import shutil
from typing import Dict, List, Any

def generate_report(
    paper_info: Dict[str, Any],
    experiment_results: Dict[str, Any],
    analysis: Dict[str, Any],
    report_dir: str,
    report_format: str,
    client,
    client_model: str
) -> str:
    """
    Generate a comprehensive report of the paper reproduction.
    
    Args:
        paper_info: Extracted information from the paper
        experiment_results: Results from the experiments
        analysis: Analysis of the results
        report_dir: Directory to save the report
        report_format: Format of the report ('latex' or 'markdown')
        client: LLM client
        client_model: Name of the LLM model
        
    Returns:
        Path to the generated report
    """
    os.makedirs(report_dir, exist_ok=True)
    
    # Choose report generation method based on format
    if report_format == 'latex':
        return generate_latex_report(
            paper_info, experiment_results, analysis, report_dir, client, client_model
        )
    else:  # markdown
        return generate_markdown_report(
            paper_info, experiment_results, analysis, report_dir, client, client_model
        )


def generate_markdown_report(
    paper_info: Dict[str, Any],
    experiment_results: Dict[str, Any],
    analysis: Dict[str, Any],
    report_dir: str,
    client,
    client_model: str
) -> str:
    """
    Generate a Markdown report of the paper reproduction.
    
    Args:
        paper_info: Extracted information from the paper
        experiment_results: Results from the experiments
        analysis: Analysis of the results
        report_dir: Directory to save the report
        client: LLM client
        client_model: Name of the LLM model
        
    Returns:
        Path to the generated report
    """
    # Create report sections using LLM
    sections = {}
    
    # Introduction section
    sections["introduction"] = generate_report_section(
        "introduction", paper_info, experiment_results, analysis, client, client_model
    )
    
    # Method section
    sections["method"] = generate_report_section(
        "method", paper_info, experiment_results, analysis, client, client_model
    )
    
    # Implementation section
    sections["implementation"] = generate_report_section(
        "implementation", paper_info, experiment_results, analysis, client, client_model
    )
    
    # Results section
    sections["results"] = generate_report_section(
        "results", paper_info, experiment_results, analysis, client, client_model
    )
    
    # Analysis section
    sections["analysis"] = generate_report_section(
        "analysis", paper_info, experiment_results, analysis, client, client_model
    )
    
    # Discussion section
    sections["discussion"] = generate_report_section(
        "discussion", paper_info, experiment_results, analysis, client, client_model
    )
    
    # Conclusion section
    sections["conclusion"] = generate_report_section(
        "conclusion", paper_info, experiment_results, analysis, client, client_model
    )
    
    # Combine sections
    report_content = f"""# Paper Reproduction Report: {paper_info['basic_info'].get('title', '')}

## Abstract

{paper_info['basic_info'].get('abstract', '')}

## 1. Introduction

{sections['introduction']}

## 2. Paper Methods

{sections['method']}

## 3. Implementation Details

{sections['implementation']}

## 4. Experimental Results

{sections['results']}

## 5. Analysis

{sections['analysis']}

## 6. Discussion

{sections['discussion']}

## 7. Conclusion

{sections['conclusion']}

## References

1. {paper_info['basic_info'].get('title', '')} by {', '.join(paper_info['basic_info'].get('authors', []))}

"""
    
    # Save the report
    report_path = osp.join(report_dir, "reproduction_report.md")
    with open(report_path, "w") as f:
        f.write(report_content)
    
    return report_path


def generate_latex_report(
    paper_info: Dict[str, Any],
    experiment_results: Dict[str, Any],
    analysis: Dict[str, Any],
    report_dir: str,
    client,
    client_model: str
) -> str:
    """
    Generate a LaTeX report of the paper reproduction.
    
    Args:
        paper_info: Extracted information from the paper
        experiment_results: Results from the experiments
        analysis: Analysis of the results
        report_dir: Directory to save the report
        client: LLM client
        client_model: Name of the LLM model
        
    Returns:
        Path to the generated PDF report
    """
    # Create LaTeX source directory
    latex_dir = osp.join(report_dir, "latex")
    os.makedirs(latex_dir, exist_ok=True)
    
    # Create figures directory
    figures_dir = osp.join(latex_dir, "figures")
    os.makedirs(figures_dir, exist_ok=True)
    
    # Copy any analysis plots to the figures directory
    if "plot_paths" in analysis:
        for plot_path in analysis["plot_paths"]:
            if osp.exists(plot_path):
                shutil.copy2(plot_path, figures_dir)
    
    # Create report sections using LLM
    sections = {}
    
    # Introduction section
    sections["introduction"] = generate_report_section(
        "introduction", paper_info, experiment_results, analysis, client, client_model
    )
    
    # Method section
    sections["method"] = generate_report_section(
        "method", paper_info, experiment_results, analysis, client, client_model
    )
    
    # Implementation section
    sections["implementation"] = generate_report_section(
        "implementation", paper_info, experiment_results, analysis, client, client_model
    )
    
    # Results section
    sections["results"] = generate_report_section(
        "results", paper_info, experiment_results, analysis, client, client_model
    )
    
    # Analysis section
    sections["analysis"] = generate_report_section(
        "analysis", paper_info, experiment_results, analysis, client, client_model
    )
    
    # Discussion section
    sections["discussion"] = generate_report_section(
        "discussion", paper_info, experiment_results, analysis, client, client_model
    )
    
    # Conclusion section
    sections["conclusion"] = generate_report_section(
        "conclusion", paper_info, experiment_results, analysis, client, client_model
    )
    
    # Get the title and authors
    title = paper_info['basic_info'].get('title', 'Paper Reproduction Report')
    authors = paper_info['basic_info'].get('authors', [])
    if not authors:
        authors = ["AI Scientist"]
    
    # Generate LaTeX content
    latex_content = generate_latex_content(
        title, authors, sections, paper_info, analysis
    )
    
    # Save the LaTeX file
    latex_path = osp.join(latex_dir, "reproduction_report.tex")
    with open(latex_path, "w") as f:
        f.write(latex_content)
    
    # Compile the LaTeX file to PDF
    try:
        # First run (create aux files)
        subprocess.run(
            ["pdflatex", "-interaction=nonstopmode", "reproduction_report.tex"],
            cwd=latex_dir,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Second run (resolve references)
        subprocess.run(
            ["pdflatex", "-interaction=nonstopmode", "reproduction_report.tex"],
            cwd=latex_dir,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Copy the PDF to the report directory
        pdf_path = osp.join(latex_dir, "reproduction_report.pdf")
        if osp.exists(pdf_path):
            shutil.copy2(pdf_path, report_dir)
            
        return osp.join(report_dir, "reproduction_report.pdf")
    
    except subprocess.CalledProcessError:
        print("Error compiling LaTeX to PDF. See logs in the latex directory.")
        return latex_path


def generate_report_section(
    section_name: str,
    paper_info: Dict[str, Any],
    experiment_results: Dict[str, Any],
    analysis: Dict[str, Any],
    client,
    client_model: str
) -> str:
    """
    Generate a section of the report using LLM.
    
    Args:
        section_name: Name of the section to generate
        paper_info: Extracted information from the paper
        experiment_results: Results from the experiments
        analysis: Analysis of the results
        client: LLM client
        client_model: Name of the LLM model
        
    Returns:
        Content of the generated section
    """
    # Prepare section-specific prompts
    prompts = {
        "introduction": f"""
        You are writing the introduction section of a paper reproduction report.
        
        Paper title: {paper_info['basic_info'].get('title', '')}
        Authors: {', '.join(paper_info['basic_info'].get('authors', []))}
        
        Write a comprehensive introduction that:
        1. Introduces the original paper and its significance
        2. Explains the motivation for reproducing the paper
        3. Outlines the challenges in reproducing the paper
        4. Briefly summarizes the reproduction approach
        5. Outlines the structure of the report
        
        The section should be 2-3 paragraphs. Make it informative, formal, and well-structured.
        """,
        
        "method": f"""
        You are writing the method section of a paper reproduction report.
        
        Paper title: {paper_info['basic_info'].get('title', '')}
        
        Paper methods:
        {json.dumps(paper_info["code_guidance"].get("algorithms", []), indent=2)}
        
        Write a comprehensive method section that:
        1. Summarizes the key methods and algorithms from the original paper
        2. Explains the theoretical foundations of these methods
        3. Describes any mathematical formulations or equations
        4. Clarifies any ambiguities or underspecified aspects in the original paper
        
        The section should be 3-4 paragraphs. Make it technical, precise, and well-structured.
        """,
        
        "implementation": f"""
        You are writing the implementation section of a paper reproduction report.
        
        Paper title: {paper_info['basic_info'].get('title', '')}
        
        Implementation details:
        {json.dumps(paper_info["code_guidance"].get("implementation_details", []), indent=2)}
        
        Write a comprehensive implementation section that:
        1. Describes the software stack and frameworks used
        2. Explains key implementation choices and decisions
        3. Discusses any deviations from the original paper's description
        4. Highlights any challenges encountered during implementation
        5. Describes the datasets used and how they were processed
        
        The section should be 3-4 paragraphs. Make it technical, detailed, and well-structured.
        """,
        
        "results": f"""
        You are writing the results section of a paper reproduction report.
        
        Paper title: {paper_info['basic_info'].get('title', '')}
        
        Paper results tables:
        {json.dumps(paper_info["results_tables"], indent=2)}
        
        Our experiment results:
        {json.dumps(experiment_results, indent=2)}
        
        Write a comprehensive results section that:
        1. Presents the main experimental results in a clear, organized manner
        2. Compares our reproduction results with the original paper's results
        3. Highlights any discrepancies or inconsistencies
        4. Presents both quantitative metrics and qualitative observations
        
        The section should be 3-4 paragraphs with references to tables and figures where appropriate.
        Make it objective, data-driven, and well-structured.
        """,
        
        "analysis": f"""
        You are writing the analysis section of a paper reproduction report.
        
        Paper title: {paper_info['basic_info'].get('title', '')}
        
        Results analysis:
        {json.dumps(analysis.get("analysis", {}), indent=2)}
        
        Write a comprehensive analysis section that:
        1. Performs a detailed analysis of the reproduction results
        2. Investigates reasons for any discrepancies between reproduction and original results
        3. Discusses the statistical significance and reliability of the results
        4. Analyzes the sensitivity of the results to hyperparameters or implementation details
        
        The section should be 3-4 paragraphs. Make it analytical, insightful, and well-structured.
        """,
        
        "discussion": f"""
        You are writing the discussion section of a paper reproduction report.
        
        Paper title: {paper_info['basic_info'].get('title', '')}
        
        Analysis results:
        {json.dumps(analysis.get("analysis", {}), indent=2)}
        
        Write a comprehensive discussion section that:
        1. Discusses the broader implications of the reproduction results
        2. Reflects on the reproducibility of the original paper
        3. Identifies limitations of both the original work and our reproduction
        4. Suggests improvements or extensions to the original method
        5. Discusses the practical applicability of the method
        
        The section should be 3-4 paragraphs. Make it reflective, thoughtful, and well-structured.
        """,
        
        "conclusion": f"""
        You are writing the conclusion section of a paper reproduction report.
        
        Paper title: {paper_info['basic_info'].get('title', '')}
        
        Overall success:
        {analysis.get("analysis", {}).get("overall_success", "Unable to determine overall success")}
        
        Write a concise conclusion that:
        1. Summarizes the main findings of the reproduction effort
        2. States whether the reproduction was successful and to what extent
        3. Highlights key insights gained from the reproduction process
        4. Suggests future work for improving reproducibility in this area
        
        The section should be 1-2 paragraphs. Make it conclusive, clear, and well-structured.
        """
    }
    
    # Get prompt for the requested section
    prompt = prompts.get(section_name, f"Write a section about {section_name} for a paper reproduction report.")
    
    # Generate the section content
    response = client.get(prompt, model=client_model)
    
    return response


def generate_latex_content(
    title: str,
    authors: List[str],
    sections: Dict[str, str],
    paper_info: Dict[str, Any],
    analysis: Dict[str, Any]
) -> str:
    """
    Generate the LaTeX content for the report.
    
    Args:
        title: Title of the report
        authors: List of authors
        sections: Dictionary mapping section names to content
        paper_info: Extracted information from the paper
        analysis: Analysis of the results
        
    Returns:
        LaTeX content as a string
    """
    # Convert section content to LaTeX-friendly format
    latex_sections = {}
    for section_name, content in sections.items():
        # Replace certain characters with LaTeX escapes
        latex_content = content.replace('_', '\\_')
        latex_content = latex_content.replace('%', '\\%')
        latex_content = latex_content.replace('&', '\\&')
        latex_content = latex_content.replace('#', '\\#')
        
        latex_sections[section_name] = latex_content
    
    # Generate author string
    author_string = " \\and ".join(authors)
    
    # LaTeX preamble
    latex_content = r"""
\documentclass[11pt,a4paper]{article}

% Packages
\usepackage[utf8]{inputenc}
\usepackage{graphicx}
\usepackage{amsmath}
\usepackage{amssymb}
\usepackage{hyperref}
\usepackage{booktabs}
\usepackage{xcolor}
\usepackage{listings}
\usepackage{float}
\usepackage{caption}
\usepackage{subcaption}

% Set page margins
\usepackage[margin=1in]{geometry}

% Define code listing style
\definecolor{codegreen}{rgb}{0,0.6,0}
\definecolor{codegray}{rgb}{0.5,0.5,0.5}
\definecolor{codepurple}{rgb}{0.58,0,0.82}
\definecolor{backcolour}{rgb}{0.95,0.95,0.92}

\lstdefinestyle{mystyle}{
    backgroundcolor=\color{backcolour},   
    commentstyle=\color{codegreen},
    keywordstyle=\color{blue},
    numberstyle=\tiny\color{codegray},
    stringstyle=\color{codepurple},
    basicstyle=\ttfamily\footnotesize,
    breakatwhitespace=false,         
    breaklines=true,                 
    captionpos=b,                    
    keepspaces=true,                 
    numbers=left,                    
    numbersep=5pt,                  
    showspaces=false,                
    showstringspaces=false,
    showtabs=false,                  
    tabsize=2
}

\lstset{style=mystyle}

\title{Reproduction Report: """ + title + r"""}
\author{""" + author_string + r"""}
\date{\today}

\begin{document}

\maketitle

\begin{abstract}
""" + paper_info['basic_info'].get('abstract', '') + r"""
\end{abstract}

\tableofcontents
\newpage

\section{Introduction}
""" + latex_sections['introduction'] + r"""

\section{Paper Methods}
""" + latex_sections['method'] + r"""

\section{Implementation Details}
""" + latex_sections['implementation'] + r"""

\section{Experimental Results}
""" + latex_sections['results'] + r"""

\section{Analysis}
""" + latex_sections['analysis'] + r"""

\section{Discussion}
""" + latex_sections['discussion'] + r"""

\section{Conclusion}
""" + latex_sections['conclusion'] + r"""

\section*{References}
\begin{enumerate}
    \item """ + title + " by " + ", ".join(authors) + r"""
\end{enumerate}

\end{document}
"""
    
    return latex_content 