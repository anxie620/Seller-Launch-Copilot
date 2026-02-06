from langchain_core.prompts import ChatPromptTemplate
from src.state import AgentState, ComplianceReport
from src.llm_factory import get_llm
import json

class ComplianceAgent:
    def __init__(self):
        self.llm = get_llm(temperature=0)

    def run(self, state: AgentState) -> AgentState:
        print("--- Compliance Agent ---")
        state["step_progress"] = "Audit"
        product_info = state["product_info"]
        evidence = state["evidence"]
        
        if not self.llm or not evidence:
            state["compliance_report"] = {
                "risk_level": "UNKNOWN", 
                "confidence_score": 0.0,
                "issues": [], 
                "required_qualifications": [], 
                "prohibited_expressions": []
            }
            state["debug_logs"].append("Compliance Agent skipped: No LLM or No Evidence.")
            return state

        # P0: Safe Prohibited Replacement & Strict Evidence Binding
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a strict compliance auditor. 
            Analyze the product against the evidence.
            
            TASKS:
            1. Risk Level: RED (Ban/High Risk), YELLOW (Restricted), GREEN (Safe).
            2. Confidence: 0.0 to 1.0 based on evidence coverage.
            3. Issues: List violations. MUST cite a specific Evidence ID (e.g., E1). 
               - If no specific evidence supports a rule, mark evidence_id as 'Rule Inference'.
               - Quote the specific text snippet from the evidence that supports the issue.
            4. Prohibited Expressions: Extract risky phrases from input.
               - Suggested replacements MUST be 'safe' (descriptive, non-functional).
               - DO NOT introduce new claims (e.g., do not suggest 'clinically tested' to replace 'best').
               - Use phrases like 'formulated to', 'appearance of', 'contains'.
            
            Input:
            Product: {product_info}
            Evidence: {evidence}
            """),
        ])

        structured_llm = self.llm.with_structured_output(ComplianceReport)
        chain = prompt | structured_llm
        
        try:
            report = chain.invoke({
                "product_info": json.dumps(product_info), 
                "evidence": json.dumps(evidence)
            })
            state["compliance_report"] = report
            state["debug_logs"].append(f"Compliance analysis done. Risk: {report['risk_level']}")
        except Exception as e:
            print(f"Error in Compliance Agent: {e}")
            state["compliance_report"] = {
                "risk_level": "ERROR", 
                "confidence_score": 0.0,
                "issues": [{"issue": str(e), "risk_level": "RED", "severity": "Critical", "suggestion": "Check logs", "evidence_id": "N/A"}], 
                "required_qualifications": [], 
                "prohibited_expressions": []
            }
            state["debug_logs"].append(f"Compliance Agent Error: {e}")
            
        return state

compliance_agent = ComplianceAgent()
