# AI Scientist: Paper Reproduction

This module enables the AI Scientist framework to reproduce results from research papers that don't provide code.

## Overview

The paper reproduction component allows the AI Scientist to:

1. Extract key information from a research paper (PDF)
2. Generate an implementation using OpenHands
3. Run experiments to reproduce the paper's results
4. Analyze the results and compare them to the paper's claims
5. Generate a comprehensive report documenting the reproduction process

## Features

- **Paper Understanding**: Extract key information from research papers, including methodologies, algorithms, and experimental setups.
- **Code Generation**: Use OpenHands to generate high-quality implementations of the paper's algorithms and methods.
- **Experiment Reproduction**: Execute the implementation to reproduce the paper's results.
- **Result Analysis**: Compare the reproduced results with the original paper's claims.
- **Report Generation**: Create a detailed report documenting the entire reproduction process.

## Usage

```bash
python launch_paper_repro.py --pdf_path /path/to/paper.pdf --openhands_model_config llm.eval_sonnet
```

### Options

- `--pdf_path`: Path to the PDF file of the paper to reproduce (required)
- `--openhands_model_config`: OpenHands model configuration name (default: llm.eval_sonnet)
- `--skip_paper_extraction`: Skip paper information extraction and use existing extracted data
- `--skip_code_generation`: Skip code generation and use existing implementation
- `--skip_experiments`: Skip running experiments and use existing results
- `--template`: Template to use for reproduction (if applicable)
- `--model`: Model to use for AI Scientist paper reproduction
- `--report_format`: What format to use for the reproduction report (latex or markdown)
- `--parallel`: Number of parallel processes to run (0 for sequential execution)
- `--gpus`: Comma-separated list of GPU IDs to use

## Example

```bash
python launch_paper_repro.py --pdf_path papers/example_paper.pdf --openhands_model_config llm.eval_sonnet --report_format markdown
```

## Requirements

- Access to a compatible LLM
- OpenHands installed and configured
- LaTeX (optional, for generating PDF reports)

## Directory Structure

When reproducing a paper, the following directory structure is created:

```
repro_papers/
└── paper_name/
    ├── paper_info.json         # Extracted information from the paper
    ├── implementation/         # Generated code implementation
    ├── results/                # Results from running the experiments
    ├── analysis/               # Analysis of the results
    └── report/                 # Generated reproduction report
```

## Integration with OpenHands

This module uses [OpenHands](https://github.com/openhands/openhands) for code generation and experiment execution. OpenHands provides a powerful agent-based framework specifically designed for this purpose, greatly enhancing the system's ability to reproduce research papers accurately.

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