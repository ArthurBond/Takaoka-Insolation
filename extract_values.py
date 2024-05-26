import csv
import pandas as pd
import os
import numpy as np

# Define the file path
file_path = r"./hm51116year.csv"

# Function to extract measurement values from METPV-20 normal irradiance
def extract_measurements(file_path):
    measurements = []
    with open(file_path, "r") as file:
        csv_reader = csv.reader(file)
        for row in csv_reader:
            if row and int(row[0]) in [1, 2, 3, 4, 5]:
                # Extract measurement values
                measurement_values = row[4:-5]
                measurements.append(measurement_values)
                # print(row)
    return measurements

if True:

    # Call the function and print the extracted measurements
    extracted_measurements = extract_measurements(file_path)
    # for measurement in extracted_measurements:
    #     print(measurement)

    start = "2018-01-01 00:00"
    end = "2018-12-31 23:00"
    freq = "H"  # Hourly frequency

    timestamps = pd.date_range(start=start, end=end, freq=freq)

    df = pd.DataFrame({
        "Time" : timestamps,
        "Global" : [int(item)/360 for sublist in extracted_measurements[::5] for item in sublist],
        "Direct" : [int(item)/360 for sublist in extracted_measurements[1::5] for item in sublist],
        "Diffuse" : [int(item)/360 for sublist in extracted_measurements[2::5] for item in sublist],
        "SunlightHours" : [int(item)/10 for sublist in extracted_measurements[3::5] for item in sublist],
        "Temperature" : [int(item)/10 for sublist in extracted_measurements[4::5] for item in sublist]
    })

    df.set_index("Time",inplace=True)

    df = df.astype(float)

    df1 = df.copy()

    daily = df.resample("D").sum()
    monthly = daily.resample("M").mean()
    yearly = monthly.resample("Y").mean()
    temp = df.Temperature.resample("D").mean()
    temp = temp.resample("M").mean()

    print("Average daily insolation for each month:")
    print(monthly.round(2),end="\n\n")

    print("Average temp for each month:")
    print(temp.round(2),end="\n\n")

    print("Average of the months:")
    print(yearly.round(2),end="\n\n")

    print("Minimum daily average insolation in a month:")
    print(monthly.min().round(2))


# Function to extract measurement values from METPV-20 at various angles
def extract_measurements(angle):
    # Define the file path
    directory = f"./{angle}/"

    month = {
        "01":[],
        "02":[],
        "03":[],
        "04":[],
        "05":[],
        "06":[],
        "07":[],
        "08":[],
        "09":[],
        "10":[],
        "11":[],
        "12":[]
    }
    for f_name in os.listdir(directory):

        if f_name.endswith("csv"):
        
            measurements = []
            month_key = f_name[-14:-12]
            
            with open(directory+f_name, "r") as file:
                csv_reader = csv.reader(file)
                
                for row in csv_reader:
                    if row[0] != "51116":
                        # Extract measurement values
                        measurement_values = row[5:-5]
                        measurements.append(measurement_values)
            month[month_key] = measurements
    
    return month

# Call the function and print the extracted measurements, e.g. 25 degrees
extracted_measurements = extract_measurements(25)

if True:
    start = "2018-01-01 00:00"
    end = "2018-12-31 23:00"
    freq = "H"  # Hourly frequency

    timestamps = pd.date_range(start=start, end=end, freq=freq)

    df = pd.DataFrame({
        "Time" : timestamps,
        "Global" : [int(item)/360 for sublist in list(extracted_measurements.values()) \
                    for subsublist in sublist for item in subsublist] #MJ/m2 -> avg hourly kW/m2
    })

    df.set_index("Time",inplace=True)

    df["Temp"] = df1["Temperature"]

    # ensure that the direct irradiance does not dip below zero, since it is a combination of two different datasets
    df["Direct"] = np.where(df["Global"] - df1["Diffuse"]>0, df["Global"] - df1["Diffuse"], 0)

    df = df.astype(float)

    # areas = [660e3,670e3,680e3,690e3,700e3,710e3,720e3,730e3,740e3,750e3,760e3,770e3]
    # area = 665832 # worst month no degradation
    # area = 956665 # worst month degradation at 25 years 
    area = 400e3
    # area = 1050e3
    # eff = 0.2244 # no degradation
    # area = 762178 # worst month degradation after 30 years
    # eff = 0.2244*0.874 # degradataion after 30 years
    # eff = 0.2244*0.937 # mean degradataion after 30 years, assume linear
    eff = 0.2244*0.944*0.8 # mean degradation across 25 years, piecewise linear
    # area = 990e3 # area required for direct taking into account degradation

    # TEMP COEF of PMAX is -0.30%/C
    # NOCT is 45

    # assumption, if cell temp is not greater than 25, the power output is the insolation*area*eff
    df["cell_temp"] = df["Temp"] + (45-20)/800*df["Global"]*1000
    df["expected_25"] = df.Global*area*eff
    df["expected_25_direct"] = df.Direct*area*eff
    df["expected_actual"] = np.where((df["cell_temp"]-25)>0,df.Global*area*eff*(1-((df["cell_temp"]-25)*0.003)),df.Global*area*eff)
    df["expected_actual_direct"] = np.where((df["cell_temp"]-25)>0,df.Direct*area*eff*(1-((df["cell_temp"]-25)*0.003)),df.Direct*area*eff)

    daily = df.resample("D").sum()
    monthly = daily.resample("M").sum()
    yearly = daily.resample("Y").sum()

    # print("Total daily energy generated:")
    # print(daily.round(2),end="\n\n")

    # print("Total energy generated each month:")
    # print(monthly.round(2),end="\n\n")

    print("Total energy generated each year:")
    print(yearly.round(2),end="\n\n")
