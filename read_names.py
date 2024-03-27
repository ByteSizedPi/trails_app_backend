import pandas as pd

# Specify the path to the Excel file
excel_file = (
    "C:/Personal/Coding/Trails App/Data/Trials info/NRTC 2024 Riding Numbers.xlsx"
)

# Read the Excel file into a pandas DataFrame, skipping the first 2 rows
df = pd.read_excel(excel_file, skiprows=2)


def getClass(cls):
    switcher = {"M": 1, "E": 2, "I": 3, "C": 4}
    return switcher.get(cls, "Unknown")


insert_query = (
    "INSERT INTO Riders (event_id, rider_number, rider_name, class_id) VALUES "
)

# Create a dictionary to keep track of processed numbers
processed_numbers = {}

for Number, Name, Class in zip(df["NUMBER"], df["NAME"], df["CLASS"]):
    if pd.isnull(Number) or pd.isnull(Name) or pd.isnull(Class):
        continue
    if Number in processed_numbers:
        print(f"Error: Duplicate number {Number} for {Name}, {Class}\n\n")
        break
    processed_numbers[Number] = True
    class_name = getClass(Class)
    insert_query += f"(1, {int(Number)}, '{Name}', {class_name}),"
insert_query = insert_query[:-1] + ";"
print(insert_query)
