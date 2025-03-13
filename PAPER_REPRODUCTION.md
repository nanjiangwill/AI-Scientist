# Paper Reproduction with AI Scientist

This extension of the AI Scientist framework allows you to reproduce results from scientific papers that don't provide code implementations. It provides a systematic approach to extract information from papers, implement the described methods, run experiments, and validate the reproduced results against the original claims.

## Overview

The paper reproduction workflow consists of the following steps:

1. **Paper Extraction**: Extract key information from the paper, including:
   - Methods, experiments, and results
   - Tables with numerical data
   - Images, figures, and diagrams
   - Algorithms and pseudocode
2. **Method Implementation**: Generate code implementations based on the extracted method descriptions.
3. **Experiment Execution**: Run experiments following the original paper's setup.
4. **Result Validation**: Compare reproduced results with the original paper's claims.
5. **Report Generation**: Generate a comprehensive report on the reproduction process and findings.

### Enhanced Table and Image Extraction

The system includes advanced capabilities for extracting critical information from tables and images:

- **Table Extraction**: Automatically extracts tables from PDFs using multiple methods:
  - PyMuPDF for layout-based extraction
  - Tabula-py for grid-based extraction
  - Regex patterns for text-based tables
  - Saves tables in both CSV and JSON formats

- **Image Extraction**: Extracts figures and diagrams with:
  - Automatic caption detection
  - OCR for text embedded in images
  - Association of figures with their descriptions
  - Preservation of image context

## Quick Start

To reproduce a paper, run the following command:

```bash
python reproduce_paper.py --paper path/to/paper.pdf --model "claude-3-5-sonnet-20240620" --output_dir paper_reproductions
```

This will:
1. Extract information from the paper
2. Implement the methods described in the paper
3. Run experiments following the paper's setup
4. Compare the reproduced results with the original claims
5. Generate a report on the reproduction process

## Installation

First, ensure you have installed the required dependencies:

```bash
# Install AI Scientist dependencies
pip install -r requirements.txt

# Install paper reproduction specific dependencies
pip install -r templates/paper_reproduction/requirements.txt
```

## Usage

### Basic Usage

```bash
python reproduce_paper.py --paper path/to/paper.pdf
```

### Advanced Options

```bash
python reproduce_paper.py \
  --paper path/to/paper.pdf \
  --model "gpt-4o-2024-05-13" \
  --output_dir custom_output_directory \
  --gpu 0
```

### Skip Specific Steps

You can skip specific steps if you've already completed them:

```bash
# Skip paper extraction and use existing extracted_info.json
python reproduce_paper.py --paper path/to/paper.pdf --skip_extraction

# Skip implementation and use existing code
python reproduce_paper.py --paper path/to/paper.pdf --skip_extraction --skip_implementation

# Skip experiments and use existing results
python reproduce_paper.py --paper path/to/paper.pdf --skip_extraction --skip_implementation --skip_experiments
```

## Input

The system accepts the following inputs:

- **Paper PDF**: Local path to a PDF file
- **Paper URL**: URL to a PDF file (will be downloaded automatically)

## Output

The system generates the following outputs in the specified output directory:

- **extracted_info.json**: Extracted information from the paper, including:
  - Paper metadata (title, authors, abstract)
  - Methods with descriptions and parameters
  - Experiments with setup details
  - Results with metrics and values
  - Tables, figures, and algorithms

- **extracted_tables/**: Directory containing extracted tables:
  - CSV files for each table (for easy data import)
  - JSON files with table metadata (captions, locations)
  - Original structure and formatting preserved

- **extracted_images/**: Directory containing extracted figures:
  - PNG files of all figures and diagrams
  - Text extracted from images via OCR
  - JSON files with figure metadata (captions, locations)

- **extracted_algorithms/**: Directory containing extracted algorithms:
  - Text files with algorithm steps
  - JSON files with algorithm metadata
  - Preserved structure and indentation

- **implementation/**: Generated code implementations:
  - Python files for each method
  - Experiment script to run all methods
  - Implementation metadata

- **results/**: Results from running the experiments:
  - Numerical results in JSON format
  - Generated plots and visualizations
  - Logs from experiment runs

- **validation/**: Validation of reproduced results:
  - Comparison between original and reproduced results
  - Visualizations of differences
  - Analysis of reproduction quality

- **report/**: LaTeX source and PDF report on the reproduction
- **reproduction_report.pdf**: Final report summarizing the reproduction

## Example

Here's an example of reproducing a paper on a new machine learning method:

```bash
# Reproduce a paper on a new optimization algorithm
python reproduce_paper.py --paper https://example.com/paper.pdf --model "claude-3-5-sonnet-20240620"
```

## Limitations

The paper reproduction system has the following limitations:

- **Extraction Quality**: The quality of information extraction depends on the clarity and structure of the paper.
- **Implementation Accuracy**: Generated implementations may not perfectly match the authors' original implementations.
- **Computational Resources**: Some papers may require significant computational resources to reproduce.
- **Domain Knowledge**: Papers in specialized domains may require domain-specific knowledge for accurate reproduction.

## Troubleshooting

### Common Issues

1. **PDF Extraction Fails**:
   - Ensure the PDF is not password-protected
   - Try providing a direct URL to the paper instead

2. **Implementation Errors**:
   - Check the generated code for errors
   - Try using a more capable LLM model

3. **Experiment Failures**:
   - Check if all dependencies are installed
   - Ensure sufficient computational resources are available

4. **Result Discrepancies**:
   - Check for missing details in the paper
   - Consider contacting the original authors for clarification

## How It Works

### 1. Paper Extraction

The system uses a combination of PDF parsing, text analysis, and computer vision techniques to extract:

#### Text Content
- Title, authors, and abstract
- Method descriptions and algorithms
- Experimental setup and datasets
- Reported results and evaluation metrics

#### Tables
The system extracts tables using multiple complementary approaches:
- **Layout Analysis**: Uses PyMuPDF to detect tables based on document layout
- **Grid Detection**: Uses Tabula-py to identify grid structures in the PDF
- **Text Pattern Matching**: Uses regex patterns to identify tabular data in plain text
- **Post-processing**: Cleans and structures extracted tables, preserving relationships between cells

#### Images and Figures
The system extracts visual content with:
- **Image Extraction**: Directly extracts embedded images from the PDF
- **Caption Association**: Matches images with their captions by analyzing nearby text
- **OCR Processing**: Applies optical character recognition to extract text from diagrams
- **Context Preservation**: Maintains the relationship between figures and their descriptions

#### Algorithms
The system extracts algorithms and pseudocode by:
- **Block Detection**: Identifies algorithm blocks based on formatting and keywords
- **Structure Preservation**: Maintains indentation and hierarchical structure
- **Step Extraction**: Separates individual steps while preserving their sequence
- **Parameter Identification**: Extracts input/output parameters and their descriptions

### 2. Method Implementation

The system generates code implementations by:
- Analyzing method descriptions to determine appropriate implementation strategies
- Generating code for each method, including classes and functions
- Creating an experiment script to run the implemented methods

### 3. Experiment Execution

The system runs experiments by:
- Setting up the experimental environment
- Loading or generating datasets
- Running the implemented methods with appropriate parameters
- Collecting and saving results

### 4. Result Validation

The system validates results by:
- Matching reproduced results with original claims
- Calculating differences and determining if results match within a tolerance
- Identifying issues and generating recommendations

### 5. Report Generation

The system generates a comprehensive report that includes:
- Summary of the original paper
- Description of implemented methods
- Experimental setup and results
- Comparison with original claims
- Discussion of challenges and limitations

## Contributing

Contributions to improve the paper reproduction system are welcome! Please submit a pull request with your changes.