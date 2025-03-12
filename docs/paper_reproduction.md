# Paper Reproduction with AI-Scientist

This document explains how to use the paper reproduction feature of AI-Scientist, which allows you to reproduce results from academic papers that don't provide code.

## Overview

The paper reproduction module:
1. Extracts information from academic papers (in PDF format)
2. Generates implementation code based on the paper's methods
3. Runs experiments to reproduce the results
4. Compares the reproduced results with those reported in the paper

## Requirements

- Python 3.8+
- OpenHands (installed via `pip install openhands-aci>=0.2.5`)
- PyMuPDF4LLM (for PDF parsing)
- FPDF (for PDF creation in testing)
- Other dependencies listed in requirements.txt

## Usage

### Basic Usage

```bash
python launch_paper_reproduction.py --pdf path/to/paper.pdf --model gpt-4o
```

### Command-line Arguments

- `--pdf`: Path to the PDF file of the paper to reproduce (required)
- `--model`: LLM model to use for code generation and analysis (default: gpt-4o)
- `--output-dir`: Directory to store reproduction results (default: results/paper_reproduction)

### Example

```bash
python launch_paper_reproduction.py --pdf example_papers/sample_paper.pdf --model gpt-4o
```

## Output

The paper reproduction process generates:
1. Implementation code for the methods described in the paper
2. Experiment code to reproduce the results
3. A comparison of the reproduced results with those reported in the paper
4. A JSON file containing all the results and metadata

## How It Works

1. **Paper Parsing**: The module extracts text content from the PDF and parses it into sections (abstract, introduction, methods, experiments, results, etc.).

2. **Code Generation**: Using the extracted information, the module generates implementation code for the methods described in the paper and experiment code to reproduce the results.

3. **Experiment Running**: The module runs the generated code to reproduce the results reported in the paper.

4. **Result Comparison**: The module compares the reproduced results with those reported in the paper and analyzes any differences.

## Limitations

- PDF parsing may not be perfect, especially for papers with complex formatting or equations
- Code generation depends on the quality and clarity of the paper's descriptions
- Some papers may require specialized hardware or datasets that are not readily available
- The module may not be able to reproduce results from papers that rely on proprietary data or methods

## Future Work

- Improve PDF parsing to better handle complex formatting and equations
- Add support for extracting information from figures and tables
- Implement more sophisticated result comparison methods
- Add support for more types of papers and domains