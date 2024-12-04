import os
import sys
import pandas as pd

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.abspath(os.path.join(current_dir, '..'))
sys.path.insert(0, parent_dir)

from cypher_generator.cypher_generator import cypher_generator
from query_executor.cypher_executor import execute_query
from response_generator.response_generator import generate_response

def get_parameters(repo_name):
    # df = pd.read_csv('repo_neo4j_map.csv')
    df = pd.read_csv('play_repo_neo4j_map.csv')
    repo_row = df[df['Repository'] == repo_name]
    if not repo_row.empty:
        url = repo_row['Neo4j_DB'].values[0]
        password = repo_row['Password'].values[0]
        return url, password
    else:
        return None, None
    
def run_step_2(repo_name, query, no_exec, learning_type):
    """GETTING THE NEO4J URI, USER, AND PASSWORD"""
    # neo4j_uri = os.getenv("NEO4J_URI")
    # neo4j_user = os.getenv("NEO4J_USER")
    # neo4j_password = os.getenv("NEO4J_PASSWORD")

    neo4j_user = "neo4j"
    neo4j_uri, neo4j_password = get_parameters(repo_name)

    """RUN CYPHER GENERATOR PASSING THE NATURAL LANGUAGE QUESTION"""
    cypher_text = cypher_generator(repo_name, query, no_exec, learning_type)

    """RUN QUERY EXECUTOR PASSING THE GENERATED CYPHER QUERY"""
    results, cypher_query = execute_query(cypher_text, neo4j_uri, neo4j_user, neo4j_password)

    response = generate_response(query, results, cypher_query)

    return response, cypher_text, cypher_query, results


"""RUNNING EXAMPLE"""
# repo_name = "vue"
repo_name = "repochat.tool"
# query = "who added the most lines of code in December, 2023?"
query = "which commit introduced bug 18"
no_exec = 0
learning_type = 'fs_cot'

response, cypher_text, cypher_query, results = run_step_2(repo_name, query, no_exec, learning_type)

print(f'Cypher Text: {cypher_text} \n\nCypher Query: {cypher_query} \n\nResults: {results} \n\nResponse: {response}')