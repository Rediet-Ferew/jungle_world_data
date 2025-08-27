from simple_salesforce import Salesforce
import requests
import pandas as pd
from io import StringIO
from dotenv import load_dotenv
import os
from datetime import datetime
import pytz

# Load environment variables from .env file
load_dotenv()

# Connect to Salesforce
sf = Salesforce(
    username=os.getenv('SF_USERNAME'),
    password=os.getenv('SF_PASSWORD'),
    security_token=os.getenv('SF_SECURITY_TOKEN')
)

def get_data():

    # Get the current date and time, and set it to midnight UTC
    current_time = datetime.now(pytz.utc)
    current_time_midnight = current_time.replace(hour=0, minute=0, second=0, microsecond=0)

    # Define the start date (2023-08-27) and ensure it is set to midnight UTC
    start_date = datetime(2023, 8, 28, 0, 0, 0, 0).replace(tzinfo=pytz.utc)

    # Format the dates in the required format 'YYYY-MM-DDTHH:MM:SS.000+00:00'
    start_date_str = start_date.isoformat()  # e.g. "2023-08-27T00:00:00+00:00"
    current_time_str = current_time_midnight.isoformat()  # e.g. "2025-03-13T00:00:00+00:00"

    # Now remove quotes around the DateTime fields in the query:
    results = sf.query_all(f"""
        SELECT
            Bnow__Booking__c.Bnow__Customer_Email__c,
            Bnow__Booking__c.Bnow__All_Products_Processed__c,
            Bnow__Booking__c.Bnow__Balance_Paid__c,
            Bnow__Booking__c.Bnow__Status__c,
            Bnow__Customer_ID__c
        FROM Bnow__Booking__c
        WHERE
            Bnow__Booking__c.Bnow__All_Products_Processed__c >= {start_date_str}
            AND Bnow__Booking__c.Bnow__All_Products_Processed__c <= {current_time_str}
            AND Bnow__Booking__c.Bnow__Status__c IN ('Booked', 'Cancelled', 'Checked In', 'Moved', 'Not Paid', 'Parked', 'Pending', '')
            AND Bnow__Booking__c.Bnow__Site_Name__c = 'Jungle World'
    """)
    return results

def get_dataframe(results):

    # Extract records from the Salesforce response
    records = results["records"]

    # Convert to DataFrame
    df = pd.DataFrame(records)

    # Select only relevant columns
    df = df[["Bnow__Customer_Email__c", "Bnow__All_Products_Processed__c", "Bnow__Balance_Paid__c", "Bnow__Customer_ID__c"]]
    
    # Rename columns for better readability
    df.columns = ["email", "visit_date", "purchase_value", "customer_id"]

    # Convert Booking Date to datetime format
    df["visit_date"] = pd.to_datetime(df["visit_date"])

    # Convert Balance Paid to float
    df["purchase_value"] = df["purchase_value"].astype(float)


    # Total purchases for null emails but with a valid customer_id
    # df_null_emails_with_customer = df[(df['email'].isna() | (df['email'] == '')) & (df['customer_id'].notna() & (df['customer_id'] != ''))]

    # total_null_email_purchases = df_null_emails_with_customer['purchase_value'].sum()

    # print(f"Total purchase value for null emails with customer_id: {total_null_email_purchases}")

    df_customers = df[df['customer_id'].notna() & (df['customer_id'] != '')]
    df_cleaned = df_customers[df_customers['email'].notna() & (df_customers['email'] != '')]

    emails_to_remove = ['beth.a.w.1998@gmail.com', 'ellison.melanie@yahoo.co.uk', 'hello@jungleworldpark.com', 'madirose1202@outlook.com']

#     df_to_remove = df[df['email'].isin(emails_to_remove)]

# # Sum the purchase values
#     total_removed_purchases = df_to_remove['purchase_value'].sum()

#     print(f"Total purchase value for removed emails: {total_removed_purchases}")

    df_filtered = df_cleaned[~df_cleaned['email'].isin(emails_to_remove)]

    
    # total_filtered_purchases = df_filtered['purchase_value'].sum()

    # print(f"Total purchase value for filtered emails: {total_filtered_purchases}")
    
    return [df_filtered, df]


