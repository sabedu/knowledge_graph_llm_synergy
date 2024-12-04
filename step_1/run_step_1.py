import os
import sys
import pandas as pd
from dotenv import load_dotenv

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.abspath(os.path.join(current_dir, '..'))
sys.path.insert(0, parent_dir)


from data_collection.github_data_collector import GitHubDataCollector
from szz_execution.link_bugs import LinkBugs
from graph_construction.construct_graph import construct_graph

def get_parameters(repo_name):
    df = pd.read_csv('repo_neo4j_map.csv')
    repo_row = df[df['Repository'] == repo_name]
    if not repo_row.empty:
        url = repo_row['Neo4j_DB'].values[0]
        password = repo_row['Password'].values[0]
        return url, password
    else:
        return None, None

def step_1(repo_url, github_token, neo4j_uri, neo4j_user, neo4j_password):
    """COLLECT DATA FROM GITHUB USING THE GRAPHQL API"""
    # data_collector = GitHubDataCollector(github_token, repo_url)
    # data_collector.collect_data()
    
    """RUN THE SZZ ALGORITHM TO LINK BUGS TO COMMITS"""
    # bics = LinkBugs(repo_url).process_issues()

    """CONSTRUCT THE GRAPH"""
    message = construct_graph(repo_url, neo4j_uri, neo4j_user, neo4j_password)
    return message

# repo_urls = ["https://github.com/facebook/react",
#              "https://github.com/ohmyzsh/ohmyzsh",
#              "https://github.com/Significant-Gravitas/AutoGPT",
#              "https://github.com/vuejs/vue", 
#              "https://github.com/twbs/bootstrap"
#              ]

# repo_urls = ["https://github.com/sabedu/repochat.tool"]
# repo_urls = ["https://github.com/vuejs/vue"]
# repo_urls = ["https://github.com/Significant-Gravitas/AutoGPT",
#              "https://github.com/facebook/react"
#              ]

# repo_urls = ["https://github.com/ohmyzsh/ohmyzsh"]

repo_urls = ["https://github.com/twbs/bootstrap"]

for repo_url in repo_urls:
    load_dotenv()
    github_token = os.getenv("GITHUB_TOKEN")
    # neo4j_uri = os.getenv("NEO4J_URI")
    # neo4j_user = os.getenv("NEO4J_USER")
    # neo4j_password = os.getenv("NEO4J_PASSWORD")

    repo_name = repo_url.split("/")[-1]
    neo4j_user = "neo4j"
    neo4j_uri, neo4j_password = get_parameters(repo_name)

    message = step_1(repo_url, github_token, neo4j_uri, neo4j_user, neo4j_password)
    print(f"Finished constructing graph for {repo_url}.")

