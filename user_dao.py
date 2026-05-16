from math import floor
import tasklists
from dataclasses import dataclass
from datetime import datetime, timezone
from bson.objectid import ObjectId
from task_types import UserTaskList, TierProgress, UserCompletedTask, UserCurrentTask, TaskData, PageTask, CollectionLogVerificationData

LMS_TASK_IDS = {
    "df3f714e-eb7e-4b86-8b73-f25d6ebc3020",
    "bf07a401-9a81-4520-9dd8-1c5af2bc5986",
    "69b50b44-33f2-485e-a4e0-195e8f8fa044",
    "60cbbdb2-b233-48a0-8413-8867217ce53a",
    "4ba185cd-ee9b-45ce-b2c9-10462a8ee843",
    "0e7ab87d-cde1-4224-b731-0f4b16308e59",
    "2cff2acd-a0c8-446b-a83b-9ac734b308ad",
    "bc76ea57-5ef9-4ab0-bdcb-37c410c2183a",
    "1cf06859-ff55-476e-9387-80ca82f480ca",
    "5407a890-c3dd-4453-96a2-59f97fc98479",
    "11f65391-8e33-49dc-bd81-47744eb34ed9",
    "2a5428a2-a6a5-44fd-ad89-d8bb4d1cf516",
    "116ba1f6-6416-4f8f-8e32-42f096b3fe04",
    "ccf42f4a-78e9-4968-b696-b75522198ef4",
    "fa5841dd-eb4f-4140-84aa-e10201e3f1cb",
    "e218b954-430c-4baf-b2eb-aa174cddbfc7",
    "655a77fa-21f6-43e8-9cde-5eb2b660f829",
    "347d5712-ebc3-4b74-8aba-ba909c39013e",
    "2eb6623e-a326-4b63-9cae-8fa0823c5d49",
    "50b61b0e-70d0-40a9-bf42-c1b8ac917717",
    "917b912c-2716-4b12-a020-a758ee467e72",
    "5cbcc790-10d1-4c17-8b39-cad7b48dadf8",
    "4a387bb0-dfc3-4374-aa35-9bacfc2fc92d",
}

@dataclass
class UserDatabaseObject:
    id: ObjectId
    username: str
    is_official: bool
    lms_enabled: bool
    easy: UserTaskList
    medium: UserTaskList
    hard: UserTaskList
    elite: UserTaskList
    master: UserTaskList
    passive: UserTaskList
    extra: UserTaskList
    pets: UserTaskList

    def get_task_list(self, tier: str) -> UserTaskList:
        return {
            'easyTasks': self.easy,
            'mediumTasks': self.medium,
            'hardTasks': self.hard,
            'eliteTasks': self.elite,
            'masterTasks': self.master,
            'easy': self.easy,
            'medium': self.medium,
            'hard': self.hard,
            'elite': self.elite,
            'master': self.master,
            'passive': self.passive,
            'extra': self.extra,
            'pets': self.pets,
        }[tier]


    def current_task_for_tier(self, tier: str) -> tuple | None:
        user_task_list = self.get_task_list(tier)
        if user_task_list.current_task is None:
            return None
        task = task_info_for_id(tasklists.list_for_tier(tier), user_task_list.current_task.id)
        # TODO Fix this format
        return task.name, task.image_link, tier, task.id, task.tip, task.wiki_link, task.image_link

    def current_task(self) -> tuple | None:
        if self.easy.current_task is not None:
            return self.current_task_for_tier('easyTasks')
        elif self.medium.current_task is not None:
            return self.current_task_for_tier('mediumTasks')
        elif self.hard.current_task is not None:
            return self.current_task_for_tier('hardTasks')
        elif self.elite.current_task is not None:
            return self.current_task_for_tier('eliteTasks')
        elif self.master.current_task is not None:
            return self.current_task_for_tier('masterTasks')
        else:
            return None

    def current_task_id(self) -> str | None:
        current_task = self.current_task()

        if not current_task:
            return None

        return current_task[3]


    def get_tier_progress(self, tier: str) -> TierProgress:
        # remove instance of duplicate uuid in completed tasks
        def clean_tasklists(tier: str):
            tasklist = self.get_task_list(tier)
            tasklist.completed_tasks = list({task.id: task for task in tasklist.completed_tasks}.values())
            if not self.lms_enabled:
                tasklist.completed_tasks = [
                    task for task in tasklist.completed_tasks
                    if task.id not in LMS_TASK_IDS
                ]
            return tasklist
        completed = len(clean_tasklists(tier).completed_tasks)

        # completed = len(self.get_task_list(tier).completed_tasks)
        total_tasks = tasklists.list_for_tier(tier, self.lms_enabled)
        total = len(total_tasks)
        percent = floor(completed / total * 100)
        return TierProgress(percent, total, completed)

    def page_tasks(self, tier: str) -> list[PageTask]:
        if tier in ['easy', 'medium', 'hard', 'elite', 'master']:
            current_task = self.current_task_for_tier(tier)
            current_task_id = current_task[3] if current_task is not None else None
        else:
            current_task_id = None

        def completed_date_to_iso(value) -> str | None:
            if value is None:
                return None
            if isinstance(value, datetime):
                if value.tzinfo is None:
                    value = value.replace(tzinfo=timezone.utc)
                return value.isoformat()
            if isinstance(value, str):
                parsed = None
                try:
                    parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
                except ValueError:
                    pass
                if parsed is not None:
                    if parsed.tzinfo is None:
                        parsed = parsed.replace(tzinfo=timezone.utc)
                    return parsed.isoformat()
                return value
            return str(value)

        task_list = self.get_task_list(tier)
        recorded_item_ids_by_task = task_list.recorded_item_ids_by_task or {}
        completed_task_lookup = {
            task.id: task for task in task_list.completed_tasks
        }
        completed_task_ids = list(completed_task_lookup.keys())

        def page_task(task: TaskData):
            completed_task = completed_task_lookup.get(task.id)
            completed_date = completed_task.completed_date if completed_task is not None else None
            related_item_ids = recorded_item_ids_by_task.get(task.id, [])
            completed_item_ids = []
            if completed_task is not None and completed_task.completed_item_ids:
                completed_item_ids = completed_task.completed_item_ids
            verification_item_ids = []
            verification_required_count = None
            if isinstance(task.verification, CollectionLogVerificationData):
                verification_item_ids = task.verification.item_ids
                verification_required_count = task.verification.count
            return PageTask(is_current=task.id == current_task_id,
                            is_completed=task.id in completed_task_ids,
                            task_data=task,
                            completed_date=completed_date,
                            completed_date_iso=completed_date_to_iso(completed_date),
                            verification_item_ids=verification_item_ids,
                            verification_required_count=verification_required_count,
                            related_item_ids=related_item_ids,
                            completed_item_ids=completed_item_ids)

        tier_tasks = list(map(page_task, tasklists.list_for_tier(tier, self.lms_enabled)))

        tasks_by_name: dict[str, list[PageTask]] = {}
        ordered_names: list[str] = []
        for task in tier_tasks:
            if task.name not in tasks_by_name:
                tasks_by_name[task.name] = []
                ordered_names.append(task.name)
            tasks_by_name[task.name].append(task)

        def status_sort_key(task: PageTask, has_current_for_name: bool) -> int:
            if has_current_for_name:
                if task.is_current:
                    return 0
                if task.is_completed:
                    return 1
                return 2

            if task.is_completed:
                return 0
            return 1

        ordered_tasks: list[PageTask] = []
        for task_name in ordered_names:
            grouped_tasks = tasks_by_name[task_name]
            has_current_for_name = any(task.is_current for task in grouped_tasks)
            grouped_tasks = sorted(grouped_tasks, key=lambda task: status_sort_key(task, has_current_for_name))
            ordered_tasks.extend(grouped_tasks)

        return ordered_tasks


def task_info_for_id(task_list: list[TaskData], task_id: str) -> tasklists.TaskData:
    filtered = list(filter(lambda x: x.id == task_id, task_list))
    if len(filtered) == 0:
        raise Exception("No id found in list " + task_id)
    return filtered[0]


'''
convert_database_user

Converts a dict object from the taskLists Mongo collection to a UserDatabaseObject

Args:
    dict: user_data - User data from MongoDB

Returns:
    UserDatabaseObject

'''


def convert_database_user(user_data: dict) -> UserDatabaseObject:
    tiers = user_data['tiers']
    lms_enabled = user_data.get('lmsEnabled', False)

    def to_item_ids(value) -> list[int]:
        if not isinstance(value, list):
            return []
        output = []
        for item in value:
            try:
                output.append(int(item))
            except (TypeError, ValueError):
                continue
        return output

    def normalize_completed_task(value: dict) -> UserCompletedTask | None:
        if not isinstance(value, dict):
            return None
        task_id = value.get('id')
        if not task_id:
            return None
        retained_item_ids = value.get('retainedItemIds')
        if retained_item_ids is None:
            retained_item_ids = value.get('completedItemIds', [])
        return UserCompletedTask(
            id=str(task_id),
            assigned_date=value.get('assignedDate'),
            completed_date=value.get('completedDate'),
            completed_item_ids=to_item_ids(retained_item_ids),
        )

    root_completed_tasks: list[UserCompletedTask] = []
    for entry in user_data.get('completedTasks', []):
        normalized = normalize_completed_task(entry)
        if normalized is not None:
            root_completed_tasks.append(normalized)

    root_recorded_item_ids_by_task: dict[str, list[int]] = {}
    raw_root_recorded_map = user_data.get('recordedItemIdsByTask', {})
    if isinstance(raw_root_recorded_map, dict):
        for task_id, item_ids in raw_root_recorded_map.items():
            root_recorded_item_ids_by_task[str(task_id)] = to_item_ids(item_ids)

    def convert_database_tier(tier: str) -> UserTaskList:
        data = tiers.get(tier, {})
        if not isinstance(data, dict):
            data = {}
        completed_tasks: list[UserCompletedTask] = []
        recorded_item_ids_by_task: dict[str, list[int]] = {}

        all_current_tier_ids = set(map(lambda x: x.id, tasklists.list_for_tier(tier, lms_enabled)))

        if root_recorded_item_ids_by_task:
            recorded_item_ids_by_task = {
                task_id: item_ids
                for task_id, item_ids in root_recorded_item_ids_by_task.items()
                if task_id in all_current_tier_ids
            }
        else:
            raw_recorded_map = data.get('recordedItemIdsByTask', {})
            if isinstance(raw_recorded_map, dict):
                for task_id, item_ids in raw_recorded_map.items():
                    task_id_str = str(task_id)
                    if task_id_str in all_current_tier_ids:
                        recorded_item_ids_by_task[task_id_str] = to_item_ids(item_ids)

        if root_completed_tasks:
            completed_tasks = [task for task in root_completed_tasks if task.id in all_current_tier_ids]
        else:
            for entry in data.get('completedTasks', []):
                normalized = normalize_completed_task(entry)
                if normalized is not None:
                    completed_tasks.append(normalized)
            completed_tasks = [task for task in completed_tasks if task.id in all_current_tier_ids]
        # print(completed_tasks)
        current = data.get('currentTask', None)
        if current:
            current = UserCurrentTask(id=current['id'])
        return UserTaskList(current_task=current,
                            completed_tasks=completed_tasks,
                            recorded_item_ids_by_task=recorded_item_ids_by_task)

    return UserDatabaseObject(
        id=user_data['_id'],
        username=user_data['username'],
        is_official=user_data['isOfficial'],
        lms_enabled=user_data['lmsEnabled'],
        easy=convert_database_tier('easy'),
        medium=convert_database_tier('medium'),
        hard=convert_database_tier('hard'),
        elite=convert_database_tier('elite'),
        master=convert_database_tier('master'),
        passive=convert_database_tier('passive'),
        extra=convert_database_tier('extra'),
        pets=convert_database_tier('pets')
    )
