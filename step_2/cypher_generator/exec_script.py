from cypher_generator import cypher_generator
import json
from os import path

repositories = ["AutoGPT", "bootstrap", "ohmyzsh", "react", "vue"]

learning_type = 'fs_cot'

for repo_name in repositories:
    file_path = f'ground_truth/{repo_name}.json'
    with open(file_path, 'r') as file:
        questions = json.load(file)
        
    no_exec = 0

    while no_exec < 5:
        for question in questions:
            query = question['question']
            # query = "Determine the developers that had the most unfixed bugs?"
            # query = "What files have Aarushi modified the most?"
            response = cypher_generator(repo_name, query, no_exec, learning_type)

            q_number = question['number']
            q_cat = question['category']
            amb = question['isAmbiguous']

            entry = {
                "question": query,
                "number": q_number,
                "category": q_cat,
                "response": None,
                "chain_of_thought": response,
                "query": None, #query,
                "result": None,
                "isAmbiguous": amb,
                "iteration": no_exec
            }

            if learning_type == 'zs':
                file_name = f'zs_responses/{repo_name}.json'
            elif learning_type == 'fs_cot':
                file_name = f'fs_responses_3/{repo_name}.json'
            else:
                file_name = f'cot_responses/{repo_name}.json'

            if path.exists(file_name):
                with open(file_name, 'r') as file:
                    data = json.load(file)
            else:
                data = []

            data.append(entry)
            with open(file_name, 'w', encoding='utf-8') as file:
                json.dump(data, file, indent=4, ensure_ascii=False)

        no_exec += 1