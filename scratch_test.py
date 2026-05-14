import pandas as pd
import numpy as np
import re

target_columns = ["titre", "entreprise", "secteur", "localisation", "experience", "contrat", "description"]

df_rekrute = pd.DataFrame()
df_morocco = pd.DataFrame()

for col in target_columns:
    if col not in df_rekrute.columns:
        df_rekrute[col] = np.nan
    if col not in df_morocco.columns:
        df_morocco[col] = np.nan

df_rekrute = df_rekrute[target_columns]
df_morocco = df_morocco[target_columns]

df = pd.concat([df_rekrute, df_morocco], ignore_index=True)
print("Columns after concat:", df.columns)

df['titre'] = df['titre'].astype(str)

def contains_arabic(text):
    return bool(re.search(r'[\u0600-\u06FF]', text))

df = df[~df['titre'].apply(contains_arabic)]
print("Columns after arabic filter:", df.columns)

df = df[df['titre'].str.len() >= 5]
print("Columns after len filter:", df.columns)
