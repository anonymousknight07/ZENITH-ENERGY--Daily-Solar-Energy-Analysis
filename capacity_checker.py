import csv
from datetime import datetime

def format_date(date_string):
   
    date_formats = ['%Y-%m-%d', '%d-%m-%Y', '%m-%d-%Y', '%d/%m/%Y', '%m/%d/%Y']
    for fmt in date_formats:
        try:
            date_obj = datetime.strptime(date_string, fmt)
            return date_obj.strftime('%m/%d/%Y')
        except ValueError:
            continue
    return date_string 

def check_low_generation(csv_file_path):
    with open(csv_file_path, 'r') as file:
        csv_reader = csv.reader(file)
        headers = next(csv_reader)  

        print("Available columns:")
        for i, header in enumerate(headers):
            print(f"{i}: {header}")

        plant_name_index = int(input("Enter the index for 'Plant name' column: "))
        capacity_index = int(input("Enter the index for 'Plant capacity in KW' column: "))

        for row in csv_reader:
            plant_name = row[plant_name_index]
            try:
                capacity = float(row[capacity_index])
            except ValueError:
                print(f"Warning: Invalid capacity value for {plant_name}. Skipping this row.")
                continue

            for i, value in enumerate(row):
                if i > capacity_index:  
                    try:
                        daily_value = float(value)
                        if daily_value < capacity * 3:
                            date = format_date(headers[i])
                            print(f"Generation is low for {plant_name} on {date}")
                    except ValueError:
                       
                        pass
csv_file_path = 'plant_data.csv'  
check_low_generation(csv_file_path)