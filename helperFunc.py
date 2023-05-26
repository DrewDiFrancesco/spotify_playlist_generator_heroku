import joblib
import pandas as pd
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from spotipy.oauth2 import SpotifyClientCredentials
import spotipy.util as util
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from flask import request

def get_saved_tracks(limit = 50, offset = 0):
    client_id = request.args.get('clieid', '')
    client_secret = request.args.get('clisec', '')
    username = request.args.get('usrnme', '')
    redirect_uri = request.args.get('reduri', '')

    client_credentials_manager = SpotifyClientCredentials(client_id, client_secret)
    scope = 'user-library-read'
    token = util.prompt_for_user_token(username, scope, client_id=client_id, client_secret=client_secret, redirect_uri=redirect_uri)
    sp = spotipy.Spotify(auth=token)
    saved_tracks = [ ]
    
    # get initial list of tracks to determine length
    saved_tracks_obj = sp.current_user_saved_tracks(limit = limit, offset = offset)
    num_saved_tracks = saved_tracks_obj['total']
    
    # loop through to get all saved tracked
    while (offset < num_saved_tracks):
        saved_tracks_obj = sp.current_user_saved_tracks(limit = limit, offset = offset)
        
        # add track information to running list
        for track_obj in saved_tracks_obj['items']:
            saved_tracks.append({
                'name': track_obj['track']['name'],
                'artists': ', '.join([artist['name'] for artist in track_obj['track']['artists']]),
                'track_id': track_obj['track']['id']
            })
            
        offset += limit
        
    return saved_tracks

def get_audio_features(track_ids):
    client_id = request.args.get('clieid', '')
    client_secret = request.args.get('clisec', '')
    username = request.args.get('usrnme', '')
    redirect_uri = request.args.get('reduri', '')

    saved_tracks_audiofeat = [ ]
    client_credentials_manager = SpotifyClientCredentials(client_id, client_secret)
    scope = 'user-library-read'
    token = util.prompt_for_user_token(username, scope, client_id=client_id, client_secret=client_secret, redirect_uri=redirect_uri)
    sp = spotipy.Spotify(auth=token)
    
    # iterate through track_ids in groups of 50
    for ix in range(0,len(track_ids),50):
        audio_feats = sp.audio_features(track_ids[ix:ix+50])
        saved_tracks_audiofeat += audio_feats
        
    return saved_tracks_audiofeat

def save_cluster_tracks_to_playlist(playlist_name, track_ids):
    client_id = request.args.get('clieid', '')
    client_secret = request.args.get('clisec', '')
    username = request.args.get('usrnme', '')
    redirect_uri = request.args.get('reduri', '')

    client_credentials_manager = SpotifyClientCredentials(client_id, client_secret)
    scope = 'user-library-read'
    token = util.prompt_for_user_token(username, scope, client_id=client_id, client_secret=client_secret, redirect_uri=redirect_uri)
    sp = spotipy.Spotify(auth=token)

    # get all of the users playlists
    all_playlists = get_all_user_playlists()
    
    # check if playlist already exists
    if (playlist_name not in [playlist['name'] for playlist in all_playlists]):
        playlist = sp.user_playlist_create(user = user_id, name = playlist_name, public = True)
    else:
        playlist_id = [playlist['id'] for playlist in all_playlists if playlist['name'] == playlist_name][0]
        playlist = sp.user_playlist(user = user_id, playlist_id = playlist_id)

    # remove any existing tracks in playlist
    while (playlist['tracks']['total'] > 0):
        sp.user_playlist_remove_all_occurrences_of_tracks(user_id, playlist['id'], \
                                                          tracks = [track['track']['id'] for track in \
                                                                    playlist['tracks']['items']])
        playlist = sp.user_playlist(user = user_id, playlist_id = playlist_id)

    # add tracks from cluster
    sp.user_playlist_add_tracks(user_id, playlist_id = playlist['id'], tracks = track_ids)
    
def get_all_user_playlists(playlist_limit = 50, playlist_offset = 0):
    client_id = request.args.get('clieid', '')
    client_secret = request.args.get('clisec', '')
    username = request.args.get('usrnme', '')
    redirect_uri = request.args.get('reduri', '')

    client_credentials_manager = SpotifyClientCredentials(client_id, client_secret)
    scope = 'user-library-read'
    token = util.prompt_for_user_token(username, scope, client_id=client_id, client_secret=client_secret, redirect_uri=redirect_uri)
    sp = spotipy.Spotify(auth=token)
    # get initial list of users playlists (first n = playlist_limit), determine total number of playlists
    playlists_obj = sp.user_playlists(user_id, limit = playlist_limit, offset = playlist_offset)
    num_playlists = playlists_obj['total']

    # start accumulating playlist names and ids
    all_playlists = [{'name': playlist['name'], 'id': playlist['id']} for playlist in playlists_obj['items']]
    playlist_offset += playlist_limit

    # continue accumulating through all playlists
    while (playlist_offset < num_playlists):
        playlists_obj = sp.user_playlists(user_id, limit = playlist_limit, offset = playlist_offset)
        all_playlists += [{'name': playlist['name'], 'id': playlist['id']} for playlist in playlists_obj['items']]
        playlist_offset += playlist_limit
        
    return(all_playlists)