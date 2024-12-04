import os
import sys
import pandas as pd

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.abspath(os.path.join(current_dir, '..'))
sys.path.insert(0, parent_dir)

from cypher_generator import cypher_generator
from cypher_executor import execute_query

def get_parameters(repo_name):
    df = pd.read_csv('repo_neo4j_map.csv')
    repo_row = df[df['Repository'] == repo_name]
    if not repo_row.empty:
        url = repo_row['Neo4j_DB'].values[0]
        password = repo_row['Password'].values[0]
        return url, password
    else:
        return None, None
    
def run_rq0(model, repo_name, query):
    """GETTING THE NEO4J URI, USER, AND PASSWORD"""
    neo4j_user = "neo4j"
    neo4j_uri, neo4j_password = get_parameters(repo_name)

    """RUN CYPHER GENERATOR PASSING THE NATURAL LANGUAGE QUESTION"""
    cypher_text = cypher_generator(model, repo_name, query)

    """RUN QUERY EXECUTOR PASSING THE GENERATED CYPHER QUERY"""
    results, cypher_query = execute_query(cypher_text, neo4j_uri, neo4j_user, neo4j_password)

    return cypher_text, cypher_query, results


"""RUNNING EXAMPLE"""
models = ["gpt-4o", "llama3", "claude3_5"]
repo_name = "vue"
query = "who added the most lines of code in December, 2023?"

for model in models:
    model = "claude3_5"
    print(f"Running RQ0 for {model}")
    cypher_text, cypher_query, results = run_rq0(model, repo_name, query)

    print(f'Cypher Text: {cypher_text} \n\nCypher Query: {cypher_query} \n\nResults: {results}')