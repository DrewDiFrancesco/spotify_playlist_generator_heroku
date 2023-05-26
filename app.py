from flask import Flask, render_template, request, json
import joblib
import pandas as pd
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from spotipy.oauth2 import SpotifyClientCredentials
import spotipy.util as util
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from helperFunc import *

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate')
def generate():
    client_id = request.args.get('clieid', '')
    client_secret = request.args.get('clisec', '')
    username = request.args.get('usrnme', '')
    redirect_uri = request.args.get('reduri', '')
    
    client_credentials_manager = SpotifyClientCredentials(client_id, client_secret)
    scope = 'user-library-read'
    token = util.prompt_for_user_token(username, scope, client_id=client_id, client_secret=client_secret, redirect_uri=redirect_uri)
    sp = spotipy.Spotify(auth=token)
    FEATURE_KEYS = ['danceability', 'energy', 'key', 'loudness', 'mode', 'speechiness', 'acousticness', 'instrumentalness', 'liveness', 'valence', 'tempo','duration_ms','time_signature']

    saved_tracks = get_saved_tracks()
    saved_tracks_df = pd.DataFrame(saved_tracks)

    saved_tracks_audiofeat  = get_audio_features(track_ids = list(saved_tracks_df['track_id']))
    saved_tracks_audiofeat_df = pd.DataFrame(saved_tracks_audiofeat).drop(['analysis_url', 'track_href', \
                                                                       'type', 'uri'], axis = 1)

    saved_tracks_plus_df = saved_tracks_df.merge(saved_tracks_audiofeat_df, how = 'left', \
                                             left_on = 'track_id', right_on = 'id').drop('id', axis = 1)    

    scaler = StandardScaler()
    norm_d = scaler.fit_transform(saved_tracks_plus_df[FEATURE_KEYS])
    norm_d = pd.DataFrame(norm_d, columns = FEATURE_KEYS)
    norm_d['name'] = saved_tracks_plus_df['name']
    norm_d['artists'] = saved_tracks_plus_df['artists']
    loaded_model = joblib.load('model.sav')
    norm_d['cluster'] = loaded_model.predict(norm_d[FEATURE_KEYS]) + 1
    
    songs = norm_d[['name','artists','cluster']]
    songs = songs.sort_values('cluster', ascending=True)
    

    return render_template('generate.html', songs=songs)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')