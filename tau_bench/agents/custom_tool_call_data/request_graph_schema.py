from cashier.graph.request_graph import RequestGraphSchema

from tau_bench.agents.custom_tool_call_data.book_flight_graph import BOOK_FLIGHT_GRAPH
from tau_bench.agents.custom_tool_call_data.change_flight_graph import CHANGE_FLIGHT_GRAPH
from tau_bench.agents.custom_tool_call_data.update_reservation_baggage_graph import CHANGE_BAGGAGE_GRAPH


AIRLINE_REQUEST_GRAPH = RequestGraphSchema(
    graph_schemas=[BOOK_FLIGHT_GRAPH, CHANGE_FLIGHT_GRAPH, CHANGE_BAGGAGE_GRAPH],
    system_prompt="You are a helpful assistant that helps customers with flight-related requests.",
)