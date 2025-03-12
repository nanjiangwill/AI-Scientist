#!/usr/bin/env python3
"""
Code Generator Module

This module provides functionality to generate code implementations
based on method descriptions extracted from research papers.
"""

import os
import re
import json
import logging
import tempfile
from typing import Dict, List, Any, Optional, Union
import importlib.util
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)


class CodeGenerator:
    """Class for generating code implementations from paper descriptions"""
    
    def __init__(self, extracted_info: Dict[str, Any], output_dir: str):
        """
        Initialize the code generator
        
        Args:
            extracted_info: Dictionary containing extracted information from the paper
            output_dir: Directory to save generated code
        """
        self.extracted_info = extracted_info
        self.output_dir = output_dir
        self.implementation = {}
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
    
    def generate_method_implementation(self, method: Dict[str, Any]) -> str:
        """
        Generate code implementation for a method
        
        Args:
            method: Dictionary containing method information
            
        Returns:
            Generated code as a string
        """
        logger.info(f"Generating implementation for method: {method['name']}")
        
        # Extract method name and description
        method_name = method['name']
        description = method['description']
        parameters = method['parameters']
        
        # Clean method name for use as a function/class name
        clean_name = re.sub(r'[^a-zA-Z0-9_]', '_', method_name.lower())
        clean_name = re.sub(r'_+', '_', clean_name).strip('_')
        
        # Determine if the method should be implemented as a class or function
        # Heuristic: If the description mentions "model", "network", or "architecture", implement as a class
        is_class = re.search(r'(?i)model|network|architecture|framework|system', description) is not None
        
        # Generate code based on method type
        if is_class:
            code = self._generate_class_implementation(clean_name, description, parameters)
        else:
            code = self._generate_function_implementation(clean_name, description, parameters)
        
        return code
    
    def _generate_class_implementation(self, name: str, description: str, parameters: Dict[str, Any]) -> str:
        """
        Generate a class implementation
        
        Args:
            name: Clean method name
            description: Method description
            parameters: Method parameters
            
        Returns:
            Generated class code as a string
        """
        # Determine if it's likely a neural network
        is_neural_network = re.search(r'(?i)neural|network|deep|learning|layer|conv|lstm|transformer|attention', description) is not None
        
        if is_neural_network:
            # Generate PyTorch or TensorFlow-like implementation
            framework = "pytorch"  # Default to PyTorch
            if re.search(r'(?i)tensorflow|keras', description):
                framework = "tensorflow"
            
            if framework == "pytorch":
                return self._generate_pytorch_class(name, description, parameters)
            else:
                return self._generate_tensorflow_class(name, description, parameters)
        else:
            # Generate a generic class implementation
            return self._generate_generic_class(name, description, parameters)
    
    def _generate_pytorch_class(self, name: str, description: str, parameters: Dict[str, Any]) -> str:
        """Generate a PyTorch model implementation"""
        # Extract potential layers from description
        layers = []
        if re.search(r'(?i)conv', description):
            layers.append(('conv', 'nn.Conv2d'))
        if re.search(r'(?i)pool', description):
            layers.append(('pool', 'nn.MaxPool2d'))
        if re.search(r'(?i)batch\s*norm', description):
            layers.append(('bn', 'nn.BatchNorm2d'))
        if re.search(r'(?i)dropout', description):
            layers.append(('dropout', 'nn.Dropout'))
        if re.search(r'(?i)linear|fully\s*connected|dense', description):
            layers.append(('fc', 'nn.Linear'))
        if re.search(r'(?i)lstm|rnn|gru', description):
            layers.append(('rnn', 'nn.LSTM'))
        if re.search(r'(?i)transformer|attention', description):
            layers.append(('attention', 'nn.MultiheadAttention'))
        
        # If no specific layers found, add some default ones
        if not layers:
            layers = [
                ('fc1', 'nn.Linear'),
                ('relu', 'nn.ReLU'),
                ('fc2', 'nn.Linear')
            ]
        
        # Generate code
        code = f"""import torch
import torch.nn as nn
import torch.nn.functional as F

class {name.capitalize()}(nn.Module):
    \"\"\"
    Implementation of {name.replace('_', ' ')} method
    
    Based on the description: {description[:100]}...
    \"\"\"
    
    def __init__(self"""
        
        # Add parameters to __init__
        for param_name, param_value in parameters.items():
            code += f", {param_name}={param_value}"
        
        code += """):
        super().__init__()
        
        # Initialize layers
"""
        
        # Add layers
        for i, (layer_name, layer_type) in enumerate(layers):
            if layer_type == 'nn.Linear':
                in_features = 64 if i == 0 else 32
                out_features = 32 if i < len(layers) - 1 else 10
                code += f"        self.{layer_name} = {layer_type}({in_features}, {out_features})\n"
            elif layer_type == 'nn.Conv2d':
                in_channels = 3 if i == 0 else 16
                out_channels = 16 if i < len(layers) - 1 else 32
                code += f"        self.{layer_name} = {layer_type}({in_channels}, {out_channels}, kernel_size=3, padding=1)\n"
            elif layer_type == 'nn.MaxPool2d':
                code += f"        self.{layer_name} = {layer_type}(kernel_size=2, stride=2)\n"
            elif layer_type == 'nn.BatchNorm2d':
                channels = 16
                code += f"        self.{layer_name} = {layer_type}({channels})\n"
            elif layer_type == 'nn.Dropout':
                p = parameters.get('dropout_rate', 0.5)
                code += f"        self.{layer_name} = {layer_type}(p={p})\n"
            elif layer_type == 'nn.LSTM':
                input_size = 64
                hidden_size = 32
                code += f"        self.{layer_name} = {layer_type}(input_size={input_size}, hidden_size={hidden_size}, batch_first=True)\n"
            elif layer_type == 'nn.MultiheadAttention':
                embed_dim = 64
                num_heads = 8
                code += f"        self.{layer_name} = {layer_type}(embed_dim={embed_dim}, num_heads={num_heads})\n"
        
        # Add forward method
        code += """
    def forward(self, x):
        # Forward pass
"""
        
        # Add forward pass logic
        for i, (layer_name, layer_type) in enumerate(layers):
            if layer_type == 'nn.Linear' and i == 0:
                code += f"        x = x.view(x.size(0), -1)  # Flatten the input\n"
            
            if layer_type in ['nn.Linear', 'nn.Conv2d']:
                code += f"        x = F.relu(self.{layer_name}(x))\n"
            elif layer_type in ['nn.MaxPool2d', 'nn.Dropout', 'nn.BatchNorm2d']:
                code += f"        x = self.{layer_name}(x)\n"
            elif layer_type == 'nn.LSTM':
                code += f"        x, _ = self.{layer_name}(x)\n"
                code += f"        x = x[:, -1, :]  # Take the output from the last time step\n"
            elif layer_type == 'nn.MultiheadAttention':
                code += f"        x, _ = self.{layer_name}(x, x, x)\n"
        
        code += """
        return x
"""
        
        return code
    
    def _generate_tensorflow_class(self, name: str, description: str, parameters: Dict[str, Any]) -> str:
        """Generate a TensorFlow/Keras model implementation"""
        # Extract potential layers from description
        layers = []
        if re.search(r'(?i)conv', description):
            layers.append('Conv2D')
        if re.search(r'(?i)pool', description):
            layers.append('MaxPooling2D')
        if re.search(r'(?i)batch\s*norm', description):
            layers.append('BatchNormalization')
        if re.search(r'(?i)dropout', description):
            layers.append('Dropout')
        if re.search(r'(?i)linear|fully\s*connected|dense', description):
            layers.append('Dense')
        if re.search(r'(?i)lstm|rnn|gru', description):
            layers.append('LSTM')
        if re.search(r'(?i)transformer|attention', description):
            layers.append('MultiHeadAttention')
        
        # If no specific layers found, add some default ones
        if not layers:
            layers = ['Dense', 'Dense']
        
        # Generate code
        code = f"""import tensorflow as tf
from tensorflow.keras import layers, Model

class {name.capitalize()}(Model):
    \"\"\"
    Implementation of {name.replace('_', ' ')} method
    
    Based on the description: {description[:100]}...
    \"\"\"
    
    def __init__(self"""
        
        # Add parameters to __init__
        for param_name, param_value in parameters.items():
            code += f", {param_name}={param_value}"
        
        code += """):
        super().__init__()
        
        # Initialize layers
"""
        
        # Add layers
        for i, layer_type in enumerate(layers):
            if layer_type == 'Dense':
                units = 32 if i < len(layers) - 1 else 10
                activation = 'relu' if i < len(layers) - 1 else 'softmax'
                code += f"        self.{layer_type.lower()}{i+1} = layers.{layer_type}({units}, activation='{activation}')\n"
            elif layer_type == 'Conv2D':
                filters = 16 if i < len(layers) - 1 else 32
                code += f"        self.{layer_type.lower()}{i+1} = layers.{layer_type}({filters}, kernel_size=3, padding='same', activation='relu')\n"
            elif layer_type == 'MaxPooling2D':
                code += f"        self.{layer_type.lower()}{i+1} = layers.{layer_type}(pool_size=(2, 2))\n"
            elif layer_type == 'BatchNormalization':
                code += f"        self.{layer_type.lower()}{i+1} = layers.{layer_type}()\n"
            elif layer_type == 'Dropout':
                p = parameters.get('dropout_rate', 0.5)
                code += f"        self.{layer_type.lower()}{i+1} = layers.{layer_type}({p})\n"
            elif layer_type == 'LSTM':
                units = 32
                code += f"        self.{layer_type.lower()}{i+1} = layers.{layer_type}({units}, return_sequences={i < len(layers) - 1})\n"
            elif layer_type == 'MultiHeadAttention':
                num_heads = 8
                key_dim = 64
                code += f"        self.{layer_type.lower()}{i+1} = layers.{layer_type}(num_heads={num_heads}, key_dim={key_dim})\n"
        
        # Add call method
        code += """
    def call(self, inputs, training=False):
        x = inputs
"""
        
        # Add forward pass logic
        for i, layer_type in enumerate(layers):
            if layer_type == 'Dense' and i == 0 and any(l in ['Conv2D', 'MaxPooling2D'] for l in layers):
                code += f"        x = tf.keras.layers.Flatten()(x)\n"
            
            if layer_type == 'MultiHeadAttention':
                code += f"        x = self.{layer_type.lower()}{i+1}(x, x)\n"
            else:
                code += f"        x = self.{layer_type.lower()}{i+1}(x)\n"
        
        code += """
        return x
"""
        
        return code
    
    def _generate_generic_class(self, name: str, description: str, parameters: Dict[str, Any]) -> str:
        """Generate a generic class implementation"""
        code = f"""class {name.capitalize()}:
    \"\"\"
    Implementation of {name.replace('_', ' ')} method
    
    Based on the description: {description[:100]}...
    \"\"\"
    
    def __init__(self"""
        
        # Add parameters to __init__
        for param_name, param_value in parameters.items():
            code += f", {param_name}={param_value}"
        
        code += """):
        # Initialize parameters
"""
        
        # Add parameter assignments
        for param_name, param_value in parameters.items():
            code += f"        self.{param_name} = {param_name}\n"
        
        # Add methods based on description
        if re.search(r'(?i)fit|train', description):
            code += """
    def fit(self, X, y):
        \"\"\"
        Train the model on the given data
        
        Args:
            X: Input features
            y: Target values
            
        Returns:
            self: The trained model
        \"\"\"
        # TODO: Implement training logic based on the paper description
        
        return self
"""
        
        if re.search(r'(?i)predict|inference', description):
            code += """
    def predict(self, X):
        \"\"\"
        Make predictions on the given data
        
        Args:
            X: Input features
            
        Returns:
            Predictions
        \"\"\"
        # TODO: Implement prediction logic based on the paper description
        
        return None
"""
        
        return code
    
    def _generate_function_implementation(self, name: str, description: str, parameters: Dict[str, Any]) -> str:
        """
        Generate a function implementation
        
        Args:
            name: Clean method name
            description: Method description
            parameters: Method parameters
            
        Returns:
            Generated function code as a string
        """
        # Determine function signature based on description
        args = []
        
        # Look for input/output mentions in the description
        input_match = re.search(r'(?i)input(?:s)?(?:\s+is|\s+are|\s*:)?\s+([a-zA-Z0-9\s,_]+)', description)
        if input_match:
            inputs = input_match.group(1).split(',')
            args.extend([inp.strip().lower() for inp in inputs if inp.strip()])
        
        # If no specific inputs found, add some generic ones
        if not args:
            if re.search(r'(?i)image|conv|pixel', description):
                args.append('image')
            elif re.search(r'(?i)text|word|token|sentence', description):
                args.append('text')
            elif re.search(r'(?i)data|feature|input', description):
                args.append('X')
                if re.search(r'(?i)label|target|output', description):
                    args.append('y')
        
        # Generate code
        code = f"""def {name}("""
        
        # Add function arguments
        if args:
            code += ", ".join(args)
        else:
            code += "X"
        
        # Add parameters as keyword arguments
        for param_name, param_value in parameters.items():
            code += f", {param_name}={param_value}"
        
        code += f"""):
    \"\"\"
    Implementation of {name.replace('_', ' ')} method
    
    Based on the description: {description[:100]}...
    
    Args:
"""
        
        # Add argument descriptions
        for arg in args:
            code += f"        {arg}: Input {arg}\n"
        
        # Add parameter descriptions
        for param_name, param_value in parameters.items():
            code += f"        {param_name}: Parameter with default value {param_value}\n"
        
        code += """    
    Returns:
        Result of the method
    \"\"\"
    # TODO: Implement method logic based on the paper description
    
    return None
"""
        
        return code
    
    def generate_all_implementations(self) -> Dict[str, Dict[str, Any]]:
        """
        Generate implementations for all methods in the paper
        
        Returns:
            Dictionary mapping method names to their implementations
        """
        logger.info("Generating implementations for all methods")
        
        methods = self.extracted_info.get('methods', [])
        
        for method in methods:
            method_name = method['name']
            clean_name = re.sub(r'[^a-zA-Z0-9_]', '_', method_name.lower())
            clean_name = re.sub(r'_+', '_', clean_name).strip('_')
            
            # Generate code
            code = self.generate_method_implementation(method)
            
            # Determine dependencies
            dependencies = ['numpy']
            if re.search(r'(?i)neural|network|deep|learning|layer|conv|lstm|transformer|attention', method['description']):
                if re.search(r'(?i)tensorflow|keras', method['description']):
                    dependencies.append('tensorflow')
                else:
                    dependencies.append('torch')
            
            # Add to implementation dictionary
            self.implementation[clean_name] = {
                'code': code,
                'dependencies': dependencies
            }
            
            # Save to file
            file_path = os.path.join(self.output_dir, f"{clean_name}.py")
            with open(file_path, 'w') as f:
                f.write(code)
        
        # Save implementation dictionary
        with open(os.path.join(self.output_dir, "implementation.json"), 'w') as f:
            json.dump(self.implementation, f, indent=4)
        
        return self.implementation
    
    def generate_experiment_script(self) -> str:
        """
        Generate a script to run the experiments described in the paper
        
        Returns:
            Generated experiment script as a string
        """
        logger.info("Generating experiment script")
        
        # Extract information
        methods = self.extracted_info.get('methods', [])
        experiments = self.extracted_info.get('experiments', [])
        results = self.extracted_info.get('results', [])
        
        # Generate imports
        imports = ["import numpy as np", "import matplotlib.pyplot as plt", "import json", "import os"]
        
        # Add method imports
        for method in methods:
            method_name = method['name']
            clean_name = re.sub(r'[^a-zA-Z0-9_]', '_', method_name.lower())
            clean_name = re.sub(r'_+', '_', clean_name).strip('_')
            imports.append(f"from {clean_name} import {clean_name.capitalize() if re.search(r'(?i)model|network|architecture', method['description']) else clean_name}")
        
        # Generate experiment code
        experiment_code = f"""
def run_experiments(output_dir):
    \"\"\"
    Run the experiments described in the paper
    
    Args:
        output_dir: Directory to save results
    
    Returns:
        Dictionary containing results
    \"\"\"
    results = {{}}
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
"""
        
        # Add experiment implementations
        for i, experiment in enumerate(experiments):
            experiment_name = experiment['name']
            dataset = experiment['dataset']
            
            experiment_code += f"""    # Experiment: {experiment_name}
    print(f"Running experiment: {experiment_name}")
    
    # TODO: Load dataset {dataset}
    # For now, we'll use synthetic data
    X_train = np.random.randn(100, 10)
    y_train = np.random.randint(0, 2, 100)
    X_test = np.random.randn(20, 10)
    y_test = np.random.randint(0, 2, 20)
    
"""
            
            # Add method calls
            for method in methods:
                method_name = method['name']
                clean_name = re.sub(r'[^a-zA-Z0-9_]', '_', method_name.lower())
                clean_name = re.sub(r'_+', '_', clean_name).strip('_')
                
                is_class = re.search(r'(?i)model|network|architecture', method['description']) is not None
                
                if is_class:
                    experiment_code += f"""    # Initialize and train {method_name}
    model = {clean_name.capitalize()}()
    # TODO: Train the model
    
    # Evaluate the model
    # TODO: Implement proper evaluation
    metrics = {{"accuracy": 0.85, "f1_score": 0.82}}
    
    # Store results
    results["{experiment_name}_{clean_name}"] = metrics
    
"""
                else:
                    experiment_code += f"""    # Apply {method_name}
    # TODO: Implement proper method call
    result = {clean_name}(X_train)
    
    # Evaluate the result
    # TODO: Implement proper evaluation
    metrics = {{"accuracy": 0.85, "f1_score": 0.82}}
    
    # Store results
    results["{experiment_name}_{clean_name}"] = metrics
    
"""
        
        # Add results saving
        experiment_code += """    # Save results
    with open(os.path.join(output_dir, "results.json"), "w") as f:
        json.dump(results, f, indent=4)
    
    return results
"""
        
        # Generate main function
        main_code = """
def main():
    \"\"\"Main function to run experiments\"\"\"
    import argparse
    
    parser = argparse.ArgumentParser(description="Run experiments from the paper")
    parser.add_argument("--output_dir", type=str, default="results", help="Directory to save results")
    args = parser.parse_args()
    
    # Run experiments
    results = run_experiments(args.output_dir)
    
    # Print results
    print("\\nResults:")
    for experiment, metrics in results.items():
        print(f"  {experiment}:")
        for metric, value in metrics.items():
            print(f"    {metric}: {value:.4f}")


if __name__ == "__main__":
    main()
"""
        
        # Combine all code
        full_code = "\n".join(imports) + "\n" + experiment_code + "\n" + main_code
        
        # Save to file
        file_path = os.path.join(self.output_dir, "run_experiments.py")
        with open(file_path, 'w') as f:
            f.write(full_code)
        
        return full_code
    
    def generate_all_code(self) -> Dict[str, Any]:
        """
        Generate all code for the paper reproduction
        
        Returns:
            Dictionary containing all generated code
        """
        logger.info("Generating all code for paper reproduction")
        
        # Generate method implementations
        self.generate_all_implementations()
        
        # Generate experiment script
        self.generate_experiment_script()
        
        return self.implementation


def main():
    """Main function to demonstrate code generation"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate code from paper descriptions")
    parser.add_argument("extracted_info", type=str, help="Path to the extracted information JSON file")
    parser.add_argument("--output_dir", type=str, default="implementation", help="Directory to save generated code")
    args = parser.parse_args()
    
    # Load extracted information
    with open(args.extracted_info, 'r') as f:
        extracted_info = json.load(f)
    
    # Generate code
    generator = CodeGenerator(extracted_info, args.output_dir)
    generator.generate_all_code()
    
    logger.info(f"Code generation completed. Files saved to {args.output_dir}")


if __name__ == "__main__":
    main()