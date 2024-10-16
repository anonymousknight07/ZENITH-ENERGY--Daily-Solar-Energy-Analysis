import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import schedule
import time
import os
from dotenv import load_dotenv
import logging
import re

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('energy_monitor.log'),
        logging.StreamHandler()
    ]
)

# Load environment variables
load_dotenv()

# Get environment variables with error handling
def get_env_variable(var_name):
    value = os.getenv(var_name)
    if value is None:
        raise ValueError(f"Environment variable {var_name} is not set")
    return value

try:
    # Google Sheets configuration
    SHEET_ID = get_env_variable('GOOGLE_SHEET_ID')
    CREDENTIALS_PATH = get_env_variable('GOOGLE_CREDENTIALS_PATH')
    
    # Email configuration
    SENDER_EMAIL = get_env_variable('EMAIL_SENDER')
    EMAIL_PASSWORD = get_env_variable('EMAIL_PASSWORD')
    RECEIVER_EMAIL = get_env_variable('EMAIL_RECEIVER')
    CC_EMAIL = os.getenv('EMAIL_CC')  # Optional
    
    # SMTP configuration
    SMTP_SERVER = get_env_variable('SMTP_SERVER')
    SMTP_PORT = int(get_env_variable('SMTP_PORT'))
    SMTP_USE_TLS = get_env_variable('SMTP_USE_TLS').lower() == 'true'
    SMTP_USE_SSL = get_env_variable('SMTP_USE_SSL').lower() == 'true'
    
except ValueError as e:
    logging.error(f"Configuration error: {e}")
    exit(1)

def normalize_column_name(col_name):
    """Normalize column names by removing extra spaces and converting to lowercase"""
    return re.sub(r'\s+', ' ', col_name).strip()

def find_column_by_pattern(df, pattern):
    """Find a column that matches a given pattern"""
    pattern = re.compile(pattern, re.IGNORECASE)
    for col in df.columns:
        if pattern.search(normalize_column_name(col)):
            return col
    return None

def find_latest_month_worksheet(worksheets):
    month_pattern = re.compile(r'^(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)-\d{2}$')
    
    # Filter out non-month worksheets and sort them
    month_worksheets = [ws for ws in worksheets if month_pattern.match(ws)]
    
    if not month_worksheets:
        return None
    
    # Convert month names to datetime objects for proper sorting
    month_dates = []
    for ws in month_worksheets:
        try:
            date = datetime.strptime(ws, '%b-%y')
            month_dates.append((date, ws))
        except ValueError:
            # Handle any unexpected format
            continue
    
    if not month_dates:
        return None
    
    # Sort by date and get the latest
    latest = sorted(month_dates, key=lambda x: x[0], reverse=True)[0][1]
    return latest

def test_email_connection():
    try:
        if SMTP_USE_SSL:
            server = smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT)
        else:
            server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
            if SMTP_USE_TLS:
                server.starttls()

        server.login(SENDER_EMAIL, EMAIL_PASSWORD)
        logging.info("Email connection test successful")
        server.quit()
        return True
    except Exception as e:
        logging.error(f"Email connection test failed: {e}")
        return False

def get_google_sheet_data():
    try:
        # Setup credentials
        scope = ['https://spreadsheets.google.com/feeds',
                 'https://www.googleapis.com/auth/drive']
        credentials = ServiceAccountCredentials.from_json_keyfile_name(
            CREDENTIALS_PATH, scope)
        client = gspread.authorize(credentials)
        
        # Open the specific spreadsheet using the ID
        spreadsheet = client.open_by_key(SHEET_ID)
        
        # List all worksheets
        all_worksheets = [worksheet.title for worksheet in spreadsheet.worksheets()]
        logging.info(f"Available worksheets: {all_worksheets}")
        
        # Find the latest month worksheet
        latest_month = find_latest_month_worksheet(all_worksheets)
        
        if not latest_month:
            logging.error("No valid month worksheets found")
            return None, None, None
        
        logging.info(f"Using worksheet: {latest_month}")
        worksheet = spreadsheet.worksheet(latest_month)
        
        # Get all values
        data = worksheet.get_all_values()
        
        if not data:
            logging.error("No data found in the worksheet")
            return None, None, None

        # Convert to pandas DataFrame
        df = pd.DataFrame(data[1:], columns=data[0])
        
        # Log all column names for debugging
        logging.info(f"Available columns: {list(df.columns)}")
        
        # Find the plant capacity column - try different patterns
        capacity_patterns = [
            r'plant capacity.*kw',
            r'capacity.*kw',
            r'.*capacity.*kw',
            r'.*kw'
        ]
        
        capacity_col = None
        for pattern in capacity_patterns:
            capacity_col = find_column_by_pattern(df, pattern)
            if capacity_col:
                logging.info(f"Found capacity column: {capacity_col}")
                break
        
        # Find the plant name column
        plant_name_patterns = [
            r'plant name',
            r'name',
            r'plant'
        ]
        
        plant_name_col = None
        for pattern in plant_name_patterns:
            plant_name_col = find_column_by_pattern(df, pattern)
            if plant_name_col:
                logging.info(f"Found plant name column: {plant_name_col}")
                break
        
        if not capacity_col or not plant_name_col:
            raise ValueError(f"Required columns not found. Capacity col: {capacity_col}, Plant name col: {plant_name_col}")
        
        # Convert capacity column to numeric
        df[capacity_col] = pd.to_numeric(df[capacity_col], errors='coerce')
        
        # Convert date columns to numeric
        date_pattern = re.compile(r'\d{1,2}/\d{1,2}/\d{4}')
        date_columns = [col for col in df.columns if date_pattern.match(col)]
        for col in date_columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        
        logging.info(f"Successfully retrieved data. Shape: {df.shape}")
        return df, capacity_col, plant_name_col
    
    except Exception as e:
        logging.error(f"Error getting Google Sheet data: {e}")
        return None, None, None

def send_email(low_generation_sites, date):
    msg = MIMEMultipart()
    msg['From'] = SENDER_EMAIL
    msg['To'] = RECEIVER_EMAIL
    if CC_EMAIL:
        msg['Cc'] = CC_EMAIL
    msg['Subject'] = f"Low Energy Generation Report - {date}"
    
    if isinstance(low_generation_sites, str):
        body = f"Error in analysis: {low_generation_sites}"
    elif low_generation_sites:
        body = f"The following sites have lower than expected energy generation for {date}:\n\n"
        for site, capacity, actual in low_generation_sites:
            body += f"- {site}: Generated {actual:.2f} kWh (Capacity: {capacity} kW)\n"
    else:
        body = f"All sites are generating sufficient energy for {date}"
    
    msg.attach(MIMEText(body, 'plain'))
    
    try:
        if SMTP_USE_SSL:
            server = smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT)
        else:
            server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
            if SMTP_USE_TLS:
                server.starttls()

        server.login(SENDER_EMAIL, EMAIL_PASSWORD)
        
        all_recipients = [RECEIVER_EMAIL] + ([CC_EMAIL] if CC_EMAIL else [])
        server.send_message(msg)
        
        server.quit()
        logging.info("Email sent successfully")
        return True
    except Exception as e:
        logging.error(f"Failed to send email: {e}")
        return False

def analyze_energy_generation():
    try:
        result = get_google_sheet_data()
        if result[0] is None:
            return "Failed to retrieve data from Google Sheet"
        
        df, capacity_col, plant_name_col = result
        
        today = get_today_format()
        logging.info(f"Analyzing data for date: {today}")
        
        if today not in df.columns:
            logging.warning(f"No data available for {today}")
            return f"No data available for {today}"
        
        low_generation_sites = []
        
        for index, row in df.iterrows():
            plant_name = row[plant_name_col]
            plant_capacity = row[capacity_col]
            
            if pd.isna(plant_name) or pd.isna(plant_capacity):
                continue
                
            today_generation = row[today]
            
            if pd.notna(today_generation) and float(today_generation) < (3 * float(plant_capacity)):
                low_generation_sites.append((plant_name, plant_capacity, float(today_generation)))
        
        logging.info(f"Analysis complete. Found {len(low_generation_sites)} low generation sites")
        return low_generation_sites
        
    except Exception as e:
        logging.error(f"Error during analysis: {str(e)}")
        import traceback
        logging.error(f"Traceback: {traceback.format_exc()}")
        return f"Error during analysis: {str(e)}"


def get_today_format():
    """Get today's date in the format that matches the spreadsheet"""
    today = datetime.now()
    day = today.day
    # Format the date as 'MM/D/YYYY' for single digit days or 'MM/DD/YYYY' for double digit days
    return f"{today.month}/{day}/{today.year}"


def should_run_job():
    current_time = datetime.now()
    target_time = current_time.replace(hour=19, minute=0, second=0, microsecond=0)
    return current_time >= target_time

def job():
    if should_run_job():
        current_date = get_today_format()
        logging.info(f"Running analysis at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        result = analyze_energy_generation()
        send_email(result, current_date)
    else:
        logging.info("Not yet 7:00 PM, skipping job")
        
        
if __name__ == "__main__":
    logging.info("Starting script and running initial tests...")
    
    # Test date formatting
    test_date = get_today_format()
    logging.info(f"Using date format: {test_date}")
    
    # Run initial tests
    test_email_connection()
    
    # Schedule the job to run every hour
    schedule.every().hour.do(job)
    
    logging.info("Script is running. Press Ctrl+C to stop.")
    try:
        # Run the job immediately if it's after 7 PM
        if should_run_job():
            job()
        
        while True:
            schedule.run_pending()
            time.sleep(60)
    except KeyboardInterrupt:
        logging.info("\nScript stopped by user")