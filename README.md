# **File Context Copier**

![Version](https://img.shields.io/badge/version-0.1.0-blue.svg)
![Security](https://img.shields.io/badge/security-hardened-green.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.8+-brightgreen.svg)
![Status](https://img.shields.io/badge/status-production%20ready-green.svg)
![Slash Commands](https://img.shields.io/badge/slash%20commands-20+-orange.svg)

A Python CLI tool for interactively selecting project files and folders to copy their contents into a single, clipboard-ready context or into structured output files.

It's the perfect developer utility for grabbing the context of a project to share with a colleague, feed to an AI, or archive.

## **Features**

* **Interactive TUI:** A Textual-based terminal user interface for easy file and folder selection.  
* **Directory Tree:** A navigable directory tree with checkboxes for quick selection.  
* **Smart Filtering:** Automatically ignores files and folders listed in your .gitignore file.  
* **Robust File Handling:** Gracefully skips binary files and other non-text content that can't be read.  
* **Flexible Output Modes:**  
  * Copy a combined context to the clipboard (default).  
  * Save the combined context to a single file.  
  * Save the context of each selected item to a separate file in a specified directory.  
* **Customizable File Types:** Choose to save output files as .md (default) or .txt.

## **Installation**

This project uses uv for package management.

1. **Clone the repository:**  
   git clone \<your-repo-url\>  
   cd file-context-copier

2. **Create a virtual environment:**  
   uv venv

3. **Activate the virtual environment:**  
   source .venv/bin/activate

4. **Install the project in editable mode:**  
   uv pip install \-e .

   The tool is now installed. You can run it using the fcc command from within the activated environment.

## **Usage**

Once the virtual environment is activated, you can use the fcc command.

#### **Basic Usage (Copy to Clipboard)**

To open the interactive selector in the current directory and copy the combined content of your selections to the clipboard, simply run:

fcc

#### **Targeting a Different Project**

To run the tool on a different project, pass its path as an argument:

fcc /path/to/another/project

*Example:*

fcc \~/Developer/Projects/Jarvis-Assistant

### **Output Options**

#### **Save to a Single File**

To save the combined context of all selected items into a single file:

fcc \--output-file context.md

#### **Save to a Directory (One File Per Selection)**

This is the most powerful feature for archiving or sharing complex contexts. It saves the context for each of your top-level selections into its own file inside a specified directory.

fcc \--output-dir /path/to/output/directory

*Example: Save context from two folders into \~/Developer/Resources/*

\# This will create src.md and tests.md inside the Resources folder  
fcc \--output-dir \~/Developer/Resources/

#### **Save as .txt Files**

When using \--output-dir, you can choose to save the files as .txt instead of the default .md.

fcc \--output-dir ./output \--as-txt

### **Deactivating the Environment**

When you are finished using the tool, you can deactivate the virtual environment:

deactivate  
