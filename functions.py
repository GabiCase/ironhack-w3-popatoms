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
from os.path import exists


# Load environment variables
load_dotenv()

# Set up Spotify API credentials
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
from spotipy.oauth2 import SpotifyClientCredentials

#Initialize SpotiPy with user credentials
sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(client_id=CLIENT_ID,
                                                           client_secret=CLIENT_SECRET))


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


# create_weekly_ranks_df generates a pandas DataFrame containing weekly music chart rankings from Billboard.
# It takes in a date range (start_dt and end_dt) and optionally an input CSV file. If an input file is provided, it continues from the last date in the file; otherwise, it starts from the specified start_dt.
# The function then iterates over each week in the date range, fetches the corresponding Billboard chart data, and appends it to the DataFrame, which is saved to a CSV file (output_file) after each week's data is added.
# The function returns the final DataFrame.
def create_weekly_ranks_df(start_dt, end_dt, step=30, chart_name = "hot-100", csv_file = "df_weekly_ranks.csv"):

     # if the csv file exists, we can use it as starting point. 

    if exists(csv_file):
        df = pd.read_csv(csv_file)
        start_dt = str(date.fromisoformat(df.date.max()) + timedelta(days=step))
        i=len(df)
    
    else: 
        df = pd.DataFrame(columns = ["date", "title", "artist", "peak_pos", "rank", "weeks"])
        i=0

    dates = list_dates_in_range(start_dt, end_dt, step)
    
    for value in dates: 
        chart = billboard.ChartData("hot-100", date=value) # get new chart from billboard api
        for entry in chart:
            df.loc[i, "date"] = value
            df.loc[i, "title"] = entry.title
            df.loc[i, "artist"] = entry.artist
            df.loc[i, "peak_pos"] = entry.peakPos
            df.loc[i, "rank"] = entry.rank
            df.loc[i, "weeks"] = entry.weeks
            df.to_csv(csv_file, index=False) #save data continously
            i+=1

    return df


def calculate_ranks_peaks(df):

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


''' 
def get_audio_analysis(id,sp=sp):
# This query would allow us to get more detailed data on the song
# (fade out, tempo confidence, etc.)
   result = sp.audio_analysis(id)['track']
   
   return {'duration': result['duration'],
           'start_of_fade_out': ['start_of_fade_out'],
           'tempo': result['tempo'],
           'tempo_confidence': result['tempo_confidence'],
           'key': result['key'],
           'key_confidence': result['key_confidence'],
           'mode': result['mode'],
           'mode_confidence': result['mode_confidence']
   }

'''

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


# plot function for df
def plot_year_mean(df, params, type="bar", year_column='peak_year', figsize=(10,6), grid=True):

    plt.figure(figsize=figsize)
    
    # plot each parameter

    if type =="bar": 
        for param in params:
            sns.barplot(df, x=df[year_column],y=df[param])
    elif type == "line": 
        for param in params:
            sns.lineplot(x=year_column, y=param, data=df, label=param)
    
    # Configurar la gráfica
    plt.title(f'{", ".join(params)} mean per year', fontsize=16)
    plt.xlabel('Year', fontsize=14)
    plt.ylabel(f'{", ".join(params)}', fontsize=14)
    plt.legend(title="Params")
    plt.grid(grid)
    plt.xticks(rotation=45)
    
    # Mostrar la gráfica
    plt.show()

def parse_dates(date_str):
    """
    Try to parse a date from a string.

    This function tries to parse a date from a string, using the following
    formats: %Y-%m-%d. If no valid date can be parsed, it returns NaT.

    Parameters
    ----------
    date_str : str
        The string to parse as a date

    Returns
    -------
    date : pd.Timestamp or pd.NaT
        The parsed date, or NaT if no valid date can be parsed
    """
    date_formats = ['%Y-%m-%d']
    for fmt in date_formats:
        try:
            return pd.to_datetime(date_str, format=fmt)
        except ValueError:
            continue
    return pd.NaT


def parse_years(date_str):
    if pd.to_datetime(date_str, format='%Y', errors='coerce') is not pd.NaT:
        return pd.to_datetime(date_str, format='%Y').replace(month=1, day=1)
    return pd.NaT
