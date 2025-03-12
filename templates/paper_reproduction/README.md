# Paper Reproduction Template

This template extends the AI Scientist framework to reproduce results from scientific papers that don't provide code implementations. It provides a systematic approach to extract information from papers, implement the described methods, run experiments, and validate the reproduced results against the original claims.

## Overview

The paper reproduction template consists of the following components:

1. **Paper Parser**: Extracts key information from research papers, including methods, experiments, and results.
2. **Code Generator**: Generates code implementations based on the extracted method descriptions.
3. **Experiment Runner**: Executes the implemented methods and runs experiments following the original setup.
4. **Result Validator**: Compares the reproduced results with the original paper's claims and validates the reproduction.

## Usage

### 1. Setup

First, ensure you have installed the required dependencies:

```bash
pip install -r requirements.txt
```

### 2. Reproduce a Paper

To reproduce a paper, follow these steps:

1. **Extract Information from the Paper**:

```bash
python paper_parser.py path/to/paper.pdf --output extracted_info.json
```

2. **Generate Code Implementations**:

```bash
python code_generator.py extracted_info.json --output_dir implementation
```

3. **Run Experiments**:

```bash
cd implementation
python run_experiments.py --output_dir results
```

4. **Validate Results**:

```bash
python result_validator.py extracted_info.json results/results.json --output_dir validation
```

### 3. Generate a Report

After completing the reproduction process, you can generate a LaTeX report:

```bash
python experiment.py --paper path/to/paper.pdf --out_dir reproduction_results
```

This will run the complete reproduction pipeline and generate a report comparing the reproduced results with the original paper's claims.

## Components

### Paper Parser (`paper_parser.py`)

The paper parser extracts key information from research papers, including:

- Title and authors
- Abstract
- Methods and algorithms
- Experimental setup
- Reported results and metrics

It uses a combination of text processing techniques to identify and extract relevant information from the paper's PDF.

### Code Generator (`code_generator.py`)

The code generator creates implementations of the methods described in the paper. It:

- Analyzes method descriptions to determine appropriate implementation strategies
- Generates code for each method, including classes and functions
- Creates an experiment script to run the implemented methods
- Handles dependencies and imports

### Experiment Runner (part of `experiment.py`)

The experiment runner executes the implemented methods and runs experiments following the original setup. It:

- Sets up the experimental environment
- Loads or generates datasets
- Runs the implemented methods with appropriate parameters
- Collects and saves results

### Result Validator (`result_validator.py`)

The result validator compares the reproduced results with the original paper's claims. It:

- Matches reproduced results with original claims
- Calculates differences and determines if results match within a tolerance
- Identifies issues and generates recommendations
- Creates visualizations comparing original and reproduced results
- Generates a detailed validation report

## Example

Here's an example of reproducing a paper using this template:

```bash
# Extract information from the paper
python paper_parser.py example_paper.pdf --output extracted_info.json

# Generate code implementations
python code_generator.py extracted_info.json --output_dir implementation

# Run experiments
cd implementation
python run_experiments.py --output_dir results

# Validate results
python result_validator.py extracted_info.json results/results.json --output_dir validation

# Generate a report
cd ..
python experiment.py --paper example_paper.pdf --out_dir reproduction_results
```

## Customization

You can customize the reproduction process by modifying the following:

- **Extraction Parameters**: Adjust how information is extracted from papers
- **Implementation Strategies**: Customize how methods are implemented
- **Experiment Configuration**: Modify experimental setup and parameters
- **Validation Criteria**: Change the criteria for determining if results match

## Limitations

The paper reproduction template has the following limitations:

- **Ambiguous Descriptions**: Papers often contain ambiguous or incomplete method descriptions
- **Missing Details**: Important implementation details may be omitted from papers
- **Domain Knowledge**: Some papers require domain-specific knowledge for proper implementation
- **Computational Resources**: Reproducing some papers may require significant computational resources

## Contributing

Contributions to improve the paper reproduction template are welcome! Please submit a pull request with your changes.