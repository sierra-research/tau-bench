from tau_bench.types import Action, Task

TASKS_DEV = [
    Task(
        annotator="0",
        user_id="emily_chen_9012",
        instruction="You are Emily Chen, born July 8, 1992. You want to reschedule appointment APPT003 to a later time the same day.",
        actions=[
            Action(
                name="find_patient_by_name_dob",
                kwargs={"first_name": "Emily", "last_name": "Chen", "date_of_birth": "1992-07-08"},
            ),
            Action(name="get_appointment_details", kwargs={"appointment_id": "APPT003"}),
        ],
        outputs=[],
    ),
]
