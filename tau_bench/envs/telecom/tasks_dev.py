from tau_bench.types import Action, Task

TASKS_TEST = [
    ## Verified - Hard 
    Task(
        annotator="0",
        user_id="john_smith_1234",
        instruction="""
        You are John Smith, customer ID john_smith_1234. You want to figure out your account information, specifically 
        your account number and devices you have. You've noticed that your internet has been quite slow recently, and 
        want to get some advice on how to fix the issue. Finally, you want to check your current billing details to 
        see what you are paying monthly for your services.
        """,
        actions=[
            Action(name="get_customer_details", kwargs={"customer_id": "john_smith_1234"}),
            Action(name="troubleshoot_device", kwargs={"device_id": "router_wifi6", "issue": "slow internet speeds"}),
            Action(name="get_billing_details", kwargs={"customer_id": "john_smith_1234"}),
        ],
        outputs=["ACC001234567", ## at the minimum, the account number and devices should be shown to the user 
                "iPhone 15 Pro",
                "WiFi 6 Router",
                "Samsung",
                "Unplug", # step 1
                "cable", # step 2
                "test", # step 3
                "support", # step 4    
                "85.00", # monthly charges
                "80.00",
                "95.00",
                "18.50",
                "278.50", # total monthly charges
                ],
    ),
    ## Verified - Hard 
    Task(
        annotator="1",
        user_id="sarah_johnson_5678",
        instruction="""
        You are Sarah Johnson, email sarah.johnson@email.com. You first want to figure out what your customer ID is. 
        Then you want to get your billing details. You think that you are only paying for internet cable and tv basic.
        If you learn that you are paying for other stuff you should get very upset and demand to be helped by a human.
        State that if you are not helped in the next day you will cancell all your services.
        """,
        actions=[
            Action(name="find_customer_by_email", kwargs={"email": "sarah.johnson@email.com"}),
            Action(name="get_billing_details", kwargs={"customer_id": "sarah_johnson_5678"}),
            Action(name="create_support_ticket", kwargs={"customer_id": "sarah_johnson_5678", "category": "billing", "priority": "urgent"}),
        ],
        outputs=["sarah_johnson_5678"],
    ),
    ## Verified 
    Task(
        annotator="2",
        user_id="mike_davis_9012",
        instruction="""
        You are Mike Davis, phone number (555) 456-7890. 
        First, find your customer ID using your phone number.
        Then get your customer details to see your account information.
        Next, troubleshoot your conference phone (device ID: conference_phone) for not receiving calls.
        Finally, list all your current services to see what you have.
        """,
        actions=[
            Action(name="find_customer_by_phone", kwargs={"phone": "(555) 456-7890"}),
            Action(name="get_customer_details", kwargs={"customer_id": "mike_davis_9012"}),
            Action(name="troubleshoot_device", kwargs={"device_id": "conference_phone", "issue": "not receiving incoming calls"}),
            Action(name="manage_service", kwargs={"customer_id": "mike_davis_9012", "action": "list"}),
        ],
        outputs=[
            "mike_davis_9012",
            "iPhone 15",
            "Android Pixel 8",
            "Conference Phone",
            "Router Enterprise",
            "TV Conference Room",
            "Restart", # step 1
            "coverage", # step 2
            "network", # step 3
            "support", # step 4
        ],
    ),
    ## Verified - Hard
    Task(
        annotator="3",
        user_id="lisa_chen_3456",
        instruction="""
        You are Lisa Chen, customer ID lisa_chen_3456. 
        The phone number currently associated with your account is (555) 234-5678.
        You want to add a new iPhone 15 to your account with the phone number (301) 666-7777.
        Then, you want to add the mobile_unlimited service to your account, attaching the iPhone 15 to the service.
        """,
        actions=[
            Action(name="get_customer_details", kwargs={"customer_id": "lisa_chen_3456"}),
            Action(name="add_device", kwargs={"customer_id": "lisa_chen_3456", "device_name": "iPhone 15"}),
            Action(name="manage_devices", kwargs={"customer_id": "lisa_chen_3456", "action": "list"}),
            Action(name="manage_service", kwargs={"customer_id": "lisa_chen_3456", "action": "add", "service_id": "mobile_unlimited", "devices_ids": ["3"]}),
        ],
        outputs=[],
    ),
    Task(
        annotator="4",
        user_id="lisa_chen_3456",
        instruction="".join((
            "You are Lisa Chen, customer ID lisa_chen_3456. ",
            "You want to change your billing preferences to turn autopay off. ",
        )),
        actions=[
            Action(name="manage_billing", kwargs={"customer_id": "lisa_chen_3456", "paperless": True, "auto_pay": False, "billing_cycle": "monthly"}),

        ],
        outputs=[],
    ),
    ### Check the customer ID by email 
    Task(
        annotator="5",
        user_id="lisa_chen_3456",
        instruction="".join((
            "You are Lisa Chen, your email is lisa.chen@email.com. ",
            "You want to find your customer ID. ",
        )),
        actions=[
            Action(name="find_customer_by_email", kwargs={"email": "lisa.chen@email.com"}),
        ],
        outputs=["lisa_chen_3456"],
    ),
    ### Check the find customer by phone
    Task(
        annotator="6",
        user_id="lisa_chen_3456",
        instruction="".join((
            "You are Lisa Chen, your phone number is (555) 234-5678. ",
            "You want to find your customer ID. ",
        )),
        actions=[
            Action(name="find_customer_by_phone", kwargs={"phone": "(555) 234-5678"}),
        ],
        outputs=["lisa_chen_3456"],
    ),
    ### Get the billing details for a customer 
    Task(
        annotator="7",
        user_id="lisa_chen_3456",
        instruction="".join((
            "You are Lisa Chen, phone number (555) 234-5678. ",
            "You want to get the total monthly charges for your services. ",
        )),
        actions=[
            Action(name="get_billing_details", kwargs={"customer_id": "lisa_chen_3456"}),
        ],
        outputs=["105.50"],
    ),


    # Task(
    #     annotator="5",
    #     user_id="new_customer_inquiry",
    #     instruction="""
    #     You are a potential new customer interested in telecom services.
    #     First, list all available mobile services to see the options.
    #     Then list all available internet services to compare speeds.
    #     Next, get details about the mobile_family_4lines service.
    #     Finally, get details about the internet_fiber_1gb service.
    #     """,
    #     actions=[
    #         Action(name="list_available_services", kwargs={"category": "mobile"}),
    #         Action(name="list_available_services", kwargs={"category": "internet"}),
    #         Action(name="get_service_details", kwargs={"service_id": "mobile_family_4lines"}),
    #         Action(name="get_service_details", kwargs={"service_id": "internet_fiber_1gb"}),
    #     ],
    #     outputs=[],
    # ),
]
