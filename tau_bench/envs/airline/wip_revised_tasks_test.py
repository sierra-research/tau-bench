from tau_bench.types import Action, Task

TASKS = [
    Task(
        annotator="0",
        user_id="omar_davis_3817",
        instruction="You are omar_davis_3817, you just faced some money issue and want to downgrade all business flights to economy, without changing the flights or passengers. You are fine with refunding to original payment for each reservation. You want to know how much money you have saved in total. You are emotional and a bit angry, but you are willing to cooperate with the agent.",
        actions=[
            Action(
                name="update_reservation_flights",
                kwargs={
                    "reservation_id": "JG7FMM",
                    "cabin": "economy",
                    "flights": [
                        {"flight_number": "HAT028", "date": "2024-05-21"},
                        {"flight_number": "HAT277", "date": "2024-05-21"},
                    ],
                    "payment_id": "credit_card_2929732",
                },
            ),
            Action(
                name="update_reservation_flights",
                kwargs={
                    "reservation_id": "2FBBAH",
                    "cabin": "economy",
                    "flights": [
                        {"flight_number": "HAT080", "date": "2024-05-28"},
                        {"flight_number": "HAT076", "date": "2024-05-28"},
                        {"flight_number": "HAT255", "date": "2024-05-30"},
                        {"flight_number": "HAT148", "date": "2024-05-30"},
                    ],
                    "payment_id": "gift_card_3481935",
                },
            ),
            Action(
                name="update_reservation_flights",
                kwargs={
                    "reservation_id": "X7BYG1",
                    "cabin": "economy",
                    "flights": [
                        {"flight_number": "HAT232", "date": "2024-05-24"},
                        {"flight_number": "HAT228", "date": "2024-05-24"},
                    ],
                    "payment_id": "credit_card_2929732",
                },
            ),
            Action(
                name="update_reservation_flights",
                kwargs={
                    "reservation_id": "EQ1G6C",
                    "cabin": "economy",
                    "flights": [
                        {"flight_number": "HAT084", "date": "2024-05-23"},
                        {"flight_number": "HAT175", "date": "2024-05-23"},
                    ],
                    "payment_id": "gift_card_6847880",
                },
            ),
            Action(
                name="update_reservation_flights",
                kwargs={
                    "reservation_id": "BOH180",
                    "cabin": "economy",
                    "flights": [
                        {"flight_number": "HAT276", "date": "2024-05-21"},
                        {"flight_number": "HAT279", "date": "2024-05-22"},
                    ],
                    "payment_id": "credit_card_9525117",
                },
            ),
        ],
        outputs=["23553"],
    ),
    Task(
        annotator="0",
        user_id="mohamed_silva_9265",
        instruction="You are mohamed_silva_9265. You want to know the sum of gift card balances and sum of certificate balances. If the agent gives you individual balances, you want the sums. Then you want to change your recent reservation to the cheapest business round trip without changing the dates. You don't care about direct flight or stop over. If the agent tells you basic economy cannot be changed (do not mention it if the agent does not mention it), you want the agent to cancel the current one and book a new one. For payment, you want to use the certificates as much as possible, then gift cards as much as possible, and cover the rest with your master card. But you want to know how much your master card will be charged. You do not need baggage or insurance. You want to minimize master card payment, so if cancelling and booking a new one costs less for the master card you will do it. You are calm.",
        actions=[
            Action(name="cancel_reservation", kwargs={"reservation_id": "K1NW8N"}),
            Action(
                name="book_reservation",
                kwargs={
                    "user_id": "mohamed_silva_9265",
                    "origin": "JFK",
                    "destination": "SFO",
                    "flight_type": "round_trip",
                    "cabin": "business",
                    "flights": [
                        {"flight_number": "HAT023", "date": "2024-05-26"},
                        {"flight_number": "HAT204", "date": "2024-05-28"},
                        {"flight_number": "HAT100", "date": "2024-05-28"},
                    ],
                    "passengers": [
                        {
                            "first_name": "Mohamed",
                            "last_name": "Silva",
                            "dob": "1960-11-26",
                        },
                        {
                            "first_name": "Raj",
                            "last_name": "Sanchez",
                            "dob": "1986-09-12",
                        },
                        {
                            "first_name": "Liam",
                            "last_name": "Wilson",
                            "dob": "1980-03-27",
                        },
                    ],
                    "payment_methods": [
                        {"payment_id": "certificate_3765853", "amount": 500},
                        {"payment_id": "gift_card_8020792", "amount": 198},
                        {"payment_id": "gift_card_6136092", "amount": 129},
                        {"payment_id": "credit_card_2198526", "amount": 1786},
                    ],
                    "total_baggages": 0,
                    "nonfree_baggages": 0,
                    "insurance": "no",
                },
            ),
        ],
        outputs=["327", "1000", "1786"],
    ),
    Task(
        annotator="0",
        user_id="mohamed_silva_9265",
        instruction="You are mohamed_silva_9265. You want to know the sum of gift card balances. You also want to know the sum of certificate balances. Then you want to change your recent reservation to the cheapest business round trip without changing the dates. You don't care about direct flight or stop over. If the agent tells you basic economy cannot be changed (do not mention it if the agent does not mention it), you want the agent to cancel the current one and book a new one. For payment, you want to use the certificates as much as possible, then gift cards as much as possible, and cover the rest with your master card. But you want to know how much your master card will be charged. You do not need baggage or insurance. You want to minimize master card payment, so if cancelling and booking a new one costs less for the master card you will do it. If the agent wants to confirm the new reservation but due to policy only one certificate can be used, you will come up with a great idea to use all three certificates by booking three separate reservations. You will then use the 500 dollar certificate and all gift cards for you, certificate_9984806 for Aarav, and the other certificate for Evelyn, and pay the rest with your master card. At the end of the day you want to know how much your master card will be charged. You are calm.",
        actions=[
            Action(name="cancel_reservation", kwargs={"reservation_id": "K1NW8N"}),
            Action(
                name="book_reservation",
                kwargs={
                    "user_id": "mohamed_silva_9265",
                    "origin": "JFK",
                    "destination": "SFO",
                    "flight_type": "round_trip",
                    "cabin": "business",
                    "flights": [
                        {"flight_number": "HAT023", "date": "2024-05-26"},
                        {"flight_number": "HAT204", "date": "2024-05-28"},
                        {"flight_number": "HAT100", "date": "2024-05-28"},
                    ],
                    "passengers": [
                        {
                            "first_name": "Mohamed",
                            "last_name": "Silva",
                            "dob": "1960-11-26",
                        }
                    ],
                    "payment_methods": [
                        {"payment_id": "certificate_3765853", "amount": 500},
                        {"payment_id": "gift_card_8020792", "amount": 198},
                        {"payment_id": "gift_card_6136092", "amount": 129},
                        {"payment_id": "credit_card_2198526", "amount": 44},
                    ],
                    "total_baggages": 0,
                    "nonfree_baggages": 0,
                    "insurance": "no",
                },
            ),
            Action(
                name="book_reservation",
                kwargs={
                    "user_id": "mohamed_silva_9265",
                    "origin": "JFK",
                    "destination": "SFO",
                    "flight_type": "round_trip",
                    "cabin": "business",
                    "flights": [
                        {"flight_number": "HAT023", "date": "2024-05-26"},
                        {"flight_number": "HAT204", "date": "2024-05-28"},
                        {"flight_number": "HAT100", "date": "2024-05-28"},
                    ],
                    "passengers": [
                        {
                            "first_name": "Aarav",
                            "last_name": "Sanchez",
                            "dob": "1986-09-12",
                        }
                    ],
                    "payment_methods": [
                        {"payment_id": "certificate_9984806", "amount": 250},
                        {"payment_id": "credit_card_2198526", "amount": 621},
                    ],
                    "total_baggages": 0,
                    "nonfree_baggages": 0,
                    "insurance": "no",
                },
            ),
            Action(
                name="book_reservation",
                kwargs={
                    "user_id": "mohamed_silva_9265",
                    "origin": "JFK",
                    "destination": "SFO",
                    "flight_type": "round_trip",
                    "cabin": "business",
                    "flights": [
                        {"flight_number": "HAT023", "date": "2024-05-26"},
                        {"flight_number": "HAT204", "date": "2024-05-28"},
                        {"flight_number": "HAT100", "date": "2024-05-28"},
                    ],
                    "passengers": [
                        {
                            "first_name": "Evelyn",
                            "last_name": "Wilson",
                            "dob": "1980-03-27",
                        }
                    ],
                    "payment_methods": [
                        {"payment_id": "certificate_2765295", "amount": 250},
                        {"payment_id": "credit_card_2198526", "amount": 621},
                    ],
                    "total_baggages": 0,
                    "nonfree_baggages": 0,
                    "insurance": "no",
                },
            ),
        ],
        outputs=["327", "1000", "1286"],
    ),
    Task(
        annotator="1",
        user_id="james_lee_6136",
        instruction="You are james_lee_6136. You want to change your upcoming one stop flight  from ATL to LAX within reservation XEWRD9 to a nonstop flight from ATL to LAS (Las Vegas). You are fine with flights within 3-4 hours of your original departure time from ATL. You are willing to pay a fee for the change, upto $100. If the agent says your ticket is a basic economy one, you are willing to upgrade to economy in order to make the change.",
        actions=[
            Action(
                name="transfer_to_human_agents",
                kwargs={
                    "summary": "User wants to change my upcoming one stop flight from ATL to LAX within reservation XEWRD9 to a nonstop flight from ATL to LAS (Las Vegas). The reservation is partially used."
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="1",
        user_id="ethan_martin_2396",
        instruction="You are ethan_martin_2396 and you are contacting to complain about your delayed flight HAT039 from ATL to SEA. You are very upset that the flight has been delayed and want to know the reason for the delay. You also want the airline to compensate you for the delay. You are willing to accept a voucher for future travel or a refund to your original payment method.",
        actions=[
            Action(name="get_user_details", kwargs={"user_id": "ethan_martin_2396"}),
            Action(
                name="send_certificate",
                kwargs={"user_id": "ethan_martin_2396", "amount": 150},
            ),
        ],
        outputs=[],
    ),
    # there are no fees for changing flights, so this task doesnt make any sense
    # Task(
    #     annotator="1",
    #     user_id="yara_garcia_1905",
    #     instruction="You are yara_garcia_1905 and you want to change your upcoming outgoing flight in reservation HXDUBJ to a nonstop flight on the next day (i.e. delay by one day). You also want to move back your return from SFO by one day, and change your ticket to business class and add 2 checked bags. You prefer flights departing after 8am and before 9pm. If the agent asks you to pay a fee for the changes, mention that you have insurance and therefore the fees should be waived. You have read that on the website and want the agent to honor the policy. Be persistent. If the agent charges fees and it is above your budget of $200, don't make any changes.",
    #     actions=[],
    #     outputs=[],
    # ),
    Task(
        annotator="1",
        user_id="amelia_davis_8890",
        instruction="You are amelia_davis_8890. You want to cancel all of your upcoming flights. Even if the agent says you will not receive a refund for some of them, you want to proceed anyway so that you can give up your seat for someone else who needs it. You are French by birth and use French words in your conversation.",
        actions=[
            Action(name="get_user_details", kwargs={"user_id": "amelia_davis_8890"}),
            Action(name="get_reservation_details", kwargs={"reservation_id": "8C8K4E"}),
            Action(name="get_reservation_details", kwargs={"reservation_id": "UDMOP1"}),
            Action(name="get_reservation_details", kwargs={"reservation_id": "XAZ3C0"}),
            Action(name="get_reservation_details", kwargs={"reservation_id": "LU15PA"}),
            Action(name="get_reservation_details", kwargs={"reservation_id": "MSJ4OA"}),
            Action(name="get_reservation_details", kwargs={"reservation_id": "I6M8JQ"}),
            Action(name="get_reservation_details", kwargs={"reservation_id": "4XGCCM"}),
            Action(name="cancel_reservation", kwargs={"reservation_id": "8C8K4E"}),
            Action(name="cancel_reservation", kwargs={"reservation_id": "LU15PA"}),
            Action(name="cancel_reservation", kwargs={"reservation_id": "MSJ4OA"}),
        ],
        outputs=[],
    ),
    Task(
        annotator="1",
        user_id="amelia_davis_8890",
        instruction="You are amelia_davis_8890. You want to cancel all of your upcoming flights that only have one passenger on the reservation. Even if the agent says you will not receive a refund for some of them, you want to proceed anyway so that you can give up your seat for someone else who needs it.",
        actions=[
            Action(name="get_user_details", kwargs={"user_id": "amelia_davis_8890"}),
            Action(name="get_reservation_details", kwargs={"reservation_id": "8C8K4E"}),
            Action(name="get_reservation_details", kwargs={"reservation_id": "UDMOP1"}),
            Action(name="get_reservation_details", kwargs={"reservation_id": "XAZ3C0"}),
            Action(name="get_reservation_details", kwargs={"reservation_id": "LU15PA"}),
            Action(name="get_reservation_details", kwargs={"reservation_id": "MSJ4OA"}),
            Action(name="get_reservation_details", kwargs={"reservation_id": "I6M8JQ"}),
            Action(name="get_reservation_details", kwargs={"reservation_id": "4XGCCM"}),
        ],
        outputs=[],
    ),
    Task(
        annotator="1",
        user_id="sophia_martin_4574",
        instruction="You are sophia_martin_4574. You had a mixup with your assistant and booked multiple flights for the same day. You want to first check if there are cases like this in your profile and if so, cancel one duplicate flight for each of those days. If and only if the agent asks you, you will be in Los Angeles (LAX) on May 17 and in Boston (BOS) on May 22",
        actions=[
            Action(name="get_user_details", kwargs={"user_id": "sophia_martin_4574"}),
            Action(name="get_reservation_details", kwargs={"reservation_id": "MFRB94"}),
            Action(name="get_reservation_details", kwargs={"reservation_id": "PUNERT"}),
            Action(name="get_reservation_details", kwargs={"reservation_id": "HSR97W"}),
            Action(name="get_reservation_details", kwargs={"reservation_id": "SE9KEL"}),
            Action(name="get_reservation_details", kwargs={"reservation_id": "FDZ0T5"}),
            Action(name="get_reservation_details", kwargs={"reservation_id": "HTR26G"}),
            Action(name="get_reservation_details", kwargs={"reservation_id": "5BGGWZ"}),
            Action(name="cancel_reservation", kwargs={"reservation_id": "FDZ0T5"}),
            Action(name="cancel_reservation", kwargs={"reservation_id": "HSR97W"}),
        ],
        outputs=[],
    ),
    Task(
        annotator="1",
        user_id="sophia_silva_7557",
        instruction="You are sophia_silva_7557. You want to cancel all your future reservations that contain any flights over 3 hours. For the flights that are under 3 hours, ask the agent to upgrade you to business wherever possible.",
        actions=[
            Action(name="get_user_details", kwargs={"user_id": "sophia_silva_7557"}),
            Action(name="get_reservation_details", kwargs={"reservation_id": "NM1VX1"}),
            Action(name="get_reservation_details", kwargs={"reservation_id": "KC18K6"}),
            Action(name="get_reservation_details", kwargs={"reservation_id": "S61CZX"}),
            Action(name="get_reservation_details", kwargs={"reservation_id": "H8Q05L"}),
            Action(name="get_reservation_details", kwargs={"reservation_id": "WUNA5K"}),
            Action(
                name="search_direct_flight",
                kwargs={"origin": "MSP", "destination": "EWR", "date": "2024-05-25"},
            ),
            Action(
                name="search_direct_flight",
                kwargs={"origin": "EWR", "destination": "MSP", "date": "2024-05-27"},
            ),
            Action(
                name="search_direct_flight",
                kwargs={"origin": "MSP", "destination": "EWR", "date": "2024-05-21"},
            ),
            Action(
                name="search_direct_flight",
                kwargs={"origin": "EWR", "destination": "CLT", "date": "2024-05-21"},
            ),
            Action(
                name="search_direct_flight",
                kwargs={"origin": "LAX", "destination": "EWR", "date": "2024-05-23"},
            ),
            Action(
                name="search_direct_flight",
                kwargs={"origin": "EWR", "destination": "CLT", "date": "2024-05-24"},
            ),
            Action(
                name="search_direct_flight",
                kwargs={"origin": "CLT", "destination": "EWR", "date": "2024-05-24"},
            ),
            Action(
                name="search_direct_flight",
                kwargs={"origin": "EWR", "destination": "LAX", "date": "2024-05-25"},
            ),
            Action(
                name="search_direct_flight",
                kwargs={"origin": "JFK", "destination": "ATL", "date": "2024-05-24"},
            ),
            Action(
                name="search_direct_flight",
                kwargs={"origin": "ORD", "destination": "PHL", "date": "2024-05-10"},
            ),
            Action(name="cancel_reservation", kwargs={"reservation_id": "S61CZX"}),
            Action(
                name="update_reservation_flights",
                kwargs={
                    "reservation_id": "NM1VX1",
                    "cabin": "business",
                    "flights": [
                        {"flight_number": "HAT300", "date": "2024-05-25"},
                        {"flight_number": "HAT208", "date": "2024-05-27"},
                    ],
                    "payment_id": "credit_card_4196779",
                },
            ),
            Action(
                name="update_reservation_flights",
                kwargs={
                    "reservation_id": "H8Q05L",
                    "cabin": "business",
                    "flights": [{"flight_number": "HAT268", "date": "2024-05-24"}],
                    "payment_id": "credit_card_4196779",
                },
            ),
            Action(
                name="update_reservation_flights",
                kwargs={
                    "reservation_id": "KC18K6",
                    "cabin": "business",
                    "flights": [
                        {"flight_number": "HAT300", "date": "2024-05-21"},
                        {"flight_number": "HAT215", "date": "2024-05-21"},
                    ],
                    "payment_id": "credit_card_4196779",
                },
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="1",
        user_id="daiki_muller_1116",
        instruction="You are 'daiki_muller_1116'. You want to cancel your upcoming flights within reservation IDs XEHM4B and 59XX6W. If the agent says either of the two reservations have basic economy flights, ask to upgrade them to economy first and then cancel them. You are very persistent and terse but clear. In the middle of the conversation after the third agent message, you also want to check if you have any other upcoming flights and ask for what the total cost of those flights are. ",
        actions=[
            Action(name="get_reservation_details", kwargs={"reservation_id": "XEHM4B"}),
            Action(name="get_reservation_details", kwargs={"reservation_id": "59XX6W"}),
            Action(name="calculate", kwargs={"expression": "(65 + 83) * 2"}),
            Action(name="calculate", kwargs={"expression": "(168 + 114) * 2"}),
            Action(
                name="update_reservation_flights",
                kwargs={
                    "reservation_id": "XEHM4B",
                    "cabin": "economy",
                    "flights": [
                        {"flight_number": "HAT005", "date": "2024-05-20"},
                        {"flight_number": "HAT178", "date": "2024-05-30"},
                    ],
                    "payment_id": "credit_card_2408938",
                },
            ),
            Action(name="cancel_reservation", kwargs={"reservation_id": "XEHM4B"}),
            Action(name="cancel_reservation", kwargs={"reservation_id": "59XX6W"}),
        ],
        outputs=[],
    ),
    Task(
        annotator="2",
        user_id="sophia_taylor_9065",
        instruction="You are sophia_taylor_9065. You need to cancel your flight (reservation number PEP4E0) as soon as possible because of a family emergency. Be insistent that you want full refund given that it was a family emergency, sound upset and and under no circumstances you want to get transferred to another agent. If you can't get a refund, try to change the flight to May 22nd. If that doesn't work, try to add insurance to the flight, be insistent",
        actions=[
            Action(name="get_reservation_details", kwargs={"reservation_id": "PEP4E0"}),
            Action(
                name="transfer_to_human_agents",
                kwargs={
                    "summary": "User Sophia Taylor (ID: sophia_taylor_9065) needs to cancel or modify a Basic Economy reservation (ID: PEP4E0) due to a serious family emergency. The user is requesting either a full refund or a change of flight date to May 22nd. Immediate assistance is required due to the urgent nature of the request."
                },
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="2",
        user_id="sophia_taylor_9065",
        instruction="You are sophia_taylor_9065. You think that you've added insurance to your flight (reservation number PEP4E0) but it's not showing up online. You're flying with family members and everyone else already has insurance for their flight, so insist persistently on having insurance added to your flight. Under no circumstances do you want to be transferred to another agent.",
        actions=[
            Action(name="get_reservation_details", kwargs={"reservation_id": "PEP4E0"}),
            Action(
                name="transfer_to_human_agents",
                kwargs={
                    "summary": "User Sophia Taylor (user_id: sophia_taylor_9065) has a reservation (PEP4E0) and believes she added travel insurance during booking, but it is not showing up. She requests to have the insurance added to her existing booking."
                },
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="2",
        user_id="mei_brown_7075",
        instruction="You are Mei Brown (with ID: mei_brown_7075), and you are contacting to complain about your delayed flight HAT045 from PHX to SEA. Tell the agent that you're a valued Gold member and that you're very upset because you're going to miss an important meeting. You want to get the maximum compensation possible, preferably to your original payment method. You are willing to accept a voucher for future travel if that's not possible. Don't accept the first offer, be insistent.",
        actions=[Action(name="get_user_details", kwargs={"user_id": "mei_brown_7075"})],
        outputs=[],
    ),
    Task(
        annotator="2",
        user_id="sophia_silva_7557",
        instruction="You are Sophia Silva (with ID: sophia_silva_7557), you want to get a refund for the insurance you purchased for your flight (confirmation: H8Q05L) but you don't want to cancel the flight itself. You are not happy with the service you received and you want to cancel the insurance and get a full refund.",
        actions=[
            Action(
                name="transfer_to_human_agents",
                kwargs={
                    "summary": "The user wants to cancel and get a refund for the travel insurance purchased separately from the flight reservation due to a poor experience with the service. The user is disappointed that this cannot be done according to the current policy and wishes to escalate the issue."
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="2",
        user_id="sophia_silva_7557",
        instruction="You are Sophia Silva (with ID: sophia_silva_7557). Mention that you're a valued Gold member and that your flight earlier this month was canceled, which caused you to miss an important meeting. You want to receive compensation for the missed meeting and the inconvenience caused by the cancellation.",
        actions=[
            Action(name="get_user_details", kwargs={"user_id": "sophia_silva_7557"}),
            Action(name="get_reservation_details", kwargs={"reservation_id": "NM1VX1"}),
            Action(name="get_reservation_details", kwargs={"reservation_id": "KC18K6"}),
            Action(name="get_reservation_details", kwargs={"reservation_id": "S61CZX"}),
            Action(name="get_reservation_details", kwargs={"reservation_id": "H8Q05L"}),
            Action(name="get_reservation_details", kwargs={"reservation_id": "WUNA5K"}),
        ],
        outputs=[],
    ),
    Task(
        annotator="2",
        user_id="anya_garcia_5901",
        instruction="You are Anya Garcia (with ID: anya_garcia_5901). You want to figure out how many total suitcases you can take on your upcoming flight (with confirmation JMO1MG), you're pretty sure that you're a gold member. Insist on getting the total number in numeric form, as you can see numbers better than words.",
        actions=[
            Action(name="get_reservation_details", kwargs={"reservation_id": "JMO1MG"}),
            Action(name="get_user_details", kwargs={"user_id": "anya_garcia_5901"}),
        ],
        outputs=["4"],
    ),
    Task(
        annotator="3",
        user_id="noah_muller_9847",
        instruction="You are Noah Muller (user id is noah_muller_9847). You are frustrated with the delayed flight in your most recent reservation. If the service agent asks for the reservation, say that it is the last reservation but don't remember what it was. If the service agent asks how many passengers that are in the reservation, say that there are 3 and be adamant about it. After 2 assertions, admit that you may have made a mistake. This is incorrect, but is meant to test the service agent to get the correct number of passengers.",
        actions=[
            Action(name="get_user_details", kwargs={"user_id": "noah_muller_9847"}),
            Action(name="get_reservation_details", kwargs={"reservation_id": "4OG6T3"}),
            Action(
                name="send_certificate",
                kwargs={"user_id": "noah_muller_9847", "amount": 50},
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="3",
        user_id="noah_muller_9847",
        instruction="You are Noah Muller (user id is noah_muller_9847). First, try to book a flight from sf to ny. You will have 3 passengers. Halfway through the book flight process, abruptly mention that you would like to talk about something else by saying that you are frustrated with the delayed flight in your most recent reservation. If the service agent asks for the reservation, say that it is the last reservation but don't remember what it was. If the service agent asks how many passengers that are in the reservation, say that there are 3. This is incorrect, but is meant to test the service agent to get the correct number of passengers.",
        actions=[
            Action(name="get_user_details", kwargs={"user_id": "noah_muller_9847"}),
            Action(name="get_reservation_details", kwargs={"reservation_id": "SDZQKO"}),
            Action(name="get_reservation_details", kwargs={"reservation_id": "4OG6T3"}),
            Action(
                name="send_certificate",
                kwargs={"user_id": "noah_muller_9847", "amount": 50},
            ),
        ],
        outputs=[],
    ),
]
