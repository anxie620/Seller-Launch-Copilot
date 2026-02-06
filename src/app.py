import streamlit as st
import sys
import os
import json
import time

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.orchestrator import app as orchestrator_app
from src.config import OPENAI_API_KEY

st.set_page_config(page_title="Seller Launch Copilot", layout="wide", initial_sidebar_state="expanded")

# --- Header & Product Semantics ---
st.title("🚀 Seller Launch Copilot")
st.markdown("""
**任务**：跨境商品上新合规审查与文案生成（带证据引用）  
**输入**：商品信息 + 目标站点 + 宣称点 + 证书  
**输出**：风险等级 + 问题清单 + A/B 上新文案 + 导出包 + 评估分数
""")
st.divider()

# --- Sidebar: Configuration & Steps ---
with st.sidebar:
    st.header("⚙️ Configuration")
    
    # Provider Selection
    provider = st.selectbox("LLM Provider", ["OpenAI", "Alibaba (DashScope)", "Custom"])
    
    # Defaults
    default_base_url = "https://api.openai.com/v1"
    default_model = "gpt-4o"
    
    if provider == "Alibaba (DashScope)":
        default_base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"
        default_model = "qwen-plus"
    
    api_key = st.text_input("API Key", value=OPENAI_API_KEY or "", type="password")
    base_url = st.text_input("Base URL", value=default_base_url)
    model_name = st.text_input("Model Name", value=default_model)
    
    if api_key:
        os.environ["OPENAI_API_KEY"] = api_key
        os.environ["OPENAI_BASE_URL"] = base_url
        os.environ["OPENAI_MODEL_NAME"] = model_name
    
    st.divider()
    st.header("📋 Workflow Steps")
    
    # Visual Step Tracker
    if "current_step" not in st.session_state:
        st.session_state.current_step = "Intake"
        
    steps = ["Intake", "Evidence", "Audit", "Insight", "Generate", "Eval", "Export"]
    for step in steps:
        if step == st.session_state.current_step:
            st.markdown(f"**👉 {step}**")
        else:
            st.markdown(f"{step}")
            
    st.divider()
    debug_mode = st.toggle("Debug Mode", value=False)

# --- Intake: Structured Form ---
with st.container():
    st.subheader("📝 Product Intake")
    with st.form("intake_form"):
        col1, col2 = st.columns(2)
        with col1:
            target_country = st.selectbox("Target Country/Market", ["US", "UK", "DE", "JP", "FR"])
            # Use session state for category to allow programmatic updates
            if "category_val" not in st.session_state:
                st.session_state.category_val = "Dietary Supplements"
            category = st.text_input("Category", key="category_val", help="e.g. Dietary Supplements, Electronics, Toys")
            
            product_name = st.text_input("Product Name/Model", "Vitamin C Serum 1000mg")
            material = st.text_input("Material/Ingredients", "Vitamin C, Hyaluronic Acid, Water")
        with col2:
            target_audience = st.selectbox("Target Audience", ["Adults", "Children", "Seniors", "Pregnant Women", "General"])
            function = st.text_input("Core Function", "Brightening, Anti-aging")
            qualifications = st.text_input("Existing Qualifications (Comma separated)", "FDA Registration, GMP")
        
        claims = st.text_area("Claims (What do you want to say?)", "Cures wrinkles instantly. 100% organic. Best in the world.", help="List your marketing claims here.")
        
        submitted = st.form_submit_button("🚀 Start Analysis")

# --- P0: Strong Consistency Check Logic ---
if submitted:
    st.session_state.intake_submitted = True
    st.session_state.analysis_started = False
    st.session_state.intake_data = {
        "target_country": target_country,
        "category": category,
        "product_name": product_name,
        "material": material,
        "function": function,
        "target_audience": target_audience,
        "claims": claims,
        "qualifications": qualifications
    }

if st.session_state.get("intake_submitted") and not st.session_state.get("analysis_started"):
    data = st.session_state.intake_data
    cat_lower = data["category"].lower()
    name_lower = data["product_name"].lower()
    
    # Detect Mismatch
    is_supplement = "supplement" in cat_lower
    is_cosmetic_name = any(x in name_lower for x in ["serum", "cream", "lotion", "moisturizer", "oil"])
    
    if is_supplement and is_cosmetic_name:
        st.error("🛑 Category Mismatch Detected!")
        st.warning(f"You selected Category='{data['category']}' (Supplement), but Product Name '{data['product_name']}' implies a Cosmetic/Topical product.")
        
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            if st.button("Change Category to 'Cosmetics'"):
                st.session_state.category_val = "Cosmetics"
                st.session_state.intake_data["category"] = "Cosmetics"
                st.session_state.analysis_started = True
                st.rerun()
        with col_c2:
            if st.button("Keep 'Supplement' (I will rename product)"):
                st.info("Please rename your product in the form above to exclude cosmetic terms (e.g. use 'Capsules', 'Tablets').")
                st.session_state.intake_submitted = False # Reset to allow edit
                st.rerun()
        
        st.stop() # Block execution
    else:
        st.session_state.analysis_started = True

# --- Main Workflow ---
if st.session_state.get("analysis_started"):
    if not api_key:
        st.error("Please provide an API Key.")
    else:
        # Use data from session state (which might have been corrected)
        input_data = st.session_state.intake_data
        
        # Construct Initial State
        initial_state = {
            "user_input": {
                "target_country": input_data["target_country"],
                "category": input_data["category"],
                "product_name": input_data["product_name"],
                "material": input_data["material"],
                "function": input_data["function"],
                "target_audience": input_data["target_audience"],
                "claims": input_data["claims"],
                "qualifications": [q.strip() for q in input_data["qualifications"].split(",")] if input_data["qualifications"] else []
            },
            "product_info": {},
            "evidence": [],
            "compliance_report": {},
            "market_data": {},
            "listings": {},
            "eval_report": {},
            "debug_logs": [],
            "step_progress": "Intake",
            "metrics": {"start_time": time.time()}
        }
        
        # Run Workflow
        status_text = st.empty()
        progress_bar = st.progress(0)
        
        final_state = initial_state
        step_count = 0
        total_steps = 6
        
        try:
            # Hot-swap Re-initialization
            from src.agents.intake import intake_agent
            from src.agents.compliance import compliance_agent
            from src.agents.listing_generator import listing_generator_agent
            from src.agents.eval import eval_agent
            from src.llm_factory import get_llm
            
            # Re-configure agents with new env vars
            intake_agent.llm = get_llm(temperature=0)
            compliance_agent.llm = get_llm(temperature=0)
            listing_generator_agent.llm = get_llm(temperature=0.7)
            eval_agent.llm = get_llm(temperature=0)
            
            for output in orchestrator_app.stream(initial_state):
                for node_name, state_update in output.items():
                    step_count += 1
                    progress_bar.progress(min(step_count / total_steps, 1.0))
                    status_text.text(f"Running: {node_name}...")
                    
                    # Update final state
                    final_state.update(state_update)
                    
                    # Update Sidebar Step
                    if "step_progress" in state_update:
                        st.session_state.current_step = state_update["step_progress"]

            progress_bar.progress(1.0)
            status_text.text("Workflow Complete!")
            st.session_state.current_step = "Export"
            
            # --- Results Display ---
            st.divider()
            
            # 1. Evidence Panel
            st.header("🔍 Evidence Audit")
            evidence = final_state.get("evidence", [])
            
            # Evidence Health (P0)
            queries = set(item.get("query", "Unknown") for item in evidence)
            coverage_score = 0
            if len(queries) >= 3: coverage_score += 50
            if len(evidence) >= 5: coverage_score += 50
            
            col_h1, col_h2, col_h3 = st.columns([1, 2, 2])
            with col_h1:
                st.metric("Evidence Items", len(evidence))
            with col_h2:
                st.metric("Coverage Score", f"{coverage_score}/100")
            with col_h3:
                if coverage_score < 50:
                    st.error("Data Health: POOR. Results may be unreliable.")
                elif coverage_score < 100:
                    st.warning("Data Health: FAIR. Some gaps in evidence.")
                else:
                    st.success("Data Health: GOOD.")
            
            if evidence:
                # Group by Query
                for q in queries:
                    with st.expander(f"Query: {q}"):
                        query_items = [i for i in evidence if i.get("query") == q]
                        for item in query_items:
                            st.markdown(f"**[{item['id']}] {item['source']}**")
                            st.text_area("Content", item['content'], height=100, key=item['id'])
                            st.divider()

            # 2. Compliance Panel
            st.header("🛡️ Compliance Report")
            report = final_state.get("compliance_report", {})
            risk_level = report.get("risk_level", "UNKNOWN")
            
            # Metrics
            m1, m2, m3 = st.columns(3)
            color = "red" if risk_level == "RED" else "orange" if risk_level == "YELLOW" else "green"
            m1.markdown(f"### Risk: :{color}[{risk_level}]")
            m2.metric("Issues Found", len(report.get("issues", [])))
            m3.metric("Confidence Score", f"{report.get('confidence_score', 0.0) * 100:.0f}%")
            
            # Required Qualifications Checklist
            st.subheader("Required Qualifications")
            req_quals = report.get("required_qualifications", [])
            if req_quals:
                for req in req_quals:
                    st.checkbox(req, key=f"req_{req}", help="Missing this may cause rejection.")
            else:
                st.info("No specific qualifications identified.")

            # Issues List
            st.subheader("Risk Issues")
            for issue in report.get("issues", []):
                with st.expander(f"[{issue['risk_level']}] {issue['issue']}"):
                    st.write(f"**Severity:** {issue['severity']}")
                    st.write(f"**Suggestion:** {issue['suggestion']}")
                    st.info(f"**Reference:** Evidence {issue['evidence_id']}")
            
            # Prohibited Expressions Table
            st.subheader("🚫 Prohibited Expressions")
            prohibited = report.get("prohibited_expressions", [])
            if prohibited:
                st.table(prohibited)
            else:
                st.success("No prohibited expressions detected in input.")

            # 3. Market Insight
            st.header("📊 Market Insight")
            market = final_state.get("market_data", {})
            if market:
                st.caption(f"Source: {market.get('source', 'Unknown')}")
                col_m1, col_m2 = st.columns(2)
                with col_m1:
                    st.metric("Search Volume", market.get("search_volume", "N/A"))
                    st.metric("Trend", market.get("trend", "N/A"))
                with col_m2:
                    st.write("**Recommended Keywords:**")
                    st.write(", ".join(market.get("keywords", [])))
            else:
                st.info("No market data available.")

            # 4. Generation Panel
            st.header("✍️ Generated Listings")
            listings = final_state.get("listings", {})
            
            # Safe Mode Display (P0)
            if risk_level == "RED":
                st.error("🚨 RISK ALERT: Product is High Risk. Outputting Safe Mode Template.")
            
            tab_a, tab_b = st.tabs(["🅰️ Version A (Conversion)", "🅱️ Version B (Compliance)"])
            
            with tab_a:
                ver_a = listings.get("version_a", {})
                if ver_a:
                    st.subheader(ver_a.get("title", "No Title"))
                    st.markdown("**Bullets:**")
                    for b in ver_a.get("bullets", []):
                        st.markdown(f"- {b}")
                    st.markdown("**Description:**")
                    st.write(ver_a.get("description", ""))
            
            with tab_b:
                ver_b = listings.get("version_b", {})
                if ver_b:
                    st.subheader(ver_b.get("title", "No Title"))
                    st.markdown("**Bullets:**")
                    for b in ver_b.get("bullets", []):
                        st.markdown(f"- {b}")
                    st.markdown("**Description:**")
                    st.write(ver_b.get("description", ""))
                    
            # Difference Summary
            with st.sidebar:
                st.header("🆚 Difference Summary")
                for diff in listings.get("difference_summary", []):
                    st.info(diff)

            # 5. Export & Eval
            st.header("📤 Export & Eval")
            
            col_ex, col_ev = st.columns(2)
            
            with col_ex:
                # Markdown Construction (Full Package)
                md_output = f"""# Seller Launch Copilot Report
**Date:** {time.strftime("%Y-%m-%d")}
**Product:** {input_data['product_name']}
**Risk Level:** {risk_level}

## 1. Compliance Report
### Issues
"""
                for issue in report.get("issues", []):
                    md_output += f"- **{issue['issue']}** ({issue['risk_level']})\n  Suggestion: {issue['suggestion']}\n"
                
                md_output += "\n### Required Qualifications\n"
                for req in req_quals:
                    md_output += f"- [ ] {req}\n"

                md_output += "\n## 2. Listings\n"
                md_output += "### Version A (Conversion)\n"
                md_output += f"**Title:** {listings.get('version_a', {}).get('title', '')}\n\n"
                md_output += "**Bullets:**\n"
                for b in listings.get('version_a', {}).get('bullets', []):
                    md_output += f"- {b}\n"
                md_output += f"\n**Description:**\n{listings.get('version_a', {}).get('description', '')}\n"
                
                md_output += "\n### Version B (Compliance)\n"
                md_output += f"**Title:** {listings.get('version_b', {}).get('title', '')}\n\n"
                md_output += "**Bullets:**\n"
                for b in listings.get('version_b', {}).get('bullets', []):
                    md_output += f"- {b}\n"
                md_output += f"\n**Description:**\n{listings.get('version_b', {}).get('description', '')}\n"

                md_output += "\n## 3. Evidence Appendix\n"
                for item in evidence:
                     md_output += f"- **{item['id']}**: {item['source']} ({item['date']})\n  {item['content'][:200]}...\n"

                # Gate
                if risk_level == "RED":
                    confirm = st.checkbox("I acknowledge the RED risk and want to export anyway.")
                    disabled = not confirm
                else:
                    disabled = False
                
                st.download_button(
                    label="📥 Download Full Package (MD)",
                    data=md_output,
                    file_name=f"report-{input_data['product_name'].replace(' ', '_')}.md",
                    mime="text/markdown",
                    disabled=disabled
                )
            
            with col_ev:
                eval_rep = final_state.get("eval_report", {})
                
                # Hard Metrics Display
                metrics = eval_rep.get("metrics", {})
                c1, c2, c3 = st.columns(3)
                c1.metric("Prohibited (Out)", metrics.get("prohibited_terms_output", 0))
                c2.metric("Hallucinations", metrics.get("hallucinations_count", 0))
                c3.metric("Risk Gating", "PASS" if metrics.get("risk_gating_passed") else "FAIL")
                
                st.write("**Soft Eval (LLM):**")
                try:
                    soft_json = json.loads(eval_rep.get("soft_eval", "{}"))
                    st.json(soft_json)
                except:
                    st.write(eval_rep.get("soft_eval", "N/A"))
                    
                if "error" in eval_rep:
                    st.error(eval_rep["error"])

            # Debug Logs
            if debug_mode:
                st.header("🐞 Debug Logs")
                st.metric("Total Time", f"{time.time() - final_state['metrics']['start_time']:.2f}s")
                for log in final_state.get("debug_logs", []):
                    st.text(log)
                    
        except Exception as e:
            st.error(f"Workflow Failed: {e}")
            st.exception(e)
