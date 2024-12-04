import requests
from github import Github
import json
import os
from dotenv import load_dotenv
from logging import getLogger
import time

logger = getLogger(__name__)
load_dotenv()

class GitHubDataCollector:
    def __init__(self, token, repo_url):
        self.github = Github(token)
        self.repo_url = repo_url
        self.repo_owner = repo_url.split("/")[-2]
        self.repo_name = repo_url.split("/")[-1]
        self.base_dir = f'data/{self.repo_name}'
        self.repo_path = f'repos/{self.repo_name}'
        os.makedirs(self.base_dir, exist_ok=True)
        self.headers = {"Authorization": f"Bearer {token}"}
        self.repo = self.github.get_repo(f"{self.repo_owner}/{self.repo_name}")
        if not os.path.exists(self.repo_path):
            os.makedirs(self.repo_path)
            try:
                os.system(f"git clone {self.repo_url} {self.repo_path}")
                logger.info(f"Repository {self.repo_name} cloned successfully")
            except Exception as e:
                logger.error(f"Error cloning repository: {e}")
        else:
            logger.info(f"Repository {self.repo_name} already exists")
            os.system(f"git -C {self.repo_path} pull")
        logger.info(f"Created instance of GithubDataCollector")

    def query_graphql(self, query, variables):
        logger.info(f"Executing GraphQL query with variables: {variables}")
        try:
            payload = {"query": query, "variables": variables}
            response = requests.post('https://api.github.com/graphql', json=payload, headers=self.headers, timeout=60)

            if response.status_code != 200:
                error_message = f"GraphQL query failed with status code {response.status_code}: {response.text}"
                logger.exception(error_message)
                raise Exception(error_message)
            remaining_requests = int(response.headers.get('X-RateLimit-Remaining', 1))
            if remaining_requests == 0:
                reset_time = int(response.headers.get('X-RateLimit-Reset', time.time()))
                sleep_duration = max(reset_time - time.time(), 0)
                logger.warning(f"Rate limit exceeded. Sleeping for {sleep_duration} seconds.")
                time.sleep(sleep_duration)
            return response.json()['data']
        except requests.exceptions.Timeout as e:
            logger.error(f"Request timed out: {e}", exc_info=True)
            raise
        except Exception as e:
            logger.error(f"Error occurred while querying graphql: {e}", exc_info=True)
            return {}

    def get_all_instances_of_entity(self, entity, after_cursor=None):
        CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
        queries_dir = os.path.join(CURRENT_DIR, 'queries')
        query_file_path = os.path.join(queries_dir, f'{entity}.graphql')
        logger.info(f"Getting all instances of {entity}, after_cursor: {after_cursor}")
        with open(query_file_path, 'r', encoding='utf-8') as file:
            query = file.read()

        variables = {
            'owner': self.repo_owner,
            'name': self.repo_name,
            'after_clause': after_cursor
        }

        return self.query_graphql(query=query, variables=variables)

    def get_additional_commit_details(self, commit_sha):
        try:
            commit = self.repo.get_commit(sha=commit_sha)
            modified_files = [
                {
                    "filename": file.filename,
                    "change_type": file.status,
                    "additions": file.additions,
                    "deletions": file.deletions
                } for file in commit.files
            ]
            return modified_files
        except Exception as e:
            logger.error(f"Error occurred while getting additional commit details: {e}", exc_info=True)
            return []
        
    def collect_all_commits(self):
        logger.info("Collecting all commits")
        file_path = f'{self.base_dir}/{self.repo_name}_commits.json'

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write('[')

        try:
            has_next_page = True
            after_cursor = None

            first_write = True

            while has_next_page:
                data = self.get_all_instances_of_entity('commits', after_cursor=after_cursor)
                repository_id = data['repository']['id']
                branch_id = data['repository']['defaultBranchRef']['id']
                commits = data['repository']['defaultBranchRef']['target']['history']['nodes']

                for commit in commits:
                    if commit['author']['user'] is None:
                        if commit['committer']['user'] is None:
                            logger.error(f"Commit with no author and no committer: {commit}")
                            continue
                    modified_files = self.get_additional_commit_details(commit['oid'])
                    comments_count = commit.get('comments', {}).get('totalCount', 0)
                    parents = commit.get('parents', [])
                    commit_data = {
                        'repository_id': repository_id,
                        'branch_id': branch_id,
                        "hash": commit['oid'],
                        "message": commit['message'],
                        "changed_files_if_available": commit['changedFilesIfAvailable'],
                        "additions": commit['additions'],
                        "deletions": commit['deletions'],
                        "comments_count": comments_count,
                        "abbreviatedOid": commit['abbreviatedOid'],
                        "committedDate": commit['committedDate'],
                        "parents": parents['nodes'],
                        "author_login": commit['author']['user']['login'] if commit['author']['user'] is not None else
                        commit['committer']['user']['login'] if commit['committer']['user'] is not None else None,
                        'author_id': commit['author']['user']['id'] if commit['author']['user'] is not None else
                        commit['committer']['user']['id'] if commit['committer']['user'] is not None else None,
                        'author_name': commit['author']['user']['name'] if commit['author']['user'] is not None else
                        commit['committer']['user']['name'] if commit['committer']['user'] is not None else None,
                        'author_email': commit['author']['user']['email'] if commit['author']['user'] is not None else
                        commit['committer']['user']['email'] if commit['committer']['user'] is not None else None,
                        "modified_files": modified_files
                    }

                    with open(file_path, 'a', encoding='utf-8') as f:
                        if not first_write:
                            f.write(',')
                        else:
                            first_write = False
                        json.dump(commit_data, f, ensure_ascii=False, indent=4)

                pageInfo = data['repository']['defaultBranchRef']['target']['history']['pageInfo']
                has_next_page = pageInfo['hasNextPage']
                after_cursor = pageInfo['endCursor']

        except Exception as e:
            logger.error(f"Error occurred while collecting commits: {e}", exc_info=True)
        finally:
            with open(file_path, 'a', encoding='utf-8') as f:
                f.write(']')

    def collect_all_issues(self):
        logger.info("Collecting all issues")
        file_path = f'{self.base_dir}/{self.repo_name}_issues.json'
        has_next_page = True
        after_cursor = None

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write('[')

        try:
            first_write = True

            while has_next_page:
                data = self.get_all_instances_of_entity('issues', after_cursor=after_cursor)
                repository_id = data['repository']['id']
                issues = data['repository']['issues']['nodes']

                for issue in issues:
                    issue_data = {
                        'repository_id': repository_id,
                        'id': issue['id'],
                        'author_login': issue['author']['login'] if issue['author'] else None,
                        'author_id': issue['author']['id'] if issue['author'] else None,
                        'author_email': issue['author']['email'] if issue['author'] else None,
                        'author_name': issue['author']['name'] if issue['author'] else None,
                        "number": issue['number'],
                        "title": issue['title'],
                        "body": issue['body'],
                        "state": issue['state'],
                        "created_at": issue['createdAt'],
                        "assignees": issue['assignees']['nodes'],
                        "closed_at": issue['closedAt'],
                        "participants": issue['participants']['nodes'],
                        "state_reason": issue['stateReason'],
                        "updated_at": issue['updatedAt'],
                        'url': issue['url'],
                        'labels': issue['labels']['nodes'],
                    }

                    with open(file_path, 'a', encoding='utf-8') as f:
                        if not first_write:
                            f.write(',')
                        else:
                            first_write = False
                        json.dump(issue_data, f, ensure_ascii=False, indent=4)

                has_next_page = data['repository']['issues']['pageInfo']['hasNextPage']
                after_cursor = data['repository']['issues']['pageInfo']['endCursor']

            # with open(file_path, 'a', encoding='utf-8') as f:
            #     f.write(']')
        except Exception as e:
            logger.error(f"Error occurred while collecting issues: {e}", exc_info=True)
        finally:
            with open(file_path, 'a', encoding='utf-8') as f:
                f.write(']')

    def collect_all_collaborators(self):
        logger.info('Collecting all collaborators')
        file_path = f'{self.base_dir}/{self.repo_name}_collaborators.json'
        has_next_page = True
        after_cursor = None

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write('[')

        try:
            first_write = True

            while has_next_page:
                data = self.get_all_instances_of_entity('collaborators', after_cursor=after_cursor)
                repository_id = data['repository']['id']
                collaborators_edges = data['repository']['collaborators']['edges']
                # collaborators = data['repository']['collaborators']['nodes']

                for edge in collaborators_edges:
                # for collaborator in collaborators:
                    collaborator = edge['node']
                    permission = edge['permission'] 

                    collaborator_data = {
                        'repository_id': repository_id,
                        'id': collaborator['id'],
                        'login': collaborator['login'],
                        'name': collaborator['name'],
                        'email': collaborator['email'],
                        'permission': permission,
                    }

                    with open(file_path, 'a', encoding='utf-8') as f:
                        if not first_write:
                            f.write(',')
                        else:
                            first_write = False
                        json.dump(collaborator_data, f, ensure_ascii=False, indent=4)
                has_next_page = data['repository']['collaborators']['pageInfo']['hasNextPage']
                after_cursor = data['repository']['collaborators']['pageInfo']['endCursor']

        except Exception as e:
            logger.error(f"Error occurred while collecting collaborators: {e}", exc_info=True)
        finally:
            with open(file_path, 'a', encoding='utf-8') as f:
                f.write(']')

    def collect_data(self):
        logger.info("Collecting repository data")
        self.collect_all_commits()
        self.collect_all_collaborators()
        self.collect_all_issues()
        print("Data collection completed")
