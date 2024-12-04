import os
from langchain_openai import ChatOpenAI
import concurrent.futures
import json

def generate_response(question, result, cypher_query, timeout=30):
    llm = ChatOpenAI(model="gpt-4o",
                    temperature=0.7,
                    max_tokens=None,
                    timeout=None)

    current_dir = os.path.dirname(os.path.abspath(__file__))
    schema_path = os.path.join(current_dir, 'const', 'schema.txt')
    # schema_path = f"const/schema.txt"
    with open(schema_path, "r") as file:
        graph_schema = file.read()

    prompt_path = os.path.join(current_dir, 'const', 'prompt_template.txt')
    # prompt_path = f"const/prompt_template.txt"
    with open(prompt_path, "r") as file:
        prompt_template = file.read()

    prompt = prompt_template.format(schema=graph_schema, graph_query=cypher_query, context=result, question=question)
        
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future = executor.submit(llm.invoke, prompt)
        try:
            response = future.result(timeout=timeout)
            return response.content
        except concurrent.futures.TimeoutError:
            raise TimeoutError(f"Invocation timed out after {timeout} seconds")
        except Exception as e:
            raise e