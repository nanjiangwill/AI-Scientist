#!/usr/bin/env python3
"""
Paper Parser Module

This module provides functionality to extract information from research papers,
including methods, experiments, and results.
"""

import os
import re
import json
import logging
import tempfile
from typing import Dict, List, Any, Optional, Union
import requests
from pathlib import Path

# Try to import PDF processing libraries
try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False

try:
    from pypdf import PdfReader
    PYPDF_AVAILABLE = True
except ImportError:
    PYPDF_AVAILABLE = False

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)


class PaperParser:
    """Class for parsing research papers and extracting information"""
    
    def __init__(self, paper_path: str):
        """
        Initialize the paper parser
        
        Args:
            paper_path: Path to the paper PDF or URL
        """
        self.paper_path = paper_path
        self.text = None
        self.sections = {}
        self.extracted_info = {
            "title": "",
            "authors": [],
            "abstract": "",
            "methods": [],
            "experiments": [],
            "results": [],
            "metrics": []
        }
    
    def load_paper(self) -> str:
        """
        Load the paper from the provided path or URL
        
        Returns:
            The text content of the paper
        """
        logger.info(f"Loading paper from {self.paper_path}")
        
        # Check if the path is a URL
        if self.paper_path.startswith(('http://', 'https://')):
            # Download the paper to a temporary file
            try:
                response = requests.get(self.paper_path)
                response.raise_for_status()
                
                with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
                    temp_file.write(response.content)
                    temp_path = temp_file.name
                
                # Extract text from the downloaded PDF
                self.text = self._extract_text_from_pdf(temp_path)
                
                # Clean up the temporary file
                os.unlink(temp_path)
                
            except requests.exceptions.RequestException as e:
                logger.error(f"Error downloading paper: {e}")
                self.text = ""
        else:
            # Extract text from the local PDF file
            self.text = self._extract_text_from_pdf(self.paper_path)
        
        return self.text
    
    def _extract_text_from_pdf(self, pdf_path: str) -> str:
        """
        Extract text from a PDF file
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            The extracted text
        """
        text = ""
        
        # Try PyMuPDF first (better quality)
        if PYMUPDF_AVAILABLE:
            try:
                doc = fitz.open(pdf_path)
                text = ""
                for page in doc:
                    text += page.get_text()
                doc.close()
                return text
            except Exception as e:
                logger.warning(f"PyMuPDF extraction failed: {e}")
        
        # Fall back to PyPDF
        if PYPDF_AVAILABLE:
            try:
                with open(pdf_path, 'rb') as file:
                    reader = PdfReader(file)
                    text = ""
                    for page in reader.pages:
                        text += page.extract_text()
                return text
            except Exception as e:
                logger.warning(f"PyPDF extraction failed: {e}")
        
        # If both methods failed
        if not text:
            logger.error("Failed to extract text from PDF. Please install PyMuPDF or PyPDF.")
        
        return text
    
    def extract_sections(self) -> Dict[str, str]:
        """
        Extract sections from the paper text
        
        Returns:
            Dictionary mapping section names to their content
        """
        if not self.text:
            logger.warning("No text loaded. Call load_paper() first.")
            return {}
        
        logger.info("Extracting sections from paper")
        
        # Common section headers in research papers
        section_patterns = [
            r'(?i)abstract',
            r'(?i)introduction',
            r'(?i)related work',
            r'(?i)background',
            r'(?i)method(?:s|ology)?',
            r'(?i)approach',
            r'(?i)implementation',
            r'(?i)experiment(?:s|al setup)?',
            r'(?i)evaluation',
            r'(?i)result(?:s)?',
            r'(?i)discussion',
            r'(?i)conclusion(?:s)?',
            r'(?i)future work',
            r'(?i)reference(?:s)?'
        ]
        
        # Find potential section headers
        section_matches = []
        for pattern in section_patterns:
            for match in re.finditer(pattern, self.text, re.IGNORECASE):
                # Check if the match is likely a section header (e.g., preceded by a number or at the start of a line)
                context_before = self.text[max(0, match.start() - 20):match.start()]
                if re.search(r'(?:\n|\r|^|\d+\.)', context_before):
                    section_matches.append((match.start(), match.group(0)))
        
        # Sort matches by position in the text
        section_matches.sort()
        
        # Extract section content
        self.sections = {}
        for i, (pos, name) in enumerate(section_matches):
            # Section content goes from current position to the next section (or end of text)
            end_pos = section_matches[i+1][0] if i < len(section_matches) - 1 else len(self.text)
            content = self.text[pos + len(name):end_pos].strip()
            self.sections[name.lower()] = content
        
        return self.sections
    
    def extract_title_and_authors(self) -> Dict[str, Any]:
        """
        Extract the paper title and authors
        
        Returns:
            Dictionary with title and authors
        """
        if not self.text:
            logger.warning("No text loaded. Call load_paper() first.")
            return {"title": "", "authors": []}
        
        logger.info("Extracting title and authors")
        
        # Simple heuristic: Title is often at the beginning, followed by authors
        lines = self.text.split('\n')
        title_candidates = []
        author_candidates = []
        
        # Look at the first few non-empty lines
        for i, line in enumerate(lines[:10]):
            line = line.strip()
            if not line:
                continue
            
            # Title is typically the first substantial line
            if not title_candidates and len(line) > 10:
                title_candidates.append(line)
            
            # Authors often follow the title and contain names
            elif title_candidates and not author_candidates:
                # Check if the line contains typical author patterns (names, affiliations)
                if re.search(r'(?i)(?:\b[A-Z][a-z]+ [A-Z][a-z]+\b)|(?:University|Institute|Lab)', line):
                    author_candidates.append(line)
        
        # Extract title
        title = title_candidates[0] if title_candidates else ""
        
        # Extract authors
        authors = []
        if author_candidates:
            # Split author line by common separators
            author_text = author_candidates[0]
            author_parts = re.split(r'(?:,|;|and|\band\b)', author_text)
            authors = [part.strip() for part in author_parts if part.strip()]
        
        self.extracted_info["title"] = title
        self.extracted_info["authors"] = authors
        
        return {"title": title, "authors": authors}
    
    def extract_abstract(self) -> str:
        """
        Extract the abstract from the paper
        
        Returns:
            The abstract text
        """
        if not self.sections:
            logger.warning("No sections extracted. Call extract_sections() first.")
            return ""
        
        logger.info("Extracting abstract")
        
        # Look for abstract in the sections
        abstract = self.sections.get("abstract", "")
        
        # If not found in sections, try to find it in the text
        if not abstract and self.text:
            abstract_match = re.search(r'(?i)abstract(?:\s*\n\s*)(.*?)(?:\n\n|\n\d+\.|\nIntroduction)', self.text, re.DOTALL)
            if abstract_match:
                abstract = abstract_match.group(1).strip()
        
        self.extracted_info["abstract"] = abstract
        return abstract
    
    def extract_methods(self) -> List[Dict[str, Any]]:
        """
        Extract methods from the paper
        
        Returns:
            List of dictionaries containing method information
        """
        if not self.sections:
            logger.warning("No sections extracted. Call extract_sections() first.")
            return []
        
        logger.info("Extracting methods")
        
        methods = []
        
        # Look for method sections
        method_section = None
        for section_name, content in self.sections.items():
            if re.search(r'(?i)method|approach|implementation', section_name):
                method_section = content
                break
        
        if not method_section:
            logger.warning("No method section found")
            return []
        
        # Split the method section into subsections
        subsections = re.split(r'\n(?:\d+\.\d+|\w+\.\d+|\w+\.\w+)\s+', method_section)
        
        # Process each subsection as a potential method
        for i, subsection in enumerate(subsections):
            if len(subsection.strip()) < 100:  # Skip very short subsections
                continue
            
            # Try to extract method name
            name_match = re.search(r'^([A-Z][a-zA-Z0-9\s]+)', subsection)
            name = name_match.group(1).strip() if name_match else f"Method {i+1}"
            
            # Extract parameters (look for variables, values, hyperparameters)
            parameters = {}
            param_matches = re.finditer(r'(?:(?:we|is|are|was|were)\s+set\s+to|parameter|hyperparameter)\s+([a-zA-Z0-9_]+)\s*(?:=|is|to|as)\s*([0-9.]+)', subsection)
            for match in param_matches:
                param_name = match.group(1).strip()
                param_value = match.group(2).strip()
                try:
                    # Convert to appropriate type (int or float)
                    if '.' in param_value:
                        parameters[param_name] = float(param_value)
                    else:
                        parameters[param_name] = int(param_value)
                except ValueError:
                    parameters[param_name] = param_value
            
            # Create method entry
            method = {
                "name": name,
                "description": subsection.strip(),
                "parameters": parameters
            }
            
            methods.append(method)
        
        self.extracted_info["methods"] = methods
        return methods
    
    def extract_experiments(self) -> List[Dict[str, Any]]:
        """
        Extract experiments from the paper
        
        Returns:
            List of dictionaries containing experiment information
        """
        if not self.sections:
            logger.warning("No sections extracted. Call extract_sections() first.")
            return []
        
        logger.info("Extracting experiments")
        
        experiments = []
        
        # Look for experiment sections
        experiment_section = None
        for section_name, content in self.sections.items():
            if re.search(r'(?i)experiment|evaluation|setup', section_name):
                experiment_section = content
                break
        
        if not experiment_section:
            logger.warning("No experiment section found")
            return []
        
        # Extract dataset information
        datasets = []
        dataset_matches = re.finditer(r'(?i)(?:dataset|data set|corpus)(?:\s+called)?\s+([A-Za-z0-9\-_]+)', experiment_section)
        for match in dataset_matches:
            datasets.append(match.group(1).strip())
        
        # Split the experiment section into subsections
        subsections = re.split(r'\n(?:\d+\.\d+|\w+\.\d+|\w+\.\w+)\s+', experiment_section)
        
        # Process each subsection as a potential experiment
        for i, subsection in enumerate(subsections):
            if len(subsection.strip()) < 100:  # Skip very short subsections
                continue
            
            # Try to extract experiment name
            name_match = re.search(r'^([A-Z][a-zA-Z0-9\s]+)', subsection)
            name = name_match.group(1).strip() if name_match else f"Experiment {i+1}"
            
            # Create experiment entry
            experiment = {
                "name": name,
                "description": subsection.strip(),
                "dataset": datasets[0] if datasets else "Unknown",
                "setup": subsection.strip()
            }
            
            experiments.append(experiment)
        
        self.extracted_info["experiments"] = experiments
        return experiments
    
    def extract_results(self) -> List[Dict[str, Any]]:
        """
        Extract results from the paper
        
        Returns:
            List of dictionaries containing result information
        """
        if not self.sections:
            logger.warning("No sections extracted. Call extract_sections() first.")
            return []
        
        logger.info("Extracting results")
        
        results = []
        metrics = set()
        
        # Look for results sections
        results_section = None
        for section_name, content in self.sections.items():
            if re.search(r'(?i)result|evaluation|performance', section_name):
                results_section = content
                break
        
        if not results_section:
            logger.warning("No results section found")
            return []
        
        # Extract common metrics
        common_metrics = [
            'accuracy', 'precision', 'recall', 'f1', 'f1-score', 'auc', 'auroc', 'map', 'bleu',
            'rouge', 'perplexity', 'ppl', 'mse', 'rmse', 'mae', 'r2', 'iou', 'dice'
        ]
        
        # Look for metric values in the results section
        for metric in common_metrics:
            # Pattern to match metric values (e.g., "accuracy of 85.2%" or "BLEU score: 32.1")
            pattern = fr'(?i)(?:{metric}(?:\s+score)?(?:\s+of|\s+is|\s*:|=)\s*(\d+\.\d+|\d+\.|\d+)%?)'
            matches = re.finditer(pattern, results_section)
            
            for match in matches:
                value_str = match.group(1).strip()
                try:
                    value = float(value_str)
                    # If the value is a percentage, convert to decimal
                    if '%' in match.group(0) and value > 0 and value <= 100:
                        value = value / 100
                    
                    # Add to results
                    results.append({
                        "experiment": "Main Experiment",  # Default name
                        "metric": metric.lower(),
                        "value": value
                    })
                    
                    # Add to metrics set
                    metrics.add(metric.lower())
                except ValueError:
                    logger.warning(f"Could not convert {value_str} to float")
        
        # Look for tables with results
        table_pattern = r'(?:Table|Tab\.)\s+\d+(?:.*?)(?:\n|\r\n)(?:.*?)(?:\n|\r\n)((?:(?:\||\+)?(?:[-]+(?:\||\+))+[-]+(?:\||\+)?(?:\n|\r\n))+)'
        table_matches = re.finditer(table_pattern, results_section, re.DOTALL)
        
        for table_match in table_matches:
            table_text = table_match.group(1)
            # Process table rows
            rows = table_text.strip().split('\n')
            for row in rows:
                # Skip separator rows
                if re.match(r'^(?:\||\+)?(?:[-]+(?:\||\+))+[-]+(?:\||\+)?$', row):
                    continue
                
                # Extract cells
                cells = re.split(r'\|', row.strip('|'))
                cells = [cell.strip() for cell in cells if cell.strip()]
                
                if len(cells) >= 2:
                    # Assume first cell is experiment/method name, others are metrics
                    experiment = cells[0]
                    for i, cell in enumerate(cells[1:], 1):
                        # Try to extract numeric values
                        value_match = re.search(r'(\d+\.\d+|\d+\.|\d+)%?', cell)
                        if value_match:
                            value_str = value_match.group(1)
                            try:
                                value = float(value_str)
                                # If the value is a percentage, convert to decimal
                                if '%' in cell and value > 0 and value <= 100:
                                    value = value / 100
                                
                                # Add to results
                                results.append({
                                    "experiment": experiment,
                                    "metric": f"Metric {i}",  # Default name
                                    "value": value
                                })
                            except ValueError:
                                pass
        
        self.extracted_info["results"] = results
        self.extracted_info["metrics"] = list(metrics)
        
        return results
    
    def extract_all_info(self) -> Dict[str, Any]:
        """
        Extract all information from the paper
        
        Returns:
            Dictionary containing all extracted information
        """
        logger.info("Extracting all information from paper")
        
        # Load the paper
        self.load_paper()
        
        # Extract sections
        self.extract_sections()
        
        # Extract title and authors
        self.extract_title_and_authors()
        
        # Extract abstract
        self.extract_abstract()
        
        # Extract methods
        self.extract_methods()
        
        # Extract experiments
        self.extract_experiments()
        
        # Extract results
        self.extract_results()
        
        return self.extracted_info
    
    def save_extracted_info(self, output_path: str) -> None:
        """
        Save extracted information to a JSON file
        
        Args:
            output_path: Path to save the JSON file
        """
        with open(output_path, 'w') as f:
            json.dump(self.extracted_info, f, indent=4)
        
        logger.info(f"Extracted information saved to {output_path}")


def main():
    """Main function to demonstrate paper parsing"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Extract information from research papers")
    parser.add_argument("paper_path", type=str, help="Path to the paper PDF or URL")
    parser.add_argument("--output", type=str, default="extracted_info.json", help="Path to save the extracted information")
    args = parser.parse_args()
    
    # Parse the paper
    parser = PaperParser(args.paper_path)
    parser.extract_all_info()
    
    # Save the extracted information
    parser.save_extracted_info(args.output)


if __name__ == "__main__":
    main()