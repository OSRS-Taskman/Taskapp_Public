import json
from task_types import TaskData, TaskTag, VerificationData, CollectionLogVerificationData

def to_verification_data(data: dict) -> VerificationData or None: # type: ignore
    if data is None:
        return None

    method: str = data['method']
    if (method != "collection-log"):
        return None

    return CollectionLogVerificationData(method=data['method'],
                                         item_ids=data['itemIds'],
                                         count=data['count'])

def to_task_class(data: dict) -> TaskData:
    return TaskData(id=data['id'],
                    name=data['name'],
                    tip=data.get('tip'),
                    wiki_link=data['wikiLink'],
                    image_link=data['imageLink'],
                    display_item_id=data['displayItemId'],
                    tags=data.get('tags', []),
                    verification=to_verification_data(data.get('verification')))

def read_tasks(filename: str) -> list[TaskData]:
    with open('task-lists/' + filename + '.json') as f:
        json_list = json.load(f)
        return list(map(to_task_class, json_list.get('tasks')))


easy = read_tasks('easy')
medium = read_tasks('medium')
hard = read_tasks('hard')
elite = read_tasks('elite')
master = read_tasks('master')
passive = read_tasks('passive')
extra = read_tasks('extra')
pets = read_tasks('pets')
# boss_pet = read_tasks('bossPets')
# skill_pet = read_tasks('skillPets')
# other_pet = read_tasks('otherPets')

#
def list_for_tier(tier: str, include_lms: bool = True) -> list[TaskData]:
    all_tasks = {
        'easyTasks': easy,
        'mediumTasks': medium,
        'hardTasks': hard,
        'eliteTasks': elite,
        'masterTasks' : master,
        'passiveTasks' : passive,
        'extraTasks' : extra,
        'passive': passive,
        'extra': extra,
        'pets': pets,
        'easy': easy,
        'medium': medium,
        'hard': hard,
        'elite': elite,
        'master': master
    }[tier]
    if not include_lms:
        return [task for task in all_tasks if (TaskTag.LMS not in task.tags)]
    return all_tasks
