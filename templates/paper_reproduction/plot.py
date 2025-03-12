#!/usr/bin/env python3
"""
Plot generation for paper reproduction results

This script generates plots comparing the original paper results with the reproduced results.
"""

import argparse
import json
import os
import glob
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from pathlib import Path


def load_results(base_dir):
    """
    Load results from all runs in the base directory
    
    Args:
        base_dir: Base directory containing run directories
        
    Returns:
        Dictionary mapping run names to their results
    """
    results = {}
    
    # Find all run directories
    run_dirs = [d for d in os.listdir(base_dir) if d.startswith('run_')]
    
    for run_dir in sorted(run_dirs):
        run_path = os.path.join(base_dir, run_dir)
        final_info_path = os.path.join(run_path, 'final_info.json')
        
        if os.path.exists(final_info_path):
            with open(final_info_path, 'r') as f:
                results[run_dir] = json.load(f)
    
    return results


def plot_reproduction_accuracy(results, output_dir):
    """
    Plot the reproduction accuracy across different runs
    
    Args:
        results: Dictionary mapping run names to their results
        output_dir: Directory to save the plots
    """
    # Extract summary metrics
    run_names = list(results.keys())
    avg_rel_diffs = [result['summary']['average_relative_difference'] for result in results.values()]
    match_rates = [result['summary']['matched_metrics'] / result['summary']['total_metrics'] 
                  for result in results.values()]
    
    # Create figure
    fig, ax1 = plt.subplots(figsize=(10, 6))
    
    # Plot average relative difference
    color = 'tab:blue'
    ax1.set_xlabel('Run')
    ax1.set_ylabel('Average Relative Difference', color=color)
    ax1.bar(run_names, avg_rel_diffs, color=color, alpha=0.7)
    ax1.tick_params(axis='y', labelcolor=color)
    ax1.set_ylim(0, max(avg_rel_diffs) * 1.2 if avg_rel_diffs else 1)
    
    # Create second y-axis for match rate
    ax2 = ax1.twinx()
    color = 'tab:red'
    ax2.set_ylabel('Match Rate', color=color)
    ax2.plot(run_names, match_rates, color=color, marker='o', linestyle='-', linewidth=2)
    ax2.tick_params(axis='y', labelcolor=color)
    ax2.set_ylim(0, 1.1)
    
    # Add title and adjust layout
    plt.title('Reproduction Accuracy Across Runs')
    fig.tight_layout()
    
    # Save figure
    plt.savefig(os.path.join(output_dir, 'reproduction_accuracy.png'))
    plt.close()


def plot_metric_comparison(results, output_dir):
    """
    Plot comparison of metrics between original and reproduced results
    
    Args:
        results: Dictionary mapping run names to their results
        output_dir: Directory to save the plots
    """
    # Get the latest run (assuming it's the best)
    latest_run = sorted(results.keys())[-1]
    latest_results = results[latest_run]
    
    # Extract comparison data
    comparison = latest_results['comparison']
    
    # For each experiment, create a plot comparing metrics
    for exp_name, metrics in comparison.items():
        metric_names = list(metrics.keys())
        original_values = [metrics[m]['original'] for m in metric_names]
        reproduced_values = [metrics[m]['reproduced'] for m in metric_names]
        
        # Create figure
        plt.figure(figsize=(10, 6))
        
        # Set up bar positions
        x = np.arange(len(metric_names))
        width = 0.35
        
        # Create bars
        plt.bar(x - width/2, original_values, width, label='Original Paper')
        plt.bar(x + width/2, reproduced_values, width, label='Reproduced')
        
        # Add labels and title
        plt.xlabel('Metrics')
        plt.ylabel('Values')
        plt.title(f'Comparison of Original vs. Reproduced Results for {exp_name}')
        plt.xticks(x, metric_names)
        plt.legend()
        
        # Save figure
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, f'metric_comparison_{exp_name}.png'))
        plt.close()


def plot_implementation_progress(results, output_dir):
    """
    Plot the progress of implementation across runs
    
    Args:
        results: Dictionary mapping run names to their results
        output_dir: Directory to save the plots
    """
    # Extract data on implemented methods
    run_names = list(results.keys())
    
    # Count implemented methods in each run
    # In a real implementation, we would track more detailed metrics
    implemented_methods = []
    for run in run_names:
        if 'implementation' in results[run]:
            implemented_methods.append(len(results[run].get('implementation', {})))
        else:
            implemented_methods.append(0)
    
    # Create figure
    plt.figure(figsize=(10, 6))
    
    # Plot implemented methods
    plt.plot(run_names, implemented_methods, marker='o', linestyle='-', linewidth=2)
    
    # Add labels and title
    plt.xlabel('Run')
    plt.ylabel('Number of Implemented Methods')
    plt.title('Implementation Progress Across Runs')
    
    # Save figure
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'implementation_progress.png'))
    plt.close()


def create_summary_table(results, output_dir):
    """
    Create a summary table of reproduction results
    
    Args:
        results: Dictionary mapping run names to their results
        output_dir: Directory to save the table
    """
    # Extract summary data
    data = []
    for run_name, result in results.items():
        summary = result['summary']
        data.append({
            'Run': run_name,
            'Total Experiments': summary['total_experiments'],
            'Total Metrics': summary['total_metrics'],
            'Matched Metrics': summary['matched_metrics'],
            'Match Rate': summary['matched_metrics'] / summary['total_metrics'] if summary['total_metrics'] > 0 else 0,
            'Avg. Relative Difference': summary['average_relative_difference']
        })
    
    # Create DataFrame
    df = pd.DataFrame(data)
    
    # Save as CSV
    df.to_csv(os.path.join(output_dir, 'summary_table.csv'), index=False)
    
    # Create a visual table as an image
    fig, ax = plt.subplots(figsize=(12, len(data) * 0.5 + 1))
    ax.axis('tight')
    ax.axis('off')
    
    table = ax.table(
        cellText=df.values,
        colLabels=df.columns,
        loc='center',
        cellLoc='center'
    )
    
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1, 1.5)
    
    plt.savefig(os.path.join(output_dir, 'summary_table.png'), bbox_inches='tight')
    plt.close()


def main():
    """Main function to generate plots"""
    parser = argparse.ArgumentParser(description="Generate plots for paper reproduction results")
    parser.add_argument("--base_dir", type=str, default=".",
                        help="Base directory containing run directories")
    parser.add_argument("--output_dir", type=str, default="plots",
                        help="Directory to save the plots")
    args = parser.parse_args()
    
    # Create output directory if it doesn't exist
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Load results
    results = load_results(args.base_dir)
    
    if not results:
        print("No results found. Make sure the run directories contain final_info.json files.")
        return
    
    # Generate plots
    plot_reproduction_accuracy(results, args.output_dir)
    plot_metric_comparison(results, args.output_dir)
    plot_implementation_progress(results, args.output_dir)
    create_summary_table(results, args.output_dir)
    
    print(f"Plots generated and saved to {args.output_dir}")


if __name__ == "__main__":
    main()