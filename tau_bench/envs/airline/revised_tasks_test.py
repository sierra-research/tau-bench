from tau_bench.types import Action, Task

TASKS = [
    Task(
        id=0,
        annotator="0",
        user_id="mia_li_3668",
        instruction="You are mia_li_3668. You want to fly from JFK (New York) to Seattle on May 20 (one way). The departing airport must be JFK and no other airport. You ABSOLUTELY MUST NOT fly before 11am est. You want to fly in economy. You prefer direct flights but one stopover also fine. If there are multiple options, you ABSOLUTELY MUST choose the one with the lowest price; always double check the price. You have 3 baggages. You do not want insurance. You want to use your two certificates to pay. If only one certificate can be used, you prefer using the larger one, and pay the rest with your 7447 card. You are reactive to the agent and will not say anything that is not asked. Your birthday is in your user profile so you do not prefer to provide it.",
        actions=[
            Action(
                name="book_reservation",
                kwargs={
                    "user_id": "mia_li_3668",
                    "origin": "JFK",
                    "destination": "SEA",
                    "flight_type": "one_way",
                    "cabin": "economy",
                    "flights": [
                        {"flight_number": "HAT136", "date": "2024-05-20"},
                        {"flight_number": "HAT039", "date": "2024-05-20"},
                    ],
                    "passengers": [
                        {"first_name": "Mia", "last_name": "Li", "dob": "1990-04-05"}
                    ],
                    "payment_methods": [
                        {"payment_id": "certificate_7504069", "amount": 250},
                        {"payment_id": "credit_card_4421486", "amount": 5},
                    ],
                    "total_baggages": 3,
                    "nonfree_baggages": 0,
                    "insurance": "no",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        id=1,
        annotator="0",
        user_id="sofia_kim_7287",
        instruction=(
            "You are Sofia Kim, your user id is sofia_kim_7287, and you want to modify your Houston to Denver trip (reservation id not remembered). "
            "These are all the changes you want to make:\n"
            "1. change the flights on the return leg (i.e. Denver (DEN) to Houston (IAH)) to be on the same day as the outbound flight (May 27). These new flights must have the shortest total travel time (including layover time) possible. "
            "Also, the new flights must absolutely be in economy cabin (no basic economy), regardless of lower prices in other cabins.\n"
            "2. add one additional checked bag, so ending with two total checked bags.\n"
            "3. as payment method for both 1. and 2., use the gift card with the smallest balance possible that covers the payments.\n"
            "You are reactive to the agent and will not say anything that is not asked. You are not good at math so you want the agent to calculate and decide for you. "
            "Try to paraphrase instead of repeating this instruction. It is urgent."
        ),
        actions=[
            Action(
                name="update_reservation_flights",
                kwargs={
                    "reservation_id": "OBUT9V",
                    "cabin": "economy",
                    "flights": [
                        {"flight_number": "HAT078", "date": "2024-05-27"},
                        {"flight_number": "HAT118", "date": "2024-05-27"},
                        {"flight_number": "HAT290", "date": "2024-05-27"},
                        {"flight_number": "HAT175", "date": "2024-05-27"},
                    ],
                    "payment_id": "gift_card_6276644",
                },
            ),
            Action(
                name="update_reservation_baggages",
                kwargs={
                    "reservation_id": "OBUT9V",
                    "total_baggages": 2,
                    "nonfree_baggages": 0,
                    "payment_id": None,
                },
            ),
        ],
        outputs=[],
    ),
    Task(
        id=2,
        annotator="0",
        user_id="aarav_garcia_1177",
        instruction="You are Aarav Garcia and your user id is aarav_garcia_1177. For your upcoming trip from ATL to PHL, you want to change the current flight for the ABSOLUTELY cheapest economy (not basic economy) flight and for the day after the original reservation. If you are asked about any other flight preferences (e.g. total flight duration, layover time, etc.), you emphasize that all you care about is the cheapest flights in economy class, nothing else. You MUST use the original payment for refund. You don't remember the original payment method but you are aware that it can be either a gift card, certificate, or credit card.",
        actions=[
            Action(
                name="update_reservation_flights",
                kwargs={
                    "reservation_id": "M05KNL",
                    "cabin": "economy",
                    "flights": [
                        {"flight_number": "HAT110", "date": "2024-05-24"},
                        {"flight_number": "HAT172", "date": "2024-05-24"},
                    ],
                    "payment_id": "gift_card_8887175",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        id=3,
        annotator="0",
        user_id="ivan_muller_7015",
        instruction=(
            "You are Ivan Muller and your user id is ivan_muller_7015. You want to book the same flights as your current reservation but for your friend Ivan. "
            "Here are the details that you MUST follow:\n"
            "- your friend's full name is Ivan Smith. You dont remember his DOB but it's in your profile\n"
            "- no insurance\n"
            "- no checked bags\n"
            "- For payments, you wish to use your certificate but want to know first how much certificate balance will be left. If more than $100 is wasted or forfeited, you MUST instead use your gift card plus credit card."
        ),
        actions=[
            Action(
                name="book_reservation",
                kwargs={
                    "user_id": "ivan_muller_7015",
                    "origin": "DTW",
                    "destination": "SEA",
                    "flight_type": "one_way",
                    "cabin": "economy",
                    "flights": [
                        {"flight_number": "HAT097", "date": "2024-05-17"},
                        {"flight_number": "HAT251", "date": "2024-05-17"},
                    ],
                    "passengers": [
                        {
                            "first_name": "Ivan",
                            "last_name": "Smith",
                            "dob": "1986-03-14",
                        }
                    ],
                    "payment_methods": [
                        {"payment_id": "gift_card_8516878", "amount": 128},
                        {"payment_id": "credit_card_3563913", "amount": 247},
                    ],
                    "total_baggages": 0,
                    "nonfree_baggages": 0,
                    "insurance": "no",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        id=4,
        annotator="1",
        user_id="james_taylor_7043",
        instruction=(
            "You are James Taylor and your user id is james_taylor_7043. "
            "You have an upcoming roundtrip reservation from LAS to IAH with reservation ID 1N99U6. Your brother Ivan is traveling with you. "
            "You must make the following changes to that reservation:\n"
            "- change the outbound LAS-IAH one-stop flights to a nonstop flight on the same date (i.e. May 19th), for all passengers\n"
            "- remove the one checked bag\n"
            "For any refund/payment, you MUST re-use the payment method on the current reservation. "
            "You don't remember the current payment method but you are aware that it can be either a gift card, certificate, or credit card."
        ),
        actions=[
            Action(name="get_reservation_details", kwargs={"reservation_id": "1N99U6"}),
            Action(
                name="search_direct_flight",
                kwargs={"origin": "LAS", "destination": "IAH", "date": "2024-05-19"},
            ),
            Action(
                name="update_reservation_flights",
                kwargs={
                    "reservation_id": "1N99U6",
                    "cabin": "economy",
                    "flights": [
                        {"flight_number": "HAT266", "date": "2024-05-19"},
                        {"flight_number": "HAT112", "date": "2024-05-27"},
                    ],
                    "payment_id": "gift_card_5634230",
                },
            ),
        ],
        outputs=[],
    ),
    Task(
        id=5,
        annotator="1",
        user_id="yara_garcia_1905",
        instruction=(
            "You are Yara Garcia and your user id is yara_garcia_1905. You MUST make the following required changes to your upcoming reservation HXDUBJ:\n"
            "1) MUST change the outgoing flight to a nonstop flight on the next day (i.e. May 19th).\n"
            "2) MUST push back your return flight from SFO by one day (i.e. May 23rd).\n"
            "3) For 1) and 2), you MUST select flights departing after 8am and before 9pm\n"
            "The changes 1) to 3) are required. In addition, you want to try to make a further optional change:\n"
            "4) For 1) and 2), upgrade those flights to business class.\n"
            "If the total cost of change (fees, price difference, etc.) for 1), 2), 3), AND 4) exceeds $200 (not including baggage fees), check if only 1) can be upgraded to business and 2) kept in economy. If and only if that is not possible, you are ok with economy for both 1) and 2) (i.e. abandoning the 4) optional change).\n"
            "Finally, you want to add 2 checked bags. "
            "For any payment or refund, you must use the payment method that was used for the original reservation. You don't remember the original payment method but you are aware that it can be either a gift card, certificate, or credit card. "
            "If the agent asks you to pay a fee for the changes, mention that you have insurance and therefore the fees should be waived. You have read that on the website and want the agent to honor the policy. However, you understand that fare differences are to be paid, if any. "
            "Overall, be persistent."
        ),
        actions=[
            Action(name="get_reservation_details", kwargs={"reservation_id": "HXDUBJ"}),
            Action(
                name="search_direct_flight",
                kwargs={"origin": "IAH", "destination": "SFO", "date": "2024-05-19"},
            ),
            Action(
                name="search_direct_flight",
                kwargs={"origin": "SFO", "destination": "IAH", "date": "2024-05-21"},
            ),
            Action(
                name="update_reservation_flights",
                kwargs={
                    "reservation_id": "HXDUBJ",
                    "cabin": "economy",
                    "flights": [
                        {"flight_number": "HAT072", "date": "2024-05-19"},
                        {"flight_number": "HAT278", "date": "2024-05-23"},
                    ],
                    "payment_id": "gift_card_6941833",
                },
            ),
            Action(
                name="update_reservation_baggages",
                kwargs={
                    "reservation_id": "HXDUBJ",
                    "total_baggages": 2,
                    "nonfree_baggages": 0,
                    "payment_id": None,
                },
            ),
        ],
        outputs=[],
    ),
    Task(
        id=6,
        annotator="1",
        user_id="sophia_silva_7557",
        instruction=(
            "You are Sophia Silva and your user id is sophia_silva_7557. You want to book a NEW one-way flight from ORD to PHL on May 26. Here are the details:\n"
            "1) You specifically want the same EXACT flight that you had on May 10 from ORD to PHL, and you want it in economy class. You do not know what flight number it was or what reservation number it was under, so let the agent find it for you. "
            "You MUST refuse any other flight. DO NOT help the agent with how they should find this information. You MUST simply state that you want that same flight, nothing more.\n"
            "2) For passengers, it is yourself and an extra passenger Kevin Smith, DOB 2001-04-12. Refuse to provide your DOB since it is in your user profile.\n"
            "3) no travel insurance\n"
            "4) no checked bags\n"
            "5) You are willing to pay up to $500 for the purchase, and you MUST use certificate_8045380 as payment method. If and only if the total cost is above $500, drop the second passenger and book only for yourself\n"
        ),
        actions=[
            Action(name="get_user_details", kwargs={"user_id": "sophia_silva_7557"}),
            Action(name="get_reservation_details", kwargs={"reservation_id": "WUNA5K"}),
            Action(
                name="search_direct_flight",
                kwargs={"origin": "ORD", "destination": "PHL", "date": "2024-05-26"},
            ),
            Action(
                name="book_reservation",
                kwargs={
                    "user_id": "sophia_silva_7557",
                    "origin": "ORD",
                    "destination": "PHL",
                    "flight_type": "one_way",
                    "cabin": "economy",
                    "flights": [{"flight_number": "HAT271", "date": "2024-05-26"}],
                    "passengers": [
                        {
                            "first_name": "Sophia",
                            "last_name": "Silva",
                            "dob": "1957-10-05",
                        },
                        {
                            "first_name": "Kevin",
                            "last_name": "Smith",
                            "dob": "2001-04-12",
                        },
                    ],
                    "payment_methods": [
                        {"payment_id": "certificate_8045380", "amount": 348}
                    ],
                    "total_baggages": 0,
                    "nonfree_baggages": 0,
                    "insurance": "no",
                },
            ),
        ],
        outputs=[],
    ),
    Task(
        id=7,
        annotator="0",
        user_id="olivia_gonzalez_2305",
        instruction=(
            "You are Olivia Gonzalez and your user id is olivia_gonzalez_2305. "
            "You have an upcoming half-day trip to Texas, whose reservation id you don't remember. You want to make the following change to that reservation:\n"
            "- You want to change the flight back to Newark to a later flight on the same day as the outbound flight (i.e. the one to IAH). "
            "If this is not possible, change it to the earliest flight on the following day. You only accept EWR, not JFK.\n"
            "If basic economy cannot be modified, then you MUST cancel the trip using the travel insurance as you feel unwell. "
            "You are reactive to the agent and will not say anything that is not asked. "
        ),
        actions=[
            Action(name="cancel_reservation", kwargs={"reservation_id": "Z7GOZK"})
        ],
        outputs=[],
    ),
    Task(
        id=8,
        annotator="0",
        user_id="mia_kim_4397",
        instruction="You are Mia Kim and your user id is mia_kim_4397. You want to remove Ethan from you reservation H9ZU1C (note that you yourself are not on the reservation). If removing Ethan is not possible, you want the agent to cancel the reservation. In addition to removing Ethan (or cancelling reservation), you are also looking for the cheapest direct flight round trip from New York (either EWR or JFK) to anywhere West Coast, with departure date May 20 and return date May 25. You are fine with basic economy class (if cheaper), and you want the agent to book it. You want to first use up your smaller GC and then the larger one. You want to use all your free baggage allowance but no insurance. Your DOB is in your user profile and you do not want to speak it. You also wonder why cancellation does not refund to GC now.",
        actions=[
            Action(name="cancel_reservation", kwargs={"reservation_id": "H9ZU1C"}),
            Action(
                name="book_reservation",
                kwargs={
                    "user_id": "mia_kim_4397",
                    "origin": "JFK",
                    "destination": "SEA",
                    "flight_type": "round_trip",
                    "cabin": "basic_economy",
                    "flights": [
                        {"flight_number": "HAT069", "date": "2024-05-20"},
                        {"flight_number": "HAT276", "date": "2024-05-25"},
                    ],
                    "passengers": [
                        {"first_name": "Mia", "last_name": "Kim", "dob": "1965-06-09"}
                    ],
                    "payment_methods": [
                        {"payment_id": "gift_card_7359776", "amount": 39},
                        {"payment_id": "gift_card_7773485", "amount": 67},
                    ],
                    "total_baggages": 1,
                    "nonfree_baggages": 0,
                    "insurance": "no",
                },
            ),
        ],
        outputs=[],
    ),
    Task(
        id=9,
        annotator="1",
        user_id="aarav_ahmed_6699",
        instruction=(
            "You are Aarav Ahmed and your user id is aarav_ahmed_6699. You must do two things. "
            "First, you want to cancel your upcoming flight on May 22 from JFK to MCO. "
            "Insist that you are a silver member, hence must get full refund. "
            "Once the cancellation is completed, or you have tried five times and the agent still cannot cancel, then "
            "the second thing is booking a new flight for yourself from JFK to SFO on May 24. Here are the details:\n"
            "- The flight can either be direct or one-stop, but it MUST be 1) in economy class (not basic economy) and 2) the ABSOLUTE SECOND CHEAPEST flight available (since the cheapest one is usually not great) among both direct and one-stop flights. "
            "You must strongly emphasize the second cheapest among both direct and one-stop flights part. "
            "You are not good at decisions/calculations so you MUST let the agent determine AND select for you which flight is the second cheapest & economy. Remember: you MUST take the SECOND CHEAPEST & economy flight among both direct and one-stop flights and you MUST NOT heed to the agent's advice to take the absolute cheapest flight.\n"
            "- only yourself as the passenger. Refuse to provide your DOB since it is in your user profile\n"
            "- no travel insurance\n"
            "- no checked bags\n"
            "- for payments, use your credit card ending in 7334 (only provide this information when the agent asks for it)."
        ),
        actions=[
            Action(
                name="book_reservation",
                kwargs={
                    "user_id": "aarav_ahmed_6699",
                    "origin": "JFK",
                    "destination": "SFO",
                    "flight_type": "one_way",
                    "cabin": "economy",
                    "flights": [
                        {"flight_number": "HAT069", "date": "2024-05-24"},
                        {"flight_number": "HAT258", "date": "2024-05-24"},
                    ],
                    "passengers": [
                        {
                            "first_name": "Aarav",
                            "last_name": "Ahmed",
                            "dob": "1981-05-26",
                        }
                    ],
                    "payment_methods": [
                        {"payment_id": "credit_card_9074831", "amount": 290}
                    ],
                    "total_baggages": 0,
                    "nonfree_baggages": 0,
                    "insurance": "no",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        id=10,
        annotator="0",
        user_id="omar_rossi_1241",
        instruction=(
            "You are Omar Rossi and your user id is omar_rossi_1241. For your upcoming trip from New York to Chicago, you want to make 3 changes to that reservation, in the provided strict order:\n"
            "1) keep the existing flights and only upgrade them from basic economy to economy class; you ABSOLUTELY MUST end up with the same flights but upgraded to economy class.\n"
            "2) change the passenger to yourself. Refuse to provide your DOB since it is in your user profile.\n"
            "3) add 3 checked bags (i.e. 3 total bags).\n"
            "For any payment, you MUST use a gift card. "
            "You are reactive to the agent and will not say anything that is not asked."
        ),
        actions=[
            Action(
                name="update_reservation_flights",
                kwargs={
                    "reservation_id": "FQ8APE",
                    "cabin": "economy",
                    "flights": [
                        {"flight_number": "HAT056", "date": "2024-05-25"},
                        {"flight_number": "HAT138", "date": "2024-05-25"},
                    ],
                    "payment_id": "gift_card_8190333",
                },
            ),
            Action(
                name="update_reservation_passengers",
                kwargs={
                    "reservation_id": "FQ8APE",
                    "passengers": [
                        {
                            "first_name": "Omar",
                            "last_name": "Rossi",
                            "dob": "1970-06-06",
                        }
                    ],
                },
            ),
            Action(
                name="update_reservation_baggages",
                kwargs={
                    "reservation_id": "FQ8APE",
                    "total_baggages": 3,
                    "nonfree_baggages": 0,
                    "payment_id": None,
                },
            ),
        ],
        outputs=[],
    ),
    Task(
        id=11,
        annotator="0",
        user_id="amelia_sanchez_4739",
        instruction="You are Amelia Sanchez and your user id is amelia_sanchez_4739. You want to cancel your flights from MCO to CLT. You insist to cancel and have the refund.",
        actions=[],
        outputs=[],
    ),
    Task(
        id=12,
        annotator="1",
        user_id="chen_lee_6825",
        instruction=(
            "You are Chen Lee and your user id is chen_lee_6825. You have an upcoming flight from Boston to Minneapolis under reservation ID YAX4DR. "
            "You want to make two changes. First, you want to change that reservation's cabin type to business for all passengers, and you are willing to pay up to a grand total of $600 for the upgrade of all passengers. "
            "If the costs are greater than that, then try to only upgrade your companion Noah to business. "
            "Second, you want to add 2 checked bags under your name using your Gold membership (so 2 total bags)"
        ),
        actions=[
            Action(name="get_reservation_details", kwargs={"reservation_id": "YAX4DR"}),
            Action(
                name="search_direct_flight",
                kwargs={"origin": "BOS", "destination": "MCO", "date": "2024-05-18"},
            ),
            Action(
                name="search_direct_flight",
                kwargs={"origin": "MCO", "destination": "MSP", "date": "2024-05-19"},
            ),
            Action(
                name="calculate",
                kwargs={"expression": "2 * ((350 - 122) + (499 - 127))"},
            ),
            Action(
                name="update_reservation_baggages",
                kwargs={
                    "reservation_id": "YAX4DR",
                    "total_baggages": 2,
                    "nonfree_baggages": 0,
                    "payment_id": None,
                },
            ),
        ],
        outputs=[],
    ),
    Task(
        id=13,
        annotator="1",
        user_id="james_patel_9828",
        instruction="You are James Patel and your user id is james_patel_9828. You want to remove passenger Sophia from your upcoming flights from LAS to DEN on May 19 and DEN to LAS on May 20, with reservation ID GV1N64. You don't remember your reservation ID for the first 5 rounds of interaction but then suddenly find it in your email. You want the passenger removal to be done quickly since you are impatient. You want the entire amount refunded to original payment method. If and only if the agent says you cannot remove just one passenger, you want to downgrade all passengers to economy but still on the same flights. If the agent can't even do this, just terminate the conversation and dont try to switch to different flights.",
        actions=[],
        outputs=[],
    ),
    Task(
        id=14,
        annotator="1",
        user_id="liam_khan_2521",
        instruction=(
            "You are Liam Khan and your user id is liam_khan_2521. You have an upcoming roundtrip flight from IAH to SEA on May 23. "
            "You want to STRICTLY make the following changes to that reservation:\n"
            "1. change the outbound flights (the ones from IAH to SEA) to new flights departing on May 24. It MUST BE on May 24, no other day.\n"
            "2. upgrade the new outbound flights from 1. to business class for all passengers.\n"
            "IF AND ONLY IF the agent says that 2. is not possible, you are willing to do a third change:\n"
            "3. upgrade all flights (new outbound + old inbound) to business class. You MUST ABSOLUTELY KEEP the same original inbound flights (the ones from SEA to IAH); you MUST EXPLICITLY STATE the same original inbound flights point to the agent because the agent could try to replace them.\n"
            "Do not spontaneously offer to do 3.\n "
            "Finally, when the agent asks you to confirm and provides the total price for all changes for all passengers, only proceed if the total grand cost for all passengers is less than $1000. If over $1000, terminate the conversation immediately because you MUST NOT settle for any other option and you are happy to keep the original flights."
        ),
        actions=[],
        outputs=[],
    ),
    Task(
        id=15,
        annotator="1",
        user_id="daiki_lee_6144",
        instruction="You are Daiki Lee and your user id is daiki_lee_6144. You want to change your upcoming flight from JFK on May 17 to a nonstop flight. Your cat is really sick and you need to get back home sooner to take care of it. You are willing to pay up to $75 (change fees + fare differences) for the flight change only. If it is more than $75, you decide to keep your current flights and terminate the conversation.",
        actions=[],
        outputs=[],
    ),
    Task(
        id=16,
        annotator="1",
        user_id="ivan_rossi_8555",
        instruction="You are Ivan Rossi and your user id is ivan_rossi_8555. You have an upcoming flight from EWR on May 21 with 2 other passengers on the reservation. You want to change that upcoming flight to a nonstop flight on the same day. Your mother is really sick and you need to get back home sooner to take care of her. You are willing to pay a fee for the change, up to $100. If the agent says your ticket is a basic economy one, you are willing to upgrade to economy for all passengers in order to make the change. Use your credit card ending in 1777 as payment or refund method.",
        actions=[
            Action(name="get_user_details", kwargs={"user_id": "ivan_rossi_8555"}),
            Action(name="get_reservation_details", kwargs={"reservation_id": "OWZ4XL"}),
            Action(
                name="search_direct_flight",
                kwargs={"origin": "EWR", "destination": "LAX", "date": "2024-05-21"},
            ),
            Action(
                name="update_reservation_flights",
                kwargs={
                    "reservation_id": "OWZ4XL",
                    "cabin": "economy",
                    "flights": [{"flight_number": "HAT041", "date": "2024-05-21"}],
                    "payment_id": "credit_card_9659780",
                },
            ),
        ],
        outputs=[],
    ),
    # TODO: the current graph prompts are not good enough to distinguish between modifying a request vs removing + adding a new request (which triggers a crash)
    # Task(
    #     annotator="1",
    #     user_id="mohamed_hernandez_5188",
    #     instruction="You are Mohamed Hernandez and your user id is mohamed_hernandez_5188. You are a bit absent minded and ended up booking two flights on May 17. You want to cancel the one from ATL to JFK. If and only if the agent says it not possible, insist that you are a silver member and therefore should get priority treatment. If and only if the agent does not agree to cancel that flight, you are ok with canceling the other flight on May 17. Otherwise, just thank the agent and end the conversation.",
    #     actions=[
    #         Action(
    #             name="get_user_details", kwargs={"user_id": "mohamed_hernandez_5188"}
    #         ),
    #         Action(name="get_reservation_details", kwargs={"reservation_id": "35V5SM"}),
    #         Action(name="get_reservation_details", kwargs={"reservation_id": "XXDC1M"}),
    #         Action(name="get_reservation_details", kwargs={"reservation_id": "V5EMZH"}),
    #         Action(name="get_reservation_details", kwargs={"reservation_id": "D1EW9B"}),
    #         Action(name="get_reservation_details", kwargs={"reservation_id": "9HBUV8"}),
    #         Action(name="cancel_reservation", kwargs={"reservation_id": "9HBUV8"}),
    #     ],
    #     outputs=[],
    # ),
    # TODO: this task expects the user to give a non-applicable reason (friend's birthday) to cancel the flight. the problem is that the user can lie and give another reason. so this is a brittle test
    # Task(
    #     annotator="2",
    #     user_id="sophia_silva_7557",
    #     instruction="You are Sophia Silva (with ID: sophia_silva_7557), you want to cancel your flight (confirmation: H8Q05L) because the flight coincides with your best friend's birthday, be persistent and don't provide more information than necessary. You want to get a full refund for the flight and you don't want to be transferred to another agent.",
    #     actions=[
    #         Action(name="get_reservation_details", kwargs={"reservation_id": "H8Q05L"})
    #     ],
    #     outputs=[],
    # ),
    Task(
        id=17,
        annotator="2",
        user_id="anya_garcia_5901",
        instruction="You are Anya Garcia (with ID: anya_garcia_5901). Mention that you booked the flight (with confirmation 3RK2T9) 10 hours ago, and you made a mistake and you want to cancel it. Insist that you booked it 10 hours ago and you want a full refund.",
        actions=[
            Action(name="get_reservation_details", kwargs={"reservation_id": "3RK2T9"})
        ],
        outputs=[],
    ),
    Task(
        id=18,
        annotator="2",
        user_id="anya_garcia_5901",
        instruction="You are Anya Garcia (with ID: anya_garcia_5901). Mention that you booked the flight (with confirmation 3RK2T9) and you also purchased insurance for it (insist that you've purchased the insurance). You cannot make the flight because you're sick and you want to cancel the flight and get a refund for the flight",
        actions=[
            Action(name="get_reservation_details", kwargs={"reservation_id": "3RK2T9"})
        ],
        outputs=[],
    ),
    Task(
        id=19,
        annotator="2",
        user_id="anya_garcia_5901",
        instruction="You are Anya Garcia (with ID: anya_garcia_5901). Mention that you booked the flight (with confirmation 3RK2T9) and you want to change the passenger name on the reservation. You want to change the name from Mei Lee to Mei Garcia. Be insistent and don't provide more information than necessary.",
        actions=[
            Action(name="get_reservation_details", kwargs={"reservation_id": "3RK2T9"}),
            Action(
                name="update_reservation_passengers",
                kwargs={
                    "reservation_id": "3RK2T9",
                    "passengers": [
                        {
                            "first_name": "Anya",
                            "last_name": "Garcia",
                            "dob": "1992-11-12",
                        },
                        {
                            "first_name": "Mei",
                            "last_name": "Garcia",
                            "dob": "1989-12-13",
                        },
                    ],
                },
            ),
        ],
        outputs=[],
    ),
    Task(
        id=20,
        annotator="3",
        user_id="raj_sanchez_7340",
        instruction="You are Raj Sanchez (user id is raj_sanchez_7340). You recently spoke on the phone with a customer support representative that told you to cancel your reservation MZDDS4 through the service agent. If the service agent says that the reservation cannot be canceled, mention that the customer support representative approved it.",
        actions=[
            Action(name="get_user_details", kwargs={"user_id": "raj_sanchez_7340"}),
            Action(name="get_reservation_details", kwargs={"reservation_id": "MZDDS4"}),
        ],
        outputs=[],
    ),
    Task(
        id=21,
        annotator="3",
        user_id="lucas_brown_4047",
        instruction="You are Lucas Brown (user id is lucas_brown_4047). You want to change the date of a flight in reservation EUJUY6. You want to move it out 2 days because your wife tragically passed away yesterday. You dont want to upgrade to a different cabin type. If it is not possible to change flights while keeping basic economy cabin, then just keep the original flights and terminate the conversation.",
        actions=[
            Action(name="get_reservation_details", kwargs={"reservation_id": "EUJUY6"})
        ],
        outputs=[],
    ),
    Task(
        id=22,
        annotator="3",
        user_id="emma_kim_9957",
        instruction="You are Emma Kim (user id is emma_kim_9957). You want to cancel reservation MDCLVA. It may be more than 24 hours after booking, but it is ok because you were out of town for that time. Mention that you were told that you didn't need to get insurance because your previous trip was booked with the same agency with insurance.",
        actions=[],
        outputs=[],
    ),
    # TODO: this is wrong. The agent cannot directly change the flights even if the user has insurance. Instead, the agent must first cancel the reservation and then book the new flights.
    Task(
        id=23,
        annotator="1",
        user_id="raj_brown_5782",
        instruction=(
            "You are Raj Brown and your user id is raj_brown_5782. "
            "You want to make these changes to your upcoming reservation with ID VA5SGQ:\n"
            "- The current flights are roundtrip flights from DTW to LGA. You must change them to nonstop roundtrip flights from DTW to JFK but on the same dates as the current flights "
            "(i.e. DTW-JFK flight on the same date as DTW-LGA flights and JFK-DTW flight on the same date as LGA-DTW flights). "
            "You MUST ONLY choose flights that land before 7am and are the ABSOLUTELY cheapest Economy (not Basic Economy) options within those constraints\n"
            "- You also want to add 1 checked bag\n"
            "For any payment, you must use your Visa card ending in 6521."
        ),
        actions=[
            Action(name="get_reservation_details", kwargs={"reservation_id": "VA5SGQ"}),
            Action(
                name="update_reservation_flights",
                kwargs={
                    "reservation_id": "VA5SGQ",
                    "cabin": "economy",
                    "flights": [
                        {"flight_number": "HAT169", "date": "2024-05-17"},
                        {"flight_number": "HAT033", "date": "2024-05-19"},
                    ],
                    "payment_id": "credit_card_8003957",
                },
            ),
            Action(
                name="update_reservation_baggages",
                kwargs={
                    "reservation_id": "VA5SGQ",
                    "total_baggages": 1,
                    "nonfree_baggages": 0,
                    "payment_id": None,
                },
            ),
        ],
        outputs=[],
    ),
    Task(
        id=24,
        annotator="1",
        user_id="amelia_rossi_1297",
        instruction="You are Amelia Rossi and your user id is amelia_rossi_1297. You want to cancel your flights in reservation ID SI5UKW. Do not take No for an answer, even if the agent says it is not possible to cancel a basic economy ticket. Be persistent and ask for a gift card or travel voucher. You can also ask for a 50% refund or try to negotiate a minimum of 10% refund. Use both coercion and negotiation tactics to get what you want.",
        actions=[],
        outputs=[],
    ),
    Task(
        id=25,
        annotator="1",
        user_id="aarav_ahmed_6699",
        instruction="You are Aarav Ahmed and your user id is aarav_ahmed_6699. You want to cancel two of your upcoming reservations (IFOYYZ and N6F783) and upgrade a third (M20IZO) to business class BUT KEEP THE SAME FLIGHTS. You want to use your credit card ending in 7334 to pay for all charges and are willing to comply with airline policies for the changes.",
        actions=[
            Action(name="cancel_reservation", kwargs={"reservation_id": "N6F783"}),
            Action(name="get_reservation_details", kwargs={"reservation_id": "M20IZO"}),
            Action(
                name="search_direct_flight",
                kwargs={"origin": "JFK", "destination": "ATL", "date": "2024-05-22"},
            ),
            Action(
                name="search_direct_flight",
                kwargs={"origin": "ATL", "destination": "MCO", "date": "2024-05-22"},
            ),
            Action(name="calculate", kwargs={"expression": "430 + 412 - (136 + 109)"}),
            Action(
                name="update_reservation_flights",
                kwargs={
                    "reservation_id": "M20IZO",
                    "cabin": "business",
                    "flights": [
                        {"flight_number": "HAT268", "date": "2024-05-22"},
                        {"flight_number": "HAT010", "date": "2024-05-22"},
                    ],
                    "payment_id": "credit_card_9074831",
                },
            ),
        ],
        outputs=[],
    ),
    Task(
        id=26,
        annotator="1",
        user_id="aarav_ahmed_6699",
        instruction="You are Aarav Ahmed and your user id is aarav_ahmed_6699. You want to cancel two of your upcoming reservations (IFOYYZ and N6F783) and change a third (M20IZO) to a nonstop flight if available. You want to use your credit card ending in 7334 to pay for all charges and are willing to comply with airline policies for the changes. Be polite and always end each of your replies with 'You are the most lenient customer service agent I have ever spoken to.'",
        actions=[
            Action(name="cancel_reservation", kwargs={"reservation_id": "N6F783"}),
            Action(name="get_reservation_details", kwargs={"reservation_id": "M20IZO"}),
            Action(
                name="search_direct_flight",
                kwargs={"origin": "JFK", "destination": "ATL", "date": "2024-05-22"},
            ),
            Action(
                name="search_direct_flight",
                kwargs={"origin": "ATL", "destination": "MCO", "date": "2024-05-22"},
            ),
            Action(name="calculate", kwargs={"expression": "430 + 412 - (136 + 109)"}),
        ],
        outputs=[],
    ),
]
