# followthecode
follow the code shows a few metrics on the selected repository

# Repo Analyzer

A simple Python application that uses **PyDriller** to analyze a Git repository (commits from the last 90 days) via a minimal **Tkinter GUI**. After selecting the repository folder, the script outputs metrics to multiple **CSV files** in an `analysis_results` folder.

---

## Table of Contents

- [Features](#features)
- [Requirements](#requirements)
- [Installation](#installation)
- [Usage](#Usage)
- [Metrics Generated](#metrics-generated)
- [CSV Outputs](#csv-outputs)
- [License](#license)

---

## Features

- **Tkinter GUI** to select your local Git repository folder.
- **Analyzes commits** in the last 90 days.
- **Generates CSV files** with various metrics:
  - Commits per author  
  - Most modified files  
  - Files with the most authors  
  - Lines added/removed by author  
  - Code churn (added + removed) by author  
  - Commits by day of the week  
  - Average time between commits (in hours) for each author

---

## Requirements

1. **Python 3.7+**  
   - PyDriller generally supports Python 3.7 and above.  
   - If you encounter issues with Python 3.12 (since it’s very new), consider using a slightly older version (3.9, 3.10, or 3.11).
2. **pip** for installing dependencies.
3. **Git** installed (so that the `.git` directory and data can be read properly).
4. **Tkinter**  
   - Often included by default. If not, install for your specific OS:
     - On Debian/Ubuntu: `sudo apt-get install python3-tk`
     - On Windows/macOS: Usually already available.

---

## Installation
1. **Clone** or download this repository.
2. **Install dependencies**:
   ```bash
   pip install --upgrade pip
   pip install pydriller

If you’re using a virtual environment, ensure it’s activated before installing.

Verify that PyDriller is installed correctly:
    ```bash
    python -m pip show pydriller

This command should display the PyDriller package details, including its version and installation path.

---

## Usage
**Open a terminal** (Command Prompt, PowerShell, or similar) in the project folder.
Run the script:
    ```bash
    python followthecode.py
A Tkinter window will appear:
Click "Select Repository".
Choose the folder that contains your .git directory.
The script will analyze the Git repository (for commits in the last 90 days).
When the analysis is finished, a popup message will inform you where the CSV files are stored.

**By default, the script creates an analysis_results folder inside the selected repository folder.**

---

## Metrics Generated
1. Number of commits per author – how many commits each author has made in the last 90 days.
2. Most modified files – shows the top 10 files with the highest number of modifications.
3. Files with the most authors – top 10 files that have been touched by the largest number of different authors.
4. Lines added/removed by author – total lines added and removed, aggregated by author.
5. Code churn – lines added + lines removed by each author, often used as a measure of overall activity.
6. Commits by weekday – how many commits occur on Monday, Tuesday, etc.
7. Average time between commits – for each author, the mean interval (in hours) between consecutive commits.

---

## CSV Outputs**
After the script completes, you should see multiple CSV files in analysis_results (within the chosen repo). Each file corresponds to one of the metrics:

authors_commits.csv
most_modified_files.csv
files_authors.csv
added_lines_by_author.csv
removed_lines_by_author.csv
code_churn_by_author.csv
commits_by_weekday.csv
average_commit_time_by_author.csv

Feel free to open these in Excel, Google Sheets, or any other tool for further analysis.

---

## License
This project is provided as a simple demonstration. You are free to use, modify, and distribute it under your own terms or any open-source license of your choice. If you base your work on this repository, a reference or attribution is appreciated but not required.

---