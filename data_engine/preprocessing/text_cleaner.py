import pandas as pd

# charger les fichiers
df1 = pd.read_csv("../scraping/BeautifulSoup/marocannonces_offres_emploi.csv")
df2 = pd.read_csv("../scraping/rekrute_jobs_.csv")

# renommer colonnes pour uniformiser
df1 = df1.rename(columns={
    "Titre du poste": "titre",
    "Entreprise": "entreprise",
    "Secteur d'activite": "secteur",
    "Localisation geographique": "localisation",
    "Competences requises": "competences",
    "Niveau d'experience requis": "experience",
    "Type de contrat": "contrat",
})

df2 = df2.rename(columns={
    "description": "competences"
})

# garder colonnes utiles
cols = ["titre", "entreprise","secteur", "localisation", "competences", "experience", "contrat"]

df1 = df1[cols]
df2 = df2[cols]

# concat
df = pd.concat([df1, df2], ignore_index=True)
df = df.fillna("")
df.head()
df.to_csv("cleaned_offres.csv", index=False)