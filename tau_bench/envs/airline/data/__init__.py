# Copyright Sierra

import json
import os

FOLDER_PATH = os.path.dirname(__file__)

data = {
    "flights": json.load(open(os.path.join(FOLDER_PATH, "flights.json"))),
    "reservations": json.load(open(os.path.join(FOLDER_PATH, "reservations.json"))),
    "users": json.load(open(os.path.join(FOLDER_PATH, "users.json"))),
}
