# ChatGPT Champions Dashboard

This is a Streamlit web application that analyzes user activity from a CSV file to identify and rank "ChatGPT Champions."

## Getting Started

### Prerequisites
- Python 3.8+
- pip

### Installation

1. **Clone the repository:**
   ```bash
   git clone <your-repo-url>
   cd <your-repo-name>
   ```

2. **Create and activate a virtual environment (recommended):**
   ```bash
   # For macOS and Linux
   python3 -m venv venv
   source venv/bin/activate

   # For Windows
   python -m venv venv
   .\venv\Scripts\activate
   ```

3. **Install the required packages:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up your password:**

   This application uses Streamlit's secrets management for password protection. You'll need to create a file to store the password.

   - Create a directory named `.streamlit` in the root of the project folder.
   - Inside that directory, create a file named `secrets.toml`.

### Running the App

Once the dependencies are installed and you have set up your password, you can run the Streamlit app with the following command:

```bash
streamlit run app.py
```

The application will open in your default web browser.

## About the App

The dashboard allows you to:
- View a leaderboard of top "Champions."
- Adjust the weighting of different metrics to calculate a `Champion Score`.
- See a detailed, week-by-week breakdown of individual user performance.
- Explore the raw and processed data. 