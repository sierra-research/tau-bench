# Copyright Sierra

import json
from typing import Any, Dict
from tau_bench.agents.custom_tool_call_data.sort_by_general import (
    SORT_STRING_VALUES,
    sort_flights_dict,
)
from tau_bench.envs.tool import Tool


class SearchDirectFlight(Tool):
    @staticmethod
    def invoke(
        data: Dict[str, Any],
        origin: str,
        destination: str,
        date: str,
        sort_by: str = "price",
    ) -> str:
        output = SearchDirectFlightWithSort.invoke(
            data, origin, destination, date, sort_by
        )
        return json.dumps(output)

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return SearchDirectFlightWithSort.get_info()


class SearchDirectFlightWithSort:
    @staticmethod
    def invoke(
        data: Dict[str, Any],
        origin: str,
        destination: str,
        date: str,
        sort_by: str = "price",
    ) -> str:
        results = SearchDirectFlightWithoutSort.invoke(data, origin, destination, date)
        results = sort_flights_dict(results, sort_by)
        return results

    @staticmethod
    def get_info() -> Dict[str, Any]:
        info = SearchDirectFlightWithoutSort.get_info()
        info["function"]["parameters"]["properties"]["sort_by"] = {
            "type": "string",
            "description": "The attribute to sort the flights by. The default is 'price'.",
            "enum": SORT_STRING_VALUES,
        }
        info["function"]["parameters"]["required"].append("sort_by")
        info["function"][
            "description"
        ] = "Search direct flights between two cities on a specific date"
        return info


class SearchDirectFlightWithoutSort:
    @staticmethod
    def invoke(data: Dict[str, Any], origin: str, destination: str, date: str) -> str:
        flights = data["flights"]
        results = []
        for flight in flights.values():
            if flight["origin"] == origin and flight["destination"] == destination:
                if (
                    date in flight["dates"]
                    and flight["dates"][date]["status"] == "available"
                ):
                    # results add flight except dates, but add flight["datas"][date]
                    results.append({k: v for k, v in flight.items() if k != "dates"})
                    results[-1].update(flight["dates"][date])
                    results[-1]["date"] = date
        return results

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "search_direct_flight",
                "description": "Search direct flights between two cities on a specific date. The results won't be sorted in any way.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "origin": {
                            "type": "string",
                            "description": "The origin city airport in three letters, such as 'JFK'.",
                        },
                        "destination": {
                            "type": "string",
                            "description": "The destination city airport in three letters, such as 'LAX'.",
                        },
                        "date": {
                            "type": "string",
                            "description": "The date of the flight in the format 'YYYY-MM-DD', such as '2024-01-01'.",
                        },
                    },
                    "required": ["origin", "destination", "date"],
                },
            },
        }
