# Paper Reproduction with AI Scientist

This extension of the AI Scientist framework allows for automatic reproduction of results from research papers that don't provide code. It uses large language models to extract key information from papers, generate implementations, run experiments, and analyze results.

## Overview

The paper reproduction system follows these steps:

1. **Paper Understanding**: Extract key information from a research paper PDF, including methods, algorithms, datasets, evaluation metrics, and reported results.
2. **Code Generation**: Generate a complete implementation of the methods described in the paper.
3. **Experiment Reproduction**: Set up and run experiments to reproduce the paper's results.
4. **Result Analysis**: Compare the reproduced results with the original paper's results and analyze discrepancies.
5. **Report Generation**: Generate a comprehensive report documenting the reproduction process and results.

## Requirements

In addition to the original AI Scientist requirements, you'll need:

- **PDF Processing Tools**: Install poppler-utils for PDF extraction:
  ```bash
  sudo apt-get install poppler-utils
  ```

## Usage

### Basic Usage

To reproduce a paper, run:

```bash
python launch_paper_repro.py --pdf_path path/to/paper.pdf --model claude-3-5-sonnet-20240620
```

This will:
1. Extract information from the paper
2. Generate an implementation
3. Run experiments
4. Analyze results
5. Generate a report

### Arguments

The following command-line arguments are available:

- `--pdf_path`: Path to the PDF file of the paper to reproduce (required)
- `--model`: LLM model to use (default: claude-3-5-sonnet-20240620)
- `--template`: Optional template to use for implementation (if applicable)
- `--report_format`: Format for the final report (latex or markdown, default: latex)
- `--gpus`: Comma-separated list of GPU IDs to use (default: all available GPUs)
- `--parallel`: Number of parallel processes to run (default: 0 for sequential execution)

### Skipping Steps

You can skip certain steps if you've already completed them:

- `--skip_paper_extraction`: Skip paper information extraction and use existing extracted data
- `--skip_code_generation`: Skip code generation and use existing implementation
- `--skip_experiments`: Skip running experiments and use existing results

## Output Structure

The system creates a directory structure for each paper:

```
repro_papers/
└── paper_name/
    ├── paper_info.json
    ├── implementation/
    │   ├── models/
    │   ├── data/
    │   ├── experiments/
    │   └── ...
    ├── results/
    │   ├── experiment_plan.json
    │   ├── experiment_results.json
    │   └── ...
    ├── analysis/
    │   ├── result_analysis.json
    │   └── plots/
    └── report/
        ├── reproduction_report.pdf
        └── ...
```

## How It Works

### Paper Understanding

The system extracts text and images from the PDF and uses an LLM to:
- Identify the paper's title, authors, and abstract
- Extract key methods and algorithms
- Parse results tables
- Process figures and diagrams
- Generate guidance for implementation

### Code Generation

The system generates a complete implementation, including:
- Core models and algorithms
- Data processing pipelines
- Training scripts
- Evaluation code
- Utility functions

### Experiment Reproduction

The system:
- Creates an experiment plan based on the paper's methodology
- Sets up the required environments
- Runs experiments using available GPUs
- Collects and organizes results

### Result Analysis

The system:
- Compares reproduced results with the paper's reported results
- Generates visualizations of the comparison
- Analyzes discrepancies and their potential causes
- Evaluates the overall success of the reproduction

### Report Generation

The system generates a comprehensive report documenting:
- The paper's methods and contributions
- Implementation details
- Experimental setup
- Results comparison
- Analysis of discrepancies
- Conclusions about reproducibility

## Customization

You can customize the system by:
- Adding custom templates for specific research domains
- Modifying prompts in the code to focus on particular aspects of papers
- Extending the result analysis for specific metrics or visualization types

## Limitations

- The system may struggle with papers that have complex mathematical notation
- Some experimental setups may be challenging to reproduce automatically
- The accuracy of result extraction depends on the clarity of the paper's presentation
- Very computationally intensive papers may require manual optimization

## Citation

If you use this system in your research, please cite:

```
@article{ai_scientist_paper_repro,
  title={The AI Scientist: Towards Fully Automated Open-Ended Scientific Discovery},
  author={The AI Scientist Team},
  journal={arXiv preprint},
  year={2024}
}
``` 