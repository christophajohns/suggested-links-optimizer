def valid_data(sources_and_targets):
    """Returns True if the provided input data can be processed by the optimizer.

    :param sources_and_targets: Information about potential source elements and target pages in JSON format
    :type sources_and_targets: dict
    """
    # TODO: Add validation
    if not "sources" in sources_and_targets:
        print("Missing key: 'sources'")
        return False
    if not isinstance(sources_and_targets["sources"], list):
        print("Should be list: 'sources'")
        return False
    if not len(sources_and_targets["sources"]) > 0:
        print("Should have length greater 0: 'sources'")
        return False
    for index, source in enumerate(sources_and_targets["sources"]):
        if not isinstance(source, dict):
            print(f"Should be dict: 'sources[{index}]'")
            return False
        if not "id" in source:
            print(f"Missing key: 'id' in 'sources[{index}]'")
            return False
    if not isinstance(sources_and_targets["targets"], list):
        print("Should be list: 'targets'")
        return False
    if not len(sources_and_targets["targets"]) > 1:
        print("Should have length greater 1: 'sources'")
        return False
    for index, target in enumerate(sources_and_targets["targets"]):
        if not isinstance(target, dict):
            print(f"Should be dict: 'targets[{index}]'")
            return False
        if not "id" in target:
            print(f"Missing key: 'id' in 'sources[{index}]'")
            return False
    return True


def suggested_links(sources_and_targets):
    # TODO: Add combinatorial optimization
    return {
        "links": [
            {
                "sourceId": sources_and_targets["sources"][0]["id"],
                "targetId": sources_and_targets["targets"][1]["id"],
            }
        ]
    }
