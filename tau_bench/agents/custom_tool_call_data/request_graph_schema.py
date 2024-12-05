from cashier.graph.request_graph import RequestGraphSchema, GraphEdgeSchema
from cashier.graph.mixin.base_edge_schema import FunctionTransitionConfig, FunctionState

from tau_bench.agents.custom_tool_call_data.book_flight_graph import BOOK_FLIGHT_GRAPH
from tau_bench.agents.custom_tool_call_data.change_flight_graph import CHANGE_FLIGHT_GRAPH
from tau_bench.agents.custom_tool_call_data.update_reservation_baggage_graph import CHANGE_BAGGAGE_GRAPH



GRAPH_EDGE_SCHEMA_1 = GraphEdgeSchema(
    from_graph_schema=CHANGE_FLIGHT_GRAPH,
    to_graph_schema=CHANGE_BAGGAGE_GRAPH,
    transition_config= FunctionTransitionConfig(need_user_msg=False,fn_name="update_reservation_flights", state=FunctionState.CALLED_AND_SUCCEEDED)
)

AIRLINE_REQUEST_GRAPH = RequestGraphSchema(
    graph_schemas=[BOOK_FLIGHT_GRAPH, CHANGE_FLIGHT_GRAPH, CHANGE_BAGGAGE_GRAPH],
    graph_edge_schemas=[GRAPH_EDGE_SCHEMA_1],
    system_prompt="You are a helpful assistant that helps customers with flight-related requests.",
)