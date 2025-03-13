"""
Paper Reproduction Module for AI Scientist

This module contains functionality for automatically reproducing results from
research papers that don't provide code.
"""

from .paper_understanding import extract_paper_info
from .openhands_integration import generate_code_with_openhands, run_experiments_with_openhands
from .result_analysis import analyze_results
from .report_generation import generate_report

__all__ = [
    "extract_paper_info",
    "generate_code_with_openhands",
    "run_experiments_with_openhands",
    "analyze_results",
    "generate_report",
] 