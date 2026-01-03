# Monthly Data Bot 📊

A Streamlit application for tracking and visualizing monthly meter readings (e.g., electricity, water, gas). This app allows users to manually enter data, manage meter types, and view historical trends via an interactive dashboard.

## Features

-   **User Authentication:** Secure login and registration using bcrypt.
-   **Dashboard:** Visualize consumption trends over time.
-   **Data Entry:** Easy-to-use form for inputting new meter readings.
-   **Meter Management:** Define and customize different types of meters.
-   **Cloud Storage:** Uses AWS DynamoDB for reliable data persistence.

## Prerequisites

-   Python 3.9+
-   AWS Account with DynamoDB access

## Installation

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd monthly-data-streamlit
    ```

2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

## Configuration

This application requires AWS credentials to access DynamoDB.

### Local Development
Create a file at `.streamlit/secrets.toml` with the following content:

```toml
AWS_ACCESS_KEY_ID = "your_access_key"
AWS_SECRET_ACCESS_KEY = "your_secret_key"
AWS_DEFAULT_REGION = "eu-central-1"
```

### Streamlit Cloud Deployment
When deploying to Streamlit Cloud, add the same secrets in the **Advanced Settings** -> **Secrets** area of your app dashboard.

## Database Structure

The app expects two DynamoDB tables:

1.  **`meter_reading_bot`** (Main Data)
    -   Partition Key: `chat_id_and_type` (String)
    -   Sort Key: `reading_date` (String, ISO format)

2.  **`meter_reading_users`** (User Data)
    -   Partition Key: `username` (String)

## Running the App

```bash
streamlit run app.py
```
