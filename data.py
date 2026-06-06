import json
import os

PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data.json")

DEFAULT = {
    "accent": "#4EC9B0",
    "bg": "#1e1e1e",
    "expanded": [],
    "categories": []
}

def load():
    if not os.path.exists(PATH):
        save(DEFAULT)
        return dict(DEFAULT)
    with open(PATH, "r") as f:
        d = json.load(f)
    # patch missing keys for older data files
    for k, v in DEFAULT.items():
        if k not in d:
            d[k] = v
    return d

def save(data):
    with open(PATH, "w") as f:
        json.dump(data, f, indent=2)