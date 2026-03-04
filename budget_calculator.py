def estimate_budget(days, user_budget, interests):
    if isinstance(interests, str):
        interests = [item.strip() for item in interests.split(",") if item.strip()]

    interest_multiplier = 1 + (0.06 * max(len(interests) - 1, 0))

    hotel_per_day = 1800 * interest_multiplier
    food_per_day = 900 * interest_multiplier
    travel_cost = 2200 + (days * 250)

    total_estimated_cost = (hotel_per_day * days) + (food_per_day * days) + travel_cost

    return {
        "hotel_per_day": round(hotel_per_day, 2),
        "food_per_day": round(food_per_day, 2),
        "travel_cost": round(travel_cost, 2),
        "total_estimated_cost": round(total_estimated_cost, 2),
        "status": "Within budget" if total_estimated_cost <= user_budget else "Exceeds budget",
    }
