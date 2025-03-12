#!/usr/bin/env python3
"""
Result Validator Module

This module provides functionality to compare reproduced results with
the original paper's claims and validate the reproduction.
"""

import os
import json
import logging
import numpy as np
import matplotlib.pyplot as plt
from typing import Dict, List, Any, Optional, Union, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)


class ResultValidator:
    """Class for validating reproduced results against original paper claims"""
    
    def __init__(self, extracted_info: Dict[str, Any], reproduced_results: Dict[str, Any], output_dir: str):
        """
        Initialize the result validator
        
        Args:
            extracted_info: Dictionary containing extracted information from the paper
            reproduced_results: Dictionary containing reproduced results
            output_dir: Directory to save validation results
        """
        self.extracted_info = extracted_info
        self.reproduced_results = reproduced_results
        self.output_dir = output_dir
        self.comparison = {}
        self.validation_summary = {}
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
    
    def compare_results(self) -> Dict[str, Any]:
        """
        Compare reproduced results with original paper results
        
        Returns:
            Dictionary containing comparison metrics
        """
        logger.info("Comparing reproduced results with original paper claims")
        
        # Extract original results from the paper
        original_results = {}
        for result in self.extracted_info.get('results', []):
            experiment = result.get('experiment', 'Main Experiment')
            metric = result.get('metric', 'Unknown')
            value = result.get('value', 0.0)
            
            if experiment not in original_results:
                original_results[experiment] = {}
            
            original_results[experiment][metric] = value
        
        # Compare with reproduced results
        self.comparison = {}
        for exp_name, metrics in self.reproduced_results.items():
            self.comparison[exp_name] = {}
            
            # Find matching experiment in original results
            # This is a simple matching strategy - in practice, you might need more sophisticated matching
            matching_exp = None
            for orig_exp in original_results:
                if orig_exp.lower() in exp_name.lower() or exp_name.lower() in orig_exp.lower():
                    matching_exp = orig_exp
                    break
            
            if matching_exp is None:
                logger.warning(f"No matching experiment found for {exp_name} in original results")
                continue
            
            # Compare metrics
            for metric_name, repro_value in metrics.items():
                self.comparison[exp_name][metric_name] = {}
                
                # Find matching metric in original results
                matching_metric = None
                for orig_metric in original_results[matching_exp]:
                    if orig_metric.lower() == metric_name.lower() or metric_name.lower() in orig_metric.lower():
                        matching_metric = orig_metric
                        break
                
                if matching_metric is None:
                    logger.warning(f"No matching metric found for {metric_name} in original results for {matching_exp}")
                    continue
                
                # Calculate differences
                orig_value = original_results[matching_exp][matching_metric]
                abs_diff = abs(repro_value - orig_value)
                rel_diff = abs_diff / orig_value if orig_value != 0 else float('inf')
                
                # Determine if the results match (within a tolerance)
                match_threshold = 0.05  # 5% relative difference
                is_match = rel_diff <= match_threshold
                
                # Store comparison
                self.comparison[exp_name][metric_name] = {
                    "original_experiment": matching_exp,
                    "original_metric": matching_metric,
                    "original_value": orig_value,
                    "reproduced_value": repro_value,
                    "absolute_difference": abs_diff,
                    "relative_difference": rel_diff,
                    "match": is_match
                }
        
        # Save comparison
        with open(os.path.join(self.output_dir, "comparison.json"), "w") as f:
            json.dump(self.comparison, f, indent=4)
        
        return self.comparison
    
    def validate_reproduction(self) -> Dict[str, Any]:
        """
        Validate the overall reproduction quality
        
        Returns:
            Dictionary containing validation summary
        """
        logger.info("Validating reproduction quality")
        
        if not self.comparison:
            logger.warning("No comparison data available. Call compare_results() first.")
            return {}
        
        # Calculate validation metrics
        total_metrics = 0
        matched_metrics = 0
        total_rel_diff = 0.0
        
        for exp_name, metrics in self.comparison.items():
            for metric_name, comp in metrics.items():
                total_metrics += 1
                if comp.get('match', False):
                    matched_metrics += 1
                total_rel_diff += comp.get('relative_difference', 0.0)
        
        # Calculate summary statistics
        match_rate = matched_metrics / total_metrics if total_metrics > 0 else 0.0
        avg_rel_diff = total_rel_diff / total_metrics if total_metrics > 0 else 0.0
        
        # Determine overall reproduction quality
        if match_rate >= 0.9:
            quality = "Excellent"
        elif match_rate >= 0.7:
            quality = "Good"
        elif match_rate >= 0.5:
            quality = "Fair"
        else:
            quality = "Poor"
        
        # Create validation summary
        self.validation_summary = {
            "total_metrics": total_metrics,
            "matched_metrics": matched_metrics,
            "match_rate": match_rate,
            "average_relative_difference": avg_rel_diff,
            "reproduction_quality": quality,
            "issues": self._identify_issues(),
            "recommendations": self._generate_recommendations()
        }
        
        # Save validation summary
        with open(os.path.join(self.output_dir, "validation_summary.json"), "w") as f:
            json.dump(self.validation_summary, f, indent=4)
        
        return self.validation_summary
    
    def _identify_issues(self) -> List[str]:
        """
        Identify issues in the reproduction
        
        Returns:
            List of identified issues
        """
        issues = []
        
        # Check for missing experiments
        original_experiments = set(result.get('experiment', 'Main Experiment') 
                                for result in self.extracted_info.get('results', []))
        reproduced_experiments = set(self.reproduced_results.keys())
        
        missing_experiments = []
        for orig_exp in original_experiments:
            found = False
            for repro_exp in reproduced_experiments:
                if orig_exp.lower() in repro_exp.lower() or repro_exp.lower() in orig_exp.lower():
                    found = True
                    break
            if not found:
                missing_experiments.append(orig_exp)
        
        if missing_experiments:
            issues.append(f"Missing experiments: {', '.join(missing_experiments)}")
        
        # Check for large discrepancies
        large_discrepancies = []
        for exp_name, metrics in self.comparison.items():
            for metric_name, comp in metrics.items():
                if comp.get('relative_difference', 0.0) > 0.1:  # More than 10% difference
                    large_discrepancies.append(f"{exp_name} - {metric_name}: "
                                              f"Original {comp.get('original_value', 0.0):.4f} vs. "
                                              f"Reproduced {comp.get('reproduced_value', 0.0):.4f}")
        
        if large_discrepancies:
            issues.append("Large discrepancies in results:")
            issues.extend(large_discrepancies)
        
        # Check for inconsistent trends
        # This is a simple check - in practice, you might need more sophisticated analysis
        inconsistent_trends = []
        original_results = {}
        for result in self.extracted_info.get('results', []):
            experiment = result.get('experiment', 'Main Experiment')
            metric = result.get('metric', 'Unknown')
            value = result.get('value', 0.0)
            
            if experiment not in original_results:
                original_results[experiment] = {}
            
            original_results[experiment][metric] = value
        
        # Compare trends across experiments
        for metric in self.extracted_info.get('metrics', []):
            orig_values = []
            repro_values = []
            exp_names = []
            
            for exp_name, metrics in self.comparison.items():
                if metric in metrics:
                    orig_values.append(metrics[metric].get('original_value', 0.0))
                    repro_values.append(metrics[metric].get('reproduced_value', 0.0))
                    exp_names.append(exp_name)
            
            if len(orig_values) >= 2:
                # Check if the trend (which is better) is consistent
                for i in range(len(orig_values) - 1):
                    for j in range(i + 1, len(orig_values)):
                        orig_comparison = orig_values[i] > orig_values[j]
                        repro_comparison = repro_values[i] > repro_values[j]
                        
                        if orig_comparison != repro_comparison:
                            inconsistent_trends.append(f"Inconsistent trend for {metric} between "
                                                     f"{exp_names[i]} and {exp_names[j]}")
        
        if inconsistent_trends:
            issues.append("Inconsistent trends in results:")
            issues.extend(inconsistent_trends)
        
        return issues
    
    def _generate_recommendations(self) -> List[str]:
        """
        Generate recommendations for improving the reproduction
        
        Returns:
            List of recommendations
        """
        recommendations = []
        
        # Check match rate
        match_rate = self.validation_summary.get('match_rate', 0.0)
        if match_rate < 0.7:
            recommendations.append("Review the implementation for potential errors or misinterpretations")
        
        # Check for missing experiments
        if any("Missing experiments" in issue for issue in self.validation_summary.get('issues', [])):
            recommendations.append("Implement the missing experiments to complete the reproduction")
        
        # Check for large discrepancies
        if any("Large discrepancies" in issue for issue in self.validation_summary.get('issues', [])):
            recommendations.append("Investigate the large discrepancies in results, focusing on:")
            recommendations.append("- Hyperparameter settings")
            recommendations.append("- Data preprocessing steps")
            recommendations.append("- Evaluation methodology")
            recommendations.append("- Random seed initialization")
        
        # Check for inconsistent trends
        if any("Inconsistent trends" in issue for issue in self.validation_summary.get('issues', [])):
            recommendations.append("Review the implementation to ensure the relative performance across methods is consistent with the paper")
        
        # General recommendations
        recommendations.append("Contact the original authors for clarification on ambiguous details")
        recommendations.append("Document all assumptions made during the reproduction process")
        recommendations.append("Run multiple trials with different random seeds to assess robustness")
        
        return recommendations
    
    def generate_plots(self) -> None:
        """
        Generate plots comparing original and reproduced results
        """
        logger.info("Generating comparison plots")
        
        if not self.comparison:
            logger.warning("No comparison data available. Call compare_results() first.")
            return
        
        # Create a bar chart comparing original and reproduced results
        plt.figure(figsize=(12, 8))
        
        # Group by metric
        metrics = {}
        for exp_name, exp_metrics in self.comparison.items():
            for metric_name, comp in exp_metrics.items():
                if metric_name not in metrics:
                    metrics[metric_name] = []
                metrics[metric_name].append((exp_name, comp))
        
        # Plot each metric
        for i, (metric_name, comparisons) in enumerate(metrics.items()):
            plt.subplot(len(metrics), 1, i+1)
            
            exp_names = [comp[0] for comp in comparisons]
            orig_values = [comp[1]['original_value'] for comp in comparisons]
            repro_values = [comp[1]['reproduced_value'] for comp in comparisons]
            
            x = np.arange(len(exp_names))
            width = 0.35
            
            plt.bar(x - width/2, orig_values, width, label='Original')
            plt.bar(x + width/2, repro_values, width, label='Reproduced')
            
            plt.xlabel('Experiments')
            plt.ylabel(metric_name)
            plt.title(f'Comparison of {metric_name}')
            plt.xticks(x, [name[:20] + '...' if len(name) > 20 else name for name in exp_names], rotation=45, ha='right')
            plt.legend()
            plt.grid(axis='y', linestyle='--', alpha=0.7)
        
        plt.tight_layout()
        plt.savefig(os.path.join(self.output_dir, "comparison_plot.png"))
        plt.close()
        
        # Create a heatmap of relative differences
        plt.figure(figsize=(10, 8))
        
        # Prepare data for heatmap
        exp_names = []
        metric_names = []
        rel_diffs = []
        
        for exp_name, exp_metrics in self.comparison.items():
            for metric_name, comp in exp_metrics.items():
                exp_names.append(exp_name)
                metric_names.append(metric_name)
                rel_diffs.append(comp['relative_difference'])
        
        # Create a 2D grid of relative differences
        unique_exp_names = list(set(exp_names))
        unique_metric_names = list(set(metric_names))
        
        heatmap_data = np.zeros((len(unique_metric_names), len(unique_exp_names)))
        
        for i, exp_name in enumerate(exp_names):
            metric_name = metric_names[i]
            rel_diff = rel_diffs[i]
            
            exp_idx = unique_exp_names.index(exp_name)
            metric_idx = unique_metric_names.index(metric_name)
            
            heatmap_data[metric_idx, exp_idx] = rel_diff
        
        # Plot heatmap
        plt.imshow(heatmap_data, cmap='YlOrRd')
        plt.colorbar(label='Relative Difference')
        
        plt.xticks(np.arange(len(unique_exp_names)), 
                  [name[:15] + '...' if len(name) > 15 else name for name in unique_exp_names], 
                  rotation=45, ha='right')
        plt.yticks(np.arange(len(unique_metric_names)), unique_metric_names)
        
        plt.xlabel('Experiments')
        plt.ylabel('Metrics')
        plt.title('Heatmap of Relative Differences')
        
        # Add text annotations
        for i in range(len(unique_metric_names)):
            for j in range(len(unique_exp_names)):
                text_color = 'white' if heatmap_data[i, j] > 0.1 else 'black'
                plt.text(j, i, f'{heatmap_data[i, j]:.2f}', 
                        ha='center', va='center', color=text_color)
        
        plt.tight_layout()
        plt.savefig(os.path.join(self.output_dir, "difference_heatmap.png"))
        plt.close()
        
        # Create a summary plot
        plt.figure(figsize=(10, 6))
        
        # Plot match rate
        match_rate = self.validation_summary.get('match_rate', 0.0)
        avg_rel_diff = self.validation_summary.get('average_relative_difference', 0.0)
        
        plt.subplot(1, 2, 1)
        plt.pie([match_rate, 1 - match_rate], 
               labels=['Matched', 'Not Matched'], 
               autopct='%1.1f%%', 
               colors=['#4CAF50', '#F44336'])
        plt.title('Match Rate')
        
        plt.subplot(1, 2, 2)
        plt.bar(['Average Relative Difference'], [avg_rel_diff], color='#2196F3')
        plt.axhline(y=0.05, color='r', linestyle='--', label='5% Threshold')
        plt.ylabel('Relative Difference')
        plt.title('Average Relative Difference')
        plt.legend()
        
        plt.tight_layout()
        plt.savefig(os.path.join(self.output_dir, "summary_plot.png"))
        plt.close()
    
    def generate_report(self) -> str:
        """
        Generate a detailed validation report
        
        Returns:
            Path to the generated report
        """
        logger.info("Generating validation report")
        
        if not self.validation_summary:
            logger.warning("No validation summary available. Call validate_reproduction() first.")
            return ""
        
        # Create report content
        report = f"""# Reproduction Validation Report

## Summary

- **Paper Title**: {self.extracted_info.get('title', 'Unknown')}
- **Authors**: {', '.join(self.extracted_info.get('authors', ['Unknown']))}
- **Reproduction Quality**: {self.validation_summary.get('reproduction_quality', 'Unknown')}
- **Match Rate**: {self.validation_summary.get('match_rate', 0.0):.2f} ({self.validation_summary.get('matched_metrics', 0)} out of {self.validation_summary.get('total_metrics', 0)} metrics matched)
- **Average Relative Difference**: {self.validation_summary.get('average_relative_difference', 0.0):.4f}

## Detailed Comparison

| Experiment | Metric | Original Value | Reproduced Value | Absolute Difference | Relative Difference | Match |
|------------|--------|----------------|------------------|---------------------|---------------------|-------|
"""
        
        # Add comparison details
        for exp_name, metrics in self.comparison.items():
            for metric_name, comp in metrics.items():
                orig_value = comp.get('original_value', 0.0)
                repro_value = comp.get('reproduced_value', 0.0)
                abs_diff = comp.get('absolute_difference', 0.0)
                rel_diff = comp.get('relative_difference', 0.0)
                is_match = comp.get('match', False)
                
                report += f"| {exp_name} | {metric_name} | {orig_value:.4f} | {repro_value:.4f} | {abs_diff:.4f} | {rel_diff:.4f} | {'Yes' if is_match else 'No'} |\n"
        
        # Add issues
        report += "\n## Issues\n\n"
        if self.validation_summary.get('issues', []):
            for issue in self.validation_summary.get('issues', []):
                report += f"- {issue}\n"
        else:
            report += "No major issues identified.\n"
        
        # Add recommendations
        report += "\n## Recommendations\n\n"
        if self.validation_summary.get('recommendations', []):
            for recommendation in self.validation_summary.get('recommendations', []):
                report += f"- {recommendation}\n"
        else:
            report += "No specific recommendations.\n"
        
        # Save report
        report_path = os.path.join(self.output_dir, "validation_report.md")
        with open(report_path, "w") as f:
            f.write(report)
        
        return report_path


def main():
    """Main function to demonstrate result validation"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Validate reproduced results against original paper claims")
    parser.add_argument("extracted_info", type=str, help="Path to the extracted information JSON file")
    parser.add_argument("reproduced_results", type=str, help="Path to the reproduced results JSON file")
    parser.add_argument("--output_dir", type=str, default="validation", help="Directory to save validation results")
    args = parser.parse_args()
    
    # Load extracted information
    with open(args.extracted_info, 'r') as f:
        extracted_info = json.load(f)
    
    # Load reproduced results
    with open(args.reproduced_results, 'r') as f:
        reproduced_results = json.load(f)
    
    # Validate results
    validator = ResultValidator(extracted_info, reproduced_results, args.output_dir)
    validator.compare_results()
    validator.validate_reproduction()
    validator.generate_plots()
    report_path = validator.generate_report()
    
    logger.info(f"Validation completed. Report saved to {report_path}")


if __name__ == "__main__":
    main()