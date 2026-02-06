from langchain_core.prompts import ChatPromptTemplate
from src.state import AgentState
from src.llm_factory import get_llm
import json
import re

class EvalAgent:
    def __init__(self):
        self.llm = get_llm(temperature=0)

    def run(self, state: AgentState) -> AgentState:
        print("--- Eval Agent ---")
        state["step_progress"] = "Eval"
        listings = state["listings"]
        compliance_report = state["compliance_report"]
        product_info = state["product_info"]
        
        if not listings:
            state["eval_report"] = {"score": 0, "comments": "No listings to evaluate"}
            return state

        # P0: Unify Metrics & Highlight Hallucinations
        metrics = {
            "prohibited_terms_input": 0,
            "prohibited_terms_output": 0,
            "citations_coverage": 0,
            "hallucinations_count": 0,
            "risk_gating_passed": True
        }
        
        # 1. Prohibited Terms (Input vs Output)
        prohibited = compliance_report.get("prohibited_expressions", [])
        metrics["prohibited_terms_input"] = len(prohibited)
        
        combined_text = (
            str(listings.get("version_a", {})) + 
            str(listings.get("version_b", {}))
        ).lower()
        
        for item in prohibited:
            # Check original forbidden terms in output
            if item["original"].lower() in combined_text:
                metrics["prohibited_terms_output"] += 1

        # 2. Hallucinations (Strict Gating)
        # Keywords that require verification
        high_risk_keywords = [
            "fda registered", "fda approved", "gmp", "usda organic", 
            "clinically tested", "clinically proven", "certified", "guaranteed"
        ]
        
        hallucinations_found = []
        # Naive verification: check if these keywords exist in user's qualifications input
        # If not in input, but in output -> Hallucination.
        qualifications_text = " ".join(product_info.get("qualifications", [])).lower()
        
        for kw in high_risk_keywords:
            if kw in combined_text and kw not in qualifications_text:
                hallucinations_found.append(kw)
        
        metrics["hallucinations_count"] = len(hallucinations_found)
        if len(hallucinations_found) > 0:
            metrics["risk_gating_passed"] = False

        # 3. Soft Feedback (LLM)
        if self.llm:
            prompt = ChatPromptTemplate.from_messages([
                ("system", """You are a QA Auditor. Evaluate the generated listings.
                Focus ONLY on tone, clarity, and sales effectiveness.
                DO NOT verify facts (that is done by rules).
                
                Provide a JSON output with:
                - overall_score (0-100)
                - tone_feedback (string)
                - clarity_feedback (string)
                """),
                ("user", """Listings: {listings}""")
            ])
            
            chain = prompt | self.llm
            
            try:
                result = chain.invoke({"listings": json.dumps(listings)})
                soft_eval = result.content
            except Exception as e:
                soft_eval = f"Soft Eval Error: {e}"
        else:
            soft_eval = "LLM unavailable for soft eval."

        state["eval_report"] = {
            "metrics": metrics,
            "hallucinations": hallucinations_found, # For UI highlighting
            "soft_eval": soft_eval
        }
        state["debug_logs"].append("Evaluation completed (Rules + LLM).")
            
        return state

eval_agent = EvalAgent()
