# TODO: Turn into script
from bs4 import BeautifulSoup
import requests
import pandas as pd 
import numpy as np
import lxml 

urls = {'perfect_game':'https://www.perfectgame.org/Rankings/Players/NationalRankings.aspx',
        'baseball_factory':'https://www.baseballfactory.com/recruiting-and-promotion/the-top-100/', 
       }

source = 'perfect_game'
year = 2017
payload = {'gyear':str(year)}
url = urls[source]
r = requests.get(url, params=payload)
response = r.text
soup = BeautifulSoup(response)
table = soup.find(id='ContentTopLevel_ContentPlaceHolder1_gvPlayers')

# a IDs
# ContentTopLevel_ContentPlaceHolder1_gvPlayers_hlPlayerName_0
# ContentTopLevel_ContentPlaceHolder1_gvPlayers_hl4yr_0
# ContentTopLevel_ContentPlaceHolder1_gvPlayers_hlTournamentTeam_0

# span IDs
# ContentTopLevel_ContentPlaceHolder1_gvPlayers_lblNatRank_
# ContentTopLevel_ContentPlaceHolder1_gvPlayers_lblHeight_
# ContentTopLevel_ContentPlaceHolder1_gvPlayers_lblWeight_
# ContentTopLevel_ContentPlaceHolder1_gvPlayers_lblBatsThrows_
# ContentTopLevel_ContentPlaceHolder1_gvPlayers_lblHometown_
# ContentTopLevel_ContentPlaceHolder1_gvPlayers_lblDrafted_
# ContentTopLevel_ContentPlaceHolder1_gvPlayers_lblDebuted_
# ContentTopLevel_ContentPlaceHolder1_gvPlayers_lblTravelTeam_
# ContentTopLevel_ContentPlaceHolder1_gvPlayers_InternalCommentLiteral_

ids = {'player_name':'ContentTopLevel_ContentPlaceHolder1_gvPlayers_hlPlayerName_',
    'college':'ContentTopLevel_ContentPlaceHolder1_gvPlayers_hl4yr_',
    'rank':'ContentTopLevel_ContentPlaceHolder1_gvPlayers_lblNatRank_',
    'height':'ContentTopLevel_ContentPlaceHolder1_gvPlayers_lblHeight_',
    'weight':'ContentTopLevel_ContentPlaceHolder1_gvPlayers_lblWeight_',
    'bats/throws':'ContentTopLevel_ContentPlaceHolder1_gvPlayers_lblBatsThrows_',
    'hometown':'ContentTopLevel_ContentPlaceHolder1_gvPlayers_lblHometown_',
    'drafted':'ContentTopLevel_ContentPlaceHolder1_gvPlayers_lblDrafted_',
    'debuted':'ContentTopLevel_ContentPlaceHolder1_gvPlayers_lblDebuted_',
    'travel_team':'ContentTopLevel_ContentPlaceHolder1_gvPlayers_lblTravelTeam_',
    'notes':'ContentTopLevel_ContentPlaceHolder1_gvPlayers_InternalCommentLiteral_'
      }

source = 'perfect_game'
url = urls[source]

dfs = {}
for year in range(2002, 2022):
    payload = {'gyear':str(year)}
    r = requests.get(url, params=payload)
    response = r.text
    soup = BeautifulSoup(response)
    table = soup.find(id='ContentTopLevel_ContentPlaceHolder1_gvPlayers')
    
    data = {}
    for i in range(100):
        details = []
        for key in ids:
            try: 
                details.append(str(table.find(id=ids[key]+str(i)).string))
            except: 
                details.append('NULL')
        data[i]=details
    df = pd.DataFrame.from_dict(data, orient='index')
    df.columns = ids.keys()
    df = df.iloc[:50]
    df['class_year'] = year
    dfs[str(year)] = df
    
data = pd.DataFrame()
for i in dfs.items():
    data = data.append(i[1])
data.to_csv('data/perfectgame/perfectgame_top50_2002-2021_raw.csv', index=False)