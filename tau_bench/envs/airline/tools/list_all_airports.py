# Copyright Sierra

import json
from typing import Any, Dict


def list_all_airports(data: Dict[str, Any]) -> str:
    airports = [
        "SFO",
        "JFK",
        "LAX",
        "ORD",
        "DFW",
        "DEN",
        "SEA",
        "ATL",
        "MIA",
        "BOS",
        "PHX",
        "IAH",
        "LAS",
        "MCO",
        "EWR",
        "CLT",
        "MSP",
        "DTW",
        "PHL",
        "LGA",
    ]
    cities = [
        "San Francisco",
        "New York",
        "Los Angeles",
        "Chicago",
        "Dallas",
        "Denver",
        "Seattle",
        "Atlanta",
        "Miami",
        "Boston",
        "Phoenix",
        "Houston",
        "Las Vegas",
        "Orlando",
        "Newark",
        "Charlotte",
        "Minneapolis",
        "Detroit",
        "Philadelphia",
        "LaGuardia",
    ]
    return json.dumps({airport: city for airport, city in zip(airports, cities)})


list_all_airports.__info__ = {
    "type": "function",
    "function": {
        "name": "list_all_airports",
        "description": "List all airports and their cities.",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
}
