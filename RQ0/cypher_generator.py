import os
from langchain_openai import ChatOpenAI
from langchain_community.chat_models import ChatOllama
from anthropic import AnthropicVertex
from datetime import datetime, timezone
import json

def chat_claude35(system_prompt, prompt, repo_name):
    MODEL = "claude-3-5-sonnet@20240620"
    LOCATION = "us-east5"
    PROJECT_ID = "premium-summit-433817-r6"
    ENDPOINT = f"https://{LOCATION}-aiplatform.googleapis.com"

    try:
        client = AnthropicVertex(region=LOCATION, project_id=PROJECT_ID)

        message = client.messages.create(
            temperature=0.0,
            max_tokens=1024,
            system=system_prompt,
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            model=MODEL,
        )

        response = message.content[0].text
    except Exception as e:
            print(f"Error for {prompt} in {repo_name}")
            print(f"Error: {e}")
            response = "Error"
    return response

def cypher_generator(model, repo_name, query):
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

    prompt_template = zs_prompt_template
    
    current_date = datetime.now(timezone.utc).replace(microsecond=0).isoformat() + 'Z'
    current_date = "2024-08-26T00:00:00Z"
    prompt = prompt_template.format(schema=graph_schema, current_date=current_date, question=query)

    if model == "gpt-4o" or model == "llama3":
        if model == "gpt-4o":
            llm = ChatOpenAI(model="gpt-4o",
                    temperature=0,
                    max_tokens=None,
                    timeout=None)
        elif model == "llama3":
            llm = ChatOllama(model='llama3:8b',
                             temperature=0)
        try:
            res = llm.invoke(prompt)
            response = res.content
        except Exception as e:
            print(f"Error for {query} in {repo_name}")
            print(f"Error: {e}")
            response = "Error"
    
    elif model == "claude3_5":
        cld_prompt_path = os.path.join(current_dir, 'const', 'cluade_3_5_prompt_template.txt')
        with open(cld_prompt_path, "r") as file:
            prompt_template = file.read()
        system_prompt = prompt_template.format(schema=graph_schema, current_date=current_date)
        user_prompt = f'The question is: {query}'
        response = chat_claude35(system_prompt, user_prompt, repo_name)
    return response