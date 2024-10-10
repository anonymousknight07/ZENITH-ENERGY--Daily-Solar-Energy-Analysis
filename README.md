# Zenith Energy Monitoring and Analysis

This project is developed for **ZENITH-ENERGY** to monitor and analyze energy generation data. The system logs various events, errors, and information related to energy monitoring and sends notifications via email.

## Project Structure

```bash
.
├── .env
├── .gitignore
├── capacity_checker.py
├── energy_monitor.log
├── energy_monitor.py
├── energy-generation-analysis-bffd27fb246d.json
├── README.md
├── requirements.txt

```
### Files

- **capacity_checker.py**: Script to check the capacity of energy plants.
- **energy_monitor.log**: Log file containing detailed logs of the monitoring process.
- **energy_monitor.py**: Main script for monitoring energy generation and sending notifications.
- **energy-generation-analysis-bffd27fb246d.json**: JSON file containing service account credentials for accessing Google APIs.
- **requirements.txt**: List of Python dependencies required for the project.

## Setup

1. **Clone the repository**:

    ```sh
    git clone <repository-url>
    cd <repository-directory>
    ```

2. **Install dependencies**:

    ```sh
    pip install -r requirements.txt
    ```

3. **Set up environment variables**:

    Create a `.env` file and add the necessary environment variables:
    ```
    EMAIL_USER=<your-email>
    EMAIL_PASS=<your-email-password>
    ```

4. **Enable Google Drive API**:
    Ensure that the Google Drive API is enabled for your project. Visit the following link to enable it:

    [Enable Google Drive API](https://console.developers.google.com/apis/api/drive.googleapis.com/overview?project=974107806487)
    
    [Enable Google Sheet API](https://console.cloud.google.com/marketplace/product/google/sheets.googleapis.com)

    
    Save the `energy-generation-analysis-bffd27fb246d.json` file in the root directory of the project. This JSON file should include the following fields:

    ```json
    {
      "type": "service_account",
      "project_id": "<your-project-id>",
      "private_key_id": "<your-private-key-id>",
      ":"private_key "-----BEGIN PRIVATE KEY-----\n<your-private-key>\n-----END PRIVATE KEY-----\n",
      "client_email": "<your-client-email>",
      "client_id": "<your-client-id>",
      "auth_uri": "https://accounts.google.com/o/oauth2/auth",
      "token_uri": "https://oauth2.googleapis.com/token",
      "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
      "client_x509_cert_url": "<your-client-x509-cert-url>"
    }
    ```

## Usage

1. **Run the energy monitor script**:

    ```sh
    python [energy_monitor.py]
    ```

2. **Check logs**:
    Monitor the `energy_monitor.log` file for detailed logs and error messages.


## Common Issues

- **Email Authentication Errors**:
    ```
    ERROR - Failed to send email: (535, b'5.7.8 Username and Password not accepted...')
    ```
    Ensure that your email credentials are correct and that less secure app access is enabled for your email account.

- **Google API Errors**:
    ```
    ERROR - Error getting Google Sheet data: APIError: [403]: Google Drive API has not been used in project...
    ```
    Make sure the Google Drive API is enabled and that the service account has the necessary permissions.

- **Invalid Format String**:
    ```
    ERROR - Error during analysis: Invalid format string
    ```
    Check the date format string in the [`analyze_energy_generation`]



## Contact

For any queries or support, please contact [Akshat Pandey](akshath.centaurus@gmail.com)
