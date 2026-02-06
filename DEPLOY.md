# 🚀 Deployment Guide: Seller Launch Copilot

Your application is ready for deployment! Here are the two best ways to share it with the world.

## Option 1: Streamlit Community Cloud (Recommended & Free)
This is the easiest way to deploy Streamlit apps.

### Prerequisites
1.  **GitHub Account**: You need to push your code to a GitHub repository.
2.  **Streamlit Account**: Sign up at [share.streamlit.io](https://share.streamlit.io/).

### Steps
1.  **Push Code to GitHub**:
    *   Initialize a git repo: `git init`
    *   Add files: `git add .`
    *   Commit: `git commit -m "Initial commit"`
    *   Create a new repo on GitHub and push your code there.

2.  **Deploy**:
    *   Go to [share.streamlit.io](https://share.streamlit.io/).
    *   Click **"New app"**.
    *   Select your GitHub repository, branch (usually `main`), and main file path (`src/app.py`).
    *   Click **"Deploy!"**.

3.  **Configure Secrets (API Keys)**:
    *   Once deployed, the app will fail because it needs your API Key.
    *   Go to your app dashboard on Streamlit Cloud.
    *   Click **"Settings"** -> **"Secrets"**.
    *   Add your secrets in TOML format:
        ```toml
        OPENAI_API_KEY = "sk-..."
        # If using Custom/Alibaba:
        OPENAI_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
        OPENAI_MODEL_NAME = "qwen-plus"
        ```
    *   Save. The app will restart and work!

---

## Option 2: Docker (For Cloud Platforms like Render/Fly.io)
If you prefer using a container or need to deploy to a specific cloud provider.

### Build & Run Locally
```bash
# Build the image
docker build -t seller-launch-copilot .

# Run the container (Pass API Key as env var)
docker run -p 8501:8501 -e OPENAI_API_KEY="your_key" seller-launch-copilot
```

### Deploy to Render (Example)
1.  Push your code to GitHub.
2.  Sign up at [render.com](https://render.com/).
3.  Click **"New +"** -> **"Web Service"**.
4.  Connect your GitHub repo.
5.  Select **"Docker"** as the runtime.
6.  Add Environment Variables (OPENAI_API_KEY, etc.) in the "Environment" tab.
7.  Click **"Create Web Service"**.

---

## ⚠️ Important Notes
*   **Data Persistence**: The local ChromaDB vector store (`data/chroma_db`) is ignored in `.gitignore` to prevent large files from clogging git. On a fresh deployment, the app might need to re-index the documents.
    *   *Tip*: Ensure your `data/policies` folder containing the Markdown files IS committed to git, so the app can rebuild the index on startup.
*   **API Costs**: Remember that anyone with the link can use your API quota. Streamlit Cloud allows you to add password protection in settings if needed, or you can implement a simple password check in `src/app.py`.
