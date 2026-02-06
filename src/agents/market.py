from src.state import AgentState
import random

class MarketInsightAgent:
    def run(self, state: AgentState) -> AgentState:
        print("--- Market Insight Agent ---")
        state["step_progress"] = "Insight"
        # Mock implementation for MVP
        product_info = state["product_info"]
        category = product_info.get("category", "Item")
        
        # Simulated keywords
        keywords = [
            f"best {category} 2026",
            f"{category} for beginners",
            f"organic {category}",
            f"{category} deals"
        ]
        
        state["market_data"] = {
            "keywords": keywords,
            "trend": "Rising",
            "competitor_analysis": "Moderate competition",
            "search_volume": random.randint(1000, 50000),
            "source": "Simulated Data (Demo)" # P0: Source Labeling
        }
        state["debug_logs"].append("Market data fetched (Mock).")
        return state

market_insight_agent = MarketInsightAgent()
