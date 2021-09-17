import json
from topic_extractor import TopicExtractor
import google.oauth2.credentials
import google_auth_oauthlib.flow
import googleapiclient.discovery

import flask
import os

CLIENT_SECRETS_FILE = "../../client_secret.json"

API_SERVICE_NAME = 'youtube'
API_VERSION = 'v3'
SCOPES = ['https://www.googleapis.com/auth/youtube',
          'https://www.googleapis.com/auth/youtube.upload']


app = flask.Flask("YoutubeLearningServer", static_url_path='')

app.secret_key = 'dsafjlasjdflkj'

topic_extractor = TopicExtractor()

@app.route("/")
def home():
    if 'credentials' not in flask.session:
        return flask.redirect('authorize')

    return flask.send_from_directory('static', 'index.html')


VIDEOS_PER_DURATION = 3


@app.route('/youtubelearningplaylist', methods=['POST'])
def create_learning_playlist() -> json:
    query = flask.request.form['query']

    # Convert natural language query to topic
    # I want to learn machine learning -> machine learning
    topics = topic_extractor.get_topic(query)

    # If we cannot find a topic, report error
    if len(topics) == 0:
        return flask.jsonify({'error': 'Could not find a topic in the given query'}), 400

    # Append 'learn' keyword to get more relevant videos
    topics = map(lambda topic: f'Learn {topic}', topics)

    # Get youtube client
    youtube_client = get_youtube_client()

    playlistUrls = []

    for topic in topics:
        # Get VIDEOS_PER_DURATION videos each of short, medium and long durations
        videos_ids = []
        for duration in ['short', 'medium', 'long']:
            duration_videos = get_videos(youtube=youtube_client,
                                        query=topic,
                                        duration=duration,
                                        max_results=VIDEOS_PER_DURATION)

            print(duration_videos)

            videos_ids.extend(
                map(lambda video: video['id']['videoId'], duration_videos['items']))

        print(topic)

        # Create playlist
        playlist = create_playlist(youtube=youtube_client,
                                playlist_title=topic,
                                playlist_description=topic)

        # Add videos to playlist
        for video_id in videos_ids:
            add_video_to_playlist(youtube=youtube_client,
                                playlist_id=playlist['id'],
                                video_id=video_id)

        playlistUrls.append(f'https://www.youtube.com/playlist?list={playlist["id"]}')

    # Return playlist url and response code
    return flask.jsonify({'topics': list(topics), 'playlistUrl': playlistUrls}), 201


def add_video_to_playlist(youtube, playlist_id, video_id):
    body = dict(
        snippet=dict(
            playlistId=playlist_id,
            resourceId=dict(
                kind='youtube#video',
                videoId=video_id
            )
        ),
    )

    playlist_items_insert_response = youtube.playlistItems().insert(
        part='snippet',
        body=body
    ).execute()

    return playlist_items_insert_response


def create_playlist(youtube, playlist_title, playlist_description):
    body = dict(
        snippet=dict(
            title=playlist_title,
            description=playlist_description
        ),
        status=dict(
            privacyStatus='private'
        )
    )

    playlists_insert_response = youtube.playlists().insert(
        part='snippet,status',
        body=body
    ).execute()

    return playlists_insert_response


def get_videos(youtube, query, duration, max_results):
    videos = youtube.search().list(q=query, part='snippet',
                                   type='video', videoDuration=duration, maxResults=max_results).execute()
    return videos


def get_youtube_client():
    # Taken from https://developers.google.com/youtube/v3/guides/auth/server-side-web-apps#example
    if 'credentials' not in flask.session:
        return flask.redirect('authorize')

    # Load credentials from the session.
    credentials = google.oauth2.credentials.Credentials(
        **flask.session['credentials'])

    flask.session['credentials'] = credentials_to_dict(credentials)

    return googleapiclient.discovery.build(
        API_SERVICE_NAME, API_VERSION, credentials=credentials)


@app.route('/authorize')
def authorize():
    # Taken from https://developers.google.com/youtube/v3/guides/auth/server-side-web-apps#example
    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE, scopes=SCOPES)

    flow.redirect_uri = flask.url_for('oauth2callback', _external=True)

    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true')

    flask.session['state'] = state

    return flask.redirect(authorization_url)


@app.route('/oauth2callback')
def oauth2callback():
    # Taken from https://developers.google.com/youtube/v3/guides/auth/server-side-web-apps#example
    state = flask.session['state']

    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE, scopes=SCOPES, state=state)
    flow.redirect_uri = flask.url_for('oauth2callback', _external=True)

    authorization_response = flask.request.url
    flow.fetch_token(authorization_response=authorization_response)

    credentials = flow.credentials
    flask.session['credentials'] = credentials_to_dict(credentials)

    return flask.redirect(flask.url_for('home'))


@app.route('/clear')
def clear_credentials():
    # Taken from https://developers.google.com/youtube/v3/guides/auth/server-side-web-apps#example
    if 'credentials' in flask.session:
        del flask.session['credentials']
    return ('Credentials have been cleared.<br><br>')


def credentials_to_dict(credentials):
    # Taken from https://developers.google.com/youtube/v3/guides/auth/server-side-web-apps#example
    return {'token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'token_uri': credentials.token_uri,
            'client_id': credentials.client_id,
            'client_secret': credentials.client_secret,
            'scopes': credentials.scopes}


if __name__ == "__main__":
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

    app.run('localhost', 8080, debug=True)
