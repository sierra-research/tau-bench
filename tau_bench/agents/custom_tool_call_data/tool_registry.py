from cashier.tool_registries.general import GeneralToolRegistry
from tau_bench.envs.airline.tools import ALL_TOOLS

AIRLINE_TOOL_REGISTRY = GeneralToolRegistry()

def get_tool_name(tool_def):
    return tool_def['function']['name']

for tool in ALL_TOOLS:
    AIRLINE_TOOL_REGISTRY.add_tool_def_w_oai_def(get_tool_name(tool.get_info()), tool.get_info())