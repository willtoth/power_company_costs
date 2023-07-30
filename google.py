import requests
from googleapiclient.discovery import build
from google.auth import exceptions
from google.oauth2 import service_account
from datetime import datetime

def append_gsheet(min_price_new_customer, min_price_existing_customer, months_min, months_max):
    SERVICE_ACCOUNT_FILE = 'creds.json'
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

    creds = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    service = build('sheets', 'v4', credentials=creds)

    sheet = service.spreadsheets()
    spreadsheet_id = '1CAjMipLlA6ZIbHEWf3yZiTQK7NE4OViDUqJpMastdQw'

    range_name = f'Price {months_min} - {months_max} Month'

    date = datetime.now().strftime("%m/%d/%Y")

    values = [
        [
            date,
            min_price_new_customer['company_name'] if min_price_new_customer else "",
            min_price_new_customer['term_value'] if min_price_new_customer else "",
            min_price_new_customer['price_kwh2000'] if min_price_new_customer else "",
            min_price_existing_customer['company_name'] if min_price_existing_customer else "",
            min_price_existing_customer['term_value'] if min_price_existing_customer else "",
            min_price_existing_customer['price_kwh2000'] if min_price_existing_customer else "",
        ]
    ]

    body = {
        'values': values
    }

    result = sheet.values().append(
        spreadsheetId=spreadsheet_id,
        range=range_name,
        valueInputOption='RAW',
        insertDataOption='INSERT_ROWS',
        body=body).execute()

    print('{0} cells appended.'.format(result \
                                    .get('updates') \
                                    .get('updatedCells')))


def pull_plans(months_min, months_max):
    exclude_companies = ["Octopus Energy"]

    url = "http://api.powertochoose.org/api/PowerToChoose/plans"

    headers = {'Accept': 'application/json'}

    payload = {
        "zip_code": "75007",
        "estimated_use": "2000",
        "price_from": "",
        "price_to": "",
        "monthly_fee_from": "",
        "monthly_fee_to": "",
        "plan_mo_from": f"{months_min}",
        "plan_mo_to": f"{months_max}",
        "plan_type": "1",
        "company_id": "",
    }

    response = requests.post(url, headers=headers, data=payload)

    response_json = response.json()
    data = response_json['data']

    # Filter the data to only entries with 'price_kwh2000' and not in exclude_companies
    valid_entries = [entry for entry in data if 'price_kwh2000' in entry and entry['company_name'] not in exclude_companies]

    # Separate new customer and existing customer entries
    new_customer_entries = [entry for entry in valid_entries if entry['new_customer']]
    existing_customer_entries = [entry for entry in valid_entries if not entry['new_customer']]
    
    min_price_new_customer = None
    min_price_existing_customer = None
    # Find min price entries
    if len(new_customer_entries) > 0:
        min_price_new_customer = min(new_customer_entries, key=lambda x: x['price_kwh2000'])

    if len(existing_customer_entries) > 0:
        min_price_existing_customer = min(existing_customer_entries, key=lambda x: x['price_kwh2000'])

    # Print details
    for entry in [min_price_new_customer, min_price_existing_customer]:
        try:
            print(f"Company: {entry['company_name']}")
            print(f"New customer: {'Yes' if entry['new_customer'] else 'No'}")
            print(f"Plan name: {entry['plan_name']}")
            print(f"Plan type: {entry['plan_type']}")
            print(f"Term value: {entry['term_value']}")
            print(f"Renewable energy description: {entry['renewable_energy_description']}")
            print(f"Website: {entry['website']}")
            print(f"price_kwh2000: {entry['price_kwh2000']}")
        except:
            print("Expection when printing this entry.")
        print("-------------")

    return (min_price_new_customer, min_price_existing_customer)

if __name__ == '__main__':
    min_price_new_customer, min_price_existing_customer = pull_plans(1, 6)
    append_gsheet(min_price_new_customer, min_price_existing_customer, 1, 6)
    min_price_new_customer, min_price_existing_customer = pull_plans(12, 36)
    append_gsheet(min_price_new_customer, min_price_existing_customer, 12, 36)

