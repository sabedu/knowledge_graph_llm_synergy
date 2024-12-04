import os
from logging import getLogger
from os.path import join

from graph_construction.graph_handler import GraphHandler
from helpers.neo4j_client import Neo4jClient
from helpers.data_handler import DataHandler

logger = getLogger(__name__)


def get_entities_path(current_working_dir, repo, entity):
    path = join(current_working_dir, f"data/{repo}/{repo}_{entity}.json")
    return path

def construct_graph(repo_url, neo4j_uri, neo4j_user, neo4j_password):
    repo = repo_url.split('/')[-1]
    current_working_dir = os.getcwd()
    collaborators_path = get_entities_path(current_working_dir, repo, 'collaborators')
    commits_path = get_entities_path(current_working_dir, repo, 'commits')
    issues_path = get_entities_path(current_working_dir, repo, 'issues')
    bic_path = get_entities_path(current_working_dir, repo, 'fixing_bic')

    logger.info("Creating graph for the first time")
    collaborators = DataHandler(collaborators_path).load_data()
    commits = DataHandler(commits_path).load_data()
    issues = DataHandler(issues_path).load_data()
    bics = DataHandler(bic_path).load_data()

    graph_handler = GraphHandler()
    graph_handler.add_nodes_and_edges(collaborators, commits, issues)

    if bics:
        graph_handler.add_bic_relationships(bics)

    for u, v, k in graph_handler.G.edges(keys=True):
        graph_handler.G[u][v][k]['label'] = k

    neo_client = Neo4jClient(neo4j_uri, neo4j_user, neo4j_password)
    neo_client.upload_graph(graph_handler.G)
    neo_client.close()

    message = "Graph created successfully"
    logger.info(message)
    return message
