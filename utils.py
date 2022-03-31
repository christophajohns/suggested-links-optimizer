from ortools.sat.python import cp_model
import requests
from requests.adapters import HTTPAdapter, Retry
import os
from constants import (
    PAGES,
    ID,
    TYPE,
    BOUNDS,
    X,
    Y,
    WIDTH,
    HEIGHT,
    CHILDREN,
)

# from pprint import pprint

BASE_URL = os.getenv("BASE_URL")


def validate_data(pages_data: dict):
    """Raises an error if the provided input data cannot be processed by the classifier.

    :param pages_data: Information about the application's pages in JSON format
    :type pages_data: dict
    """

    def validate_node(node: dict):
        for key in [ID, TYPE, BOUNDS]:
            if not key in node:
                print(node)
                raise Exception(f"Missing key: {key}")
        for key in [X, Y, WIDTH, HEIGHT]:
            if not key in node[BOUNDS]:
                print(node)
                raise Exception(f"Missing key: {key}")
        if CHILDREN in node:
            for child in node[CHILDREN]:
                validate_node(child)

    if not isinstance(pages_data, dict):
        raise Exception(f"Should be dict: pages_data")
    if not PAGES in pages_data:
        raise Exception(f"Missing key: {PAGES}")
    pages = pages_data[PAGES]
    if not isinstance(pages, list):
        raise Exception(f"Should be list: {PAGES}")
    for page_index, page in enumerate(pages):
        if not isinstance(page, dict):
            raise Exception(f"Should be dict: {PAGES}[{page_index}]")
        for key in [ID, WIDTH, HEIGHT, CHILDREN]:
            if not key in page:
                raise Exception(f"Missing key: {key} in {PAGES}[{page_index}]")
        for child in page[CHILDREN]:
            validate_node(child)


def get_qualifications(pages, user_id=None):
    payload = {PAGES: pages}
    url = (
        f"{BASE_URL}/model/{user_id}/qualifications"
        if user_id
        else f"{BASE_URL}/qualifications"
    )
    retries = Retry(total=5, backoff_factor=1, status_forcelist=[500])
    adapter = HTTPAdapter(max_retries=retries)
    session = requests.Session()
    session.mount("https://", adapter)
    response = session.post(url, json=payload, timeout=300)
    if response.status_code == 200:
        data = response.json()
        return data["qualifications"]
    return []


def get_links(qualifications):
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
            objective_terms.append(qualifications[e][p]["probability"] * l[e][p])
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
                            "sourceId": qualifications[e][p]["source"]["id"],
                            "targetId": qualifications[e][p]["target"]["id"],
                            "qualification": qualifications[e][p]["probability"],
                            "info": qualifications[e][p]["info"],
                        }
                    )
    return links


def suggested_links(pages_data, user_id=None):
    all_pages = pages_data[PAGES]
    qualifications = get_qualifications(pages=all_pages, user_id=user_id)
    # pprint([{'source': sources[s]['name'], 'target': targets[t]['name'], 'qualification': qualifications[s][t]} for s in range(len(qualifications)) for t in range(len(qualifications[s])) if sources[s]['characters'] in ['To Shopping Bag', 'Classics', 'More details', 'Home', 'Detail']])
    links = get_links(qualifications)
    sorted_links = sorted(links, key=lambda link: link["qualification"], reverse=True)
    return {"links": sorted_links}


def update_classifier(link_and_label, user_id):
    LINK = "link"
    IS_LINK = "isLink"
    link = link_and_label[LINK]
    is_link = link_and_label[IS_LINK]
    payload = {LINK: link, IS_LINK: is_link}
    url = f"{BASE_URL}/model/{user_id}/update"
    retries = Retry(total=5, backoff_factor=1, status_forcelist=[500])
    adapter = HTTPAdapter(max_retries=retries)
    session = requests.Session()
    session.mount("https://", adapter)
    response = session.post(url, json=payload, timeout=300)
    if response.status_code == 200:
        return {"message": "model updated"}
    return {"message": "model update failed"}


if __name__ == "__main__":
    import json
    from pprint import pprint

    BASE_URL = "http://127.0.0.1:3000"

    with open("pages-data-example.json") as f:
        pages_data = json.load(f)
    validate_data(pages_data)
    links = suggested_links(pages_data)
    pprint(links)
