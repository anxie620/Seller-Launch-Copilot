from src.state import AgentState, EvidenceItem
from src.tools.retrieval import retrieve_policy, policy_retriever
import datetime

class PolicyRetrievalAgent:
    def run(self, state: AgentState) -> AgentState:
        print("--- Policy Retrieval Agent ---")
        state["step_progress"] = "Evidence"
        product_info = state["product_info"]
        
        # Ensure retriever is fresh (Hot-swap support)
        policy_retriever.reinitialize()
        
        # Formulate queries
        queries = [
            f"{product_info['category']} prohibited {product_info['target_country']}",
            f"{product_info['category']} labeling requirements {product_info['target_country']}",
            f"{product_info['function']} claim substantiation {product_info['target_country']}"
        ]
        
        state["retrieval_queries"] = queries
        
        raw_evidence = []
        for q in queries:
            print(f"Searching for: {q}")
            results = retrieve_policy(q)
            # Tag results with the query that found them
            for r in results:
                r["query"] = q
            raw_evidence.extend(results)
            
        # Deduplicate and Format
        seen = set()
        formatted_evidence = []
        counter = 1
        
        for item in raw_evidence:
            content = item["content"]
            if content not in seen:
                seen.add(content)
                formatted_evidence.append(EvidenceItem(
                    id=f"E{counter}",
                    content=content,
                    source=item.get("source", "Policy DB"),
                    url=item.get("url", "#"), 
                    date=datetime.date.today().strftime("%Y-%m-%d"), 
                    score="High",
                    query=item.get("query", "Unknown")
                ))
                counter += 1
                
        state["evidence"] = formatted_evidence
        state["debug_logs"].append(f"Retrieval completed. Found {len(formatted_evidence)} unique evidence items.")
        return state

policy_retrieval_agent = PolicyRetrievalAgent()
