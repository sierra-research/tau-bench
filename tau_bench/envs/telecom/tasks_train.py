from tau_bench.types import Action, Task

# Training tasks for the telecom environment
# These would typically contain more tasks for training purposes
TASKS_TRAIN = [
    Task(
        annotator="train_0",
        user_id="john_smith_1234",
        instruction="""
        You are John Smith. Your internet has been running slowly for the past week.
        You want to troubleshoot the issue and check if there are any network problems in your area.
        """,
        actions=[
            Action(name="get_customer_details", kwargs={"customer_id": "john_smith_1234"}),
            Action(name="troubleshoot_device", kwargs={"device_id": "router_wifi6", "issue": "slow internet speeds"}),
            Action(name="check_network_status", kwargs={"region": "denver_co", "service_type": "internet"}),
        ],
        outputs=[],
    ),
    # Additional training tasks would be added here
]
