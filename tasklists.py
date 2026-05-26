import json
from task_types import AchievementDiaryVerificationData, SkillVerificationData, TaskData, TaskTag, VerificationData, CollectionLogVerificationData

def to_verification_data(data: dict) -> VerificationData | None:
    if data is None:
        return None

    method: str = data['method']
    if method == "collection-log":
        return CollectionLogVerificationData(
            method=data['method'],
            item_ids=data['itemIds'],
            count=data['count']
        )
    elif method == "achievement-diary":
        return AchievementDiaryVerificationData(
            method=data['method'],
            region=data['region'],
            difficulty=data['difficulty']
        )
    elif method == "skill":
        return SkillVerificationData(
            method=data['method'],
            experience=data['experience'],
            count=data['count']
        )

    return None

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

def get_task_tier(task_id: str | None) -> str | None:
    tiers = ['easy', 'medium', 'hard', 'elite', 'master', 'passive', 'extra', 'pets']
    for tier in tiers:
        tier_tasks = list_for_tier(tier)
        is_task_in_tier = next((True for task in tier_tasks if task.id == task_id), False)
        if (is_task_in_tier):
            return tier

    return None


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
