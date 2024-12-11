from cashier.graph.request_graph import RequestGraphSchema, GraphEdgeSchema

from tau_bench.agents.custom_tool_call_data.book_flight_graph import BOOK_FLIGHT_GRAPH
from tau_bench.agents.custom_tool_call_data.change_flight_graph import CHANGE_FLIGHT_GRAPH
from tau_bench.agents.custom_tool_call_data.prompts import AirlineNodeSystemPrompt
from tau_bench.agents.custom_tool_call_data.update_reservation_baggage_graph import CHANGE_BAGGAGE_GRAPH, ChangeBaggageGraphStateSchema

GRAPH_EDGE_SCHEMA_1 = GraphEdgeSchema(
    from_node_schema=CHANGE_FLIGHT_GRAPH,
    to_node_schema=CHANGE_BAGGAGE_GRAPH,
    new_input_fn = lambda state: ChangeBaggageGraphStateSchema(user_details=state.user_details, reservation_details=state.reservation_details).model_dump(include={"user_details", "reservation_details"})
)

AIRLINE_REQUEST_GRAPH = RequestGraphSchema(
    node_schemas=[BOOK_FLIGHT_GRAPH, CHANGE_FLIGHT_GRAPH, CHANGE_BAGGAGE_GRAPH],
    edge_schemas=[GRAPH_EDGE_SCHEMA_1],
    node_prompt="You are a helpful assistant that helps customers with flight-related requests.",
    node_system_prompt=AirlineNodeSystemPrompt,
    description="Help customers change flights and baggage information for a reservation.",
)