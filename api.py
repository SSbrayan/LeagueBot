import requests
import configparser
import json
import pandas as pd
from tabulate import tabulate



def load_config(file_path):
    config = configparser.ConfigParser()
    with open(file_path, 'r', encoding='utf-8') as file:
        config.read_file(file)
    return config



def get_match_details(match_id):
    url = f'https://api.opendota.com/api/matches/{match_id}'
    response = requests.get(url)
    match_details = response.json()
    return match_details


def get_matches_details_list(matches_ids_list):
    matches_details_list=[]
    for match_id in matches_ids_list:
        matches_details_list.append(get_match_details(match_id))
    return matches_details_list
        

def get_player_list(raw_matches_details_list):
    player_list=[]
    for match in raw_matches_details_list:
        for player in match['players']:
            if player['personaname'] not in player_list:
                player_list.append(player['personaname'])
    return player_list



def get_match_history(raw_matches_details_list,config):
    match_history=[]
    for match in raw_matches_details_list:
        match_dict={}
        for match_detail in config['settings']['match_stats'].split(','):
            match_dict[match_detail]=match[match_detail]
        match_dict['players']=[]
        for player in match['players']:
            player_dict={}
            for player_detail in config['settings']['personal_stats'].split(','):
                player_dict[player_detail]=player[player_detail]
            match_dict['players'].append(player_dict.copy())
        match_history.append(match_dict.copy())

    return match_history


def twin_merger(config,df):
    twins = json.loads(config['settings']['twins'])
    df = df.fillna("None")
    df['personaname'] = df['personaname'].map(lambda x: twins.get(x, x))

    return df



def create_league_table(data,config):
    league_table=pd.DataFrame()
    agg_funcs = json.loads(config['settings']['personal_agg_funcs'])

    for match in data:
        df_temp = pd.DataFrame(match['players'])
        league_table = pd.concat([league_table, df_temp], ignore_index=True)
    


    league_table = twin_merger(config,league_table)
    
    league_table = league_table.groupby('personaname').agg(agg_funcs)


    return league_table

def correction(league_table,config):
    pre_league_points = json.loads(config['settings']['correction'])
    df_correction=pd.DataFrame(pre_league_points)
    df_correction= df_correction.set_index('personaname')
    df_correction['correction']=df_correction['correction'].astype(int)
    league_table['pre_league']=df_correction['correction']

    

    league_table['score'] = (league_table['win'] - league_table['lose'] + league_table['pre_league']) * 25 + 1000
    league_table = league_table.round(0)
    x=json.loads(config['settings']['table_order'])
    league_table = league_table[x]

    return league_table





def main():
    # Load the configuration from the file
    config = load_config('config.ini')
    
    # Access the settings from the configuration
    matches_list = config['settings']['matches'].split(',')

    raw_matches_details_list=get_matches_details_list(matches_list)

    #player_list=get_player_list(raw_matches_details_list)
    #print(player_list)


    data=get_match_history(raw_matches_details_list,config)

    league_table=create_league_table(data,config)

    league_table=correction(league_table,config)


    print(tabulate(league_table.sort_values(by='score', ascending=False), headers='keys', tablefmt='fancy_grid'))  

if __name__ == "__main__":
    main()