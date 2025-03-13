#!/usr/bin/env python3
"""
Paper Parser Module

This module provides functionality to extract information from research papers,
including methods, experiments, results, tables, and images.
"""

import os
import re
import json
import logging
import tempfile
import csv
from typing import Dict, List, Any, Optional, Union, Tuple
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

# Try to import table extraction libraries
try:
    import tabula
    TABULA_AVAILABLE = True
except ImportError:
    TABULA_AVAILABLE = False

# Try to import OCR libraries
try:
    import pytesseract
    from PIL import Image
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)


class PaperParser:
    """Class for parsing research papers and extracting information"""
    
    def __init__(self, paper_path: str, output_dir: str = None):
        """
        Initialize the paper parser
        
        Args:
            paper_path: Path to the paper PDF or URL
            output_dir: Directory to save extracted files (tables, images, etc.)
        """
        self.paper_path = paper_path
        self.output_dir = output_dir or os.path.dirname(paper_path)
        self.text = None
        self.sections = {}
        self.extracted_info = {
            "title": "",
            "authors": [],
            "abstract": "",
            "methods": [],
            "experiments": [],
            "results": [],
            "metrics": [],
            "tables": [],
            "figures": [],
            "algorithms": []
        }
        
        # Create output directory if it doesn't exist
        if self.output_dir:
            os.makedirs(self.output_dir, exist_ok=True)
    
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
    
    def extract_tables(self) -> List[Dict[str, Any]]:
        """
        Extract tables from the paper
        
        Returns:
            List of dictionaries containing table information
        """
        logger.info("Extracting tables from paper")
        
        tables = []
        tables_dir = os.path.join(self.output_dir, "extracted_tables")
        os.makedirs(tables_dir, exist_ok=True)
        
        # Method 1: Extract tables using PyMuPDF
        if PYMUPDF_AVAILABLE:
            try:
                doc = fitz.open(self.paper_path)
                for page_num, page in enumerate(doc):
                    # Extract tables using PyMuPDF
                    tab_dict = page.find_tables()
                    if tab_dict and hasattr(tab_dict, 'tables'):
                        for table_idx, table in enumerate(tab_dict.tables):
                            # Convert table to structured data
                            rows = []
                            for row in table.rows:
                                cells = []
                                for cell in row.cells:
                                    rect = fitz.Rect(cell.bbox)
                                    text = page.get_text("text", clip=rect).strip()
                                    cells.append(text)
                                rows.append(cells)
                            
                            # Find caption (usually above or below the table)
                            caption = ""
                            rect_above = fitz.Rect(table.bbox[0], table.bbox[1] - 50, table.bbox[2], table.bbox[1])
                            text_above = page.get_text("text", clip=rect_above)
                            if "Table" in text_above:
                                caption = text_above.strip()
                            
                            # Add table to list
                            table_id = f"Table {page_num+1}_{table_idx+1}"
                            tables.append({
                                "id": table_id,
                                "caption": caption,
                                "content": rows,
                                "location": f"Page {page_num + 1}"
                            })
                            
                            # Save as CSV
                            csv_path = os.path.join(tables_dir, f"{table_id}.csv")
                            with open(csv_path, "w", newline="") as f:
                                writer = csv.writer(f)
                                for row in rows:
                                    writer.writerow(row)
                            
                            # Save as JSON
                            json_path = os.path.join(tables_dir, f"{table_id}.json")
                            with open(json_path, "w") as f:
                                json.dump({
                                    "id": table_id,
                                    "caption": caption,
                                    "content": rows,
                                    "location": f"Page {page_num + 1}"
                                }, f, indent=4)
                doc.close()
            except Exception as e:
                logger.warning(f"PyMuPDF table extraction failed: {e}")
        
        # Method 2: Extract tables using tabula-py
        if TABULA_AVAILABLE and not tables:
            try:
                # Convert PDF path to absolute path if it's not a URL
                pdf_path = self.paper_path
                if not pdf_path.startswith(('http://', 'https://')):
                    pdf_path = os.path.abspath(pdf_path)
                
                # Extract tables using tabula
                extracted_tables = tabula.read_pdf(pdf_path, pages='all', multiple_tables=True)
                
                for i, df in enumerate(extracted_tables):
                    if not df.empty:
                        table_id = f"Table_{i+1}"
                        
                        # Convert DataFrame to list of lists
                        rows = [df.columns.tolist()]  # Header row
                        rows.extend(df.values.tolist())
                        
                        # Add table to list
                        tables.append({
                            "id": table_id,
                            "caption": "",  # Tabula doesn't extract captions
                            "content": rows,
                            "location": "Unknown"
                        })
                        
                        # Save as CSV
                        csv_path = os.path.join(tables_dir, f"{table_id}.csv")
                        df.to_csv(csv_path, index=False)
                        
                        # Save as JSON
                        json_path = os.path.join(tables_dir, f"{table_id}.json")
                        with open(json_path, "w") as f:
                            json.dump({
                                "id": table_id,
                                "caption": "",
                                "content": rows,
                                "location": "Unknown"
                            }, f, indent=4)
            except Exception as e:
                logger.warning(f"Tabula table extraction failed: {e}")
        
        # Method 3: Extract tables using regex patterns (fallback)
        if not tables and self.text:
            # Look for table patterns in the text
            table_patterns = [
                r'(?:Table|Tab\.)\s+\d+(?:.*?)(?:\n|\r\n)(?:.*?)(?:\n|\r\n)((?:(?:\||\+)?(?:[-]+(?:\||\+))+[-]+(?:\||\+)?(?:\n|\r\n))+)',
                r'(?:\n|\r\n)((?:[^\n]+\|[^\n]+(?:\n|\r\n))+)'
            ]
            
            for pattern in table_patterns:
                table_matches = re.finditer(pattern, self.text, re.DOTALL)
                
                for i, table_match in enumerate(table_matches):
                    table_text = table_match.group(1)
                    
                    # Process table rows
                    rows = []
                    for row in table_text.strip().split('\n'):
                        # Skip separator rows
                        if re.match(r'^(?:\||\+)?(?:[-]+(?:\||\+))+[-]+(?:\||\+)?$', row):
                            continue
                        
                        # Extract cells
                        cells = re.split(r'\|', row.strip('|'))
                        cells = [cell.strip() for cell in cells if cell.strip()]
                        
                        if cells:
                            rows.append(cells)
                    
                    if rows:
                        table_id = f"Table_regex_{i+1}"
                        
                        # Find caption
                        caption = ""
                        context_before = self.text[max(0, table_match.start() - 200):table_match.start()]
                        caption_match = re.search(r'(?:Table|Tab\.)\s+\d+[\.:]?\s*([^\n]+)', context_before)
                        if caption_match:
                            caption = caption_match.group(1).strip()
                        
                        # Add table to list
                        tables.append({
                            "id": table_id,
                            "caption": caption,
                            "content": rows,
                            "location": "Unknown"
                        })
                        
                        # Save as CSV
                        csv_path = os.path.join(tables_dir, f"{table_id}.csv")
                        with open(csv_path, "w", newline="") as f:
                            writer = csv.writer(f)
                            for row in rows:
                                writer.writerow(row)
                        
                        # Save as JSON
                        json_path = os.path.join(tables_dir, f"{table_id}.json")
                        with open(json_path, "w") as f:
                            json.dump({
                                "id": table_id,
                                "caption": caption,
                                "content": rows,
                                "location": "Unknown"
                            }, f, indent=4)
        
        self.extracted_info["tables"] = tables
        return tables
    
    def extract_images(self) -> List[Dict[str, Any]]:
        """
        Extract images from the paper
        
        Returns:
            List of dictionaries containing image information
        """
        logger.info("Extracting images from paper")
        
        images = []
        images_dir = os.path.join(self.output_dir, "extracted_images")
        os.makedirs(images_dir, exist_ok=True)
        
        if PYMUPDF_AVAILABLE:
            try:
                doc = fitz.open(self.paper_path)
                
                for page_num, page in enumerate(doc):
                    # Extract images
                    image_list = page.get_images(full=True)
                    
                    for img_idx, img in enumerate(image_list):
                        xref = img[0]
                        base_image = doc.extract_image(xref)
                        image_bytes = base_image["image"]
                        
                        # Save image
                        image_filename = f"figure_{page_num+1}_{img_idx+1}.png"
                        image_path = os.path.join(images_dir, image_filename)
                        with open(image_path, "wb") as f:
                            f.write(image_bytes)
                        
                        # Find caption (usually below the image)
                        caption = ""
                        try:
                            rect = page.get_image_bbox(xref)
                            rect_below = fitz.Rect(rect[0], rect[3], rect[2], rect[3] + 50)
                            text_below = page.get_text("text", clip=rect_below)
                            
                            if "Figure" in text_below or "Fig." in text_below:
                                caption = text_below.strip()
                        except:
                            # If we can't get the image bbox, try to find captions in the text
                            pass
                        
                        # If no caption found, try to find it in the text
                        if not caption:
                            # Look for figure captions in the text
                            figure_pattern = r'(?:Figure|Fig\.)\s+\d+[\.:]?\s*([^\n]+)'
                            figure_matches = re.finditer(figure_pattern, self.text)
                            
                            for match in figure_matches:
                                caption = match.group(1).strip()
                                break
                        
                        # Perform OCR if available
                        extracted_text = ""
                        if OCR_AVAILABLE:
                            try:
                                # Open the image with PIL
                                pil_image = Image.open(image_path)
                                
                                # Perform OCR
                                extracted_text = pytesseract.image_to_string(pil_image)
                                
                                # Save extracted text
                                text_path = os.path.join(images_dir, f"{os.path.splitext(image_filename)[0]}_text.txt")
                                with open(text_path, "w") as f:
                                    f.write(extracted_text)
                            except Exception as e:
                                logger.warning(f"OCR failed for {image_filename}: {e}")
                        
                        # Add image to list
                        image_info = {
                            "id": f"Figure {page_num+1}_{img_idx+1}",
                            "caption": caption,
                            "filename": image_filename,
                            "location": f"Page {page_num + 1}",
                            "extracted_text": extracted_text
                        }
                        
                        images.append(image_info)
                        
                        # Save image info as JSON
                        json_path = os.path.join(images_dir, f"{os.path.splitext(image_filename)[0]}_info.json")
                        with open(json_path, "w") as f:
                            json.dump(image_info, f, indent=4)
                
                doc.close()
            except Exception as e:
                logger.warning(f"PyMuPDF image extraction failed: {e}")
        
        self.extracted_info["figures"] = images
        return images
    
    def extract_algorithms(self) -> List[Dict[str, Any]]:
        """
        Extract algorithms from the paper
        
        Returns:
            List of dictionaries containing algorithm information
        """
        logger.info("Extracting algorithms from paper")
        
        algorithms = []
        algorithms_dir = os.path.join(self.output_dir, "extracted_algorithms")
        os.makedirs(algorithms_dir, exist_ok=True)
        
        if not self.text:
            logger.warning("No text loaded. Call load_paper() first.")
            return []
        
        # Look for algorithm blocks in the text
        algorithm_patterns = [
            r'(?i)(?:Algorithm|Alg\.)\s+\d+[\.:]?\s*([^\n]+)(?:\n|\r\n)((?:(?:\d+:|[a-z]+:|\s{2,}|\t).+(?:\n|\r\n))+)',
            r'(?i)Procedure\s+([A-Za-z0-9_]+)(?:\n|\r\n)((?:(?:\d+:|[a-z]+:|\s{2,}|\t).+(?:\n|\r\n))+)'
        ]
        
        for pattern in algorithm_patterns:
            matches = re.finditer(pattern, self.text, re.DOTALL)
            
            for i, match in enumerate(matches):
                algorithm_name = match.group(1).strip()
                algorithm_text = match.group(2).strip()
                
                # Extract steps
                steps = []
                for line in algorithm_text.split('\n'):
                    line = line.strip()
                    if line:
                        # Remove line numbers or bullet points
                        line = re.sub(r'^\d+[\.:]|\s*•\s*', '', line).strip()
                        steps.append(line)
                
                algorithm_id = f"Algorithm_{i+1}"
                
                # Find location (page number)
                location = "Unknown"
                if PYMUPDF_AVAILABLE:
                    try:
                        doc = fitz.open(self.paper_path)
                        for page_num, page in enumerate(doc):
                            page_text = page.get_text()
                            if algorithm_name in page_text and any(step in page_text for step in steps[:2]):
                                location = f"Page {page_num + 1}"
                                break
                        doc.close()
                    except Exception as e:
                        logger.warning(f"Failed to find algorithm location: {e}")
                
                # Add algorithm to list
                algorithm_info = {
                    "id": algorithm_id,
                    "name": algorithm_name,
                    "steps": steps,
                    "location": location
                }
                
                algorithms.append(algorithm_info)
                
                # Save algorithm as text file
                text_path = os.path.join(algorithms_dir, f"{algorithm_id}.txt")
                with open(text_path, "w") as f:
                    f.write(f"{algorithm_name}\n\n")
                    for step in steps:
                        f.write(f"- {step}\n")
                
                # Save algorithm info as JSON
                json_path = os.path.join(algorithms_dir, f"{algorithm_id}.json")
                with open(json_path, "w") as f:
                    json.dump(algorithm_info, f, indent=4)
        
        self.extracted_info["algorithms"] = algorithms
        return algorithms
    
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
        
        # Extract tables
        self.extract_tables()
        
        # Extract images
        self.extract_images()
        
        # Extract algorithms
        self.extract_algorithms()
        
        logger.info("Completed extraction of all information from paper")
        
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
    parser.add_argument("--output_dir", type=str, default="paper_extraction", help="Directory to save extracted information and files")
    parser.add_argument("--output", type=str, default="extracted_info.json", help="Filename to save the extracted information")
    args = parser.parse_args()
    
    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Parse the paper
    parser = PaperParser(args.paper_path, output_dir=args.output_dir)
    parser.extract_all_info()
    
    # Save the extracted information
    output_path = os.path.join(args.output_dir, args.output)
    parser.save_extracted_info(output_path)
    
    logger.info(f"Paper extraction completed. Results saved to {args.output_dir}")
    logger.info(f"- Extracted information: {output_path}")
    logger.info(f"- Tables: {os.path.join(args.output_dir, 'extracted_tables')}")
    logger.info(f"- Images: {os.path.join(args.output_dir, 'extracted_images')}")
    logger.info(f"- Algorithms: {os.path.join(args.output_dir, 'extracted_algorithms')}")


if __name__ == "__main__":
    main()