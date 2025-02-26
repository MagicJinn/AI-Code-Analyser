import os
import shutil
import requests
import json
import re

# Configuration
OLLAMA_API_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "deepseek-r1:14b"  # Update with the appropriate model name
CODE_FOLDER = "Code"
GRADED_FOLDER = "Graded"
CODE_TO_ANALYZE = ".cs"
CATEGORIES = ["Severe", "Important", "Medium", "Minimal"]
PROMPT_TEMPLATE = """
Analyze the following code snippet and grade its performance impact as one of the following categories:
- Severe: Major performance issues, high computational cost.
- Important: Significant performance issues.
- Medium: Some performance inefficiencies but not critical.
- Minimal: Little to no performance concerns.
Please also consider the context of the code and its intended use case. If the code looks like it would rarely be run, it may be categorized as Minimal.
If the code is negligible, and you wish to cut the response short, you can respond with "FULLSTOP" and nothing else.

If the category is anything other than "FULLSTOP", please provide a brief explanation of the performance concerns.

Code:
{code}
"""

def clean_response(response):
    """Removes <think>...</think> from the response but keeps everything else."""
    return re.sub(r"<think>.*?</think>", "", response, flags=re.DOTALL).strip()

def analyze_code(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        code_content = file.read()

    payload = {
        "model": MODEL_NAME,
        "prompt": PROMPT_TEMPLATE.format(code=code_content),
        "stream": False
    }

    response = requests.post(OLLAMA_API_URL, json=payload)
    response_data = response.json()

    full_response = response_data.get("response", "FULL_STOP").strip()

    # Remove <think>...</think> but keep the rest
    cleaned_response = clean_response(full_response)

    # Extract the grading category from the cleaned response
    match = re.search(r"(Severe|Important|Medium|Minimal|FULL_STOP)", cleaned_response, re.IGNORECASE)
    category = match.group(1) if match else "Minimal"
    # print the category
    print(f"Category: {category}")
    # Save cleaned response (without <think>) only for Severe, Important, and Medium
    if category in ["Severe", "Important", "Medium"]:
        return category, cleaned_response
    else:
        return category, None  # Ignore response for Minimal/FULL_STOP

def copy_code(file_path, category, ai_response=None):
    """Copies the file to the corresponding category folder and logs the response if needed."""
    category_path = os.path.join(GRADED_FOLDER, category)
    os.makedirs(category_path, exist_ok=True)
    shutil.copy(file_path, category_path)

    if ai_response:
        response_filename = f"{os.path.basename(file_path)}_response.txt"
        response_path = os.path.join(category_path, response_filename)
        with open(response_path, "w", encoding="utf-8") as f:
            f.write(ai_response)

def process_folder(folder_path):
    """Recursively processes all files in a folder."""
    for root, _, files in os.walk(folder_path):
        for file in files:
            file_path = os.path.join(root, file)
            if file_path.endswith(CODE_TO_ANALYZE):  # Adjust for relevant file types
                category, ai_response = analyze_code(file_path)
                copy_code(file_path, category, ai_response)

if __name__ == "__main__":
    os.makedirs(GRADED_FOLDER, exist_ok=True)
    process_folder(CODE_FOLDER)
    print("Code analysis and categorization completed.")
