import pandas as pd

# Assuming the dataset is in a CSV file (replace 'your_file.csv' with the actual file path)
data = pd.read_csv('detentions_2021_25.csv')

# Extract the unique crimes from the 'offense' column
unique_crimes = data['offense'].unique()

# Display the unique crimes
print(unique_crimes)
