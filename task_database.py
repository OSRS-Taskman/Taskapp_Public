import random
# import gspread
import re
from math import floor
from datetime import datetime, timezone
import tasklists
import config
import user_dao
from dataclasses import asdict
from user_dao import UserDatabaseObject, convert_database_user
from task_types import TaskData, TierProgress, UserTierProgressCache, LeaderboardEntry, TaskData
import discord_service

mydb = config.MONGO_CLIENT["TaskApp"]

# For old taskList data format
'''
get_user

Gets the UserDatabaseObject for a given username

Args:
    str: username

Returns:
    UserDatabaseObject

'''

# def get_user(username) -> UserDatabaseObject:
#     coll = mydb['taskAccounts']
#     users = list(coll.find({'username': username}))
#     if len(users) == 0:
#         raise Exception("No user found with username " + username)
#     old_user_data = users[0]
#     return convert_database_user(migrate_database_user_to_new_format(old_user_data))

# to replace above function after migration
def get_user(username) -> UserDatabaseObject:
    coll = mydb['taskLists']
    users = list(coll.find({'username': username}))
    if len(users) == 0:
        raise Exception("No user found with username " + username)
    user_data = users[0]
    return convert_database_user(user_data)


'''
add_task_account:

The add_task_account function creates the document for the user in the taskLists collection.
The document is structured as follows:
{
    _id : randomly generated id user id,
    username: '',
    isOfficial: true/false,
    lmsEnabled: false/false,
    tiers: {
        easyTier: {
            currentTask: {
                "taskId": Matches the ids in task JSONs,
                "assignedDate": "some date/time format"
            },
            completedTasks: [ # only stores completed tasks
                {
                    "taskId": "Maybe a new id field here that matches new field in task list jsons?",
                    "completionDate": "some date/time format", # both dates are nullable
                    "assignedDate": "some date/time format from above assignedDate field"
                },...
            ],
        }
        medium: {same as easyTier},
        hard: {same as easyTier},
        elite: {same as easyTier},
        master: {same as easyTier},
        passive: {same as easyTier},
        extra: {same as easyTier},
        bossPets: {same as easyTier},
        skillPets: {same as easyTier},
        otherPets: {same as easyTier}
    }
}

Args:
    str: username - username of the user.
    bool: is_official - True/False
    bool: lms_enabled - True/False

Returns:
    None

'''
def add_task_account(username, is_official, lms_enabled):
    coll = mydb['taskLists']
    coll.insert_one({
        "username": str(username),
        "isOfficial": bool(is_official),
        "lmsEnabled": bool(lms_enabled),
        "discordLinked": False,
        "discordNameSyncEnabled": False,
        "completedTasks": [],
        "recordedItemIdsByTask": {},
        'tiers': {
            'easy': {},
            'medium': {},
            'hard': {},
            'elite': {},
            'master' : {},
            'passive': {},
            'extra': {},
            'pets': {},
        }
    })



# '''
# add_task_account:

# The add_task_account function create document for the user in the taskAccounts collection.
# The document is a dictionary with some of the keys being lists of dictionaries.
# The document is structured as follows:
# {
#     _id : randomly generated id,
#     username : username,
#     isOfficial : True/False,
#     lmsEnabled : True/False,
#     easyTasks: [
#         {
#             _id : #,
#             taskname : {
#                 name of the task : image matching the task, # would have done this differently since it horrible
#                 LMS : True/False
#             },
#             status: Incomplete/Complete,
#             taskCurrent : True/False,
#             taskTip : tip for the task,
#             wikiLink : link to the wiki page for the task
#         }
#     ],
#     mediumTasks: [ same as easyTasks ],
#     hardTasks: [ same as easyTasks ],
#     eliteTasks: [ same as easyTasks ]
#     bossPetTasks: [ same as easyTasks except does not include taskTip ],
#     otherPetTasks: [ same as easyTasks except does not include taskTip ],
#     skillingPetTasks: [ same as easyTasks except does not include taskTip ],
#     extraTasks: [ same as easyTasks except does not include taskTip ],
#     passiveTasks: [ same as easyTasks except does not include taskTip ]
# }

# Args:
#     str: username - username of the user.
#     list: completions - list of tasks
#     bool: isofficial - True/False
#     bool: lmsenabled - True/False

# Returns:
#     None

# '''


# def add_task_account(username, isOfficial, lmsEnabled):
#     coll = mydb['taskAccounts']

#     def combine_tasks(tasks: list[TaskData]):
#         new_tasks = []
#         for task in tasks:
#             new_tasks.append(
#                 {
#                     "_id": task.id,
#                     "taskname": {task.name: task.asset_image, 'LMS': task.is_lms},
#                     "status": 'Incomplete',
#                     "taskCurrent": False,
#                     "taskTip": task.tip,
#                     "wikiLink": task.wiki_link,
#                     "taskImage": task.wiki_image
#                 }
#             )
#         return new_tasks

#     taskAccount = {
#         "username": str(username),
#         "isOfficial": bool(isOfficial),
#         "lmsEnabled": bool(lmsEnabled),
#         "easyTasks": combine_tasks(tasklists.easy),
#         "mediumTasks": combine_tasks(tasklists.medium),
#         "hardTasks": combine_tasks(tasklists.hard),
#         "eliteTasks": combine_tasks(tasklists.elite),
#         "masterTasks": combine_tasks(tasklists.master),
#         "bossPetTasks": combine_tasks(tasklists.boss_pet),
#         "skillPetTasks": combine_tasks(tasklists.skill_pet),
#         "otherPetTasks": combine_tasks(tasklists.other_pet),
#         "extraTasks": combine_tasks(tasklists.extra),
#         "passiveTasks": combine_tasks(tasklists.passive)
#     }

#     coll.insert_one(taskAccount)


'''
get_taskCurrent

The get_taskCurrent function, gets the current task for a user.
Used for official accounts.

Args:
    str: username - username of the user.

Returns:
    tuple: name of the task, image for the task, tier of the task, id of the task, tip for the task, wiki link for the task.

'''


def get_taskCurrent(username):
    return get_user(username).current_task()


'''
get_taskCurrent_tier

The get_taskCurrent_tier function, gets the current task for a user.
Used for unofficial accounts.

Args:
    str: username - username of the user.
    str: tier - tier of the task.

Returns:
    tuple: name of the task, image for the task, tier of the task, id of the task, tip for the task, wiki link for the task.

'''


def get_taskCurrent_tier(username, tier):
    return get_user(username).current_task_for_tier(tier)


def __set_current_task(username: str, tier: str, task_id: str, current: bool):
    task_coll = mydb["taskLists"]
    cleaned_tier = tier.replace("Tasks", "")
    if not current:
        task_coll.update_one(
            {"username": username},
            {"$unset": {f"tiers.{cleaned_tier}.currentTask": ""}},
        )
    else:
        task_coll.update_one(
            {"username": username},
            {"$set": {f"tiers.{cleaned_tier}.currentTask": {"id": task_id}}},
        )

    clear_leaderboard_cache(username)
    if (get_discord_name_sync_enabled(username)):
        new_name = ''
        if current:
            task: TaskData = [n for n in tasklists.list_for_tier(cleaned_tier) if n.id == task_id][0]
            new_name = discord_service.generate_discord_nickname_from_current_task(username, cleaned_tier, task)
        else:
            new_name = discord_service.generate_discord_nickname_from_completed_task(username, cleaned_tier)
        discord_service.update_nickname_DISCORD(username, new_name)


def __parse_completed_iso(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)
    except ValueError:
        return None


def __sanitize_item_ids(item_ids) -> list[int]:
    if not isinstance(item_ids, list):
        return []
    output = []
    seen = set()
    for value in item_ids:
        try:
            parsed = int(value)
        except (TypeError, ValueError):
            continue
        if parsed in seen:
            continue
        seen.add(parsed)
        output.append(parsed)
    return output



def __set_task_complete(username: str, tier: str, task_id: str, complete: bool,
                        completed_at_iso: str | None = None,
                        completed_item_ids: list[int] | None = None):
    task_coll = mydb['taskLists']
    if complete:
        completed_date = __parse_completed_iso(completed_at_iso) or datetime.now(timezone.utc)
        safe_completed_item_ids = __sanitize_item_ids(completed_item_ids)
        task_coll.update_one(
            {"username": username},
            {
                "$pull": {
                    "completedTasks": {
                        "id": task_id
                    }
                }
            }
        )
        task_coll.update_one(
            {"username": username},
            {
                "$push": {
                    "completedTasks": {
                        "id": task_id,
                        "completedDate": completed_date,
                        "retainedItemIds": safe_completed_item_ids
                    }
                }
            }
        )
        task_coll.update_one(
            {"username": username},
            {
                "$set": {
                    f"recordedItemIdsByTask.{task_id}": safe_completed_item_ids
                }
            }
        )
        return completed_date, safe_completed_item_ids
    if not complete:
        task_coll.update_one(
            {
                "username" : username
            },
            {
                "$pull" : {
                    "completedTasks" : {"id" : task_id}
                }
            })
    return None, []


def __datetime_to_iso(value) -> str | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.isoformat()
    return str(value)


'''
generate_task_unofficial_tier:

The generate_task_unofficial_tier function, randomly generates a task for a unofficial user.
taskCurrent is set to True for the choosen task.
Unofficial accounts are allowed to re-roll tasks. If they already have a task, the taskCurrent is set to False.


Args:
    str: username - username of the user.
    str: tier - tier of the task.

Returns:
    None

'''
def generate_task_for_tier(username, tier) -> TaskData or None: # type: ignore
    user = get_user(username)
    uncompleted_tasks = []

    if user.current_task_for_tier(tier) is None:
        all_tasks = tasklists.list_for_tier(tier, user.lms_enabled)
        completed_task_ids = list(map(lambda x: x.id, user.get_task_list(tier).completed_tasks))
        uncompleted_tasks = list(filter(lambda x: x.id not in completed_task_ids, all_tasks))
    if len(uncompleted_tasks) != 0:
        if tier == "masterTasks" and uncompleted_tasks[0].id == "6b09384d-c06b-44ac-8a07-b7038cd30710":
            generated_task = uncompleted_tasks[0]
            __set_current_task(username, tier, generated_task.id, True)
            return generated_task
        generated_task = random.choice(uncompleted_tasks)
        __set_current_task(username, tier, generated_task.id, True)
        return generated_task

    else:
        task_info = user.current_task_for_tier(tier)
        task_tier = task_info[2]
        task_number = task_info[3]
        __set_current_task(username, task_tier, task_number, False)
        return None


def get_roll_candidates_for_tier(username: str, tier: str, min_candidates: int = 10) -> list[dict]:
    user = get_user(username)
    all_tasks = tasklists.list_for_tier(tier, user.lms_enabled)
    completed_task_ids = {task.id for task in user.get_task_list(tier).completed_tasks}
    remaining_tasks = [task for task in all_tasks if task.id not in completed_task_ids]

    candidate_tasks = remaining_tasks[:]
    random.shuffle(candidate_tasks)

    if len(candidate_tasks) < min_candidates:
        extras = all_tasks[:]
        random.shuffle(extras)

        existing_ids = {task.id for task in candidate_tasks}
        for task in extras:
            if len(candidate_tasks) >= min_candidates:
                break
            if task.id in existing_ids:
                continue
            candidate_tasks.append(task)
            existing_ids.add(task.id)

        while all_tasks and len(candidate_tasks) < min_candidates:
            candidate_tasks.append(random.choice(all_tasks))

    return [
        {
            'id': task.id,
            'name': task.name,
            'image': task.image_link,
        }
        for task in candidate_tasks
    ]

'''
generate_task:

The generate_task function, randomly generates a task for a official user.
lists of tasks are gathered for each tier.
A task is choosen from the first tier that has tasks.
This allows for new tasks to be added in a lower tier due to game updates.
taskCurrent is set to True for the choosen task.

Args:
    str: username - username of the user.

Returns:
    TaskData: The generated task, or None if user already has a task

'''


def generate_task(username: str) -> TaskData | None:
    user = get_user(username)
    if user.current_task() is not None:
        return

    def get_incomplete_tasks(tier: str) -> list[TaskData]:
        all_tasks = tasklists.list_for_tier(tier, user.lms_enabled)
        completed_task_ids = list(map(lambda x: x.id, user.get_task_list(tier).completed_tasks))
        return list(filter(lambda x: x.id not in completed_task_ids, all_tasks))

    def get_first_task_instance(generated_task: TaskData, incomplete_tasks: list[TaskData]) -> TaskData:
        if generated_task.verification:
            first_task_instance = min([task for task in incomplete_tasks if task.name == generated_task.name],
                                key=lambda task: getattr(task.verification, "count", 0))
            return first_task_instance
        return generated_task

    tasks_easy = get_incomplete_tasks('easy')
    tasks_medium = get_incomplete_tasks('medium')
    tasks_hard = get_incomplete_tasks('hard')
    tasks_elite = get_incomplete_tasks('elite')
    tasks_master = get_incomplete_tasks('master')

    if len(tasks_easy) != 0:
        generated_task = random.choice(tasks_easy)
        first_task_instance = get_first_task_instance(generated_task, tasks_easy)
        __set_current_task(username, 'easyTasks', first_task_instance.id, True)
        return first_task_instance

    elif len(tasks_medium) != 0:
        generated_task = random.choice(tasks_medium)
        first_task_instance = get_first_task_instance(generated_task, tasks_medium)
        __set_current_task(username, 'mediumTasks', first_task_instance.id, True)
        return first_task_instance

    elif len(tasks_hard) != 0:
        generated_task = random.choice(tasks_hard)
        first_task_instance = get_first_task_instance(generated_task, tasks_hard)
        __set_current_task(username, 'hardTasks', first_task_instance.id, True)
        return first_task_instance

    elif len(tasks_elite) != 0:
        generated_task = random.choice(tasks_elite)
        first_task_instance = get_first_task_instance(generated_task, tasks_elite)
        __set_current_task(username, 'eliteTasks', first_task_instance.id, True)
        return first_task_instance

    elif len(tasks_master) != 0:
        generated_task = random.choice(tasks_master)
        first_task_instance = get_first_task_instance(generated_task, tasks_master)
        __set_current_task(username, 'masterTasks', first_task_instance.id, True)
        return first_task_instance

    return None

# If user has just completed a task of the given tier and the progress is 100, then they've just completed the last task
def __get_firework_variables(username, tier):
    user = get_user(username)
    if user.get_tier_progress(tier) == 100:
        query_param_str = {
            'easyTasks': 'easy-first',
            'mediumTasks': 'medium-first',
            'hardTasks': 'hard-first',
            'eliteTasks': 'elite-first'
        }[tier]
        return {query_param_str: True}
    return {}


'''
complete_task_unofficial_tier:

The complete_task_unofficial_tier function, completes the current task for an unofficial user.
taskCurrent is set to False for the current task.
status is set to 'Complete' for the current task.

Functions also checks progress before and after for 100% completion.

Args:
    str: username - username of the user.
    str: tier - tier of the task.
    int: task_id - id of the task.

Returns:
    dict: Contains URL parameters specific for showing the fireworks when a tier goes from 99 -> 100% complete

'''


def complete_task_unofficial_tier(username: str,
                                 task_id: int,
                                 tier: str,
                                 completed_at_iso: str | None = None,
                                 completed_item_ids: list[int] | None = None) -> dict:
    __set_task_complete(username, tier, task_id, True,
                        completed_at_iso=completed_at_iso,
                        completed_item_ids=completed_item_ids)
    __set_current_task(username, tier, task_id, False)
    return __get_firework_variables(username, tier)


'''
complete_task:

The complete_task function, completes the current task for an official user.
taskCurrent is set to False for the current task.
status is set to 'Complete' for the current task.

Functions also checks progress before and after for 100% completion.

Args:
    str: username - username of the user.
    str: tier - tier of the task.
    int: task_id - id of the task.

Returns:
    dict: Contains URL parameters specific for showing the fireworks when a tier goes from 99 -> 100% complete

'''


def complete_task(username: str,
                  completed_at_iso: str | None = None,
                  completed_item_ids: list[int] | None = None) -> dict:
    user = get_user(username)
    task_check = user.current_task()
    if task_check is None:
        return {}

    tier = task_check[2]
    task_id = task_check[3]
    __set_task_complete(username, tier, task_id, True,
                        completed_at_iso=completed_at_iso,
                        completed_item_ids=completed_item_ids)
    __set_current_task(username, tier, task_id, False)

    return __get_firework_variables(username, tier)


'''
get_task_progress:

The get_task_progress function, determines the percentage of progress for each tier. Rounded down.

Args:
    str: username - username of the user.


Returns:
    tuple: easy_progress, medium_progress, hard_progress, elite_progress - percentage of progress for each tier.

'''


def get_task_progress(username: str):
    user = get_user(username)
    easy = user.get_tier_progress('easy')
    medium = user.get_tier_progress('medium')
    hard = user.get_tier_progress('hard')
    elite = user.get_tier_progress('elite')
    master = user.get_tier_progress('master')
    passive = user.get_tier_progress('passive')
    extra = user.get_tier_progress('extra')
    pets = user.get_tier_progress('pets')
    all_pets_total = pets.total
    all_pets_total_complete = pets.total_complete
    all_pets_percent_complete = floor(all_pets_total_complete / all_pets_total * 100)

    progress = {
            'easy' : {'percent_complete' : easy.percent_complete, "total_complete" : easy.total_complete , "total" : easy.total},
            'medium' : {'percent_complete' : medium.percent_complete, "total_complete" : medium.total_complete , "total" : medium.total},
            'hard' : {'percent_complete' : hard.percent_complete, "total_complete" : hard.total_complete , "total" : hard.total},
            'elite' : {'percent_complete' : elite.percent_complete, "total_complete" : elite.total_complete , "total" : elite.total},
            'master' : {'percent_complete' : master.percent_complete, "total_complete" : master.total_complete , "total" : master.total},
            'passive' : {'percent_complete' : passive.percent_complete},
            'extra' : {'percent_complete' : extra.percent_complete},
            'all_pets' : {'percent_complete' : all_pets_percent_complete}
                }
    return progress


'''
manual_complete_tasks:

The manual_complete_tasks function, sets the status of a task to complete.

Args:
    str: username - username of the user.


Returns:
    tuple: name of the task, image of the task, tip of the task, link to the task.

'''


def manual_complete_tasks(username, tier, task_id, completed_at_iso: str | None = None,
                          completed_item_ids: list[int] | None = None):
    completed_date, stored_completed_item_ids = __set_task_complete(
        username,
        tier,
        task_id,
        True,
        completed_at_iso,
        completed_item_ids,
    )
    exclude_list = ['bossPetTasks', 'skillPetTasks', 'otherPetTasks']
    if tier in exclude_list:
        tier = tier.replace('Tasks', '')
    task = user_dao.task_info_for_id(tasklists.list_for_tier(tier), task_id)
    return {
        'name': task.name,
        'image_link': task.image_link,
        'tip': task.tip,
        'wiki_link': task.wiki_link,
        'completed_date': completed_date,
        'completed_date_iso': __datetime_to_iso(completed_date),
        'completed_item_ids': stored_completed_item_ids,
    }


'''
manual_revert_tasks:

The manual_revert_tasks function, sets the status of a task to Incomplete.

Args:
    str: username - username of the user.


Returns:
    tuple: name of the task, image of the task, tip of the task, link to the task.

'''


def manual_revert_tasks(username, tier, task_id):
    __set_task_complete(username, tier, task_id, False)
    exclude_list = ['bossPetTasks', 'skillPetTasks', 'otherPetTasks']
    if tier in exclude_list:
        tier = tier.replace('Tasks', '')
    task = user_dao.task_info_for_id(tasklists.list_for_tier(tier), task_id)
    task.isCompleted = False
    return task.name, task.image_link, task.tip, task.wiki_link


def update_imported_tasks(username: str, all_tasks: list, username2: str,
                          recorded_item_ids_by_tier: dict | None = None,
                          overwrite_temple_timestamps: bool = True):
    coll = mydb['taskLists']
    include = {'easy', 'medium', 'hard', 'elite'}
    tasks_to_check = []
    recorded_item_ids_by_tier = recorded_item_ids_by_tier or {}

    for tier in include:
        current_task = get_taskCurrent_tier(username, tier)
        if current_task is not None:
            tasks_to_check.append(current_task)  # store the whole object

    all_task_ids = {task["id"] for group in all_tasks for task in group}

    for current_task in tasks_to_check:
        task_id = current_task[3]
        tier = current_task[2]  # the tier name
        if task_id in all_task_ids:
            __set_current_task(username, tier, task_id, False)  # ✅ dynamically uses tier

    # Rest of your function remains unchanged
    easy_diaries = {
        "c366a4e5-3463-46e5-a9d1-da706a86d051",
        "1c486d16-4538-424d-986a-efb457de0a8a",
        "c82332c7-d026-4d53-a8cc-50ed31e2b182",
        "82f153a8-37e7-40df-bb02-03a520ec3439",
        "740deabc-99c8-42ff-8d15-e6442796368d",
        "fb3e6897-aa5e-4ea4-a6e0-1e6e6dc4347c",
        "753aa85c-d122-4551-b9ab-a34fbe403526",
        "43847c48-e6e2-4c36-b2d4-d883b9f332a1",
        "309d3dbb-6b68-4697-8562-c72e6c48e8e5",
        "cf8660d4-cf64-4448-a4fd-e9b622293e53",
        "3f4958dd-c0f7-4315-90c6-710ee0db254a",
        "e4efcd63-f488-4a91-9307-c6662e9f612f"
    }
    medium_diaries = {
        "040f49c9-93e9-431d-8a4c-d1b8b8a7edf6",
        "5d2d9461-00bc-431b-b943-0693bb8b0fb6",
        "a455bbf7-a570-494f-9753-643aeb83aca9",
        "958d1774-5ddb-4cb3-abdf-2772de4d024f",
        "f638ebcb-aebf-4c53-bd07-c0e683bc1072",
        "306c11a3-241a-49b8-8083-ea05124d72e9",
        "19708dd7-fb75-4ebc-ad65-60697a0d6401",
        "57b5ba2a-b2b0-4442-b767-1a8b35e3be0d",
        "31e5ccaa-dd74-42d7-8749-2efdaaf01e4e",
        "f59758a3-122e-4d8a-b2ed-5b908fc60a8c",
        "993eb6f8-e30a-4f0a-977d-148b45e0f7f7",
        "59e36673-6808-4371-ba70-fd8d8003e5ef",
    }
    hard_diaries = {
        "0adb8c5f-1f25-469f-a5ca-caeb72926555",
        "6d862500-e957-438a-91d7-73afd64cbc94",
        "ac81b972-e058-4f1c-9a6d-6b584152018e",
        "ecf10542-a7dc-46a5-a104-1c2565775a0a",
        "8eadf6a7-db23-4837-af73-353b46e7f154",
        "efb50bb9-4fca-4c74-b17a-2411f462c798",
        "cf47e5f2-f8b7-4e8f-94c9-578c405ad7ba",
        "cf59d267-cfeb-4e20-91ce-083876b1393e",
        "ab6d1763-824a-42b5-b4f5-41b0e30f618a",
        "376f87f1-88c5-4180-abca-505cdaa542e4",
        "6cad11a7-d40c-4a5e-962d-0387c9eb256b",
        "4a1632cf-a847-43d9-884a-a43e135fdb76",
    }
    elite_diaries = {
        "8c0cb3d6-e137-4a4a-b567-cab75ed2077f",
        "7ec18760-279b-403f-a871-8f0bb99d3387",
        "ab7fc232-2f2d-4497-8ea8-c7073d02539b",
        "3d193ab7-67da-409b-8c21-fa79761e9693",
        "1cb67d59-85dc-4377-a348-30b87d54bbfe",
        "26fe2217-b7f0-496e-a081-5ab11d8fe7b1",
        "308e1019-6b20-45ce-9725-13df969c6f49",
        "b9e0a625-a86f-43ed-9e51-49e2b562ffa8",
        "d2ac7997-c8f8-420a-80c2-ab8e0a686e48",
        "63efc541-8946-45e1-b633-c9a56796c655",
        "0709860d-771d-4173-8160-fdbeccfa54e0",
        "2b10f0dd-ed73-48e9-8ee7-1bb8744f2005",
    }

    diaries = coll.find_one({'username': username}, {
        '_id': 0,
        'completedTasks': 1,
        'recordedItemIdsByTask': 1,
        'tiers.easy.completedTasks': 1,
        'tiers.medium.completedTasks': 1,
        'tiers.hard.completedTasks': 1,
        'tiers.elite.completedTasks': 1,
        'tiers.easy.recordedItemIdsByTask': 1,
        'tiers.medium.recordedItemIdsByTask': 1,
        'tiers.hard.recordedItemIdsByTask': 1,
        'tiers.elite.recordedItemIdsByTask': 1,
    })

    if not diaries:
        return

    def sanitize_recorded_map(value):
        if not isinstance(value, dict):
            return {}
        return {str(task_id): __sanitize_item_ids(item_ids) for task_id, item_ids in value.items()}

    tiers_data = diaries.get('tiers', {}) if isinstance(diaries.get('tiers', {}), dict) else {}

    existing_root_recorded = sanitize_recorded_map(diaries.get('recordedItemIdsByTask', {}))

    existing_recorded_easy = sanitize_recorded_map(tiers_data.get('easy', {}).get('recordedItemIdsByTask', {}))
    existing_recorded_medium = sanitize_recorded_map(tiers_data.get('medium', {}).get('recordedItemIdsByTask', {}))
    existing_recorded_hard = sanitize_recorded_map(tiers_data.get('hard', {}).get('recordedItemIdsByTask', {}))
    existing_recorded_elite = sanitize_recorded_map(tiers_data.get('elite', {}).get('recordedItemIdsByTask', {}))
    if not existing_root_recorded:
        existing_root_recorded = {
            **existing_recorded_easy,
            **existing_recorded_medium,
            **existing_recorded_hard,
            **existing_recorded_elite,
        }

    lms_enabled = get_user(username).lms_enabled
    tier_task_ids = {
        'easy': {task.id for task in tasklists.list_for_tier('easy', lms_enabled)},
        'medium': {task.id for task in tasklists.list_for_tier('medium', lms_enabled)},
        'hard': {task.id for task in tasklists.list_for_tier('hard', lms_enabled)},
        'elite': {task.id for task in tasklists.list_for_tier('elite', lms_enabled)},
    }

    def normalize_completed_entries(value):
        if not isinstance(value, list):
            return []
        output = []
        for entry in value:
            if not isinstance(entry, dict):
                continue
            task_id = entry.get('id')
            if not task_id:
                continue
            retained_item_ids = entry.get('retainedItemIds')
            if retained_item_ids is None:
                retained_item_ids = entry.get('completedItemIds', [])
            output.append({
                'id': str(task_id),
                'completedDate': entry.get('completedDate'),
                'retainedItemIds': __sanitize_item_ids(retained_item_ids),
            })
        return output

    existing_root_completed = normalize_completed_entries(diaries.get('completedTasks', []))
    if not existing_root_completed:
        existing_root_completed = (
            normalize_completed_entries(tiers_data.get('easy', {}).get('completedTasks', [])) +
            normalize_completed_entries(tiers_data.get('medium', {}).get('completedTasks', [])) +
            normalize_completed_entries(tiers_data.get('hard', {}).get('completedTasks', [])) +
            normalize_completed_entries(tiers_data.get('elite', {}).get('completedTasks', []))
        )

    def existing_completed_date_map(tier_name):
        output = {}
        valid_ids = tier_task_ids[tier_name]
        for entry in existing_root_completed:
            task_id = entry.get('id')
            if not task_id or task_id not in valid_ids:
                continue
            completed_date = entry.get('completedDate')
            if completed_date is None:
                continue
            normalized_date = __datetime_to_iso(completed_date)
            if normalized_date:
                output[task_id] = normalized_date
        return output

    existing_completed_dates_easy = existing_completed_date_map('easy')
    existing_completed_dates_medium = existing_completed_date_map('medium')
    existing_completed_dates_hard = existing_completed_date_map('hard')
    existing_completed_dates_elite = existing_completed_date_map('elite')

    if overwrite_temple_timestamps:
        tier_existing_dates = [
            existing_completed_dates_easy,
            existing_completed_dates_medium,
            existing_completed_dates_hard,
            existing_completed_dates_elite,
        ]
        for tier_tasks, tier_date_map in zip(all_tasks, tier_existing_dates):
            for imported_task in tier_tasks:
                task_id = imported_task.get('id')
                if not task_id:
                    continue
                if task_id in tier_date_map:
                    imported_task['completedDate'] = tier_date_map[task_id]

    for tier_tasks in all_tasks:
        for imported_task in tier_tasks:
            imported_task['completedItemIds'] = []

    imported_recorded_easy = sanitize_recorded_map(recorded_item_ids_by_tier.get('easy', {}))
    imported_recorded_medium = sanitize_recorded_map(recorded_item_ids_by_tier.get('medium', {}))
    imported_recorded_hard = sanitize_recorded_map(recorded_item_ids_by_tier.get('hard', {}))
    imported_recorded_elite = sanitize_recorded_map(recorded_item_ids_by_tier.get('elite', {}))

    merged_root_recorded = {
        **existing_root_recorded,
        **imported_recorded_easy,
        **imported_recorded_medium,
        **imported_recorded_hard,
        **imported_recorded_elite,
    }

    imported_root_completed = []
    for tier_tasks in all_tasks:
        for imported_task in tier_tasks:
            task_id = imported_task.get('id')
            if not task_id:
                continue
            imported_root_completed.append({
                'id': str(task_id),
                'completedDate': imported_task.get('completedDate'),
                'retainedItemIds': [],
            })

    import_tier_task_ids = set().union(
        tier_task_ids['easy'],
        tier_task_ids['medium'],
        tier_task_ids['hard'],
        tier_task_ids['elite'],
    )

    preserved_non_import_entries = []
    for entry in existing_root_completed:
        if entry['id'] not in import_tier_task_ids:
            preserved_non_import_entries.append(entry)

    merged_root_completed = preserved_non_import_entries + imported_root_completed

    coll.update_one({'username': username}, {
        '$set': {
            'completedTasks': merged_root_completed,
            'recordedItemIdsByTask': merged_root_recorded,
        }
    })

    coll.update_one({'username': username}, {'$set': {'ign': username2}})

    for diary in existing_root_completed:
        if diary['id'] in easy_diaries:
            __set_task_complete(
                username,
                'easyTasks',
                diary['id'],
                True,
                __datetime_to_iso(diary.get('completedDate')),
                diary.get('retainedItemIds', []),
            )

    for diary in existing_root_completed:
        if diary['id'] in medium_diaries:
            __set_task_complete(
                username,
                'mediumTasks',
                diary['id'],
                True,
                __datetime_to_iso(diary.get('completedDate')),
                diary.get('retainedItemIds', []),
            )

    for diary in existing_root_completed:
        if diary['id'] in hard_diaries:
            __set_task_complete(
                username,
                'hardTasks',
                diary['id'],
                True,
                __datetime_to_iso(diary.get('completedDate')),
                diary.get('retainedItemIds', []),
            )

    for diary in existing_root_completed:
        if diary['id'] in elite_diaries:
            __set_task_complete(
                username,
                'eliteTasks',
                diary['id'],
                True,
                __datetime_to_iso(diary.get('completedDate')),
                diary.get('retainedItemIds', []),
            )


'''
import_spreadsheet:

The import_spreadsheet function, Imports a spreadsheet into the database.
Reads google sheets and imports it into the database.
A tier is only imported if the spreadsheet tasks length matches our task length.
So that tasks are not updated with the wrong ID's.

Args:
    str: username - username of the user.
    str: url - url of the spreadsheet.


# very annoying to maintain since it is a google sheet, order of their rows is important.

Returns:
    str: error - error message if there is an error.
    list: each element is a str: of the tier import status.

'''
# def import_spreadsheet(username, url):
#     def update_current_task_from_sheet(username, tier, task_id):
#         coll = mydb['taskAccounts']
#         task_check = coll.find_one({'username': username, '%s._id' % tier: task_id},
#                                    {'_id': 0, '%s.status' % tier: 1, '%s._id' % tier: 1})
#         task_updated = False
#         if task_check[tier][task_id - 1]['status'] == 'Incomplete':
#             task_updated = True
#             coll.update_one({'username': username, '%s._id' % tier: task_id},
#                             {'$set': {'%s.$.taskCurrent' % tier: True}})
#         return task_updated

#     try:
#         error = None
#         task_import_logs = []
#         task_current_logs = []
#         speadsheet_key = re.search('\/d\/(.*?)(\/|$)', url)
#         if speadsheet_key:
#             service = gspread.service_account(filename="service_account.json")
#             google_sheet = service.open_by_key(speadsheet_key.group(1))
#             info_sheet = google_sheet.worksheet("Info")

#             current_sheet_tier = info_sheet.get('B13:B14')

#             tier, cell = current_sheet_tier[0][0], current_sheet_tier[1][0].replace('C', "")
#             cell = int(cell) - 1
#             sheet_tasks = []
#             sheet_list = [
#                 'Easy',
#                 'Medium',
#                 'Hard',
#                 'Elite',
#                 'Pets',
#                 'Pets',
#                 'Pets',
#                 'Extra',
#                 'Passive'
#             ]

#             cell_range = [
#                 'A2:C137',  # Easy
#                 'A2:C160',  # Medium
#                 'A2:C184',  # Hard
#                 'A2:C165',  # Elite
#                 'A2:C35',  # Pets - Boss
#                 'A37:C44',  # Pets - Skill
#                 'A46:C55',  # Pets - Other
#                 'A2:C119',  # Extra
#                 'A2:C44'  # Passive
#             ]

#             task_list = [
#                 tasklists.easy,
#                 tasklists.medium,
#                 tasklists.hard,
#                 tasklists.elite,
#                 tasklists.boss_pet,
#                 tasklists.skill_pet,
#                 tasklists.other_pet,
#                 tasklists.extra,
#                 tasklists.passive
#             ]

#             taskdb_names = [
#                 'easyTasks',
#                 'mediumTasks',
#                 'hardTasks',
#                 'eliteTasks',
#                 'bossPetTasks',
#                 'skillPetTasks',
#                 'otherPetTasks',
#                 'extraTasks',
#                 'passiveTasks'
#             ]

#             for sheet_name, cells in zip(sheet_list, cell_range):
#                 ws = google_sheet.worksheet(sheet_name)
#                 tasks = ws.get(cells)
#                 sheet_tasks.append(tasks)
#                 if sheet_name == tier:
#                     current_list = []
#                     current_list.append(tasks)

#             coll = mydb['taskAccounts']
#             user_tasks = coll.find_one({'username': username})

#             for sheet_task_list, tasks_lists, doc_list_names in zip(sheet_tasks, task_list, taskdb_names):
#                 if len(sheet_task_list) == len(tasks_lists):
#                     for i, (task_sheet, task_db) in enumerate(zip(sheet_task_list, tasks_lists), 1):
#                         if 'x' in task_sheet:
#                             user_tasks[doc_list_names][i - 1]['status'] = "Complete"
#                     coll.update_one({'username': username}, {'$set': {doc_list_names: user_tasks[doc_list_names]}})
#                     task_import_logs.append('Tasks for %s were updated!' % doc_list_names)
#                 else:
#                     task_import_logs.append(
#                         'Unable to update %s! Spreadsheet data differs from database!' % doc_list_names)

#             if get_taskCurrent(username) is None:
#                 for i, (task) in enumerate(current_list[0], 1):
#                     if i == cell:
#                         sheets_db_dict = {}
#                         for i2, (key, value) in enumerate(zip(sheet_list, taskdb_names)):
#                             sheets_db_dict[key] = value
#                             if i2 == 3:
#                                 update_current = update_current_task_from_sheet(username, sheets_db_dict[tier], i)
#                                 if update_current is True:
#                                     task_current_logs.append('Updated current task!')
#                                     break
#             else:
#                 task_current_logs.append('Current task already found!')
#         else:
#             error = "Spreadsheet URL is not valid!"
#         return task_import_logs, task_current_logs, error
#     except Exception as e:
#         print(str(e))
#         error = "There was a problem prcoessing the request. Contact Gerni Task on Discord."
#         return task_import_logs, task_current_logs, error


# NOT USED only for testing purposes.
def uncomplete_all_tasks(username):
    task_list = ['easyTasks', 'mediumTasks', 'hardTasks', 'eliteTasks']
    coll = mydb['taskAccounts']
    user_info = coll.find({'username': username})
    for info in user_info:
        for tier in task_list:
            task_tier = tier
            for task in info[tier]:
                if task['status'] == "Complete":
                    task_id = task['_id']
                    coll.update_one({'username': username, '%s._id' % tier: task_id},
                                    {'$set': {'%s.$.taskCurrent' % tier: False, '%s.$.status' % tier: 'Incomplete'}})
    task_check = get_taskCurrent(username)
    if task_check is not None:
        tier = task_check[2]
        task_id = task_check[3]
        coll.update_one({'username': username, '%s._id' % tier: task_id},
                        {'$set': {'%s.$.taskCurrent' % tier: False, '%s.$.status' % tier: 'Incomplete'}})

def get_lms_status(username):
    coll = mydb["taskLists"]
    lms_enabled = coll.find_one({"username": username}, {'lmsEnabled' : 1, '_id': 0})
    return lms_enabled["lmsEnabled"]

def get_discord_name_sync_enabled(username):
    tldb = mydb["taskLists"]
    discord_name_sync_enabled = tldb.find_one({"username": username}, {'discordNameSyncEnabled' : 1, '_id': 0})
    return discord_name_sync_enabled["discordNameSyncEnabled"]

def clear_leaderboard_cache(username):
    tldb = mydb["taskLists"]
    tldb.update_one({'username': username}, {'$unset': {'user_tier_progress_cache': ""}})

'''
lms_status_change:

The lms_status_change function, sets lmsEnabled to true or false for a given user.


Args:
    str: username - The username of the user to change the lms status for.
    bool: lmsEnabled - Whether the user is lms enabled or not.

Returns:
        None

'''


def lms_status_change(username, lms_status):
    coll = mydb['taskLists']
    coll.update_one({'username': username}, {'$set': {'lmsEnabled': lms_status}})


'''
official_status_change:

The official_status_change function, sets officialEnabled to true or false for a given user.


Args:
    str: username - The username of the user to change the lms status for.

Returns:
        None

'''


def official_status_change(username):
    coll = mydb['taskLists']
    coll.update_one({'username': username}, {'$set': {'isOfficial': False}})


'''
username_change:

The username_change function, changes the username of a user.


Args:
    str: username - The username of the user.
    str: username_value - The new username of the user.

Returns:
        str: error - The error message if there is one.
        bool: success - Whether the username change was successful or not.

'''


def username_change(username, username_value):
    coll = mydb['taskLists']
    doc_count_new_username = coll.count_documents({'username': username_value})
    if doc_count_new_username != 0:
        error = 'Username already exists'
        return error
    else:
        coll.update_one({'username': username}, {'$set': {'username': username_value}})
        success = True
        return success


'''
official_icon:

The official_icon function, determines the icon to display for official users.

Args:
    int: easy - easy percentage
    int: medium - medium percentage
    int: hard - hard percentage
    int: elite - elite percentage

Returns:
       str: rank_icon - The icon to display.

'''


def official_icon(easy, medium, hard, elite):
    if elite >= 50 and hard == 100 and medium == 100 and easy == 100:
        rank_icon = '/static/assets/rank_icons/Zenyte.png'

    elif elite <= 49 and hard == 100 and medium == 100 and easy == 100:
        rank_icon = '/static/assets/rank_icons/Onyx.png'

    elif hard >= 50 and medium == 100 and easy == 100:
        rank_icon = '/static/assets/rank_icons/Diamond.png'

    elif hard <= 49 and medium == 100 and easy == 100:
        rank_icon = '/static/assets/rank_icons/Ruby.png'

    elif medium >= 50 and easy == 100:
        rank_icon = '/static/assets/rank_icons/Emerald.png'

    elif medium <= 49 and easy == 100:
        rank_icon = '/static/assets/rank_icons/Sapphire.png'

    elif easy >= 50:
        rank_icon = '/static/assets/rank_icons/RedTopaz.png'

    elif easy <= 49:
        rank_icon = '/static/assets/rank_icons/Minion.png'

    return rank_icon


'''
unoffical_log_count:

The unoffical_log_count function, gives a rough collection log count for an unofficial user.

# Since tasks are not 1:1 to collection log slots, many tasks have increases to their log count.

Args:
    str: username - The username of the user.

Returns:
       str: total_count - The total log count for the user.

'''


def unoffical_log_count(username):
    coll = mydb['taskAccounts']
    easy_completed = 0
    medium_completed = 0
    hard_completed = 0
    elite_completed = 0
    pet_completed = 0
    extra_completed = 0
    passive_completed = 0
    dragon_hat_count = 0
    champscroll_count = 0
    unsired_count = 0
    grace_count = 0
    agility_ticket_count = 0
    task_query = coll.find({'username': username},
                           {
                               'easyTasks': 1,
                               'mediumTasks': 1,
                               'hardTasks': 1,
                               'eliteTasks': 1,
                               'extraTasks': 1,
                               'bossPetTasks': 1,
                               'skillPetTasks': 1,
                               'otherPetTasks': 1,
                               'passiveTasks': 1
                           })

    for task in task_query:
        for ele in task['easyTasks']:
            if ele['status'] == 'Complete':
                easy_completed += 1
                for key in ele['taskname']:
                    if key == 'Get 3 new uniques from beginner clues':
                        easy_completed += 2
                    if key == 'Get 5 new uniques from easy clues':
                        easy_completed += 4
                    if key == 'Get 5 new uniques from medium clues':
                        easy_completed += 4
                    if key == 'Get 5 new uniques from hard clues':
                        easy_completed += 4
                    if key == 'Get 2 unique notes from Fossil Island':
                        easy_completed += 1
                    if key == 'Get 2 unique Ancient pages':
                        easy_completed += 1
                    if key == 'Get the Marksman headpiece':
                        easy_completed += 5
                    if key == 'Get a Rune defender':
                        easy_completed += 6
                    if key == 'Get the full Red decorative set':
                        easy_completed += 7
                    if key == 'Get the Zamorak hood & cloak':
                        easy_completed += 1
                    if key == 'Get the Saradomin hood & cloak':
                        easy_completed += 1
                    if key == 'Get a Mole claw + skin':
                        easy_completed += 1
                    if key == 'Get a Fresh crab claw & Fresh crab shell':
                        easy_completed += 1
                    if key == 'Get 5 unique items at Camdozaal':
                        easy_completed += 4
                    if key == 'Get 1 piece of Graceful equipment':
                        if grace_count != 1:
                            easy_completed += 1
                            grace_count += 1

                    if key == 'Complete the Ardougne Easy Diary':
                        easy_completed -= 1
                    if key == 'Complete the Desert Easy Diary':
                        easy_completed -= 1
                    if key == 'Complete the Falador Easy Diary':
                        easy_completed -= 1
                    if key == 'Complete the Fremennik Easy Diary':
                        easy_completed -= 1
                    if key == 'Complete the Kandarin Easy Diary':
                        easy_completed -= 1
                    if key == 'Complete the Karamja Easy Diary':
                        easy_completed -= 1
                    if key == 'Complete the Kourend&Kebos Easy Diary':
                        easy_completed -= 1
                    if key == 'Complete the Lumbridge&Draynor Easy Diary':
                        easy_completed -= 1
                    if key == 'Complete the Morytania Easy Diary':
                        easy_completed -= 1
                    if key == 'Complete the Varrock Easy Diary':
                        easy_completed -= 1
                    if key == 'Complete the Western Provinces Easy Diary':
                        easy_completed -= 1
                    if key == 'Complete the Wilderness Easy Diary':
                        easy_completed -= 1

                    if key == 'Get 1 unique Champion scroll':
                        champscroll_count += 1

        for ele in task['mediumTasks']:
            if ele['status'] == 'Complete':
                medium_completed += 1
                for key in ele['taskname']:
                    if key == 'Get 3 new uniques from beginner clues':
                        medium_completed += 2
                    if key == 'Get 5 new uniques from easy clues':
                        medium_completed += 4
                    if key == 'Get 5 new uniques from medium clues':
                        medium_completed += 4
                    if key == 'Get 5 new uniques from hard clues':
                        medium_completed += 4
                    if key == 'Get 2 unique notes from Fossil Island':
                        medium_completed += 1
                    if key == 'Get 2 unique Ancient pages':
                        medium_completed += 1
                    if key == 'Get the Ogre forester headpiece':
                        medium_completed += 2
                    if key == 'Get 1 Naval set':
                        medium_completed += 2
                    if key == 'Get tier 5 Shayzien armour':
                        medium_completed += 24
                    if key == 'Get the Decorative ranged set':
                        medium_completed += 2
                    if key == 'Get the Decorative magic set':
                        medium_completed += 2

                    if key == 'Complete the Ardougne Medium Diary':
                        medium_completed -= 1
                    if key == 'Complete the Desert Medium Diary':
                        medium_completed -= 1
                    if key == 'Complete the Falador Medium Diary':
                        medium_completed -= 1
                    if key == 'Complete the Fremennik Medium Diary':
                        medium_completed -= 1
                    if key == 'Complete the Kandarin Medium Diary':
                        medium_completed -= 1
                    if key == 'Complete the Karamja Medium Diary':
                        medium_completed -= 1
                    if key == 'Complete the Kourend&Kebos Medium Diary':
                        medium_completed -= 1
                    if key == 'Complete the Lumbridge&Draynor Medium Diary':
                        medium_completed -= 1
                    if key == 'Complete the Morytania Medium Diary':
                        medium_completed -= 1
                    if key == 'Complete the Varrock Medium Diary':
                        medium_completed -= 1
                    if key == 'Complete the Western Provinces Medium Diary':
                        medium_completed -= 1
                    if key == 'Complete the Wilderness Medium Diary':
                        medium_completed -= 1

                    if key == 'Get 1 unique Champion scroll':
                        champscroll_count += 1

        for ele in task['hardTasks']:
            if ele['status'] == 'Complete':
                hard_completed += 1
                for key in ele['taskname']:
                    if key == 'Get 3 new uniques from beginner clues':
                        hard_completed += 2
                    if key == 'Get 5 new uniques from easy clues':
                        hard_completed += 4
                    if key == 'Get 5 new uniques from medium clues':
                        hard_completed += 4
                    if key == 'Get 5 new uniques from hard clues':
                        hard_completed += 4
                    if key == 'Get 2 new uniques from elite clues':
                        hard_completed += 1
                    if key == 'Get 2 unique Ancient pages':
                        hard_completed += 1
                    if key == 'Get 2 uniques from the Hallowed Sepulchre':
                        hard_completed += 1
                    if key == 'Unlock 2 monkey backpack transformations':
                        hard_completed += 1
                    if key == 'Get the Ogre expert headpiece':
                        hard_completed += 3
                    if key == 'Get 1 Naval set':
                        hard_completed += 2
                    if key == 'Get a new Boss pet':
                        hard_completed -= 1
                    if key == 'Get 2 White decorative pieces':
                        hard_completed += 1

                    if key == 'Complete the Ardougne Hard Diary':
                        hard_completed -= 1
                    if key == 'Complete the Desert Hard Diary':
                        hard_completed -= 1
                    if key == 'Complete the Falador Hard Diary':
                        hard_completed -= 1
                    if key == 'Complete the Fremennik Hard Diary':
                        hard_completed -= 1
                    if key == 'Complete the Kandarin Hard Diary':
                        hard_completed -= 1
                    if key == 'Complete the Karamja Hard Diary':
                        hard_completed -= 1
                    if key == 'Complete the Kourend&Kebos Hard Diary':
                        hard_completed -= 1
                    if key == 'Complete the Lumbridge&Draynor Hard Diary':
                        hard_completed -= 1
                    if key == 'Complete the Morytania Hard Diary':
                        hard_completed -= 1
                    if key == 'Complete the Varrock Hard Diary':
                        hard_completed -= 1
                    if key == 'Complete the Western Provinces Hard Diary':
                        hard_completed -= 1
                    if key == 'Complete the Wilderness Hard Diary':
                        hard_completed -= 1
                    if key == 'Get 1 unique Champion scroll':
                        champscroll_count += 1
                    if key == 'Get a unique from Unsired':
                        if unsired_count != 1:
                            hard_completed += 1
                            unsired_count += 1
                    if key == 'Get the Brimhaven graceful set recolour' or "Get a Pirate's hook":
                        if agility_ticket_count != 1:
                            hard_completed += 1
                            agility_ticket_count += 1

        for ele in task['eliteTasks']:
            if ele['status'] == 'Complete':
                elite_completed += 1
                for key in ele['taskname']:
                    if key == 'Upgrade to the (expert) dragon archer headpiece':
                        if dragon_hat_count != 1:
                            elite_completed += 2
                            dragon_hat_count += 1
                        else:
                            elite_completed += 1
                    if key == 'Get 5 new uniques from easy clues':
                        elite_completed += 4
                    if key == 'Get 5 new uniques from medium clues':
                        elite_completed += 4
                    if key == 'Get 5 new uniques from hard clues':
                        elite_completed += 4
                    if key == 'Get 2 unique Ancient pages':
                        elite_completed += 1
                    if key == 'Get 1 Naval set':
                        elite_completed += 2
                    if key == 'Get the Chompy chick':
                        elite_completed -= 1

                    if key == 'Complete the Ardougne Elite Diary':
                        elite_completed -= 1
                    if key == 'Complete the Desert Elite Diary':
                        elite_completed -= 1
                    if key == 'Complete the Falador Elite Diary':
                        elite_completed -= 1
                    if key == 'Complete the Fremennik Elite Diary':
                        elite_completed -= 1
                    if key == 'Complete the Kandarin Elite Diary':
                        elite_completed -= 1
                    if key == 'Complete the Karamja Elite Diary':
                        elite_completed -= 1
                    if key == 'Complete the Kourend&Kebos Elite Diary':
                        elite_completed -= 1
                    if key == 'Complete the Lumbridge&Draynor Elite Diary':
                        elite_completed -= 1
                    if key == 'Complete the Morytania Elite Diary':
                        elite_completed -= 1
                    if key == 'Complete the Varrock Elite Diary':
                        elite_completed -= 1
                    if key == 'Complete the Western Provinces Elite Diary':
                        elite_completed -= 1
                    if key == 'Complete the Wilderness Elite Diary':
                        elite_completed -= 1

                    if key == 'Get 1 unique Champion scroll':
                        champscroll_count += 1
                        if champscroll_count == 10:
                            elite_completed += 1

        for ele in task['extraTasks']:
            if ele['status'] == 'Complete':
                extra_completed += 1
                for key in ele['taskname']:
                    if key == 'Finish all easy clue uniques':
                        extra_completed += 20
                    if key == 'Finish all medium clue uniques':
                        extra_completed += 24
                    if key == 'Finish all hard clue uniques':
                        extra_completed += 28
                    if key == 'Finish all elite clue uniques':
                        extra_completed += 28
                    if key == 'Finish all master clue uniques':
                        extra_completed += 37
                    if key == 'Finish all shared clue rewards ':
                        extra_completed += 48
                    if key == 'Finish all hard clue rare uniques':
                        extra_completed += 23
                    if key == 'Finish all elite clue rare uniques':
                        extra_completed += 14
                    if key == 'Finish all master rare clue uniques':
                        extra_completed += 5
                    if key == 'Complete the Gold decorative set':
                        extra_completed += 3

        for ele in task['bossPetTasks']:
            if ele['status'] == 'Complete':
                pet_completed += 1

        for ele in task['skillPetTasks']:
            if ele['status'] == 'Complete':
                pet_completed += 1

        for ele in task['otherPetTasks']:
            if ele['status'] == 'Complete':
                pet_completed += 1

        for ele in task['passiveTasks']:
            if ele['status'] == 'Complete':

                passive_completed += 1
                for key in ele['taskname']:
                    if key == 'Get all random event outfits':
                        passive_completed += 22

    total_count = easy_completed + medium_completed + hard_completed + floor(
        elite_completed) + pet_completed + extra_completed + passive_completed
    return total_count


'''
unofficial_icon:

The unofficial_icon function, determines the rank_icon to be displayed for unofficial users.

# TODO: add recently added rank_icon

Args:
    str: username - The username of the user.

Returns:
       str: rank_icon - The rank_icon to be displayed.

'''


def unofficial_icon(username):
    log_count = unoffical_log_count(username)
    if log_count >= 1000:
        rank_icon = '/static/assets/rank_icons/Elite.png'
    elif log_count >= 750:
        rank_icon = '/static/assets/rank_icons/Completionist.png'
    elif log_count >= 500:
        rank_icon = '/static/assets/rank_icons/Achiever.png'
    elif log_count >= 250:
        rank_icon = '/static/assets/rank_icons/Explorer.png'
    else:
        rank_icon = '/static/assets/rank_icons/Minion.png'

    return rank_icon

def get_leaderboard() -> list[LeaderboardEntry]:
    def get_leaderboard_entry_from_db(data):
        display_name = discord_service.get_discord_auth_info(user.username).discord_username_default
        
        if 'user_tier_progress_cache' in data.keys():
            cache = UserTierProgressCache(
                data['user_tier_progress_cache']['easy'],
                data['user_tier_progress_cache']['medium'],
                data['user_tier_progress_cache']['hard'],
                data['user_tier_progress_cache']['elite'],
                data['user_tier_progress_cache']['master'],
                data['user_tier_progress_cache']['passive'],
                data['user_tier_progress_cache']['extra'],
                data['user_tier_progress_cache']['pets']
            )
            return LeaderboardEntry(
                display_name,
                TierProgress(**cache.easy),
                TierProgress(**cache.medium),
                TierProgress(**cache.hard),
                TierProgress(**cache.elite),
                TierProgress(**cache.master)
            )
        
        user = convert_database_user(data)
        
        cache = UserTierProgressCache(
            user.get_tier_progress('easy'),
            user.get_tier_progress('medium'),
            user.get_tier_progress('hard'),
            user.get_tier_progress('elite'),
            user.get_tier_progress('master'),
            user.get_tier_progress('passive'),
            user.get_tier_progress('extra'),
            user.get_tier_progress('pets')
        )

        tldb = mydb['taskLists']
        tldb.update_one({'username': user.username}, {'$set': {'user_tier_progress_cache': asdict(cache)}})

        return LeaderboardEntry(
            display_name,
            cache.easy,
            cache.medium,
            cache.hard,
            cache.elite,
            cache.master
        )

    tldb = mydb['taskLists']
    return list(
        sorted(
            map(
                get_leaderboard_entry_from_db,
                tldb.find({'discordLinked': True, 'isOfficial': True})
            ), 
            key=lambda x: x.points(), 
            reverse=True
        )
    )

def test():
    task_coll = mydb["taskLists"]
    # results = task_coll.find_one({"username": "Gerni Task"}, {'tiers': 1, 'username': 1})
    results = task_coll.find({}, {'tiers': 1, 'username': 1})
    valid = True

    for result in results:
        easy = result['tiers']['easy']
        medium = result['tiers']['medium']
        hard = result['tiers']['hard']
        elite = result['tiers']['elite']
        master = result['tiers']['master']
        passive = result['tiers']['passive']
        extra = result['tiers']['extra']
        bossPets = result['tiers']['bossPets']
        skillPets = result['tiers']['skillPets']
        otherPets = result['tiers']['otherPets']
        if not isinstance(easy, dict):
            valid = False
        if not isinstance(medium, dict):
            valid = False
        if not isinstance(hard, dict):
            valid = False
        if not isinstance(elite, dict):
            valid = False
        if not isinstance(master, dict):
            valid = False
        if not isinstance(passive, dict):
            valid = False
        if not isinstance(extra, dict):
            valid = False
        if not isinstance(bossPets, dict):
            valid = False
        if not isinstance(skillPets, dict):
            valid = False
        if not isinstance(otherPets, dict):
            valid = False

        if not valid:
            task_coll.update_one(
                {"username" : result['username']},
                  {"$set": {
                      "tiers.easy": {"completedTasks" : []},
                        "tiers.medium": {"completedTasks" : []},
                        "tiers.hard": {"completedTasks" : []},
                        "tiers.elite": {"completedTasks" : []},
                        "tiers.master": {"completedTasks" : []},
                        "tiers.passive": {"completedTasks" : []},
                        "tiers.extra": {"completedTasks" : []},
                        "tiers.bossPets": {"completedTasks" : []},
                        "tiers.skillPets": {"completedTasks" : []},
                        "tiers.otherPets": {"completedTasks" : []}
                        }
                  })

def fix_gerni():
    task_coll = mydb["taskLists"]
    # task_coll.update_one({"username": "EscFromTaskov"})
    results = task_coll.find({}, {'tiers': 1, '_id' : 0, 'username': 1})
    tiers = ['easy', 'medium', 'hard', 'elite', 'master', 'passive', 'extra', 'bossPets', 'skillPets', 'otherPets']
    for result in results:
        for tier in tiers:
            tasks = result["tiers"][tier]['completedTasks']
            data = set()
            to_remove = set()
            for i, completed_task in enumerate(tasks):
                task_id = completed_task["taskId"]
                if task_id not in data:
                    data.add(task_id)
                else:
                    to_remove.add(task_id)
            if to_remove:
                pass
                # for _id in to_remove:
                    # task_coll.update_one(
                    # {
                    #     "username" : result['username']
                    # },
                    # {
                    #     "$pull" : {
                    #         f"tiers.{tier}.completedTasks" : {"taskId" : _id}
                    #     }
                    # })
                    # task_coll.update_one(
                    #             {"username": result['username']},
                    #             {
                    #                 "$push": {
                    #                     f"tiers.{tier}.completedTasks": {"taskId": _id}
                    #                 }
                    #             }
                    #         )

def copy_tier_tasks(source_username: str, target_username: str, tiers: list[str]):
    collection = mydb["taskLists"]

    source_doc = collection.find_one({"username": source_username})
    if not source_doc:
        return

    updates = {}
    for tier in tiers:
        tier_data = source_doc.get("tiers", {}).get(tier, {})

        # Copy completedTasks if it exists
        if "completedTasks" in tier_data:
            updates[f"tiers.{tier}.completedTasks"] = tier_data["completedTasks"]

        # Copy currentTask if it exists
        if "currentTask" in tier_data:
            updates[f"tiers.{tier}.currentTask"] = tier_data["currentTask"]

    if updates:
        collection.update_one(
            {"username": target_username},
            {"$set": updates}
        )

def migrate_current_task(username: str, task_id: str | None) -> bool:
    user = get_user(username)

    if user.has_migrated:
        return False

    __set_current_task(username, tasklists.get_task_tier(task_id), task_id, task_id is not None)

    coll = mydb['taskLists']
    coll.update_one({ 'username': username }, { '$set': { 'hasMigrated': True } })

    return True

if __name__ == "__main__":
    copy_tier_tasks("AreYaTasking", 'Gerni Task2', tiers=["easy", "medium", "hard", "elite", "master"])
    # fix_gerni()
    # get_task_lists('GerniSleep')
    pass
