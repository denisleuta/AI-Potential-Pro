import pandas as pd

df1 = pd.read_excel("julydatasets2025/filtr/AM_players_filtr.xlsx")
df2 = pd.read_excel("julydatasets2025/filtr/FB_players_filtr.xlsx")
df3 = pd.read_excel("julydatasets2025/filtr/GK_players_filtr.xlsx")
df4 = pd.read_excel("julydatasets2025/filtr/W_players_filtr.xlsx")
df5 = pd.read_excel("julydatasets2025/filtr/DM_players_filtr.xlsx")
df6 = pd.read_excel("julydatasets2025/filtr/CD_players_filtr.xlsx")
df7 = pd.read_excel("julydatasets2025/filtr/ST_players_filtr.xlsx")

datasets = [df1, df2, df3, df4, df5, df6, df7]

combined_df = pd.concat([df.iloc[1:] for df in datasets], ignore_index=True)

combined_df.to_excel("julydatasets2025/short_2025_may.xlsx", index=False)

print("Данные объединены, дублирующиеся заголовки удалены!")
