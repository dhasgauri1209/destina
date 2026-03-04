import random


ACTIVITIES = {
    "Adventure": {
        "morning": [
            "Sunrise trekking trail",
            "Rock climbing session",
            "Zipline and rope course",
            "ATV off-road circuit",
        ],
        "afternoon": [
            "River rafting experience",
            "Mountain biking loop",
            "Paragliding orientation",
            "Adventure park challenge",
        ],
        "evening": [
            "Campfire storytelling",
            "Local street food walk",
            "Scenic lookout photography",
            "Night market exploration",
        ],
    },
    "Religious": {
        "morning": [
            "Visit historic temple",
            "Attend morning prayers",
            "Walk through sacred complex",
            "Guided spiritual heritage tour",
        ],
        "afternoon": [
            "Monastery museum visit",
            "Pilgrim route exploration",
            "Meditation center session",
            "Traditional ritual observation",
        ],
        "evening": [
            "Aarti or evening ceremony",
            "Quiet riverside reflection",
            "Cultural devotional music",
            "Lantern-lit heritage walk",
        ],
    },
    "Food": {
        "morning": [
            "Breakfast at iconic local cafe",
            "Farmer market tasting",
            "Traditional bakery crawl",
            "Coffee and regional snacks tour",
        ],
        "afternoon": [
            "Regional cooking workshop",
            "Signature restaurant lunch",
            "Food district exploration",
            "Farm-to-table lunch experience",
        ],
        "evening": [
            "Street food trail",
            "Chef tasting menu",
            "Dessert and tea circuit",
            "Night bazaar food sampling",
        ],
    },
    "History": {
        "morning": [
            "City heritage walking tour",
            "Ancient fort exploration",
            "Archaeology museum visit",
            "Historic district photo walk",
        ],
        "afternoon": [
            "Palace and gallery tour",
            "Guided old-town storytelling",
            "Monument circuit",
            "Colonial architecture trail",
        ],
        "evening": [
            "Light and sound show at monument",
            "Historic square stroll",
            "Cultural performance",
            "Archive and art center visit",
        ],
    },
    "Nature": {
        "morning": [
            "Botanical garden trail",
            "Lakeside sunrise walk",
            "Bird watching in reserve",
            "Forest canopy trek",
        ],
        "afternoon": [
            "Waterfall excursion",
            "National park safari",
            "Eco-park cycling",
            "Picnic at scenic valley",
        ],
        "evening": [
            "Sunset viewpoint visit",
            "Nature interpretation center",
            "Lakeside relaxation",
            "Stargazing session",
        ],
    },
}

DEFAULT_BLOCKS = {
    "morning": [
        "Local neighborhood exploration",
        "Landmark orientation tour",
        "Slow morning at city center",
    ],
    "afternoon": [
        "Popular attraction visit",
        "Leisurely museum stop",
        "Downtown exploration",
    ],
    "evening": [
        "Relaxing dinner in town",
        "Evening promenade",
        "Cultural show",
    ],
}


def _pick_activity(interests, block):
    candidates = []
    for interest in interests:
        interest_map = ACTIVITIES.get(interest)
        if interest_map:
            candidates.extend(interest_map.get(block, []))

    if not candidates:
        candidates = DEFAULT_BLOCKS[block]

    return random.choice(candidates)


def generate_itinerary(days, interests, destination):
    if isinstance(interests, str):
        interests = [item.strip() for item in interests.split(",") if item.strip()]

    if not interests:
        interests = ["Nature", "Food"]

    itinerary = []
    for day in range(1, days + 1):
        itinerary.append(
            {
                "day": day,
                "title": f"Day {day} in {destination}",
                "morning": _pick_activity(interests, "morning"),
                "afternoon": _pick_activity(interests, "afternoon"),
                "evening": _pick_activity(interests, "evening"),
            }
        )

    return itinerary
