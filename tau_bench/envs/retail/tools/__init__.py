# Copyright Sierra

from .calculate import calculate
from .cancel_pending_order import cancel_pending_order
from .exchange_delivered_order_items import exchange_delivered_order_items
from .find_user_id_by_email import find_user_id_by_email
from .find_user_id_by_name_zip import find_user_id_by_name_zip
from .get_order_details import get_order_details
from .get_product_details import get_product_details
from .get_user_details import get_user_details
from .list_all_product_types import list_all_product_types
from .modify_pending_order_address import modify_pending_order_address
from .modify_pending_order_items import modify_pending_order_items
from .modify_pending_order_payment import modify_pending_order_payment
from .modify_user_address import modify_user_address
from .return_delivered_order_items import return_delivered_order_items
from .think import think
from .transfer_to_human_agents import transfer_to_human_agents

tools = [
    calculate,
    cancel_pending_order,
    exchange_delivered_order_items,
    find_user_id_by_email,
    find_user_id_by_name_zip,
    get_order_details,
    get_product_details,
    get_user_details,
    list_all_product_types,
    modify_pending_order_address,
    modify_pending_order_items,
    modify_pending_order_payment,
    modify_user_address,
    return_delivered_order_items,
    think,
    transfer_to_human_agents,
]

assert all(tool.__info__ for tool in tools)

for tool in tools:
    assert tool.__name__ == tool.__info__["function"]["name"], tool
    assert list(tool.__info__["function"]["parameters"]["properties"].keys()) == list(
        tool.__info__["function"]["parameters"]["required"]
    ), tool
