"""
Result Analysis Module

This module is responsible for analyzing the results from the experiments and comparing
them with the results reported in the paper.
"""

import json
import os
import os.path as osp
from typing import Dict, List, Any, Optional
import numpy as np
import matplotlib.pyplot as plt
import re

def analyze_results(
    paper_info: Dict[str, Any],
    experiment_results: Dict[str, Any],
    analysis_dir: str,
    client,
    client_model: str
) -> Dict[str, Any]:
    """
    Analyze experiment results and compare them with paper results.
    
    Args:
        paper_info: Extracted information from the paper
        experiment_results: Results from the experiments
        analysis_dir: Directory to save analysis
        client: LLM client
        client_model: Name of the LLM model
        
    Returns:
        Dictionary containing analysis results
    """
    os.makedirs(analysis_dir, exist_ok=True)
    
    # Get paper results tables
    results_tables = paper_info["results_tables"]
    
    # Extract expected metrics from paper
    expected_metrics = extract_expected_metrics(results_tables)
    
    # Extract actual metrics from experiment results
    actual_metrics = extract_actual_metrics(experiment_results)
    
    # Generate comparison between expected and actual metrics
    comparison = compare_metrics(expected_metrics, actual_metrics)
    
    # Generate plots for visualizing the comparison
    plot_paths = generate_comparison_plots(
        expected_metrics, actual_metrics, analysis_dir
    )
    
    # Generate analysis using LLM
    analysis = generate_llm_analysis(
        paper_info, experiment_results, comparison, client, client_model
    )
    
    # Compile analysis results
    analysis_results = {
        "comparison": comparison,
        "analysis": analysis,
        "plot_paths": plot_paths
    }
    
    # Save analysis results
    with open(osp.join(analysis_dir, "result_analysis.json"), "w") as f:
        json.dump(analysis_results, f, indent=2)
    
    return analysis_results


def extract_expected_metrics(results_tables: List[Dict[str, Any]]) -> Dict[str, Dict[str, float]]:
    """
    Extract expected metrics from paper results tables.
    
    Args:
        results_tables: List of tables from the paper
        
    Returns:
        Dictionary mapping metrics to methods and values
    """
    expected_metrics = {}
    
    for table in results_tables:
        table_metrics = table.get("metrics", [])
        table_methods = table.get("methods", [])
        table_results = table.get("results", [])
        
        for result in table_results:
            method = result.get("method", "")
            metric = result.get("metric", "")
            value = result.get("value", 0.0)
            
            if metric not in expected_metrics:
                expected_metrics[metric] = {}
            
            expected_metrics[metric][method] = value
    
    return expected_metrics


def extract_actual_metrics(experiment_results: Dict[str, Any]) -> Dict[str, Dict[str, float]]:
    """
    Extract actual metrics from experiment results.
    
    Args:
        experiment_results: Results from the experiments
        
    Returns:
        Dictionary mapping metrics to methods and values
    """
    actual_metrics = {}
    
    # Check if there's an evaluation result
    if "evaluation" in experiment_results:
        eval_results = experiment_results["evaluation"]
        
        # Process generic evaluation results
        # The structure depends on the output format of the evaluation
        for key, value in eval_results.items():
            # Try to detect metrics based on common naming patterns
            if isinstance(value, (int, float)) or (isinstance(value, str) and is_numeric(value)):
                # Assume this is a metric
                if key not in actual_metrics:
                    actual_metrics[key] = {}
                
                # Use "implemented" as the method name for single values
                actual_metrics[key]["implemented"] = float(value)
            elif isinstance(value, dict):
                # This might be a method-to-metric mapping
                method = key
                for metric_key, metric_value in value.items():
                    if isinstance(metric_value, (int, float)) or (
                            isinstance(metric_value, str) and is_numeric(metric_value)):
                        if metric_key not in actual_metrics:
                            actual_metrics[metric_key] = {}
                        
                        actual_metrics[metric_key][method] = float(metric_value)
    
    # Process individual experiment results
    for exp_name, exp_result in experiment_results.items():
        if exp_name in ["evaluation", "evaluation_summary"]:
            continue
        
        # Check if the experiment has result metrics
        if "metrics" in exp_result:
            metrics = exp_result["metrics"]
            
            for metric_name, metric_value in metrics.items():
                if isinstance(metric_value, (int, float)) or (
                        isinstance(metric_value, str) and is_numeric(metric_value)):
                    if metric_name not in actual_metrics:
                        actual_metrics[metric_name] = {}
                    
                    actual_metrics[metric_name][exp_name] = float(metric_value)
    
    return actual_metrics


def is_numeric(value: str) -> bool:
    """
    Check if a string represents a numeric value.
    
    Args:
        value: String to check
        
    Returns:
        True if the string represents a numeric value, False otherwise
    """
    try:
        float(value)
        return True
    except (ValueError, TypeError):
        return False


def compare_metrics(
    expected_metrics: Dict[str, Dict[str, float]], 
    actual_metrics: Dict[str, Dict[str, float]]
) -> Dict[str, Any]:
    """
    Compare expected and actual metrics.
    
    Args:
        expected_metrics: Expected metrics from paper
        actual_metrics: Actual metrics from experiments
        
    Returns:
        Dictionary containing comparison results
    """
    comparison = {
        "metrics_comparison": [],
        "missing_metrics": [],
        "extra_metrics": []
    }
    
    # Find metrics in both expected and actual
    for metric in expected_metrics:
        if metric in actual_metrics:
            metric_comparison = {
                "metric": metric,
                "methods_comparison": []
            }
            
            # Compare methods for this metric
            for method in expected_metrics[metric]:
                expected_value = expected_metrics[metric][method]
                
                if method in actual_metrics[metric]:
                    actual_value = actual_metrics[metric][method]
                    absolute_diff = actual_value - expected_value
                    if expected_value != 0:
                        relative_diff = (actual_value - expected_value) / expected_value * 100
                    else:
                        relative_diff = float('inf') if actual_value != 0 else 0
                    
                    method_comparison = {
                        "method": method,
                        "expected": expected_value,
                        "actual": actual_value,
                        "absolute_diff": absolute_diff,
                        "relative_diff_percent": relative_diff
                    }
                    
                    metric_comparison["methods_comparison"].append(method_comparison)
                else:
                    # Method is in expected but not in actual
                    method_comparison = {
                        "method": method,
                        "expected": expected_value,
                        "actual": None,
                        "status": "missing"
                    }
                    
                    metric_comparison["methods_comparison"].append(method_comparison)
            
            # Add extra methods in actual but not in expected
            for method in actual_metrics[metric]:
                if method not in expected_metrics[metric]:
                    actual_value = actual_metrics[metric][method]
                    
                    method_comparison = {
                        "method": method,
                        "expected": None,
                        "actual": actual_value,
                        "status": "extra"
                    }
                    
                    metric_comparison["methods_comparison"].append(method_comparison)
            
            comparison["metrics_comparison"].append(metric_comparison)
        else:
            # Metric is in expected but not in actual
            comparison["missing_metrics"].append(metric)
    
    # Find metrics in actual but not in expected
    for metric in actual_metrics:
        if metric not in expected_metrics:
            comparison["extra_metrics"].append({
                "metric": metric,
                "methods": list(actual_metrics[metric].keys())
            })
    
    return comparison


def generate_comparison_plots(
    expected_metrics: Dict[str, Dict[str, float]],
    actual_metrics: Dict[str, Dict[str, float]],
    analysis_dir: str
) -> List[str]:
    """
    Generate plots comparing expected and actual metrics.
    
    Args:
        expected_metrics: Expected metrics from paper
        actual_metrics: Actual metrics from experiments
        analysis_dir: Directory to save plots
        
    Returns:
        List of paths to generated plots
    """
    plot_paths = []
    
    # Create plots directory
    plots_dir = osp.join(analysis_dir, "plots")
    os.makedirs(plots_dir, exist_ok=True)
    
    # For each metric in both expected and actual, create a bar plot
    for metric in expected_metrics:
        if metric in actual_metrics:
            # Get methods that appear in either expected or actual
            methods = list(set(list(expected_metrics[metric].keys()) + list(actual_metrics[metric].keys())))
            
            # Create bar plot
            fig, ax = plt.subplots(figsize=(10, 6))
            
            x = np.arange(len(methods))
            width = 0.35
            
            # Extract values
            expected_values = []
            actual_values = []
            
            for method in methods:
                expected_values.append(expected_metrics[metric].get(method, float('nan')))
                actual_values.append(actual_metrics[metric].get(method, float('nan')))
            
            # Create bars
            ax.bar(x - width/2, expected_values, width, label='Expected (Paper)')
            ax.bar(x + width/2, actual_values, width, label='Actual (Reproduced)')
            
            # Add labels and title
            ax.set_xlabel('Method')
            ax.set_ylabel(f'{metric}')
            ax.set_title(f'Comparison of {metric} values')
            ax.set_xticks(x)
            ax.set_xticklabels(methods, rotation=45, ha='right')
            ax.legend()
            
            # Add values on top of bars
            for i, v in enumerate(expected_values):
                if not np.isnan(v):
                    ax.text(i - width/2, v, f'{v:.3f}', ha='center', va='bottom')
            
            for i, v in enumerate(actual_values):
                if not np.isnan(v):
                    ax.text(i + width/2, v, f'{v:.3f}', ha='center', va='bottom')
            
            plt.tight_layout()
            
            # Save plot
            sanitized_metric = re.sub(r'[^\w\-_\. ]', '_', metric)
            plot_path = osp.join(plots_dir, f'{sanitized_metric}_comparison.png')
            plt.savefig(plot_path)
            plt.close()
            
            plot_paths.append(plot_path)
    
    return plot_paths


def generate_llm_analysis(
    paper_info: Dict[str, Any],
    experiment_results: Dict[str, Any],
    comparison: Dict[str, Any],
    client,
    client_model: str
) -> Dict[str, Any]:
    """
    Generate analysis of results using LLM.
    
    Args:
        paper_info: Extracted information from the paper
        experiment_results: Results from the experiments
        comparison: Comparison between expected and actual metrics
        client: LLM client
        client_model: Name of the LLM model
        
    Returns:
        Dictionary containing LLM analysis
    """
    # Prepare prompt
    prompt = f"""
    You are analyzing the results of a paper reproduction experiment.
    
    Paper title: {paper_info["basic_info"].get("title", "")}
    
    Here's a comparison between the expected results (from the paper) and the actual results (from our reproduction):
    
    {json.dumps(comparison, indent=2)}
    
    Please provide a comprehensive analysis of these results, addressing the following:
    
    1. Overall success of the reproduction: Did we successfully reproduce the main results of the paper?
    2. Specific metrics analysis: For each metric, how close are our results to the paper's reported values?
    3. Discrepancies: What might explain any significant differences between expected and actual results?
    4. Missing or extra metrics: Are there any metrics from the paper we failed to reproduce, or any extra metrics in our results?
    5. Challenges: What were the main challenges in reproducing the paper's results?
    6. Recommendations: How could the reproduction be improved?
    
    Format your response as a JSON object with the following structure:
    {{
        "overall_success": "Summary of overall success",
        "metrics_analysis": [
            {{
                "metric": "metric_name",
                "analysis": "Detailed analysis of this metric's reproduction"
            }},
            ...
        ],
        "discrepancy_explanations": [
            "Possible explanation 1",
            "Possible explanation 2",
            ...
        ],
        "missing_metrics_analysis": "Analysis of missing metrics",
        "extra_metrics_analysis": "Analysis of extra metrics",
        "challenges": [
            "Challenge 1",
            "Challenge 2",
            ...
        ],
        "recommendations": [
            "Recommendation 1",
            "Recommendation 2",
            ...
        ]
    }}
    """
    
    response = client.get(prompt, model=client_model)
    
    # Extract the JSON from the response
    json_match = re.search(r'```json\n(.*?)\n```', response, re.DOTALL)
    if json_match:
        analysis_json = json_match.group(1)
    else:
        # Try to find any JSON-like structure in the response
        analysis_json = response
    
    try:
        analysis = json.loads(analysis_json)
    except json.JSONDecodeError:
        # Default analysis if parsing fails
        analysis = {
            "overall_success": "Could not automatically determine overall success",
            "metrics_analysis": [],
            "discrepancy_explanations": [],
            "missing_metrics_analysis": "Could not automatically analyze missing metrics",
            "extra_metrics_analysis": "Could not automatically analyze extra metrics",
            "challenges": [],
            "recommendations": [],
            "raw_response": response
        }
    
    return analysis 