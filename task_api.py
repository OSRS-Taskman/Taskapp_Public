import bcrypt
import datetime
import jwt

from flask import Response, request
from functools import wraps
from http import HTTPStatus

from task_database import complete_task, generate_task, get_user, manual_complete_tasks, manual_revert_tasks, migrate_current_task
from app_setup import app, db
from tasklists import get_task_tier, list_for_tier
from templesync import sync_user_tasks
from user_dao import UserDatabaseObject


def token_required_v2(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            token = auth_header.split(" ")[1] if " " in auth_header else auth_header

        if not token:
            return { 'error': 'No token found' }, HTTPStatus.UNAUTHORIZED

        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
            user = get_user(data['sub'])
        except:
            return { 'error': 'Token is invalid' }, HTTPStatus.UNAUTHORIZED

        return f(user, *args, **kwargs)
    return decorated


@app.route('/api/v2/login', methods=['POST'])
def apiv2_login():
    body = request.json
    if not body or not body['username'] or not body['password']:
        return { 'error': 'Missing username and/or password' }, HTTPStatus.UNAUTHORIZED

    users = db['users']
    user = users.find_one({ 'username': body['username'] }, { '_id': 0 })
    if not user:
        return { 'error': 'Invalid credentials' }, HTTPStatus.UNAUTHORIZED

    if not bcrypt.checkpw(body['password'].encode('utf-8'), user['hashed_password']):
        return { 'error': 'Invalid credentials' }, HTTPStatus.UNAUTHORIZED

    now = datetime.datetime.now(datetime.timezone.utc)
    token = jwt.encode({
        'sub': user['username'],
        'iat': now,
        'exp': now + datetime.timedelta(hours=24)
    }, app.config['SECRET_KEY'])

    return { 'token': token }


@app.route('/api/v2/task-list', methods=['GET'])
def apiv2_get_task_list():
    tiers = request.args.getlist('tier') or ['easy', 'medium', 'hard', 'elite', 'master']

    return { tier: list_for_tier(tier) for tier in tiers }


@app.route('/api/v2/user/profile', methods=['GET'])
@token_required_v2
def apiv2_get_user_profile(user: UserDatabaseObject):
    return {
        'username': user.username,
        'is_official': user.is_official,
        'is_lms_enabled': user.lms_enabled,
        'has_migrated': user.has_migrated,
        'active_task_id': user.current_task_id(),
        'completed_tasks': [
            *user.easy.completed_tasks,
            *user.medium.completed_tasks,
            *user.hard.completed_tasks,
            *user.elite.completed_tasks,
            *user.master.completed_tasks,
        ]
    }


@app.route('/api/v2/user/tasks/<id>', methods=['PATCH'])
@token_required_v2
def apiv2_update_user_task(user: UserDatabaseObject, id: str) -> None:
    tier = get_task_tier(id)
    body = request.json

    if body['completed'] == True:
        if user.current_task_id() == id:
            complete_task(user.username)
        else:
            manual_complete_tasks(user.username, tier, id)
    elif body['completed'] == False:
        manual_revert_tasks(user.username, tier, id)

    return Response(status=HTTPStatus.NO_CONTENT)


@app.route('/api/v2/user/generate-task', methods=['POST'])
@token_required_v2
def apiv2_generate_task(user: UserDatabaseObject):
    if user.current_task():
        return { 'error': 'User already has an active task' }, HTTPStatus.BAD_REQUEST

    generated_task = generate_task(user.username)
    if generated_task:
        return { 'task_id': generated_task.id }

    return { 'error': 'No available tasks to generate' }, HTTPStatus.BAD_REQUEST


@app.route('/api/v2/user/sync', methods=['POST'])
@token_required_v2
def apiv2_sync(user: UserDatabaseObject):
    body = request.json

    collection_log = set(body['collection_log'])
    diaries = body['diaries']
    skills = body['skills']

    changed_tasks = sync_user_tasks(user.username, collection_log, diaries, skills)

    return {
        'completed': list(changed_tasks[0]),
        'uncompleted': list(changed_tasks[1])
    }


@app.route('/api/v2/user/migrate', methods=['POST'])
@token_required_v2
def apiv2_migrate(user: UserDatabaseObject):
    body = request.json

    new_current_task_id = body['task_id']

    if not migrate_current_task(user.username, new_current_task_id):
        return { 'error': 'User has already migrated' }, HTTPStatus.BAD_REQUEST

    return Response(status=HTTPStatus.NO_CONTENT)