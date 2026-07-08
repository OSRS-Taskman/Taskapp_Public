
import config
import requests

from app_setup import app
from dataclasses import dataclass, asdict

user_info_db = config.MONGO_CLIENT["TaskAppLoginDB"]
task_list_db = config.MONGO_CLIENT["TaskApp"]

DISCORD_API_BASE = 'https://discord.com/api/v10'
BOT_TOKEN = config.DISCORD_BOT_TOKEN
GUILD_ID = config.DISCORD_GUILD_ID

@dataclass
class DiscordAuthInfo:
    discord_user_id: int
    discord_username_default: str

def get_discord_auth_info(username: str) -> DiscordAuthInfo:
    uidb = user_info_db['users']
    users = list(uidb.find({'username': username}))
    if len(users) == 0:
        raise Exception("No user found with username " + username)
    user_data = users[0]
    return convert_database_auth_info(user_data)

def convert_database_auth_info(user_data: dict) -> DiscordAuthInfo:
    if 'discord_auth_info' in user_data.keys():
        if 'discord_user_id' in user_data['discord_auth_info'].keys():
            return DiscordAuthInfo(
                discord_user_id=user_data['discord_auth_info']['discord_user_id'],
                discord_username_default=user_data['discord_auth_info']['discord_username_default'],
            ) 

    return get_new_discord_auth_info(user_data['username'])

def get_new_discord_auth_info(username: str) -> DiscordAuthInfo:
    return DiscordAuthInfo(
        discord_user_id='',
        discord_username_default=username[:12],
    )

def save_discord_auth_info(username: str, auth_info: DiscordAuthInfo):
    uidb = user_info_db['users']
    uidb.update_one({'username': username}, {'$set': {'discord_auth_info': asdict(auth_info)}})

def save_discord_link_status(username: str, discordLinked: bool):
    uidb = task_list_db['taskLists']
    uidb.update_one({'username': username}, {'$set': {'discordLinked': discordLinked}})

def save_discord_name_sync_enabled_status(username: str, discord_name_sync_enabled: bool):
    tldb = task_list_db['taskLists']
    tldb.update_one({'username': username}, {'$set': {'discordNameSyncEnabled': discord_name_sync_enabled}})

def link_discord_id(username: str, id: int):
    auth_info: DiscordAuthInfo = get_discord_auth_info(username)
    auth_info.discord_user_id = id
    save_discord_auth_info(username, auth_info)
    save_discord_link_status(username, True)

def unlink_discord_id(username: str):
    auth_info: DiscordAuthInfo = get_discord_auth_info(username)
    auth_info.discord_user_id = None
    save_discord_auth_info(username, auth_info)
    save_discord_link_status(username, False)

def update_discord_default_name(username: str, discord_default_name: str):
    auth_info: DiscordAuthInfo = get_discord_auth_info(username)
    auth_info.discord_username_default = discord_default_name
    save_discord_auth_info(username, auth_info)
    update_nickname_DISCORD(username, discord_default_name)

def update_discord_name_sync(username: str, discord_name_sync_enabled: bool):
    save_discord_name_sync_enabled_status(username, discord_name_sync_enabled)

def update_nickname_DISCORD(username: str, nickname: str) -> bool:
    discord_user_id = get_discord_auth_info(username).discord_user_id
    
    nickname = nickname[:32]

    url = (
        f"{DISCORD_API_BASE}/guilds/"
        f"{GUILD_ID}/members/{discord_user_id}"
    )
    headers = {
        "Authorization": f"Bot {BOT_TOKEN}",
        "Content-Type": "application/json",
    }

    try:
        response = requests.patch(
            url,
            headers=headers,
            json={"nick": nickname},
            timeout=10,
        )

        if response.status_code == 200:
            print(f"Updated nickname for Discord user {discord_user_id}")
            return True

        if response.status_code == 404:
            print(f"Discord user {discord_user_id} is not in the guild.")
            save_discord_name_sync_enabled_status(username, discord_name_sync_enabled=False)
            return False

        if response.status_code == 403:
            print("Bot lacks permission to update nicknames.")
            return False

        print(f"Discord API returned {response.status_code}: {response.text}")
        return False

    except requests.RequestException as e:
        print(f"Failed to contact Discord: {e}")
        return False

def get_discord_nickname(discord_username_default: str, tier: str, short_name: str, percentage: int) -> str:
    short_tier = "" if len(tier) == 0 else tier[0].capitalize()
    return f"{discord_username_default} {percentage}%{short_tier} {short_name}"
