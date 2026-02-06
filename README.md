# Seller Launch Copilot

## Overview
A multi-agent workbench for cross-border e-commerce sellers to automate listing creation and compliance checks.

## Setup
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Set up environment variables:
   Copy `.env.example` to `.env` and add your OpenAI API key.
   ```
   OPENAI_API_KEY=your_key_here
   ```
3. Run the application:
   ```bash
   streamlit run src/app.py
   ```

## Architecture
- **Frontend**: Streamlit
- **Backend**: Python + LangChain
- **Agents**: Intake, Policy Retrieval, Compliance Auditor, Market Insight, Listing Generator, Eval.
