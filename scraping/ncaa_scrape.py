import pandas as pd 
import time
import random
from bs4 import BeautifulSoup
import requests

SCHOOL_ID_LU_PATH = 'data/ncaa/school_lookup.csv'
SEASON_ID_LU_PATH = 'data/ncaa/ncaa_seasonid_lu.csv'

def get_roster(school_id, year, season_id_lu_path = SEASON_ID_LU_PATH, headers = {'User-Agent':'Mozilla/5.0'}):     
    """    
    Transmits GET request to stats.ncaa.org, parses roster information into DataFrame
    
    Inputs
    -----
    school_id (int)
    year (int): Valid for 2012 - 2021
    headers (dict): to include with GET request. NCAA is not kind to robots
    (default: {'User-Agent':'Mozilla/5.0'})
    
    Outputs 
    -----
    DataFrame indexed by (team, season) containing the following columns:
     -   jersey
     -   stats_player_seq
     -   name
     -   position
     -   class_year
     -   games_played
     -   games_started
     -   height (if from 2019)
    
    """
    # get season_id from lookup table
    season_lu = pd.read_csv(SEASON_ID_LU_PATH).iloc[:,1:]
    season_id = season_lu[season_lu.season == year].id.values[0]
    # doesn't take regular params, have to build url manually
    r = requests.get(f"""https://stats.ncaa.org/team/{str(school_id)}/roster/{str(season_id)}""", headers=headers)
    soup = BeautifulSoup(r.text)
    res = []    
    if year == 2019: # records from 2019 season contain an additional field: 'height'
        num_values = 7
        col_names = ['jersey', 'stats_player_seq', 'name', 'position', 'height', 'class_year', 'games_played', 'games_started']
    else:
        num_values = 6
        col_names = ['jersey', 'stats_player_seq', 'name', 'position', 'class_year', 'games_played', 'games_started']
    for index, value in enumerate(soup.find_all('td')):
        if index % num_values == 0: # each player has 6 associated values in table 
            details = [] # new list for each players
            res.append(details) # DataFrame deals with extra list for us 
        if index % num_values == 1: # need to get stats_player_seq from href tag 
            try: # not sure if there is a way to do with w/o catching an error, but it works.
                details.append((value.contents[0].get('href')[-7:])) # 7-digit id 
                details.append(value.contents[0].string) # player name
            except:
                details.append(None) # no id found (occurs when players has 0 games played)
                details.append(value.contents[0]) # player name 
        else: 
            try: 
                details.append(value.contents[0]) 
            except: 
                details.append(None)
    df = pd.DataFrame(res)
    df.columns = col_names
    return df

def get_career_stats(player_id, year, headers = {'User-Agent':'Mozilla/5.0'}):
    """    
    Transmits GET request to stats.ncaa.org, parses career stats  into DataFrame
    
    Inputs
    -----
    player_id (int)
    year (int)
    headers (dict): to include with GET request. NCAA is not kind to robots
    (default: {'User-Agent':'Mozilla/5.0'})
    
    Outputs 
    -----
    DataFrame indexed by player containing the following columns:
    # TODO: fill in columns
    
    """  
    # get season_id from lookup table
    season_lu = pd.read_csv(SEASON_ID_LU_PATH).iloc[:,1:]
    season_id = season_lu[season_lu.season == year].id.values[0]
    # craft GET request to NCAA site
    payload = {'game_sport_year_ctl_id':str(season_id), 'stats_player_seq':str(player_id)}
    url = 'https://stats.ncaa.org/player/game_by_game'
    # send request
    r = requests.get(url, params=payload, headers=headers)
    # parse data
    soup = BeautifulSoup(r.text)
    table = soup.find_all('table')[2]

    # get table headers
    headers = []
    for val in table.find_all('th'):
        headers.append(val.string.strip())

    # get table data
    rows = []
    row = []
    for val in table.find_all('td'): # TODO: cleanup as much as possible
        # data is also encoded in data-order attr of td elements
        if 'data-order' in val.attrs:
            row.append(val['data-order'])
        elif val.a is not None: 
            row.append(val.a.attrs)
        elif val.string.strip() != 'Career' and 'width' not in val.attrs:
            if row != []:
                rows.append(row)
            row = []
            row.append(val.string.strip())
        else: 
            if val.string.strip() != 'Career':
                row.append(val.string.strip())
            
    # Turn into DataFrame
    df = pd.DataFrame(rows)
    df.columns = headers
    return df       

def build_roster_db(school_id_lu_path = SCHOOL_ID_LU_PATH, request_timeout = 0.25, save_as = 'players.csv', status_updates = True):
    """
    Calls get_roster to build a table of all (player, season) records
    
    Inputs
    -----
    school_id_lu_path (str): filepath of school_id lookup table
    (default: 'data/ncaa/school_lookup.csv')
    request_timeout (int): maximum timeout between requests in seconds, as to not overload NCAA servers
    (default: 0.25)
    save_as: filepath to save DataFrame as csv to. To not save, set to None
    (default: 'players.csv')
    status_updates: whether to give updates on progress of db creation
    (default: True)
    
    Outputs 
    -----
    DataFrame indexed by player, season containing stats_player_seq and relevant season_ids
    
    """
    df = pd.read_csv(school_id_lu_path).iloc[:, 1:]
    dfs = {}
    i = 0 
    # Potential Improvement. Vectorize the following loop. Is there a way to send multiple get requests at once?
    for index, row in df.iterrows():
        dfs[(row.school_id, row.year)] = get_roster(row.school_id, row.year, headers = {'User-Agent':'Mozilla/5.0'})
        # tryna be sneaky 
        time.sleep(random.uniform(0, request_timeout))
        if status_updates:
            i+=1
            if i % 50 == 0:
                print(str(i)+'/8437')
            
    players = pd.DataFrame() # create an empty df
    for key in dfs.keys(): # for each (team, season) dataframe in dictionary
        df_new = dfs[key].copy() # don't write over while iterating through
        if key[1] == 2019:  # for whatever reason 2019 season records contain an additional field
            df_new = df_new.drop(columns=['height']) # get rid of said additional field for 2019 records
        # add columns from data in dictionary
        df_new['school_id'] = key[0] 
        df_new['season'] = key[1] 
        # append data to result
        players = pd.concat([res, df_new])

    seasons = pd.read_csv(SEASON_ID_LU_PATH).iloc[:,1:]
    res = players.merge(seasons, how='left', on='season')
    players = players.rename(columns={'id':'season_id'})        
    res = players
    if save_as is not None: 
        res.to_csv('data/ncaa/player_seasons.csv', index=False)
    return res    
