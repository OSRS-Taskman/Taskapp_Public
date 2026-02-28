import requests
import tasklists
from datetime import datetime, timezone
from task_types import CollectionLogVerificationData, TaskData


def temple_player_data(username: str):
    username = username.replace(' ', '+')
    player_data = requests.get(f'https://templeosrs.com/api/collection-log/player_collection_log.php?player={username}&categories=all&itemsonly&includenames=1&onlyitems=1').json()
    used_id = set()
    cleaned_player_data = list()
    if not player_data.get('data'):
        return cleaned_player_data
    for item in player_data['data']['items']:
        if item['id'] not in used_id:
            used_id.add(item['id'])
            cleaned_player_data.append(item)

    return cleaned_player_data

# def test():
#     data = temple_player_data('Gerni Task')
#     for item in data['data']['items']:
#         print(item['name'])

# def get_unix_time(timestamp: str):
#     datetime_format = "%Y-%m-%d %H:%M:%S"
#     datetime_object = datetime.datetime.strptime(timestamp, datetime_format)
#     return time.mktime(datetime_object.timetuple())

# def import_logs(player_name: str, site_tasks: list):
#     player_data = temple_player_data(player_name)
#     completed_tasks = list()
#     for task in site_tasks:
#         task_data = task.get('colLogData', None)
#         if task_data:
#             for item in task_data['include']:
#                 for log_slot in player_data['data']['items']:
#                     if item['id'] == log_slot['id']:
#                         completed_tasks.append(task['_id'])
#                         break
#     return completed_tasks


def import_logs(username: str, site_tasks: list["TaskData"], action: str):
    def find_by_id(items, target_id):
        return [item for item in items if int(item['id']) == target_id]
    def parse_completed_date(value):
        if value is None:
            return None
        if isinstance(value, (int, float)):
            # Handle both seconds and milliseconds epoch values
            epoch_value = value / 1000 if value > 1e11 else value
            return datetime.fromtimestamp(epoch_value, tz=timezone.utc)
        if isinstance(value, str):
            parsed = None
            try:
                parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
            except ValueError:
                parsed = None
            if parsed is None:
                try:
                    parsed = datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
                except ValueError:
                    return None
            if parsed.tzinfo is None:
                return parsed.replace(tzinfo=timezone.utc)
            return parsed.astimezone(timezone.utc)
        return None

    def get_item_completed_date(item):
        possible_keys = [
            'obtainedAt', 'obtained_at', 'obtainedDate', 'obtained_date',
            'timestamp', 'date', 'updatedAt', 'updated_at', 'acquiredAt', 'acquired_at'
        ]
        for key in possible_keys:
            if key in item:
                parsed = parse_completed_date(item.get(key))
                if parsed is not None:
                    return parsed
        return None

    def format_completed_tasks(completed_tasks: dict):
        formatted_tasks = []
        for task_id in sorted(completed_tasks.keys()):
            formatted_tasks.append({
                'id' : task_id,
                'completedDate': completed_tasks[task_id]['completedDate'],
                'completedItemIds': completed_tasks[task_id]['completedItemIds'],
            })
        return formatted_tasks

    cleaned_player_data = temple_player_data(username)
    sync_completed_date = datetime.now(timezone.utc).isoformat()
    missing_tasks = list()
    completed_tasks = {}
    recorded_item_ids_by_task = {}
    for task in site_tasks:
        verification_data = task.verification
        if not isinstance(verification_data, CollectionLogVerificationData):
            continue

        log_count = 0
        matched_dates = []
        matched_item_ids = set()
        for item_id in verification_data.item_ids:
            matching_items = find_by_id(cleaned_player_data, item_id)
            if matching_items:
                log_count += 1
                matched_item_ids.add(int(item_id))
                for matched_item in matching_items:
                    item_completed_date = get_item_completed_date(matched_item)
                    if item_completed_date is not None:
                        matched_dates.append(item_completed_date)

        if log_count >= verification_data.count:
            completed_date = max(matched_dates).isoformat() if matched_dates else sync_completed_date
            completed_tasks[task.id] = {
                'completedDate': completed_date,
                'completedItemIds': sorted(matched_item_ids),
            }
        if matched_item_ids:
            recorded_item_ids_by_task[task.id] = sorted(matched_item_ids)
        else:
            missing_tasks.append(task.name)

    if action == 'check':
        return missing_tasks
    if action == 'import-recorded':
        return {
            'completedTasks': format_completed_tasks(completed_tasks),
            'recordedItemIdsByTask': recorded_item_ids_by_task,
        }
    else:
        return format_completed_tasks(completed_tasks)


def check_logs(username: str, site_tasks: list["TaskData"], action: str):
    def find_by_id(items, target_id):
        return [item for item in items if int(item['id']) == target_id]
    def format_completed_tasks(completed_tasks: set):
        formatted_tasks = []
        for task_id in completed_tasks:
            formatted_tasks.append({
                'id' : task_id
            })
        return formatted_tasks

    cleaned_player_data = temple_player_data(username)
    missing_tasks = list()
    completed_tasks = set()
    for task in site_tasks:
        verification_data = task.verification
        if not isinstance(verification_data, CollectionLogVerificationData):
            continue

        log_count = 0
        for item_id in verification_data.item_ids:
            # print(f"Checking item: {item['name']} with ID: {item['id']}")
            if find_by_id(cleaned_player_data, item_id):
                log_count += 1

        if log_count >= verification_data.count:
            completed_tasks.add(task.id)
        else:
            missing_tasks.append(task.name)

    if action == 'check':
        return missing_tasks
    else:
        sorted_completed_tasks = sorted(completed_tasks)
        # print(sorted_completed_tasks)
        return format_completed_tasks(sorted_completed_tasks)

if __name__ == "__main__":
    print(check_logs('Gerni Task', tasklists.list_for_tier('elite'), 'check'))