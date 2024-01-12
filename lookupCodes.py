import pandas as pd

def append_county(input_string):
    # Check if 'COUNTY' is in the string, and append it if not
    if 'County' not in input_string:
        input_string += ' County'
    return input_string

def state_to_abbreviation(state_name):
    # Dictionary mapping state names to their abbreviations
    if len(state_name) == 2:
        return state_name.upper()

    states = {
        'Alabama': 'AL', 'Alaska': 'AK', 'Arizona': 'AZ', 'Arkansas': 'AR',
        'California': 'CA', 'Colorado': 'CO', 'Connecticut': 'CT', 'Delaware': 'DE',
        'Florida': 'FL', 'Georgia': 'GA', 'Hawaii': 'HI', 'Idaho': 'ID',
        'Illinois': 'IL', 'Indiana': 'IN', 'Iowa': 'IA', 'Kansas': 'KS',
        'Kentucky': 'KY', 'Louisiana': 'LA', 'Maine': 'ME', 'Maryland': 'MD',
        'Massachusetts': 'MA', 'Michigan': 'MI', 'Minnesota': 'MN', 'Mississippi': 'MS',
        'Missouri': 'MO', 'Montana': 'MT', 'Nebraska': 'NE', 'Nevada': 'NV',
        'New Hampshire': 'NH', 'New Jersey': 'NJ', 'New Mexico': 'NM', 'New York': 'NY',
        'North Carolina': 'NC', 'North Dakota': 'ND', 'Ohio': 'OH', 'Oklahoma': 'OK',
        'Oregon': 'OR', 'Pennsylvania': 'PA', 'Rhode Island': 'RI', 'South Carolina': 'SC',
        'South Dakota': 'SD', 'Tennessee': 'TN', 'Texas': 'TX', 'Utah': 'UT',
        'Vermont': 'VT', 'Virginia': 'VA', 'Washington': 'WA', 'West Virginia': 'WV',
        'Wisconsin': 'WI', 'Wyoming': 'WY'
    }

    # Convert the state name to title case to match dictionary keys
    state_name_title = state_name.title()

    # Return the abbreviation or a default value if the state is not found
    return states.get(state_name_title, "Unknown State")

def find_countyns(file_path, county_name, state_name):
    # Read the CSV file into a DataFrame
    df = pd.read_csv(file_path)

    county_name = append_county(county_name)
    state_name = state_to_abbreviation(state_name)

    filtered_df = df[(df['COUNTYNAME'] == county_name) & (df['STATE'] == state_name)]

    # Extract the COUNTYNS code
    if not filtered_df.empty:
        return filtered_df['COUNTYNS'].iloc[0]
    else:
        return None

