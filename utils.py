from ortools.sat.python import cp_model
import requests
import os

# from pprint import pprint

from constants import SOURCES, TARGETS, CONTEXT

BASE_URL = os.getenv("BASE_URL")


def valid_data(sources_and_targets):
    """Returns True if the provided input data can be processed by the classifier.

    :param sources_and_targets: Information about potential source elements and target pages in JSON format
    :type sources_and_targets: dict
    """
    # TODO: Add validation
    if not SOURCES in sources_and_targets:
        print("Missing key: 'sources'")
        return False
    sources = sources_and_targets[SOURCES]
    if not isinstance(sources, list):
        print("Should be list: 'sources'")
        return False
    if not len(sources) > 0:
        print("Should have length greater 0: 'sources'")
        return False
    for index, source in enumerate(sources):
        if not isinstance(source, dict):
            print(f"Should be dict: 'sources[{index}]'")
            return False
        if not "id" in source:
            print(f"Missing key: 'id' in 'sources[{index}]'")
            return False
        if not "parentId" in source:
            print(f"Missing key: 'parentId' in 'sources[{index}]'")
            return False
        if not "characters" in source:
            print(f"Missing key: 'characters' in 'sources[{index}]'")
            return False
        if not "color" in source:
            print(f"Missing key: 'color' in 'sources[{index}]'")
            return False
        color = source["color"]
        if not isinstance(color, dict):
            print(f"Should be dict: 'sources[{index}]['color']'")
            return False
        for color_variable in ["r", "g", "b"]:
            if not color_variable in color:
                print(f"Missing key: '{color_variable}' in 'sources[{index}]['color']'")
                return False
            if not isinstance(color[color_variable], float) and not isinstance(
                color[color_variable], int
            ):
                print(f"Should be float: 'sources[{index}]['color'][{color_variable}]'")
                return False
            if not color[color_variable] >= 0:
                print(
                    f"Should be greater or equal 0: 'sources[{index}]['color'][{color_variable}]'"
                )
                return False
            if not color[color_variable] <= 1:
                print(
                    f"Should be less than or equal 1: 'sources[{index}]['color'][{color_variable}]'"
                )
                return False
    if not TARGETS in sources_and_targets:
        print("Missing key: 'targets'")
        return False
    targets = sources_and_targets[TARGETS]
    if not isinstance(targets, list):
        print("Should be list: 'targets'")
        return False
    if not len(targets) > 1:
        print("Should have length greater 1: 'sources'")
        return False
    for index, target in enumerate(targets):
        if not isinstance(target, dict):
            print(f"Should be dict: 'targets[{index}]'")
            return False
        if not "id" in target:
            print(f"Missing key: 'id' in 'sources[{index}]'")
            return False
        if not "topics" in target:
            print(f"Missing key: 'topics' in 'sources[{index}]'")
            return False
        topics = target["topics"]
        if not isinstance(topics, list):
            print(f"Should be list: 'targets[{index}]['topics']'")
            return False
        for topic_index, topic in enumerate(topics):
            if not isinstance(topic, str):
                print(f"Should be str: 'targets[{index}]['topics'][{topic_index}]'")
                return False
        if not CONTEXT in sources_and_targets:
            print("Missing key: 'context'")
            return False
        context = sources_and_targets[CONTEXT]
        if not isinstance(context, list):
            print("Should be list: 'context'")
            return False

    return True


def get_qualifications(sources, targets, context, user_id=None):
    payload = {SOURCES: sources, TARGETS: targets, CONTEXT: context}
    url = (
        f"{BASE_URL}/model/{user_id}/qualifications"
        if user_id
        else f"{BASE_URL}/qualifications"
    )
    response = requests.post(url, json=payload, timeout=30)
    if response.status_code == 200:
        data = response.json()
        return data["qualifications"]
    return []


def get_links(qualifications, sources, targets):
    # Declare model
    model = cp_model.CpModel()
    num_source_elements = len(qualifications)
    num_target_pages = len(qualifications[0])

    # Create variables
    l = []
    for e in range(num_source_elements):
        vars = []
        for p in range(num_target_pages):
            vars.append(model.NewBoolVar(f"l[{e},{p}]"))
        l.append(vars)

    # Create constraints
    # Each source element must link to at most one target page
    for e in range(num_source_elements):
        model.Add(sum(l[e][p] for p in range(num_target_pages)) <= 1)

    # Each target page needs to be reachable
    for p in range(num_target_pages):
        model.Add(sum(l[e][p] for e in range(num_source_elements)) >= 1)

    # Create objective function
    objective_terms = []
    for e in range(num_source_elements):
        for p in range(num_target_pages):
            objective_terms.append(qualifications[e][p] * l[e][p])
    model.Maximize(sum(objective_terms))

    # Invoke solver
    solver = cp_model.CpSolver()
    status = solver.Solve(model)

    # Return solution
    links = []
    if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
        for e in range(num_source_elements):
            for p in range(num_target_pages):
                if solver.BooleanValue(l[e][p]):
                    links.append(
                        {
                            "sourceId": sources[e]["id"],
                            "targetId": targets[p]["id"],
                            "qualification": qualifications[e][p],
                        }
                    )
    return links


def suggested_links(sources_and_targets, user_id=None):
    sources = sources_and_targets[SOURCES]
    targets = sources_and_targets[TARGETS]
    context = sources_and_targets[CONTEXT]
    qualifications = get_qualifications(sources, targets, context, user_id)
    # pprint([{'source': sources[s]['name'], 'target': targets[t]['name'], 'qualification': qualifications[s][t]} for s in range(len(qualifications)) for t in range(len(qualifications[s])) if sources[s]['characters'] in ['To Shopping Bag', 'Classics', 'More details', 'Home', 'Detail']])
    links = get_links(qualifications, sources, targets)
    return {"links": links}


def update_classifier(link_and_label, user_id):
    LINK = "link"
    IS_LINK = "isLink"
    link = link_and_label[LINK]
    is_link = link_and_label[IS_LINK]
    payload = {LINK: link, IS_LINK: is_link}
    url = f"{BASE_URL}/model/{user_id}/update"
    response = requests.post(url, json=payload, timeout=30)
    if response.status_code == 200:
        return {"message": "model updated"}
    return {"message": "model update failed"}
