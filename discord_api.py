import requests
import config
import discord_service

from requests.exceptions import HTTPError
from app_setup import app
from task_api import login_required
from flask import request, session, redirect, url_for, flash

DISCORD_API_BASE = 'https://discord.com/api'
CLIENT_ID = config.DISCORD_CLIENT_ID
CLIENT_SECRET = config.DISCORD_CLIENT_SECRET
REDIRECT_URI = config.DISCORD_REDIRECT_URI

@app.route("/api/v2/auth/discord/connect", methods=['GET'])
@login_required
def connect_discord():
   discord_oauth_url = (
        "https://discord.com/oauth2/authorize"
        f"?client_id={CLIENT_ID}"
        f"&redirect_uri={REDIRECT_URI}"
        f"&response_type=code"
        f"&scope=identify"
    )
   return redirect(discord_oauth_url)

@app.route("/api/v2/auth/discord/disconnect", methods=['GET'])
@login_required
def disconnect_discord():
    username = session['username']
    discord_service.unlink_discord_id(username)
    discord_service.update_discord_name_sync(username, discord_name_sync_enabled=False)
    flash('Discord authentication disconnected!')
    return redirect(url_for('profile'))

@app.route('/api/v2/auth/discord/redirect', methods=['GET'])
@login_required
def authorize():
    code = request.args.get('code')

    try:
      resp = exchange_code(code)
    except HTTPError as e:
       if (400 <= e.response.status_code < 500):
          flash('Something went wrong, please try again...')
          return redirect(url_for('profile'))

    access_token = resp['access_token']

    resp = retrieve_discord_id(access_token)

    username = session['username']
    discord_service.link_discord_id(username, resp['id'])

    return redirect(url_for('profile'))

@app.route("/api/v2/discord/change-default-name/", methods=['POST'])
@login_required
def change_discord_default_name():
    username = session['username']
    discord_default_name = request.form['discord_username']

    if (2 <= len(discord_default_name) <= 12):
      discord_service.update_discord_default_name(username, discord_default_name=discord_default_name)
      return {'success' : True}
    else:
        return {'success' : False, 'error' : "New name does not meet requirements."}

@app.route("/api/v2/discord/change-name-sync/", methods=['POST'])
@login_required
def change_discord_name_sync():
    username = session['username']
    data = request.form['discord_name_sync_enabled']
    data = False if data == 'false' else True

    discord_service.update_discord_name_sync(username, data)

    return {'success' : True}

def exchange_code(code):
  headers = {
    'Content-Type': 'application/x-www-form-urlencoded',
    'Accept-Encoding': 'application/x-www-form-urlencoded'
  }
  data = {
    'grant_type': 'authorization_code',
    'redirect_uri': REDIRECT_URI,
    'code': code
  }
  r = requests.post(
    '%s/oauth2/token' % DISCORD_API_BASE, 
    data=data, 
    headers=headers, 
    auth=(CLIENT_ID, CLIENT_SECRET)
  )

  r.raise_for_status()

  return r.json()

def retrieve_discord_id(access_token):
  headers = {
     'Authorization': 'Bearer ' + access_token
  }
  r = requests.get(
    f'{DISCORD_API_BASE}/users/@me', 
    headers=headers, 
  )

  r.raise_for_status()

  return r.json()