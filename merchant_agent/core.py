from dataclasses import dataclass


@dataclass
class Context:
    merchant: str
    amount: float
    location: str


def score_purchase(ctx: Context) -> dict:
    # minimal, deterministic demo logic
    base_rewards = ctx.amount * 0.03  # pretend 3%
    merchant_penalty = 0.0  # pretend no penalty yet
    score = round((base_rewards - merchant_penalty) / max(ctx.amount, 1) * 100, 2)
    return {
        "recommended_card": "Demo Rewards Plus",
        "score": score,
        "signals": {
            "merchant": ctx.merchant,
            "location": ctx.location,
            "rewards_value_usd": round(base_rewards, 2),
            "merchant_penalty_usd": merchant_penalty,
        },
    }
