from cashier.graph.request_graph import RequestGraphSchema, GraphEdgeSchema
from cashier.graph.mixin.base_edge_schema import FunctionTransitionConfig, FunctionState

from tau_bench.agents.custom_tool_call_data.book_flight_graph import BOOK_FLIGHT_GRAPH
from tau_bench.agents.custom_tool_call_data.change_flight_graph import CHANGE_FLIGHT_GRAPH
from tau_bench.agents.custom_tool_call_data.prompts import AirlineNodeSystemPrompt
from tau_bench.agents.custom_tool_call_data.update_reservation_baggage_graph import CHANGE_BAGGAGE_GRAPH



GRAPH_EDGE_SCHEMA_1 = GraphEdgeSchema(
    from_node_schema=CHANGE_FLIGHT_GRAPH,
    to_node_schema=CHANGE_BAGGAGE_GRAPH,
    transition_config= FunctionTransitionConfig(need_user_msg=False,fn_name="update_reservation_flights", state=FunctionState.CALLED_AND_SUCCEEDED),
    new_input_fn = lambda state: None
)

AIRLINE_REQUEST_GRAPH = RequestGraphSchema(
    node_schemas=[BOOK_FLIGHT_GRAPH, CHANGE_FLIGHT_GRAPH, CHANGE_BAGGAGE_GRAPH],
    edge_schemas=[GRAPH_EDGE_SCHEMA_1],
    node_prompt="You are a helpful assistant that helps customers with flight-related requests.",
    node_system_prompt=AirlineNodeSystemPrompt,
    description="Help customers change flights and baggage information for a reservation.",
)