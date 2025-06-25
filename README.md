# ChatGPT Champions Dashboard

This Streamlit application analyzes ChatGPT usage data to identify and rank "Champions" based on their activity and usage patterns. The dashboard provides a leaderboard, allows for deep-dive analysis into individual user performance, and features adjustable scoring weights.

## 🚀 Getting Started

### Prerequisites

- Python 3.8+
- An AWS account with credentials configured to access the data in S3.

### 1. Installation

Clone the repository and install the required Python packages.

```bash
# Clone this repository
git clone <your-repo-url>
cd <your-repo-name>

# Create and activate a virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate # On Windows, use `venv\Scripts\activate`

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Secrets

This application uses Streamlit's secrets management to securely handle credentials for accessing data from AWS S3.

1.  Create a new folder in the root of your project directory named `.streamlit`.
2.  Inside the `.streamlit` folder, create a new file named `secrets.toml`.

Your directory structure should look like this:

```
.
├── .streamlit/
│   └── secrets.toml
├── app.py
├── data_loader.py
└── requirements.txt
```

3.  Add the credentials to your `secrets.toml` file. **The specific keys and values will be sent to you via Slack.**

### 3. Running the Application

Once you have installed the dependencies and configured your secrets, you can run the app using the following command in your terminal:

```bash
streamlit run app.py
```

The application will be available at `http://localhost:8501` in your web browser. 