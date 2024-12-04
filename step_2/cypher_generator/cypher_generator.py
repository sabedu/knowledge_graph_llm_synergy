import os
from langchain_openai import ChatOpenAI
from datetime import datetime, timezone
import json

def cypher_generator(repo_name, query, iter, learning_type):
    # Load the prompt templates
    current_dir = os.path.dirname(os.path.abspath(__file__))
    schema_path = os.path.join(current_dir, 'const', 'schema.txt')
    # schema_path = f"const/schema.txt"
    with open(schema_path, "r") as file:
        graph_schema = file.read()

    zs_prompt_path = os.path.join(current_dir, 'const', 'zs_prompt_template.txt')
    # zs_prompt_path = f"const/zs_prompt_template.txt"
    with open(zs_prompt_path, "r") as file:
        zs_prompt_template = file.read()

    zs_cot_prompt_path = os.path.join(current_dir, 'const', 'zs_cot_prompt_template.txt')
    # zs_cot_prompt_path = f"const/zs_cot_prompt_template.txt"
    with open(zs_cot_prompt_path, "r") as file:
        zs_cot_prompt_template = file.read()

    fs_cot_prompt_path = os.path.join(current_dir, 'const', 'fs_cot_prompt_template.txt')
    # fs_cot_prompt_path = f"const/fs_cot_prompt_template.txt"
    with open(fs_cot_prompt_path, "r") as file:
        fs_cot_prompt_template = file.read()

    if learning_type == "zs":
        prompt_template = zs_prompt_template
    elif learning_type == "zs_cot":
        prompt_template = zs_cot_prompt_template
    elif learning_type == "fs_cot":
        prompt_template = fs_cot_prompt_template
    else:
        print("Invalid learning type")

    current_date = datetime.now(timezone.utc).replace(microsecond=0).isoformat() + 'Z'
    current_date = "2024-08-26T00:00:00Z"
    prompt = prompt_template.format(schema=graph_schema, current_date=current_date, question=query)

    llm = ChatOpenAI(model="gpt-4o",
                 temperature=0,
                 max_tokens=None,
                 timeout=None)

    try:
        res = llm.invoke(prompt)
        response = res.content
    except Exception as e:
        print(f"Error for {query} in {repo_name} at iteration {iter}")
        print(f"Error: {e}")
        response = "Error"

    return response