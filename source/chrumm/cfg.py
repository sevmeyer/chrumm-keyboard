def _init(jsonStrings):
    """Make JSON values available as native module attributes."""
    # Imports are done in local scope because
    # all public names in globals() get deleted.
    import json
    import math
    import types

    def mergeDicts(source, target):
        for key, value in source.items():
            if key.isidentifier() and not key.startswith("_"):
                if isinstance(value, dict):
                    obj = target.setdefault(key, types.SimpleNamespace())
                    mergeDicts(value, obj.__dict__)
                else:
                    if key.lower().endswith("angle"):
                        value = math.radians(value)
                    target[key] = value

    # Delete old attributes from globals()
    for key in list(globals()):
        if not key.startswith("_"):
            del globals()[key]

    # Add new attributes to globals()
    for string in jsonStrings:
        mergeDicts(json.loads(string), globals())
