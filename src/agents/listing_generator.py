from langchain_core.prompts import ChatPromptTemplate
from src.state import AgentState, ListingsCollection
from src.llm_factory import get_llm
import json

class ListingGeneratorAgent:
    def __init__(self):
        self.llm = get_llm(temperature=0.7)

    def run(self, state: AgentState) -> AgentState:
        print("--- Listing Generator Agent ---")
        state["step_progress"] = "Generate"
        product_info = state["product_info"]
        compliance_report = state["compliance_report"]
        market_data = state["market_data"]
        qualifications = product_info.get("qualifications", [])
        
        if not self.llm:
            state["listings"] = {}
            return state

        # P0: Strict Certification Gating (Verified vs Claimed)
        # Split qualifications (Naive for MVP: assume all are claimed unless 'Verified' prefix, 
        # but here we treat user input as 'claimed' and require evidence or strict rules)
        
        # Hard Rule: If qualifications list is empty or generic, BAN specific cert terms.
        # We can try to parse 'verified' from intake if we had that field, but for now we rely on the prompt.
        
        strict_constraints = """
        CRITICAL SAFETY RULES (CLAIM GATING):
        1. VERIFIED ONLY: DO NOT mention 'FDA registered', 'GMP', 'USDA Organic', 'Clinically Tested', or 'Certified' unless the user explicitly provided a certificate number or link in 'Existing Qualifications'.
           - If 'Existing Qualifications' is empty or vague (e.g. just 'FDA'), DO NOT generate these claims.
        2. NO NEW RISKS: DO NOT replace prohibited terms with functional medical claims (e.g. do not replace 'cures' with 'clinically proven to heal'). Use descriptive, appearance-based language only (e.g. 'improves appearance of').
        3. PROHIBITED TERMS: Strictly avoid all terms listed in the Compliance Report.
        """
        
        # Safe Mode Trigger (P0)
        is_red_risk = compliance_report.get("risk_level") == "RED"
        
        if is_red_risk:
            print("!!! RED RISK DETECTED: Entering Safe Mode !!!")
            strict_constraints += """
            \n!!! SAFE MODE ACTIVATED !!!
            - The product is HIGH RISK.
            - OUTPUT A CORRECTION TEMPLATE ONLY.
            - Title format: "[DRAFT - PENDING COMPLIANCE] {Product Name}"
            - Bullets: List ONLY factual ingredients and physical specs (size, count). NO BENEFITS.
            - Description: "This listing draft is withheld pending compliance resolution. Please address the Red Level risks identified in the report."
            """
        else:
            strict_constraints += "\n- Use persuasive but compliant language."

        # Prompt for Version A & B & Summary together
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert e-commerce copywriter.
            Generate two versions of a product listing (Version A: Conversion, Version B: Compliance) and a difference summary.
            
            {strict_constraints}
            
            Output strictly in JSON matching the ListingsCollection schema.
            """),
            ("user", """Product: {product_info}
            Existing Qualifications: {qualifications}
            Compliance Report: {compliance_report}
            Market Data: {market_data}
            """)
        ])

        structured_llm = self.llm.with_structured_output(ListingsCollection)
        chain = prompt | structured_llm
        
        try:
            listings = chain.invoke({
                "product_info": json.dumps(product_info),
                "qualifications": json.dumps(qualifications),
                "compliance_report": json.dumps(compliance_report),
                "market_data": json.dumps(market_data),
                "strict_constraints": strict_constraints
            })
            
            state["listings"] = listings
            state["debug_logs"].append(f"Listings generated. Safe Mode: {is_red_risk}")
        except Exception as e:
            print(f"Error in Listing Generator: {e}")
            state["debug_logs"].append(f"Listing Generator Error: {e}")
            
        return state

listing_generator_agent = ListingGeneratorAgent()
