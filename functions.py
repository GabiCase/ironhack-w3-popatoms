import pandas as pd
import billboard
import os
from dotenv import load_dotenv
import spotipy
from datetime import date, timedelta
import seaborn as sns
import pprint
import matplotlib.pyplot as plt
import time
import numpy as np


# Load environment variables
load_dotenv()

# Set up Spotify API credentials
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
from spotipy.oauth2 import SpotifyClientCredentials

#Initialize SpotiPy with user credentials
sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(client_id=CLIENT_ID,
                                                           client_secret=CLIENT_SECRET))


def get_years_rank(start_year, end_year, chart_name = "hot-100-songs"):
    
    """
    Retrieve Billboard chart data for a given range of years.

    Parameters
    ----------
    chart_name : str, optional
        The name of the Billboard chart to retrieve. Defaults to "hot-100-songs".
    start_year : int
        The first year of the range of years to retrieve.
    end_year : int
        The last year of the range of years to retrieve.

    Returns
    -------
    df : pandas.DataFrame
        A DataFrame containing the chart data for the given range of years. The columns are 'rank_year', 'title', 'artist', and 'rank'.
    """
    year_values = []
    artist_values = []
    title_values = []
    rank_values = []

    for year in range (start_year, end_year+1):
        chart = billboard.ChartData(chart_name, year=year)
        for entry in chart:
            year_values.append(year)
            title_values.append(entry.title)
            artist_values.append(entry.artist)
            rank_values.append(entry.rank)

    df = pd.DataFrame({'rank_year': year_values, 'title': title_values, 'artist': artist_values, 'rank': rank_values})
    return df


def get_track_details(name_string,sp=sp):

    result= sp.search(q=f'{name_string}', limit=1)
    track=result['tracks']['items'][0]

    return {
        'id': track['id'],
        'name': track['name'],
        'album': track['album']['name'],
        'popularity': track['popularity'],
        'artists': [artist['name'] for artist in track['artists']],
        'release_date': track['album']['release_date'],
    }


def get_track_genre(id,sp=sp):
    """
    Fetch the audio features for a given track id.

    Parameters
    ----------
    id : str
        The Spotify track ID.
    sp : SpotifyClientCredentials
        Spotify client credentials object.

    Returns
    -------
    dict
        Audio features of the track.
    """

    result= sp.audio_features(id)[0]
    return {
        'danceability': result['danceability'],
        'energy':result['energy'],
        'key': result['key'],
        'loudness': result['loudness'],
        'mode': result['mode'],
        'speechiness':result['speechiness'],
        'acousticness': result['acousticness'],
        'instrumentalness': result['instrumentalness'],
        'liveness': result['liveness'],
        'valence': result['valence'],
        'tempo': result['tempo'],
        'duration': result['duration_ms']
    }


# He dejado esos valores ahí por si nos interesa llamar al confidence
# o investigar si el fade out se ha pasado de moda ?¿?¿
'''
 def get_audio_analysis(id,sp=sp):

#   result = sp.audio_analysis(id)['track']
#  'start_of_fade_out': 171.68254,
#  'tempo': 173.988,
#  'tempo_confidence': 0.125,
#  'key': 8,
#  'key_confidence': 0.413,
#  'mode': 1,
#  'mode_confidence': 0.512,
    return {'duration': result['duration']}
'''

'''
# Deprecated
def create_multiple_tracks_df(songs_list):
    # Lista de diccionarios de cada canción 
    track_info_list = [] 

    for song in songs_list:
        try:
            # Info de la canción
            track_details = get_track_details(song)
            id = track_details['id']  # id de la canción que usamos para analysis
            
            # Llamamos a las funciones de genre y analysis
            track_genre = get_track_genre(id)
            audio_analysis = get_audio_analysis(id)
            
            # Combinamos toda la info en un sólo diccionario y vemos si es colabo
            track_info_dict = {
                'name': track_details['name'],
                'album': track_details['album'],
                'popularity': track_details['popularity'],
                'artists': ', '.join(track_details['artists']),
                'colab': ("Y" if len(track_details['artists']) > 1 else "N"),
                'release_date': track_details['release_date'],
                'danceability': track_genre['danceability'],
                'energy': track_genre['energy'],
                'key': track_genre['key'],
                'loudness': track_genre['loudness'],
                'mode': track_genre['mode'],
                'speechiness': track_genre['speechiness'],
                'acousticness': track_genre['acousticness'],
                'instrumentalness': track_genre['instrumentalness'],
                'liveness': track_genre['liveness'],
                'valence': track_genre['valence'],
                'tempo': track_genre['tempo'],
                'duration ms': audio_analysis['duration'],
            }
            
            # Añadir el diccionario a la lista
            track_info_list.append(track_info_dict)

            
        except Exception as e:
            print(f"Error obteniendo detalles para '{song}': {e}")
    
    # Convertir la lista de diccionarios en un DataFrame
    return pd.DataFrame(track_info_list)
'''

def list_dates_in_range(start_dt, end_dt, step=7):
     
    """
    Generates a list of dates in a given range with a given step.

    Parameters
    ----------
    start_dt : str
        The start date in the format 'YYYY-MM-DD'.
    end_dt : str
        The end date in the format 'YYYY-MM-DD'.
    step : int, optional
        The step between each date in days. Default is 7 (weekly).

    Returns
    -------
    list
        A list of dates in the given range with the given step.
    """
    try:
        start_dt=date.fromisoformat(start_dt)
        end_dt = date.fromisoformat(end_dt)
        date_list = []
        
        for n in range(0, int((end_dt - start_dt).days) + 1, step):
            date_list.append(str(start_dt + timedelta(n)))

        return date_list
    except:
        print("Start and end dates must be in iso format YYYY-MM-DD")


def create_weekly_ranks_df(start_dt, end_dt, chart_name = "hot-100", csv_path="", step=30):

     # if there's a csv file, we can use it as starting point. 
    if csv_path != "":
        df = pd.read_csv(csv_path)
        start_dt = str(date.fromisoformat(df.date.max()) + timedelta(days=7))
        i=len(df)
    
    else: 
        df = pd.DataFrame(columns = ["date", "title", "artist", "peak_pos", "rank", "weeks"])
        i=0


    dates = list_dates_in_range(start_dt, end_dt, step)
    

    for value in dates:
 
        chart = billboard.ChartData("hot-100", date='1961-08-18')
        for entry in chart:
            df.loc[i, "date"] = value
            df.loc[i, "title"] = entry.title
            df.loc[i, "artist"] = entry.artist
            df.loc[i, "peak_pos"] = entry.peakPos
            df.loc[i, "rank"] = entry.rank
            df.loc[i, "weeks"] = entry.weeks
            df.to_csv('weekly_rankings_temp.csv', index=False)
            i+=1

    # concatenate temp_df with df_temp if there's a csv file

    return df


# Filter duplicates

def calculate_rank_peak_data(df):

    """
    Calculate the peak position, maximum number of weeks on the chart, and earliest date reached for each song.

    Parameters
    ----------
    df : pandas.DataFrame
        A DataFrame with columns 'title', 'artist', 'peak_pos', 'rank', 'weeks', and 'date'.

    Returns
    -------
    result : pandas.DataFrame
        A DataFrame with columns 'title', 'artist', 'peak_pos', 'weeks', 'paak_rank', and 'date'.
    """
    # Group by the title of the song
    grouped = df.groupby('title').agg(
        artist = ('artist', 'first'),  # Get the first artist
        weeks=('weeks', 'max'),         # Get the maximum number of weeks
        peak_rank=('rank', 'min')         # Get the maximum rank
    ).reset_index()

    # Find the date when the max peak_pos was recorded
    peak_date = df.loc[df.groupby('title')['peak_pos'].idxmax(), ['title', 'date']]
    
    # Merge the peak date information into the grouped dataframe
    result = pd.merge(grouped, peak_date, on='title')
    
    return result

def create_audio_analysis_df(df):

    # if there's a csv file, we can use it as starting point.
    if "id" not in df.columns:
        df["id"] = np.nan

    # Lista de diccionarios de cada canción 

    for i in range(len(df)):
        if pd.isna(df.loc[i,"id"]):
            try:
                song = df.loc[i,"title"] + " " + df.loc[i,"artist"]

                # Info de la canción
                track_details = get_track_details(song)
                id = track_details['id']  # id de la canción que usamos para analysis
                
                # Llamamos a las funciones de genre y analysis
                track_genre = get_track_genre(id)
                
                # Añadimos toda la info en el df
                df.loc[i, "id"] = track_details['id']
                df.loc[i,'title_spotify'] = track_details['name']
                df.loc[i,"album"] = track_details['album']
                df.loc[i,'sp_popularity'] = track_details['popularity']
                df.loc[i,"colab"] = ("Y" if len(track_details['artists']) > 1 else "N")
                df.loc[i,"release_date"] = track_details['release_date']
                df.loc[i,"danceability"] = track_genre['danceability']
                df.loc[i,'energy'] = track_genre['energy']
                df.loc[i,'loudness'] = track_genre['loudness']
                df.loc[i,'speechiness'] = track_genre['speechiness']
                df.loc[i,'acousticness'] = track_genre['acousticness']
                df.loc[i,'instrumentalness'] = track_genre['instrumentalness']
                df.loc[i,'liveness'] = track_genre['liveness']
                df.loc[i,'valence'] = track_genre['valence']
                df.loc[i,'key'] = track_genre['key']
                df.loc[i,'mode'] = track_genre['mode']
                df.loc[i,'tempo'] = track_genre['tempo']
                df.loc[i,'duration']= track_genre['duration']
            
                df.to_csv("spotify.csv", index=False)
                time.sleep(0.1)

            except Exception as e:
                print(f"Error obteniendo detalles para '{song}': {e}")

    # Convertir la lista de diccionarios en un DataFrame
    return df