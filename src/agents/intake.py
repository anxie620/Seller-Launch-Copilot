from src.state import AgentState, ProductInfo
from src.config import OPENAI_API_KEY
from src.llm_factory import get_llm
import json

class IntakeAgent:
    def __init__(self):
        self.llm = get_llm(temperature=0)

    def run(self, state: AgentState) -> AgentState:
        print("--- Intake Agent ---")
        state["step_progress"] = "Intake"
        user_input = state["user_input"]
        
        product_info = ProductInfo(
            target_country=user_input.get("target_country", "US"),
            category=user_input.get("category", ""),
            product_name=user_input.get("product_name", ""),
            material=user_input.get("material", ""),
            function=user_input.get("function", ""),
            target_audience=user_input.get("target_audience", ""),
            claims=user_input.get("claims", ""),
            qualifications=user_input.get("qualifications", [])
        )
        
        state["product_info"] = product_info
        
        # Consistency Check (Rule-based)
        cat_lower = product_info["category"].lower()
        name_lower = product_info["product_name"].lower()
        mat_lower = product_info["material"].lower()
        
        warning = None
        if "supplement" in cat_lower:
            if any(x in name_lower for x in ["serum", "cream", "lotion", "moisturizer", "oil"]):
                warning = f"⚠️ Category mismatch detected: Category is '{product_info['category']}' but Product Name contains cosmetic terms (serum/cream). Please verify."
            if "water" in mat_lower and "acid" in mat_lower and "vitamin" in mat_lower:
                 if not any(x in name_lower for x in ["drink", "liquid"]):
                    # Loose check for cosmetic formulation
                    pass
        
        state["intake_warning"] = warning
        
        if "debug_logs" not in state:
            state["debug_logs"] = []
        state["debug_logs"].append("Intake completed. Product info structured.")
        if warning:
            state["debug_logs"].append(f"Intake Warning: {warning}")
            
        return state

intake_agent = IntakeAgent()
