# Copyright Sierra

import json
import os

FOLDER_PATH = os.path.dirname(__file__)

data = {
    "orders": json.load(open(os.path.join(FOLDER_PATH, "orders.json"))),
    "products": json.load(open(os.path.join(FOLDER_PATH, "products.json"))),
    "users": json.load(open(os.path.join(FOLDER_PATH, "users.json"))),
}
