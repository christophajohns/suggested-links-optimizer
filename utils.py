from ortools.sat.python import cp_model


def valid_data(sources_and_targets):
    """Returns True if the provided input data can be processed by the optimizer.

    :param sources_and_targets: Information about potential source elements and target pages in JSON format
    :type sources_and_targets: dict
    """
    # TODO: Add validation
    if not "sources" in sources_and_targets:
        print("Missing key: 'sources'")
        return False
    sources = sources_and_targets["sources"]
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
    if not "targets" in sources_and_targets:
        print("Missing key: 'targets'")
        return False
    targets = sources_and_targets["targets"]
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
    return True


def get_qualifications(sources, targets):
    # TODO: Add qualification computation via classification
    qualifications = [
        [-4, 0.7],
        [0.2, -4],
    ]
    return qualifications


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
                        }
                    )
    return links


def suggested_links(sources_and_targets):
    sources = sources_and_targets["sources"]
    targets = sources_and_targets["targets"]
    qualifications = get_qualifications(sources, targets)
    links = get_links(qualifications, sources, targets)
    return {"links": links}
