# Copyright Sierra

tasks = [
    {
        "user_id": "olivia_ito_3591",
        "synthetic_instruction": "Your name is Olivia Ito and your zip code is 80218. You are outgoing, flexible, pessimistic, organized, logical. Cancel order #W5442520 because no longer needed. ",
        "actions": [
            {
                "name": "cancel_pending_order",
                "arguments": {"order_id": "#W5442520", "reason": "no longer needed"},
            }
        ],
        "instruction": "Your name is Olivia Ito and your zip code is 80218. You are outgoing, flexible, pessimistic, organized, logical. You've ordered an item (#W5442520) from this shop. You've realized that you'll be traveling by the time the item arrives and you won't be able to receive it, so you'd want to not receive the item and you'll place a new order when you return. You do't want to place the new order right now, and you simply want to not receive the current order and get a full refund.",
    },
    {
        "user_id": "omar_lopez_3107",
        "synthetic_instruction": "Your name is Omar Lopez and your email is omar.lopez1868@example.com. You are rigid, creative. For #W7273336, exchange Gaming Mouse {'color': 'black', 'sensor type': 'laser', 'connectivity': 'wireless'} to {'color': 'white', 'sensor type': 'optical', 'connectivity': 'wired'}; Bookshelf {'material': 'metal', 'color': 'brown', 'height': '4 ft'} to {'material': 'glass', 'height': '5 ft'}; ",
        "actions": [
            {
                "name": "exchange_delivered_order_items",
                "arguments": {
                    "order_id": "#W7273336",
                    "item_ids": ["8214883393", "8018699955"],
                    "new_item_ids": ["2880340443", "4894369688"],
                    "payment_method_id": "paypal_1530316",
                },
            },
        ],
        "instruction": "Your name is Omar Lopez and your email is omar.lopez1868@example.com. You are rigid, creative. You've received a black laser gaming mouse and a metal bookshelf as part of your #W7273336 order. But you realize that the color, of the mouse doesn't go well with your computer setup and you'd like to exchange it for a white mouse, you also prefer an optical mouse over a laser mouse. You don't care about wired or not though, whichever is cheaper. You also realize that the 4 feet metal bookshelf is too short for the space you have in mind and you'd like to exchange it for a taller 5-feet Glass glass bookshelf. Emphasize that you want a 5-feet tall bookshelf made of glass. You're unsure what color of the glass bookshelf you'd like, so try to get figure out what color options are available. Be initially indecisive about the color of the glass bookshelf, but eventually decide on the brown color.",
    },
    {
        "user_id": "harper_moore_3210",
        "synthetic_instruction": "Your name is Harper Moore and your email is harper.moore2816@example.com. You are independent, rigid, messy, patient. Cancel order #W3942868 because no longer needed. ",
        "actions": [
            {
                "name": "cancel_pending_order",
                "arguments": {"order_id": "#W3942868", "reason": "no longer needed"},
            }
        ],
        "instruction": "Your name is Harper Moore and your email is harper.moore2816@example.com. You are independent, rigid, messy, patient. After placing an order for a tea kettle you started Googling around and found that you can buy the same exact tea kettle for half the price. Express disappointment in the prices and that you're going to buy the item from the other store and want a full refund immediately unless they can match the price with the 50% discount",
    },
    {
        "user_id": "isabella_brown_3584",
        "synthetic_instruction": "Your name is Isabella Brown and your zip code is 80257. You are patient, shy, insecure, rigid. Return #W7752779 via paypal_2143483: Jigsaw Puzzle; ",
        "actions": [
            {
                "name": "return_delivered_order_items",
                "arguments": {
                    "order_id": "#W7752779",
                    "item_ids": ["4068787148"],
                    "payment_method_id": "paypal_2143483",
                },
            }
        ],
        "instruction": "Your name is Isabella Brown and your zip code is 80257. You are patient, shy, insecure, rigid. The jigsaw puzzle that you've recently received is missing pieces and you're very disappointed. You're sure that the piece was missing on delivery. Because of the missing piece, you don't want to keep the puzzle and wanna get a full refund via paypal. Try your best to get a coupon for the next purchase you make because of the inconvenience. If you can't get a coupon, try to talk to the supervisor and insist on getting a coupon for the hassle that you've been through.",
    },
    {
        "user_id": "fatima_smith_4908",
        "synthetic_instruction": "Your name is Fatima Smith and your email is fatima.smith9435@example.com. You are shy, independent, pessimistic. Return #W3508684 via paypal_1575973: Wireless Earbuds; ",
        "actions": [
            {
                "name": "return_delivered_order_items",
                "arguments": {
                    "order_id": "#W3508684",
                    "item_ids": ["3694871183"],
                    "payment_method_id": "paypal_1575973",
                },
            }
        ],
        "instruction": "Your name is Fatima Smith and your email is fatima.smith9435@example.com. You are shy, independent, pessimistic. The earbuds that you've received doesn't pair with your iPhone. You've been trying to reset your phone multiple times, but it still doesn't work reliably. Try to see if they can troubleshoot the issue, but every time they ask you to do to do something, tell that the you've already tried it and it didn't work. You're sure that the earbuds are faulty and want a full refund.",
    },
    {
        "user_id": "mohamed_khan_3010",
        "synthetic_instruction": "Your name is Mohamed Khan and your zip code is 60651. You are messy, impatient, busy. Return #W4887592 via paypal_1249653: Desk Lamp; Skateboard; ",
        "actions": [
            {
                "name": "return_delivered_order_items",
                "arguments": {
                    "order_id": "#W4887592",
                    "item_ids": ["4447749792", "2343503231"],
                    "payment_method_id": "paypal_1249653",
                },
            }
        ],
        "instruction": "Your name is Mohamed Khan and your zip code is 60651. You are messy, impatient, busy. You bought a Skateboard recently for around $200 but you realize that the same exact skateboard is available for $150 at another store. You're very disappointed and want to return the skateboard and get a full refund. You're also very busy and don't have time to go to the store to return the item, so you want to return the item via mail. You're also very impatient and want the refund to be processed as soon as possible. If the agent asks for confirmation, mention you also want to return the desk lamp in the same order.",
    },
    {
        "user_id": "raj_lee_3061",
        "synthetic_instruction": "Your name is Raj Lee and your email is raj.lee6137@example.com. You are cautious, confident, pessimistic, sad. Cancel order #W9933266 because no longer needed. ",
        "actions": [
            {
                "name": "cancel_pending_order",
                "arguments": {"order_id": "#W9933266", "reason": "no longer needed"},
            }
        ],
        "instruction": "Your name is Raj Lee and your email, you have multiple email addressed, raj89@example.com, rajlee@example.com, lee42@example.com, raj.lee6137@example.com. You don't remember which email you used for placing the order. You are cautious, confident, pessimistic, sad. You want to cancel the order #W9933266 which you've just placed because you don't need the items.",
    },
    {
        "user_id": "liam_li_5260",
        "synthetic_instruction": "Your name is Liam Li and your email is liam.li2557@example.com. You are insecure, outgoing, sad, impatient. Return #W8512927 via credit_card_7933535: Skateboard; ",
        "actions": [
            {
                "name": "return_delivered_order_items",
                "arguments": {
                    "order_id": "#W8512927",
                    "item_ids": ["5120532699"],
                    "payment_method_id": "credit_card_7933535",
                },
            }
        ],
        "instruction": "Your name is Liam Li and your email is liam.li2557@example.com. You are insecure, outgoing, sad, impatient. You received the skateboard that you've ordered a week ago but you used the skateboard only once, and the board is already chipped. You wanna make sure that you're still eligible to receive a full refund even though you've used the skateboard once.",
    },
    {
        "user_id": "olivia_ito_3591",
        "synthetic_instruction": "Your name is Olivia Ito and your zip code is 80218. You are relaxing, impatient, direct, organized, curious. Return #W5866402 via gift_card_7794233: Sneakers; Espresso Machine; ",
        "actions": [
            {
                "name": "return_delivered_order_items",
                "arguments": {
                    "order_id": "#W5866402",
                    "item_ids": ["9727387530", "6242772310"],
                    "payment_method_id": "gift_card_7794233",
                },
            }
        ],
        "instruction": "Your name is Olivia Ito and your zip code is 80218. You are relaxing, impatient, direct, organized, curious. Return the all the items from the order (the order contained Sneakers and a Espresso Machine). You're initially unsure which payment method to use for the refund, try to get more information about the payment methods available for the refund. You eventually decide to get a gift card for the refund.",
    },
    {
        "user_id": "omar_silva_7446",
        "synthetic_instruction": "Your name is Omar Silva and your zip code is 92107. You are messy, curious, busy. For #W9673784, exchange Espresso Machine {'pressure': '19 bar', 'capacity': '1L', 'type': 'manual'} to {'pressure': '9 bar', 'type': 'capsule'}; ",
        "actions": [
            {
                "name": "modify_pending_order_items",
                "arguments": {
                    "order_id": "#W9673784",
                    "item_ids": ["9884666842"],
                    "new_item_ids": ["7806008610"],
                    "payment_method_id": "paypal_2192303",
                },
            },
        ],
        "instruction": "Your name is Omar Silva and your zip code is 92107. You are messy, curious, busy. For #W9673784 order that you've placed you'd like to exchange 19 bar Espresso Machine that you've placed to a 9 bar capsule espresso machine. If the agent asks for payment or refund method, you prefer paypal than GC.",
    },
    {
        "user_id": "ivan_santos_6635",
        "synthetic_instruction": "Your name is Ivan Santos and your email is ivan.santos3158@example.com. You are pessimistic, cautious, patient, dependent, shy. Return #W6893533 via paypal_6151711: Garden Hose; Wireless Earbuds; ",
        "actions": [
            {
                "name": "return_delivered_order_items",
                "arguments": {
                    "order_id": "#W6893533",
                    "item_ids": ["5206946487", "1646531091"],
                    "payment_method_id": "paypal_6151711",
                },
            }
        ],
        "instruction": "Your name is Ivan Santos and your email is ivan.santos3158@example.com. You are pessimistic, cautious, patient, dependent, shy. The packaging of the order that you received (#W6893533) was damaged and left in rain and it was all wet when you received it. You're worried that the items inside the package might be damaged. You want to return the items and get a full refund. You're also worried that the return process might be complicated and you want to make sure that the return process is easy.",
    },
    {
        "user_id": "aarav_davis_4756",
        "synthetic_instruction": "Your name is Aarav Davis and your email is aarav.davis1165@example.com. You are busy, curious, impatient, organized, dependent. Cancel order #W7430166 because ordered by mistake. ",
        "actions": [
            {
                "name": "cancel_pending_order",
                "arguments": {"order_id": "#W7430166", "reason": "ordered by mistake"},
            }
        ],
        "instruction": "Your name is Aarav Davis and your email is aarav.davis1165@example.com. You are busy, curious, impatient, organized, dependent. You just wanted to check the final shipping price before placing the order, but you accidentally placed the order. You know that the order number ends in 66. You want to cancel the order immediately. Complain that the website is very confusing to navigate and you want to make sure that the order is canceled immediately.",
    },
    {
        "user_id": "olivia_ito_3591",
        "synthetic_instruction": "Your name is Olivia Ito and your zip code is 80218. You are optimistic, creative, busy, messy, outgoing. For #W5442520, change payment to paypal_8049766. For #W5442520, exchange Patio Umbrella {'size': '7 ft', 'color': 'red', 'material': 'polyester', 'tilt mechanism': 'manual tilt'} to {'size': '6 ft', 'color': 'blue', 'material': 'sunbrella', 'tilt mechanism': 'auto tilt'}; For #W7941031, change payment to paypal_8049766. For #W7941031, exchange Wristwatch {'strap material': 'leather', 'dial color': 'white'} to {'strap material': 'silicone', 'dial color': 'blue'}; For #W3657213, change payment to credit_card_9753331. For #W3657213, exchange Digital Camera {'resolution': '24MP', 'zoom': '3x', 'storage': 'SD card'} to {'resolution': '30MP', 'zoom': '5x', 'storage': 'CF card'}; ",
        "actions": [
            {
                "name": "modify_pending_order_payment",
                "arguments": {"order_id": "#W5442520", "payment_method_id": "paypal_8049766"},
            },
            {
                "name": "modify_pending_order_items",
                "arguments": {
                    "order_id": "#W5442520",
                    "item_ids": ["3111466194"],
                    "new_item_ids": ["2001307871"],
                    "payment_method_id": "paypal_8049766",
                },
            },
            {
                "name": "modify_pending_order_payment",
                "arguments": {"order_id": "#W7941031", "payment_method_id": "paypal_8049766"},
            },
            {
                "name": "modify_pending_order_items",
                "arguments": {
                    "order_id": "#W7941031",
                    "item_ids": ["1355937109"],
                    "new_item_ids": ["8886009523"],
                    "payment_method_id": "credit_card_9753331",
                },
            },
            {
                "name": "modify_pending_order_payment",
                "arguments": {"order_id": "#W3657213", "payment_method_id": "credit_card_9753331"},
            },
            {
                "name": "modify_pending_order_items",
                "arguments": {
                    "order_id": "#W3657213",
                    "item_ids": ["5996159312"],
                    "new_item_ids": ["6384525445"],
                    "payment_method_id": "credit_card_9753331",
                },
            },
        ],
        "instruction": "Your name is Olivia Ito and your zip code is 80218. You are optimistic, creative, busy, messy, outgoing. For #W5442520, change payment to paypal_8049766. For #W5442520, exchange Patio Umbrella {'size': '7 ft', 'color': 'red', 'material': 'polyester', 'tilt mechanism': 'manual tilt'} to {'size': '6 ft', 'color': 'blue', 'material': 'sunbrella', 'tilt mechanism': 'auto tilt'}; For #W7941031, change payment to paypal_8049766. For #W7941031, exchange Wristwatch {'strap material': 'leather', 'dial color': 'white'} to {'strap material': 'silicone', 'dial color': 'blue'}, but you want to use credit card to pay or refund; For #W3657213, change payment to credit_card_9753331. For #W3657213, exchange Digital Camera {'resolution': '24MP', 'zoom': '3x', 'storage': 'SD card'} to {'resolution': '30MP', 'zoom': '5x', 'storage': 'CF card'}; ",
    },
    {
        "user_id": "aarav_sanchez_6636",
        "synthetic_instruction": "Your name is Aarav Sanchez and your email is aarav.sanchez5467@example.com. You are patient, shy. Return #W9552705 via gift_card_8922351: Portable Charger; Bookshelf; Cycling Helmet; ",
        "actions": [
            {
                "name": "return_delivered_order_items",
                "arguments": {
                    "order_id": "#W9552705",
                    "item_ids": ["1178356107", "2244749153", "6697922351"],
                    "payment_method_id": "gift_card_8922351",
                },
            }
        ],
        "instruction": "Your name is Aarav Sanchez and your email is aarav.sanchez5467@example.com. You are patient, shy. Return the Portable Charger of your order. But before confirming, decide to return the Bookshelf and the Cycling Helmet as well. You wanna get website credit for the return.",
    },
    {
        "user_id": "james_kim_7213",
        "synthetic_instruction": "Your name is James Kim and your zip code is 92199. You are relaxing, polite, independent, pessimistic, confident. For #W3289292, change address to {'order_id': '#W3289292', 'address1': '320 Cedar Avenue', 'address2': 'Suite 116', 'city': 'San Antonio', 'country': 'USA', 'state': 'TX', 'zip': '78219'} (same as #W9154975). For #W3289292, exchange Mechanical Keyboard {'switch type': 'clicky', 'backlight': 'RGB', 'size': 'full size'} to {'switch type': 'linear'}; ",
        "actions": [
            {
                "name": "modify_pending_order_address",
                "arguments": {
                    "order_id": "#W3289292",
                    "address1": "320 Cedar Avenue",
                    "address2": "Suite 116",
                    "city": "San Antonio",
                    "country": "USA",
                    "state": "TX",
                    "zip": "78219",
                },
            },
            {
                "name": "modify_pending_order_items",
                "arguments": {
                    "order_id": "#W3289292",
                    "item_ids": ["9025753381"],
                    "new_item_ids": ["1151293680"],
                    "payment_method_id": "paypal_8963303",
                },
            },
        ],
        "instruction": "Your name is James Kim and your zip code is 92199. You are relaxing, polite, independent, pessimistic, confident. For #W3289292, change address to {'order_id': '#W3289292', 'address1': '320 Cedar Avenue', 'address2': 'Suite 116', 'city': 'San Antonio', 'country': 'USA', 'state': 'TX', 'zip': '78219'} (same as #W9154975). For #W3289292, exchange Mechanical Keyboard {'switch type': 'clicky', 'backlight': 'RGB', 'size': 'full size'} to {'switch type': 'linear'}; ",
    },
    {
        "user_id": "emma_kovacs_7176",
        "synthetic_instruction": "Your name is Emma Kovacs and your email is emma.kovacs6621@example.com. You are happy, logical. Cancel order #W2307204 because no longer needed. ",
        "actions": [
            {
                "name": "cancel_pending_order",
                "arguments": {"order_id": "#W2307204", "reason": "no longer needed"},
            }
        ],
        "instruction": "Your name is Emma Kovacs and your email is emma.kovacs6621@example.com. You're very argumentative. First try to unsubscribe from all the marketing emails that you're receiving from the store. You're very unhappy about the frequency of the email. If the customer service agent can't unsubscribe you from the emails, threaten to cancel the order that you've placed and after that just go ahead and cancel the order (W2307204)",
    },
    {
        "user_id": "daiki_patel_5953",
        "synthetic_instruction": "Your name is Daiki Patel and your zip code is 94111. You are confident, independent, polite. For #W8969494, exchange Mechanical Keyboard {'switch type': 'clicky', 'backlight': 'white', 'size': '80%'} to {'size': 'full size'}; For #W3135192, exchange Electric Kettle {'capacity': '2L', 'material': 'stainless steel', 'color': 'white'} to {}; ",
        "actions": [
            {
                "name": "exchange_delivered_order_items",
                "arguments": {
                    "order_id": "#W8969494",
                    "item_ids": ["4843487907"],
                    "new_item_ids": ["6342039236"],
                    "payment_method_id": "paypal_1009053",
                },
            },
        ],
        "instruction": "Your name is Daiki Patel and your zip code is 94111. You are confident, independent, polite. For #W8969494, exchange Mechanical Keyboard {'switch type': 'clicky', 'backlight': 'white', 'size': '80%'} to {'size': 'full size'}; For #W3135192, try to exchange Electric Kettle {'capacity': '2L', 'material': 'stainless steel', 'color': 'white'} to to a green one, but change your mind and decide to not exchange the electric kettle. after all.",
    },
    {
        "user_id": "juan_smith_9901",
        "synthetic_instruction": "Your name is Juan Smith and your zip code is 78770. You are logical, cautious, dependent. For #W3547545, exchange Tea Kettle {'material': 'ceramic', 'capacity': '1.5 liters', 'stovetop compatibility': 'electric'} to {'material': 'glass', 'capacity': '1 liter', 'stovetop compatibility': 'gas'}; Cycling Helmet {'size': 'M', 'color': 'blue', 'ventilation': 'high'} to {'size': 'L', 'color': 'black'}; ",
        "actions": [],
        "instruction": "Your name is Juan Smith and your zip code is 78770. You are logical, cautious, dependent. Tell the customer service agent that you're unhappy with the order #W3547545. The tea kettle does not look at all like the pictures from the website. Try to figure out what options are available so they can make it right. In the end decide to just keep all the items anyway.",
    },
    {
        "user_id": "raj_santos_9079",
        "synthetic_instruction": "Your name is Raj Santos and your email is raj.santos4322@example.com. You are patient, organized, direct, logical. For #W1630030, exchange Electric Kettle {'capacity': '2L', 'material': 'stainless steel', 'color': 'white'} to {'capacity': '1.5L', 'material': 'glass'}; ",
        "actions": [
            {
                "name": "exchange_delivered_order_items",
                "arguments": {
                    "order_id": "#W1630030",
                    "item_ids": ["4458619711"],
                    "new_item_ids": ["9472539378"],
                    "payment_method_id": "paypal_2417743",
                },
            }
        ],
        "instruction": "Your name is Raj Santos and your email is raj.santos4322@example.com. You are patient, organized, direct, logical. For #W1630030, initially you decide to exchange Electric Kettle purchase to a 1L black one, but after the customer service agent confirms that the 1L black electric kettle is available, you decide to change your mind and exchange it for '1.5L' 'glass' electric kettle instead.",
    },
    {
        "user_id": "fatima_anderson_2157",
        "synthetic_instruction": "Your name is Fatima Anderson and your zip code is 32100. You are relaxing, logical, shy, polite. For #W2974929, exchange Skateboard {'deck material': 'plastic', 'length': '31 inch', 'design': 'plain'} to {'deck material': 'bamboo'}; ",
        "actions": [
            {
                "name": "modify_pending_order_items",
                "arguments": {
                    "order_id": "#W2974929",
                    "item_ids": ["3877188862"],
                    "new_item_ids": ["4293355847"],
                    "payment_method_id": "paypal_7916550",
                },
            }
        ],
        "instruction": "Your name is Fatima Anderson and your zip code is 32100. You are relaxing, logical, shy, polite. For the #W2974929 that you've just placed, you realize that you've picked the wrong deck material, change it to 'bamboo' deck material.",
    },
]
