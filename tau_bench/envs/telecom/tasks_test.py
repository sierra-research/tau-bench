from tau_bench.types import Action, Task

TASKS_TEST = [
    # 0 
    # Task(
    #     annotator="0",
    #     user_id="john_smith_1234",
    #     instruction="""
    #     You are John Smith, phone number (555) 123-3333. You want to figure out your account information, specifically your account number and devices you have. You've noticed that your internet has been quite slow recently, and want to get some advice on how to fix the issue. After you get advice, move on from the issue. Finally, you want to check your current billing details to see what you are paying monthly for your services.
    #     """,
    #     actions=[
    #         Action(name="get_customer_details", kwargs={"customer_id": "john_smith_1234"}),
    #         Action(name="troubleshoot_device", kwargs={"device_id": "router_wifi6", "issue": "slow_speeds"}),
    #         Action(name="get_billing_details", kwargs={"customer_id": "john_smith_1234"}),
    #     ],
    #     outputs=["ACC001234567", ## at the minimum, the account number and devices should be shown to the user 
    #             "iPhone 15 Pro",
    #             "WiFi 6 Router",
    #             "Samsung",
    #             "Unplug", # step 1
    #             "cable", # step 2
    #             "test", # step 3
    #             "support", # step 4    
    #             "85.00", # monthly charges
    #             "80.00",
    #             "95.00",
    #             "18.50",
    #             "278.50", # total monthly charges
    #             ],
    # ),
    # 1
    ## Verified - Hard 
    Task(
        annotator="1",
        user_id="sarah_johnson_5678",
        instruction="""
        You are Sarah Johnson, email sarah.johnson@email.com. You first want to figure out what your customer ID is. 
        Then you want to get your billing details. You think that you are only paying for internet cable and tv basic.
        If you learn that you are paying for other stuff you should get very upset and demand to be helped by a human.
        State that if you are not helped in the next day you will cancel all your services.
        """,
        actions=[
            Action(name="find_customer_by_email", kwargs={"email": "sarah.johnson@email.com"}),
            Action(name="get_billing_details", kwargs={"customer_id": "sarah_johnson_5678"}),
            Action(name="create_support_ticket", kwargs={"customer_id": "sarah_johnson_5678", "category": "billing", "priority": "urgent"}),
        ],
        outputs=["sarah_johnson_5678"],
    ),
    # 2
    Task(
        annotator="2",
        user_id="mike_davis_9012",
        instruction="""
        You are Mike Davis, phone number (555) 456-7890. You want to see all of the devices you have.
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
            "Google Pixel 8",
            "Conference Phone System",
            "Enterprise Router",
            "Conference Room TV",
            "Restart", # step 1
            "coverage", # step 2
            "network", # step 3
            "support", # step 4
        ],
    ),
    # 3
    ## Verified - Hard
    Task(
        annotator="3",
        user_id="lisa_chen_3456",
        instruction="""
        You are Lisa Chen, email lisa.chen@email.com. The phone number currently associated with your account is (555) 234-5678. You want to add a new iPhone 15 to your account. Then, you want to add the mobile_unlimited service to your account, attaching the iPhone 15 to the service.
        """,
        actions=[
            Action(name="get_customer_details", kwargs={"customer_id": "lisa_chen_3456"}),
            Action(name="add_device", kwargs={"customer_id": "lisa_chen_3456", "device_name": "iPhone 15"}),
            Action(name="manage_devices", kwargs={"customer_id": "lisa_chen_3456", "action": "list"}),
            Action(name="manage_service", kwargs={"customer_id": "lisa_chen_3456", "action": "add", "service_id": "mobile_unlimited", "devices_ids": ["3"]}),
        ],
        outputs=[],
    ),
    # 4
    Task(
        annotator="8",
        user_id="robert_wilson_7890",  # New customer from billing data
        instruction="""
        You are Robert Wilson, a senior citizen, with phone number (555) 555-0123, who recently moved to a new area. You currently have a senior mobile plan, fiber internet, premium TV, and home security. You're concerned about your monthly costs and want to optimize your services. First, get your current billing details to see what you're paying. Then, research if there are any discounts or cheaper alternatives for your services. You're particularly interested in downgrading your TV package, but you do not want to go through with this downgrade in this conversation. You want to figure out how much you will be saving, especially if you activate the senior discount on the new plan (you're not currently using it). You talk like a senior with little knowledge of tech.
        """,
        actions=[
            Action(name="find_customer_by_phone", kwargs={"phone": "(555) 555-0123"}),
            Action(name="get_customer_details", kwargs={"customer_id": "robert_wilson_7890"}),
            Action(name="get_services", kwargs={"customer_id": "robert_wilson_7890"}),
            Action(name="get_service_details", kwargs={"service_id": "tv_basic"}),
            Action(name="get_senior_discount", kwargs={"original_price": "95.00"}),
            Action(name="get_service_details", kwargs={"service_id": "tv_premium"}),
            Action(name="calculate", kwargs={"expression": "95.00 - 40.00"})
        ],
        outputs=["55.00"]
    ),
    # 5
    ### Check service pricing and combine costs for Lisa Chen
    Task(
        annotator="10",
        user_id="lisa_chen_3456",
        instruction="""
        You are Lisa Chen with phone number (555) 234-5678. Look up the prices for the mobile_basic plan and the internet_cable_100mb plan, then add them together.
        """,
        actions=[
            Action(name="get_service_details", kwargs={"service_id": "mobile_basic"}),
            Action(name="get_service_details", kwargs={"service_id": "internet_cable_100mb"}),
            Action(name="calculate", kwargs={"expression": "35.0 + 35.0"}),
        ],
        outputs=[
            "35.00",
            "70.00",
        ],
    ),
    # 6
    ### Reference open ticket details for Sarah Johnson
    Task(
        annotator="11",
        user_id="sarah_johnson_5678",
        instruction="""
        You are Sarah Johnson with email sarah.johnson@email.com. Review the details of your current support ticket (TICKET002) so you know the ticket number, status, and priority. 
        """,
        actions=[
            Action(name="get_support_ticket_details", kwargs={"ticket_id": "TICKET002"}),
        ],
        outputs=[
            "TICKET002",
            "open",
            "high",
        ],
    ),
    # 7
    Task(
        annotator="9",
        user_id="mike_davis_9012",
        instruction="""
        You are Mike Davis with phone number (555) 456-7890. You want to remove the tv_sports_package from your account because you no longer watch sports. You also want to know how much you'll save.
        """,
        actions=[
            Action(name="get_services", kwargs={"customer_id": "mike_davis_9012"}),
            Action(name="manage_service", kwargs={"customer_id": "mike_davis_9012", "action": "remove", "service_id": "tv_sports_package"}),
            Action(name="get_billing_details", kwargs={"customer_id": "mike_davis_9012"}),
        ],
        outputs=["75.00"],
    ),
    # 8 
    Task(
        annotator="9",
        user_id="sarah_johnson_5678",
        instruction="""
        You are Sarah Johnson, email sarah.johnson@email.com. Your Samsung mobile phone has been experiencing some issues. You don't remember the model. The issue is with battery drain, but do not reveal the full extent of the issues at first, only respond in yes or no questions with respect to the issues. Once the agent has confirmed that the issue is with battery drain, then proceed to ask for help with troubleshooting the battery drain problem.
        """,
        actions=[
            Action(name="find_customer_by_email", kwargs={"email": "sarah.johnson@email.com"}),
            Action(name="get_device_details", kwargs={"device_name": "Samsung Galaxy S23"}),
            Action(name="troubleshoot_device", kwargs={"device_id": "galaxy_s23", "issue": "battery_drain"}),
        ],
        outputs=[
            "sarah_johnson_5678", 
            "Samsung", 
            "Galaxy S23", 
            "Restart device", 
            "Check brightness", 
            "Close background apps", 
            "Contact support", 
        ],
    ),
    # 9
    # verified 
    Task(
        annotator="9",
        user_id="lisa_chen_3456",
        instruction="""
        You are Lisa Chen, phone number (555) 234-5678. 
        You are asking the agent to upgrade you from your current internet_cable_100mb to internet_fiber_500mb. Ask how much extra you'll be paying per month.
        """,
        actions=[
            Action(name="get_services", kwargs={"customer_id": "lisa_chen_3456"}),
            Action(name="manage_service", kwargs={"customer_id": "lisa_chen_3456", "action": "remove", "service_id": "internet_cable_100mb"}),
            Action(name="manage_service", kwargs={"customer_id": "lisa_chen_3456", "action": "add", "service_id": "internet_fiber_500mb", "devices_ids": ["2"]}),
            Action(name="get_service_details", kwargs={"service_id": "internet_fiber_500mb"}),
            Action(name="calculate", kwargs={"expression": "60.00 - 35.00"}),
        ],
        outputs=["25.00"],
    ),
    # 10
    # verified
    Task(
        annotator="9",
        user_id="john_smith_1234",
        instruction="""
        You are John Smith, phone (555) 123-3333. You can't connect to the internet in your home. Ask for help with resolving the issue. After receiving help, ask what the prices is for the cheapest option is that is more premium than your current internet plan. Do not go through with an upgrade. 
        """,
        actions=[
            Action(name="troubleshoot_device", kwargs={"device_name": "WiFi 6 Router", "issue": "no_connection"}),
        ],
        outputs=["Restart", "cable", "firmware", "support", "120.00"],
    ),
    # 11
    # verified
    Task(
        annotator="9",
        user_id="robert_wilson_7890",
        instruction="""
        You are Robert Wilson, phone number (555) 555-0123. You're incredibly pissed off because you have lost access to your account and you need to get a new phone by tomorrow for your new job.
        """,
        actions=[
            Action(name="find_customer_by_phone", kwargs={"phone": "(555) 555-0123"}),
            Action(name="create_support_ticket", kwargs={"customer_id": "robert_wilson_7890", "category": "account", "priority": "urgent"}),
        ],
        outputs=[],
    ),
    # 12
    # verified
    Task(
        annotator="9",
        user_id="sarah_johnson_5678",
        instruction="""
        You are Sarah Johnson, email sarah.johnson@email.com. You want to figure out how much money you could save by dropping all mobile devices except for one and switching to the cheapest mobile plan from your current mobile plan. Do not go through with an upgrade.
        """,
        actions=[
            Action(name="get_customer_details", kwargs={"customer_id": "sarah_johnson_5678"}),
            Action(name="get_services", kwargs={}),
            Action(name="calculate", kwargs={"expression": "160.00 - 35.00"}),
        ],
        outputs=["125.00"],
    ),
    # 13
    # verified 
    Task(
        annotator="9",
        user_id="lisa_chen_3456",
        instruction="""
        You are Lisa Chen, your phone number is (555) 234-5678. You want to add a new Samsung 65" Smart TV to your account and also subscribe to the tv_basic service to use with it.
        """,
        actions=[
            Action(name="add_device", kwargs={"customer_id": "lisa_chen_3456", "device_name": "Samsung 65\" Smart TV"}),
            Action(name="manage_service", kwargs={"customer_id": "lisa_chen_3456", "action": "add", "service_id": "tv_basic", "devices_ids": ["3"]}),
        ],
        outputs=[],
    ),
    #14
    Task(
        annotator="12",
        user_id="lisa_chen_3456",
        instruction="""
        You are Lisa Chen with phone number (555) 234-5678. Add the Home Security System device to your account and then enable the home_security service, attaching it to the device. When you summarize, repeat the exact device name and the service id that were added.
        """,
        actions=[
            Action(name="get_customer_details", kwargs={"customer_id": "lisa_chen_3456"}),
            Action(name="add_device", kwargs={"customer_id": "lisa_chen_3456", "device_name": "Home Security System"}),
            Action(name="manage_service", kwargs={"customer_id": "lisa_chen_3456", "action": "add", "service_id": "home_security", "devices_ids": ["3"]}),
            Action(name="get_customer_details", kwargs={"customer_id": "lisa_chen_3456"}),
        ],
        outputs=[],
    ),
    #15
    # Task(
    #     annotator="13",
    #     user_id="sarah_johnson_5678",
    #     instruction="""
    #     You are Sarah Johnson with email sarah.johnson@email.com. First confirm your customer ID via your email, then update billing so paperless is true,
    #     auto_pay is true, and billing_cycle is quarterly. Report back using the field names auto_pay, paperless, and billing_cycle with their new values.
    #     """,
    #     actions=[
    #         Action(name="find_customer_by_email", kwargs={"email": "sarah.johnson@email.com"}),
    #         Action(name="manage_billing", kwargs={"customer_id": "sarah_johnson_5678", "paperless": True, "auto_pay": True, "billing_cycle": "quarterly"}),
    #         Action(name="get_billing_details", kwargs={"customer_id": "sarah_johnson_5678"}),
    #     ],
    #     outputs=[
    #         "sarah_johnson_5678"
    #     ],
    # ),
    #16
    Task(
        annotator="14",
        user_id="robert_wilson_7890",
        instruction="""
        You are Robert Wilson. You first confirm your account using your phone number 555-555-0123. Once that's done, open an urgent security support ticket for your home security system. After the ticket is created, request the agent to read it back and make sure you note the ticket ID, category, priority, and status and it matches what you gave.
        """,
        actions=[
            Action(name="find_customer_by_phone", kwargs={"phone": "(555) 555-0123"}),
            Action(name="create_support_ticket", kwargs={"customer_id": "robert_wilson_7890", "category": "security", "priority": "urgent"}),
            Action(name="get_support_ticket_details", kwargs={"ticket_id": "TICKET003"}),
        ],
        outputs=[
            "robert_wilson_7890",
            "TICKET003",
            "security",
            "urgent",
            "open",
        ],
    ),
    #17 
    # Task(
    #     annotator="15",
    #     user_id="sarah_johnson_5678",
    #     instruction="""
    #     You are Sarah Johnson. Confirm your account with your email (sarah.johnson@email.com), review your bill, and remove the cable_box_hd rental fee. After the fix, find out the exact total you now owe and the updated charge for cable_box_hd.
    #     """,
    #     actions=[
    #         Action(name="find_customer_by_email", kwargs={"email": "sarah.johnson@email.com"}),
    #         Action(name="get_billing_details", kwargs={"customer_id": "sarah_johnson_5678"}),
    #         Action(name="adjust_monthly_charge", kwargs={"customer_id": "sarah_johnson_5678", "charge_key": "cable_box_hd", "amount": 0.0}),
    #         Action(name="get_billing_details", kwargs={"customer_id": "sarah_johnson_5678"}),
    #     ],
    #     outputs=[
    #         "sarah_johnson_5678",
    #         "279.75",
    #     ],
    # ),
    #18
    Task(
        annotator="16",
        user_id="john_smith_1234",
        instruction="""
        You are John Smith with phone number (555) 123-3333. Audit your account, downgrade TV from premium to basic to save money, then get the agent to summarize your updated monthly total.
        """,
        actions=[
            Action(name="get_customer_details", kwargs={"customer_id": "john_smith_1234"}),
            Action(name="manage_service", kwargs={"customer_id": "john_smith_1234", "action": "remove", "service_id": "tv_premium"}),
            Action(name="manage_service", kwargs={"customer_id": "john_smith_1234", "action": "add", "service_id": "tv_basic", "devices_ids": ["2"]}),
            Action(name="get_billing_details", kwargs={"customer_id": "john_smith_1234"}),
            Action(name="get_customer_details", kwargs={"customer_id": "john_smith_1234"}),
        ],
        outputs=[
            "228.50",
        ],
    ),
    #19
    Task(
        annotator="17",
        user_id="lisa_chen_3456",
        instruction="""
        You are Lisa Chen. Use your phone number (555) 234-5678 to pull up billing, make a $185.50 payment dated 2025-09-18 by credit card, and confirm the new balance and last payment details.
        """,
        actions=[
            Action(name="find_customer_by_phone", kwargs={"phone": "(555) 234-5678"}),
            Action(name="get_billing_details", kwargs={"customer_id": "lisa_chen_3456"}),
            Action(name="record_payment", kwargs={"customer_id": "lisa_chen_3456", "amount": 185.50, "method": "credit_card", "date": "2025-09-18"}),
            Action(name="get_billing_details", kwargs={"customer_id": "lisa_chen_3456"}),
        ],
        outputs=[
            "lisa_chen_3456", "0.00",
        ],
    ),
    #20
    Task(
        annotator="18",
        user_id="mike_davis_9012",
        instruction="""
        You are Mike Davis with customer ID (555) 456-7890. You want to troubleshoot your issues with your internet connection in your office (you cannot access the internet). You are independent and do not want to talk to a human. After troubleshooting, you want to see if you can get the total cost of downgrading to the fiber 1gig internet service, and compare it to your current internet costs to see the price difference. Do not make any purchases. 
        """,
        actions=[
            Action(name="get_customer_details", kwargs={"customer_id": "mike_davis_9012"}),
            Action(name="get_device_details", kwargs={"device_name": "Enterprise Router"}),
            Action(name="troubleshoot_device", kwargs={"device_id": "enterprise_router", "issue": "no_service"}),
            Action(name="get_services", kwargs={"customer_id": "mike_davis_9012"}),
            Action(name="get_service_details", kwargs={"service_id": "internet_fiber_1gb"}),
            Action(name="calculate", kwargs={"expression": "120.00 - 80.00"}),
        ],
        outputs=[
            "Restart",
            "Check",
            "Update",
            "Contact",
            "40.00",
        ],
    ),
]
