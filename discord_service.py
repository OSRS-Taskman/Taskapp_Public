
import config

from app_setup import app
from dataclasses import dataclass, asdict

user_info_db = config.MONGO_CLIENT["TaskAppLoginDB"]
task_list_db = config.MONGO_CLIENT["TaskApp"]

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

def update_discord_name_sync(username: str, discord_name_sync_enabled: bool):
    save_discord_name_sync_enabled_status(username, discord_name_sync_enabled)
