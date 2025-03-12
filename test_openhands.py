"""
Test script for OpenHands integration.

This script tests the OpenHands wrapper by creating a simple coder instance
and running a basic prompt.
"""

import os
import sys
from ai_scientist.openhands_wrapper import create_openhands_coder

# For backward compatibility
class InputOutput:
    def __init__(self, yes=False, chat_history_file=None):
        self.yes = yes
        self.chat_history_file = chat_history_file

# For backward compatibility
class Model:
    def __init__(self, name):
        self.name = name

def main():
    """
    Main function to test OpenHands integration.
    """
    print("Testing OpenHands integration...")
    
    # Create a test file
    test_file = "test_file.py"
    with open(test_file, "w") as f:
        f.write("# This is a test file\n\ndef hello_world():\n    pass\n")
    
    # Create a coder instance
    model = Model("gpt-4o")
    io = InputOutput(yes=True, chat_history_file="test_chat_history.txt")
    
    coder = create_openhands_coder(
        main_model=model,
        fnames=[test_file],
        io=io,
        stream=False,
        use_git=False,
        edit_format="diff",
    )
    
    # Run a simple prompt
    prompt = "Please implement the hello_world function to print 'Hello, World!'"
    print(f"Sending prompt: {prompt}")
    
    response = coder.run(prompt)
    print(f"Response: {response}")
    
    # Check if the file was modified
    with open(test_file, "r") as f:
        content = f.read()
    
    print(f"Modified file content:\n{content}")
    
    # Clean up
    os.remove(test_file)
    if os.path.exists("test_chat_history.txt"):
        os.remove("test_chat_history.txt")
    
    print("Test completed.")

if __name__ == "__main__":
    main()