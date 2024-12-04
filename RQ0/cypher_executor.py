import re

from helpers.neo4j_client import Neo4jClient

def extract_cypher(text: str) -> str:
    # The pattern to find Cypher code enclosed in triple backticks
    pattern = r"```(.*?)```"

    # Find all matches in the input text
    matches = re.findall(pattern, text, re.DOTALL)

    return matches[-1] if matches else text


def cypher_executor(query, neo4j_uri, neo4j_user, neo4j_password):
    neo_client = Neo4jClient(neo4j_uri, neo4j_user, neo4j_password)
    result = neo_client.execute_query(query)
    neo_client.close()
    return result


def execute_query(query, neo4j_uri, neo4j_user, neo4j_password):
    cypher_query = extract_cypher(query)
    results = cypher_executor(cypher_query, neo4j_uri, neo4j_user, neo4j_password)
    return results, cypher_query