from tau_bench.types import Action, Task

TASKS_TRAIN = [
    Task(
        annotator="0",
        user_id="david_martinez_5678",
        instruction="""
        You are David Martinez, email david.martinez@email.com. 
        You want to cancel appointment APPT005 because you're feeling better.",
        """,
        actions=[
            Action(
                name="find_patient_by_email",
                kwargs={"email": "david.martinez@email.com"},
            ),
            Action(name="get_appointment_details", kwargs={"appointment_id": "APPT005"}),
        ],
        outputs=[],
    ),
]
