from app_setup import app, isProd, db, taskapp_email, recaptcha
from flask import render_template, request, redirect, flash, url_for, session, jsonify, make_response # type: ignore
import jwt
import datetime
import json
import bcrypt # type: ignore
from functools import wraps
import task_login
import tasklists
import discord_service
from task_database import (get_taskCurrent, generate_task, complete_task, get_task_progress,
                           manual_complete_tasks, manual_revert_tasks,
                           get_lms_status, lms_status_change, update_imported_tasks,
                           official_status_change, username_change, get_taskCurrent_tier, generate_task_for_tier,
                           complete_task_unofficial_tier, get_user, get_leaderboard,
                           get_roll_candidates_for_tier)
import send_grid_email
from templesync import check_logs, temple_player_data, import_logs
from task_types import CollectionLogVerificationData
from task_api import login_required

import task_api
import discord_api


'''
before_request function:

The before_request function is run before every request to force HTTPS protocol.

Args:
    None
Returns:
    redirect_url str: of https://www.osrstaskapp.com
    code int: of 301


'''
if isProd:
    @app.before_request
    def before_request():
        if not request.is_secure:
            current_url = request.url
            if current_url.startswith('http://'):
                redirect_url = current_url.replace('http://', 'https://', 1)
            elif current_url.startswith('www'):
                redirect_url = current_url.replace('www', 'https://www', 1)
            else:
                redirect_url = 'https://www.osrstaskapp.com'
            code = 301
            return redirect(redirect_url, code=code)

class APIUser:
    def __init__(self, username):
        self.username = username

'''
Class to hold data that is used in many templates
'''
class BasePageInfo:
    def __init__(self):
        username = session['username']
        user = get_user(username)
        self.username = username
        self.user = user
        self.official = user.is_official
        progress = get_task_progress(username)
        self.progress = progress
        email_verify = task_login.email_verify(username)
        self.email_bool = email_verify[0]
        self.email_val = email_verify[1]


def get_related_completed_item_ids_for_task(user, tier: str, task_id: str) -> list[int]:
    tier_tasks = tasklists.list_for_tier(tier, user.lms_enabled)
    tasks_by_id = {task.id: task for task in tier_tasks}
    target_task = tasks_by_id.get(task_id)
    if target_task is None:
        return []

    task_list = user.get_task_list(tier)
    recorded_items_map = task_list.recorded_item_ids_by_task or {}
    related_ids = set()

    for completed_task in task_list.completed_tasks:
        completed_task_data = tasks_by_id.get(completed_task.id)
        if completed_task_data is None or completed_task_data.name != target_task.name:
            continue

        item_ids = recorded_items_map.get(completed_task.id, [])
        if not item_ids and getattr(completed_task, 'completed_item_ids', None):
            item_ids = completed_task.completed_item_ids

        for item_id in item_ids:
            try:
                related_ids.add(int(item_id))
            except (TypeError, ValueError):
                continue

    return sorted(related_ids)


# Converts dict from users task data to a list of user data represented as another list.
# Also filters out LMS fields
# Going forward, convert pages to use the class above instead
# def filter_lms(t_list):
#     items = []
#     for item in t_list:
#         for x in item['taskname'].items():
#             if 'LMS' not in x:
#                 tip = item.get('taskTip')
#                 newItemAsList = [x[0], x[1], item['status'], item['_id'],item['taskCurrent'],]
#                 if tip is not None:
#                     newItemAsList.append(tip)
#                 newItemAsList.append(item['wikiLink'])
#                 items.append(newItemAsList)
#     return items


@app.route('/api/v1/resource/task_list')
def api_task_list():
    return jsonify({'message' : {
                        "easy" : tasklists.list_for_tier('easy'),
                        'medium' : tasklists.list_for_tier('medium'),
                        'hard' : tasklists.list_for_tier('hard'),
                        'elite' : tasklists.list_for_tier('elite'),
                        'master' : tasklists.list_for_tier('master'),
                        'passive' : tasklists.list_for_tier('passive'),
                        'pets' : tasklists.list_for_tier('pets'),
                        'extra' : tasklists.list_for_tier('extra'),
    }}), 200

@app.route('/api/v1/resource/completed_tasks/<username>')
def api_completed_tasks(username):
    user_data = get_user(username)
    return jsonify({'message': {
                        'easy' : user_data.easy.completed_tasks,
                        'medium' : user_data.medium.completed_tasks,
                        'hard' : user_data.hard.completed_tasks,
                        'elite' : user_data.elite.completed_tasks,
                        'master' : user_data.master.completed_tasks,
                        'passive' : user_data.passive.completed_tasks,
                        'pets' : user_data.pets.completed_tasks,
                        'extra' : user_data.extra.completed_tasks
    }})

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'x-access-token' in request.headers:
            token = request.headers['x-access-token']

        if not token:
            return jsonify({'message': 'a valid token is missing'})

        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
            user = APIUser(data['username'])

        except:
            return jsonify({'message': 'Token is invalid'}), 403
        return f(user, *args, **kwargs)
    return decorated

@app.route('/api/v1/resource/login')
def api_login():
    auth = request.authorization
    if not auth or not auth.username or not auth.password:
        return make_response({'message': 'Could not verify'}, 401, {'WWW.Authentication': 'Basic realm: "login required"'})
    coll = db['users']
    user = coll.find_one({'username': auth.username}, {'_id': 0})
    if not user:
        return make_response('Could not verify', 401, {'WWW.Authentication': 'Basic realm: "login required"'})

    if bcrypt.checkpw(auth.password.encode('utf-8'), user['hashed_password']):
        token = jwt.encode({'username': user['username'], 'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)}, app.config['SECRET_KEY'])
        return jsonify({'token': token}), 200

    return make_response({'message': 'Could not verify'}, 401, {'WWW.Authentication': 'Basic realm: "login required"'})


@app.route('/api/v1/resource/current_task')
@token_required
def api_current_task(user):
    current_task = get_taskCurrent(user.username)
    if current_task:
        return jsonify({
            'message': {
                'taskId': current_task[3],
                'taskName': current_task[0],
                'taskImage': current_task[6],
                'taskTip': current_task[4]
            }
        })

    return jsonify({'message': None})

@app.route('/api/v1/resource/task_progress')
@token_required
def api_task_progress(user):
    progress = get_task_progress(user.username)
    return jsonify({'message':
    {
        'easy_progress': progress["easy"]["percent_complete"],
        'easy_complete': progress["easy"]["total_complete"],
        'easy_total': progress["easy"]["total"],
        'medium_progress': progress["medium"]["percent_complete"],
        'medium_complete': progress["medium"]["total_complete"],
        'medium_total': progress["medium"]["total"],
        'hard_progress': progress["hard"]["percent_complete"],
        'hard_complete': progress["hard"]["total_complete"],
        'hard_total': progress["hard"]["total"],
        'elite_progress': progress["elite"]["percent_complete"],
        'elite_complete': progress["elite"]["total_complete"],
        'elite_total': progress["elite"]["total"]
    }})


@app.route('/api/v1/resource/generate_task')
@token_required
def api_generate_task(user):
    current_task = get_taskCurrent(user.username)
    if current_task:
        return jsonify({'message': 'User already has a task'}), 400

    generate_task(user.username)
    current_task = get_taskCurrent(user.username)
    if current_task:
        return jsonify({
            'message': {
                'taskId': current_task[3],
                'taskName': current_task[0],
                'taskImage': current_task[6]
            }
        })

    return jsonify({'message': 'No available tasks to generate!'}), 400

@app.route('/api/v1/resource/complete_task')
@token_required
def api_complete_task(user):
    current_task = get_taskCurrent(user.username)
    if current_task:
        complete_task(user.username)
        return jsonify({'message': 'Success'})
    return jsonify({'message': 'User does not have a task'})

'''
All @app.route functions:

The @app.route functions are used to route the user to the correct page.
@app.route functions render an HTML template and pass in variables to the template.
Many @app.route functions call functions from task_login.py and/or task_database.py
Functions will be explained in more detail in the functions themselves.
'''



# Base route for the website, renders hero.html
@app.route('/')
def index():
    return render_template('hero.html')

# Register route, renders registerV2.html on GET request.
@app.route('/register/', methods=['GET', 'POST'])
def register():
    try:
        if request.method == 'POST':
            if (not isProd) or recaptcha.verify():
                if request.form["password"] != request.form["confirmPassword"]:
                    error = 'Passwords did not match. Please try again.'
                    flash(error)
                    return render_template('registerV2.html')

                if request.form.get('official') == 'on':
                    official = True
                else:
                    official = False

                if request.form.get('lms_status') == None:
                    lms = False
                else:
                    lms = True
                create_user = task_login.add_user(request.form["username"],
                                                request.form["password"],
                                                request.form["email"],
                                                official,
                                                lms)
                if not create_user[0]:
                    error = create_user[1]
                    flash(error)
                    return render_template('registerV2.html')

                send_verification_email_inital(request.form['email'], request.form["username"])
                flash(f'Account {request.form['username']} Created Successfully!')
                flash(f'Verfication email was sent to {request.form['email']}, please check your email. (be sure to check your spam folder)')
                return redirect('/login/')

            error = 'Please fill out the captcha!'
            flash(error)
            return render_template('registerV2.html')

        else:
            return render_template('registerV2.html')

    except Exception:
        error = 'An error occurred while processing your request, please try again.'
        return error



# AJAX route for user registration.
@app.route('/register/user/', methods=['POST'])
def register_user():
    try:
        if (not isProd) or recaptcha.verify():
            if request.form["password"] != request.form["confirmPassword"]:
                error = 'Passwords did not match. Please try again.'
                return {'success' : False, 'error' : error}
            official = bool(request.form["official"])
            lms = bool(request.form["lms_status"])
            create_user = task_login.add_user(request.form["username"],
                                            request.form["password"],
                                            request.form["email"],
                                            official,
                                            lms)
            if not create_user[0]:
                error = create_user[1]
                return {'success' : False, 'error' : error}

            send_verification_email_inital(request.form['email'], request.form["username"])
            flash('Verification email was sent to %s, please check your email (be sure to check your spam folder).' % request.form['email'])
            return {'success' : True, 'error' : None}

        error = 'Please fill out the captcha!'
        return {'success' : False, 'error' : error}
    except Exception:
        error = 'An error occurred while processing your request, please try again.'
        return error


# Login route, renders login.html on GET request.
# On POST request, verifies the users input and logs the user in.
@app.route('/login/', methods= ['GET', 'POST'])
def login():
    try:
        error = None
        coll = db['users']
        if request.method == 'POST':
            if (not isProd) or recaptcha.verify():
                form_data = request.form
                attempted_username = form_data['username']
                attempted_password = form_data['password']
                username_found = coll.find_one({"username": attempted_username})
                if username_found:
                    passwordcheck = username_found['hashed_password']
                    if bcrypt.checkpw(attempted_password.encode('utf-8'), passwordcheck):
                        session.permanent = True
                        session['logged_in'] = True
                        session['username'] = request.form['username']
                        return redirect(url_for('dashboard'))
                    else:
                        error = "Invalid Username or Password. Please Try again"
                        flash(error)
                        return render_template('loginV2.html')
                else:
                    error = "Invalid Username or Password. Please Try again"
                    flash(error)
                    return render_template('loginV2.html')
            else:
                error = 'Please fill out the Captcha!'
                flash(error)
                return render_template('loginV2.html')
        else:
            return render_template('loginV2.html')

    except Exception:
        error = "An error occurred while processing your request, please try again."
        flash(error)
        return render_template('loginV2.html')


# logout route, logs the user out and redirects to the login page.
@app.route('/logout/')
@login_required
def logout():
    session.clear()
    flash("You have been logged out!")
    return redirect(url_for('login'))

# dashboard route, renders index.html or dashboard_unofficial.html depending on the user's status (official or unofficial) on GET request.
# I don't remember why POST is specified here, but it works.
@app.route('/dashboard/', methods=['GET', 'POST'])
@login_required
def dashboard():
    user_info = BasePageInfo()
    # if not user_info.email_bool:
    #     return render_template('email-verify.html')
    # The "first" variables determine whether a user has just completed a task
    easy_first = bool(request.args.get('easy-first'))
    medium_first = bool(request.args.get('medium-first'))
    hard_first = bool(request.args.get('medium-first'))
    elite_first = bool(request.args.get('medium-first'))
    username = session['username']
    progress = get_task_progress(username)
    context = {
        'username': username,
        'email_verify': user_info.email_bool,
        'email_val': user_info.email_val,
        'official': user_info.official,
        'taskapp_email': taskapp_email,
        'easy': progress['easy']['percent_complete'],
        'medium': progress['medium']['percent_complete'],
        'hard': progress['hard']['percent_complete'],
        'elite': progress['elite']['percent_complete'],
        'master' : progress['master']['percent_complete'],
        'passive' : progress['passive']['percent_complete'],
        'extra' : progress['extra']['percent_complete'],
        'allPets' : progress['all_pets']['percent_complete'],
    }
    if user_info.official:
        current_task = get_taskCurrent(username)
        if current_task:
            task, image, task_tier, task_id, tip, link, _ = current_task
            verification_item_ids = []
            completed_item_ids = []

            tier_tasks = tasklists.list_for_tier(task_tier, user_info.user.lms_enabled)
            current_task_data = next((entry for entry in tier_tasks if entry.id == task_id), None)
            if current_task_data and isinstance(current_task_data.verification, CollectionLogVerificationData):
                verification_item_ids = current_task_data.verification.item_ids

            recorded_items_map = user_info.user.get_task_list(task_tier).recorded_item_ids_by_task or {}
            completed_item_ids = recorded_items_map.get(task_id, [])
            related_completed_item_ids = get_related_completed_item_ids_for_task(user_info.user, task_tier, task_id)

            context.update({
                'task': task,
                'image': image,
                'tip': tip,
                'link': link,
                'verification_item_ids': verification_item_ids,
                'completed_item_ids': completed_item_ids,
                'related_completed_item_ids': related_completed_item_ids,
            })
            return render_template('dashboard_official.html', **context)

        else:
            context.update({
                'task': '',
                'image': None,
                'tip': None,
                'link': None,
                'verification_item_ids': [],
                'completed_item_ids': [],
                'related_completed_item_ids': [],
                'easy_first': easy_first,
                'medium_first': medium_first,
                'hard_first': hard_first,
                'elite_first': elite_first

            })
            return render_template('dashboard_official.html', **context)
    else:
        context['easy_progress'], context['medium_progress'], context['hard_progress'], context['elite_progress'], context['master_progress']= progress["easy"]['percent_complete'], progress['medium']['percent_complete'], progress['hard']['percent_complete'], progress['elite']['percent_complete'],progress['master']['percent_complete']
        for tier, task_type in [('easy', 'easyTasks'), ('medium', 'mediumTasks'), ('hard', 'hardTasks'), ('elite', 'eliteTasks'), ('master', 'masterTasks')]:
            current_task = get_taskCurrent_tier(username, task_type)
            if current_task:
                context[f'task_{tier}'], context[f'image_{tier}'], _, task_id, context[f'tip_{tier}'], context[f'link_{tier}'], _ = current_task

                verification_item_ids = []
                completed_item_ids = []
                tier_tasks = tasklists.list_for_tier(task_type, user_info.user.lms_enabled)
                current_task_data = next((entry for entry in tier_tasks if entry.id == task_id), None)
                if current_task_data and isinstance(current_task_data.verification, CollectionLogVerificationData):
                    verification_item_ids = current_task_data.verification.item_ids

                recorded_items_map = user_info.user.get_task_list(task_type).recorded_item_ids_by_task or {}
                completed_item_ids = recorded_items_map.get(task_id, [])
                related_completed_item_ids = get_related_completed_item_ids_for_task(user_info.user, task_type, task_id)

                context[f'verification_item_ids_{tier}'] = verification_item_ids
                context[f'completed_item_ids_{tier}'] = completed_item_ids
                context[f'related_completed_item_ids_{tier}'] = related_completed_item_ids
            else:
                context.update({
                    f'task_{tier}': '',
                    f'image_{tier}': None,
                    f'tip_{tier}': None,
                    f'link_{tier}': None,
                    f'verification_item_ids_{tier}': [],
                    f'completed_item_ids_{tier}': [],
                    f'related_completed_item_ids_{tier}': [],
                })
        return render_template('dashboard_unofficial_v2.html', **context)


@app.route('/collectionlog_check/', methods=['POST'])
@login_required
def collection_log_check():
    form_data = request.form
    rs_username = form_data['username']
    lms_enabled = get_lms_status(session['username'])
    if not temple_player_data(rs_username):
        return render_template('collection_log_check.html', rs_username = rs_username,
                               error = "Player has not synced their collecton log on TempleOSRS yet")
    easy_check = check_logs(rs_username, tasklists.list_for_tier('easy', lms_enabled), 'check')
    medium_check = check_logs(rs_username, tasklists.list_for_tier('medium', lms_enabled), 'check')
    hard_check = check_logs(rs_username, tasklists.list_for_tier('hard', lms_enabled), 'check')
    elite_check = check_logs(rs_username, tasklists.list_for_tier('elite', lms_enabled), 'check')

    return render_template('collection_log_check.html',
                           rs_username = rs_username,
                           easy_check = easy_check,
                           medium_check = medium_check,
                           hard_check = hard_check,
                           elite_check= elite_check)

@app.route('/collectionlog_import/', methods = ['POST'])
@login_required
def collection_log_import():
    form_data = request.form
    rs_username = form_data['username']
    overwrite_temple_timestamps_raw = form_data.get('overwriteTempleTimestamps', 'true')
    overwrite_temple_timestamps = str(overwrite_temple_timestamps_raw).lower() == 'true'
    easy_import_result = import_logs(rs_username, tasklists.list_for_tier('easy'), 'import-recorded')
    medium_import_result = import_logs(rs_username, tasklists.list_for_tier('medium'), 'import-recorded')
    hard_import_result = import_logs(rs_username, tasklists.list_for_tier('hard'), 'import-recorded')
    elite_import_result = import_logs(rs_username, tasklists.list_for_tier('elite'), 'import-recorded')
    master_import_result = import_logs(rs_username, tasklists.list_for_tier('master'), 'import-recorded')
    pets_import_result = import_logs(rs_username, tasklists.list_for_tier('pets'), 'import-recorded')
    easy_import = easy_import_result.get('completedTasks', [])
    medium_import = medium_import_result.get('completedTasks', [])
    hard_import = hard_import_result.get('completedTasks', [])
    elite_import = elite_import_result.get('completedTasks', [])
    master_import = master_import_result.get('completedTasks', [])
    pets_import = pets_import_result.get('completedTasks', [])
    all_tasks = [easy_import, medium_import, hard_import, elite_import, master_import, pets_import]
    recorded_item_ids_by_tier = {
        'easy': easy_import_result.get('recordedItemIdsByTask', {}),
        'medium': medium_import_result.get('recordedItemIdsByTask', {}),
        'hard': hard_import_result.get('recordedItemIdsByTask', {}),
        'elite': elite_import_result.get('recordedItemIdsByTask', {}),
        'master': master_import_result.get('recordedItemIdsByTask', {}),
        'pets': pets_import_result.get('recordedItemIdsByTask', {}),
    }
    update = update_imported_tasks(
        session['username'],
        all_tasks,
        form_data['username'],
        recorded_item_ids_by_tier,
        overwrite_temple_timestamps,
    )

    return render_template('collection_log_import.html',
                            rs_username = rs_username,
                            easy = len(easy_import),
                            medium = len(medium_import),
                            hard = len(hard_import),
                            elite = len(elite_import),
                            master = len(master_import),
                            pets = len(pets_import))

# AJAX route for generating a task.
@app.route('/generate/', methods=['POST'])
@login_required
def generate_button():
    username = session['username']
    user = get_user(username)
    task = generate_task(username)
    current_task = get_taskCurrent(username)
    verification_item_ids = []
    related_completed_item_ids = []

    if current_task is not None:
        task_tier = current_task[2]
        roll_candidates = get_roll_candidates_for_tier(username, task_tier, 10)
    else:
        roll_candidates = []

    if task and isinstance(task.verification, CollectionLogVerificationData):
        verification_item_ids = task.verification.item_ids
    if task and current_task is not None:
        related_completed_item_ids = get_related_completed_item_ids_for_task(user, current_task[2], task.id)

    data = {
        "name" : task.name,
        "image" : task.image_link,
        "tip" : task.tip,
        "link" : task.wiki_link,
        "rollCandidates": roll_candidates,
        "verificationItemIds": verification_item_ids,
        "completedItemIds": [],
        "relatedCompletedItemIds": related_completed_item_ids,
    }
    return data

@app.route('/complete/', methods =['POST'])
@login_required
def complete_button():
    username = session['username']
    current_task = get_taskCurrent(username)
    if current_task is not None:
        completed_item_ids_raw = request.form.get('completedItemIds')
        completed_item_ids = []
        if completed_item_ids_raw:
            try:
                parsed_ids = json.loads(completed_item_ids_raw)
                if isinstance(parsed_ids, list):
                    completed_item_ids = parsed_ids
            except (TypeError, ValueError, json.JSONDecodeError):
                completed_item_ids = []

        completed_at_iso = request.form.get('completedAtISO')

        query_params = complete_task(
            username,
            completed_at_iso=completed_at_iso,
            completed_item_ids=completed_item_ids,
        )
        return redirect(url_for('dashboard', **query_params))
    return redirect(url_for('dashboard'))

# AJAX route for generating a task for unofficial users.
@app.route('/generate_unofficial/', methods=['POST'])
@login_required
def generate_unofficial():
    username = session['username']
    user = get_user(username)
    tier = request.form["tier"]
    roll_candidates = get_roll_candidates_for_tier(username, tier, 10)
    task = generate_task_for_tier(username, tier)
    verification_item_ids = []
    related_completed_item_ids = []
    if task:
        if isinstance(task.verification, CollectionLogVerificationData):
            verification_item_ids = task.verification.item_ids
        related_completed_item_ids = get_related_completed_item_ids_for_task(user, tier, task.id)
        data = {
            "name" : task.name,
            "image" : task.image_link,
            "tip" : task.tip,
            "link" : task.wiki_link,
            "rollCandidates": roll_candidates,
            "verificationItemIds": verification_item_ids,
            "completedItemIds": [],
            "relatedCompletedItemIds": related_completed_item_ids,
        }
        return data
    tier = tier.replace('Tasks', '')
    data = {"name" : f"You have no {tier} task!",
            "image" : "Cake_of_guidance_detail.png",
            "tip" : "Generate a Task!",
            "link" : "#",
            "rollCandidates": roll_candidates,
            "verificationItemIds": [],
            "completedItemIds": [],
                "relatedCompletedItemIds": [],
            }
    return data


# AJAX route for completing a task for unofficial users.
@app.route('/complete_unofficial/', methods =['POST'])
@login_required
def complete_unofficial():
    username = session['username']
    tier = request.form['tier']
    current_task = get_taskCurrent_tier(username, tier)
    completed_item_ids_raw = request.form.get('completedItemIds')
    completed_item_ids = []
    if completed_item_ids_raw:
        try:
            parsed_ids = json.loads(completed_item_ids_raw)
            if isinstance(parsed_ids, list):
                completed_item_ids = parsed_ids
        except (TypeError, ValueError, json.JSONDecodeError):
            completed_item_ids = []

    completed_at_iso = request.form.get('completedAtISO')
    progress = get_task_progress(username)
    data = {
            'easy': progress['easy']['percent_complete'],
            'medium': progress['medium']['percent_complete'],
            'hard': progress['hard']['percent_complete'],
            'elite': progress['elite']['percent_complete'],
            'master' : progress['master']['percent_complete'],
            'passive' : progress['passive']['percent_complete'],
            'extra' : progress['extra']['percent_complete'],
            'allPets' : progress['all_pets']['percent_complete'],
            }
    if current_task is not None:
        task_id = current_task[3]
        query_params = complete_task_unofficial_tier(
            username,
            task_id,
            tier,
            completed_at_iso=completed_at_iso,
            completed_item_ids=completed_item_ids,
        )
        progress = get_task_progress(username)
        data = {
            'easy': progress['easy']['percent_complete'],
            'medium': progress['medium']['percent_complete'],
            'hard': progress['hard']['percent_complete'],
            'elite': progress['elite']['percent_complete'],
            'master' : progress['master']['percent_complete'],
            'passive' : progress['passive']['percent_complete'],
            'extra' : progress['extra']['percent_complete'],
            'allPets' : progress['all_pets']['percent_complete'],
            }

        return data
    return data

# # route for task-list page, this page lists all tasks easy, medium, hard, elite, extra, passive and pets.
# @app.route('/task-list/', methods=['GET'])
# @login_required
# def task_list():
#     user_info = BasePageInfo()
#     # if not user_info.email_bool:
#     #     return render_template('email-verify.html')
#     task = get_task_lists(user_info.username)

#     # TODO Refactor template to use the user page_tasks class
#     items_easy = filter_lms(task[0])
#     items_medium = filter_lms(task[1])
#     items_hard = filter_lms(task[2])
#     items_elite = filter_lms(task[3])
#     items_master = filter_lms(task[4])
#     items_bosspet = filter_lms(task[5])
#     items_skillpet = filter_lms(task[6])
#     items_otherpet = filter_lms(task[7])
#     items_extra = filter_lms(task[8])
#     items_passive = filter_lms(task[9])

#     return render_template(
#         'task_list.html',
#         username=user_info.username,
#         email_verify=user_info.email_bool,
#         email_val=user_info.email_val,
#         items_easy=items_easy,
#         items_medium=items_medium,
#         items_hard=items_hard,
#         items_elite=items_elite,
#         items_master=items_master,
#         items_bosspet=items_bosspet,
#         items_skillpet=items_skillpet,
#         items_otherpet=items_otherpet,
#         items_extra=items_extra,
#         items_passive=items_passive,
#         taskapp_email=taskapp_email,
#         official=user_info.official
#         )

def single_task_list(list_title, task_type):
    user_info = BasePageInfo()
    progress = user_info.progress
    tasks = user_info.user.page_tasks(task_type)
    context = {
        'easy': progress['easy']['percent_complete'],
        'medium': progress['medium']['percent_complete'],
        'hard': progress['hard']['percent_complete'],
        'elite': progress['elite']['percent_complete'],
        'master' : progress['master']['percent_complete'],
        'passive' : progress['passive']['percent_complete'],
        'extra' : progress['extra']['percent_complete'],
        'allPets' : progress['all_pets']['percent_complete'],
    }


    return render_template(
        'task-list.html',
        tasks=tasks,
        list_title=list_title,
        task_type=task_type,  # Needed as it is ingrained in JS for updating tasks
        username=user_info.username,
        email_verify=user_info.email_bool,
        email_val=user_info.email_val,
        official=user_info.official,
        **context
    )

# route for task-list-easy, only shows easy tasks.
@app.route('/task-list-easy/', methods=['GET'])
@login_required
def task_list_easy():
    return single_task_list(list_title='Easy Task List', task_type='easy')

#route for task-list-medium, only shows medium tasks.
@app.route('/task-list-medium/', methods=['GET'])
@login_required
def task_list_medium():
    return single_task_list(list_title='Medium Task List', task_type='medium')

# route for the hard task list, only shows hard tasks.
@app.route('/task-list-hard/', methods=['GET'])
@login_required
def task_list_hard():
    return single_task_list(list_title='Hard Task List', task_type='hard')


# route for the elite task list, only shows elite tasks.
@app.route('/task-list-elite/', methods=['GET'])
@login_required
def task_list_elite():
    return single_task_list(list_title='Elite Task List', task_type='elite')

# route for the master task list, only shows master tasks.
@app.route('/task-list-master/', methods=['GET'])
@login_required
def task_list_master():
    return single_task_list(list_title='Master Task List', task_type='master')

# route for the pets task list, only shows pets tasks.
@app.route('/task-list-pets/', methods=['GET'])
@login_required
def task_list_pets():
    return single_task_list(list_title='Pets Task List', task_type='pets')

# route for extra task list, only shows extra tasks.
@app.route('/task-list-extra/', methods=['GET'])
@login_required
def task_list_extra():
    return single_task_list(list_title='Extra Task List', task_type='extra')

# route for passive task list, only shows passive tasks.
@app.route('/task-list-passive/', methods=['GET'])
@login_required
def task_list_passive():
    return single_task_list(list_title='Passive Task List', task_type='passive')

@app.route('/hiscores', methods=['GET'])
@login_required
def highscores():
    user_info = BasePageInfo()
    # if not user_info.email_bool:
    #     return render_template('email-verify.html')
    return render_template(
        'highscores.html',
        username=user_info.username,
        email_verify=user_info.email_bool,
        email_val=user_info.email_val,
        taskapp_email=taskapp_email,
        official=user_info.official,
        leaderboard=get_leaderboard()
    )

tier_to_type = {
    "easyTasks": 'easy',
    "mediumTasks": 'medium',
    "hardTasks": 'hard',
    "eliteTasks": 'elite',
    "masterTasks": 'master',
    "bossPetTasks": 'pet',
    "skillPetTasks": 'pet',
    "otherPetTasks": 'pet',
    "passiveTasks": 'passive',
    "extraTasks": 'extra',
}

# AJAX route for completing tasks manually on task-list page(s).
# only returns HTML specific to the task.
# Javascript used to change the HTML that is displayed.
@app.route('/update_completed/', methods= ['POST'])
@login_required
def update():
    user_info = BasePageInfo()
    task_id = request.form['id']
    tier = request.form['tier']
    completed_at_iso = request.form.get('completedAtISO')
    completed_item_ids_raw = request.form.get('completedItemIds')
    completed_item_ids = []
    if completed_item_ids_raw:
        try:
            parsed = json.loads(completed_item_ids_raw)
            if isinstance(parsed, list):
                completed_item_ids = parsed
        except json.JSONDecodeError:
            completed_item_ids = []

    completed_task = manual_complete_tasks(
        session['username'],
        tier,
        task_id,
        completed_at_iso,
        completed_item_ids,
    )
    progress = get_task_progress(user_info.username)
    data = {
        'easy': progress['easy']['percent_complete'],
        'medium': progress['medium']['percent_complete'],
        'hard': progress['hard']['percent_complete'],
        'elite': progress['elite']['percent_complete'],
        'master' : progress['master']['percent_complete'],
        'passive' : progress['passive']['percent_complete'],
        'extra' : progress['extra']['percent_complete'],
        'allPets' : progress['all_pets']['percent_complete'],
        'completedAtISO': completed_task.get('completed_date_iso') if completed_task else None,
        'completedItemIds': completed_task.get('completed_item_ids') if completed_task else [],
    }
    return data

# AJAX route for uncompleting/reverting tasks manually on task-list page(s).
# only returns HTML specific to the task.
# Javascript used to change the HTML that is displayed.
@app.route('/revert_completed/', methods = ['POST'])
@login_required
def revert():
    task_id = request.form['id']
    tier = request.form['tier']
    user_info = BasePageInfo()
    manual_revert_tasks(session['username'], tier, task_id)
    progress = get_task_progress(user_info.username)
    data = {
        'easy': progress['easy']['percent_complete'],
        'medium': progress['medium']['percent_complete'],
        'hard': progress['hard']['percent_complete'],
        'elite': progress['elite']['percent_complete'],
        'master' : progress['master']['percent_complete'],
        'passive' : progress['passive']['percent_complete'],
        'extra' : progress['extra']['percent_complete'],
        'allPets' : progress['all_pets']['percent_complete'],
    }
    return data



# route for FAQ page.
@app.route('/faq/')
@login_required
def faq():
    user_info = BasePageInfo()
    # if not user_info.email_bool:
    #     return render_template('email-verify.html')
    progress = get_task_progress(user_info.username)
    context = {
        'easy': progress['easy']['percent_complete'],
        'medium': progress['medium']['percent_complete'],
        'hard': progress['hard']['percent_complete'],
        'elite': progress['elite']['percent_complete'],
        'master' : progress['master']['percent_complete'],
        'passive' : progress['passive']['percent_complete'],
        'extra' : progress['extra']['percent_complete'],
        'allPets' : progress['all_pets']['percent_complete'],
    }

    return render_template(
        'faq-new.html',
        username=user_info.username,
        email_verify=user_info.email_bool,
        email_val=user_info.email_val,
        taskapp_email=taskapp_email,
        **context
        )

#route for Wall-of-pain page.
@app.route('/wall-of-pain/')
@login_required
def wall_of_pain():
    user_info = BasePageInfo()
    # if not user_info.email_bool:
    #     return render_template('email-verify.html')
    progress = get_task_progress(user_info.username)
    context = {
        'easy': progress['easy']['percent_complete'],
        'medium': progress['medium']['percent_complete'],
        'hard': progress['hard']['percent_complete'],
        'elite': progress['elite']['percent_complete'],
        'master' : progress['master']['percent_complete'],
        'passive' : progress['passive']['percent_complete'],
        'extra' : progress['extra']['percent_complete'],
        'allPets' : progress['all_pets']['percent_complete'],
    }
    return render_template(
        'wall_of_pain.html',
        username=user_info.username,
        email_verify=user_info.email_bool,
        email_val=user_info.email_val,
        taskapp_email=taskapp_email,
        **context
    )

@app.route('/sync-collection-logs/', methods=['GET'])
@login_required
def sync_collection_logs():
    user_info = BasePageInfo()
    progress = get_task_progress(user_info.username)
    context = {
        'easy': progress['easy']['percent_complete'],
        'medium': progress['medium']['percent_complete'],
        'hard': progress['hard']['percent_complete'],
        'elite': progress['elite']['percent_complete'],
        'master' : progress['master']['percent_complete'],
        'passive' : progress['passive']['percent_complete'],
        'extra' : progress['extra']['percent_complete'],
        'allPets' : progress['all_pets']['percent_complete'],
    }
    return render_template(
        'temple-sync.html',
        username=user_info.username,
        email_verify=user_info.email_bool,
        email_val=user_info.email_val,
        taskapp_email=taskapp_email,
        **context
    )
#route for Rank Check Page
@app.route('/rank-check/', methods=['GET'])
@login_required
def rank_check():
    user_info = BasePageInfo()
    # if not user_info.email_bool:
    #     return render_template('email-verify.html')
    progress = get_task_progress(user_info.username)
    context = {
        'easy': progress['easy']['percent_complete'],
        'medium': progress['medium']['percent_complete'],
        'hard': progress['hard']['percent_complete'],
        'elite': progress['elite']['percent_complete'],
        'master' : progress['master']['percent_complete'],
        'passive' : progress['passive']['percent_complete'],
        'extra' : progress['extra']['percent_complete'],
        'allPets' : progress['all_pets']['percent_complete'],
    }
    return render_template(
        'rank-check.html',
        username=user_info.username,
        email_verify=user_info.email_bool,
        email_val=user_info.email_val,
        taskapp_email=taskapp_email,
        **context
    )



# Function to send email using send_grid API.
def send_reset_email(email, username):
    token = task_login.get_reset_token(username)
    email_message = send_grid_email.send_message(
    email,
    'Password Reset Request For Task App',
    f'''To reset your password, visit the following link:
    {url_for('reset_token', token=token, _external=True)}

    Thank you for using Task App

    If you did not make this request simply ignore this email.
    '''
    )

# Function to send email using send_grid API.
def send_verification_email(email, username):
    token = task_login.get_email_verify_token(username, email)
    email_message = send_grid_email.send_message(
        email,
    'Email verification for OSRS Task App',
    f'''To verify your account, visit the following link:
    {url_for('email_verify', token=token, _external=True)}

    Thank you for using Task App
    ''')

# Function to send email using send_grid API.
def send_verification_email_inital(email, username):
    token = task_login.get_email_verify_token(username, email)
    email_message = send_grid_email.send_message(
        email,
    'Email verification for OSRS Task App',
    f'''To verify your account, visit the following link:
    {url_for('email_verify_inital', token=token, _external=True)}

    Thank you for using Task App
    ''')

# AJAX email verify route
@app.route('/email_verify/', methods=['POST'])
@login_required
def verify():
    email = request.form['email']
    username = session['username']
    send_verification_email(email, username)
    return render_template('email_modal.html')

# AJAX email verify requiring a token for email verification.
@app.route('/email_verify/<token>')
@login_required
def email_verify(token):
    user = task_login.verify_email_verify_token(token)
    if user is None:
        flash("That is an invalid or expired token")
        return redirect(url_for('dashboard'))
    task_login.update_email(user[0], user[1])
    flash("Thank you for verifying your email address!")
    return redirect(url_for('dashboard'))

# AJAX email verify requiring a token for email verification.
@app.route('/email_verify_inital/<token>')
def email_verify_inital(token):
    user = task_login.verify_email_verify_token(token)
    if user is None:
        flash("That is an invalid or expired token")
        return redirect(url_for('login'))
    task_login.update_email(user[0], user[1])
    flash("Thank you for verifying your email address!")
    return redirect(url_for('login'))


# Route for reset password page.
@app.route("/reset-password/", methods=['GET'])
def reset_request():
    try:
        if session.get('username'):
            return redirect(url_for('dashboard'))
        return render_template('password-request.html')
    except Exception:
        return None

@app.route("/reset-password/request/", methods=['POST'])
def reset_password_request():
    if recaptcha.verify():

        email_query = task_login.query_email(request.form['email'])
        if email_query is None:
            error = 'Email Address not found'
            flash(error)
            return render_template('password-request.html')

        send_reset_email(request.form['email'], email_query['username'])
        flash(f'Email was sent to {request.form['email']}. Be sure to check your spam folder.')
        return render_template('password-request.html')

# route for password reset page requiring a token.
@app.route("/reset_password/<token>", methods=['GET', 'POST'])
def reset_token(token):
    if request.method == 'GET':
        try:
            if session['username']:
                return redirect(url_for('dashboard'))
        except KeyError:
            pass
        user = task_login.verify_reset_token(token)
        if user is None:
            flash('That is an invalid or expired token')
            return redirect(url_for('reset_request'))

        return render_template('password-reset.html')

    if request.method == 'POST':
        user = task_login.verify_reset_token(token)
        form_data = request.form
        password = form_data['password']
        repeat_password = form_data['confirmPassword']
        if password != repeat_password:
            flash("Passwords did not match. Please Try again.")
            return render_template('password-reset.html')
        else:
            change_pass = task_login.change_password(user, password)
            if change_pass[0] == True:
                flash('Password changed sucessfully, please login.')
                return redirect(url_for('login'))
            else:
                flash(change_pass[1])
                return render_template('password-reset.html')


# Route for profile page.
@app.route("/profile/")
@login_required
def profile():
    user_info = BasePageInfo()
    discord_default_username = discord_service.get_discord_auth_info(user_info.username).discord_username_default
    # if not user_info.email_bool:
    #     return render_template('email-verify.html')
    progress = get_task_progress(user_info.username)
    context = {
        'easy': progress['easy']['percent_complete'],
        'medium': progress['medium']['percent_complete'],
        'hard': progress['hard']['percent_complete'],
        'elite': progress['elite']['percent_complete'],
        'master' : progress['master']['percent_complete'],
        'passive' : progress['passive']['percent_complete'],
        'extra' : progress['extra']['percent_complete'],
        'allPets' : progress['all_pets']['percent_complete'],
        }

    return render_template(
        'profile.html',
        username=user_info.username,
        email_verify=user_info.email_bool,
        email_val=user_info.email_val,
        official=user_info.official,
        lms_status=user_info.user.lms_enabled,
        discord_status=user_info.user.discord_linked,
        discord_default_username=discord_default_username,
        discord_name_sync_enabled=user_info.user.discord_name_sync_enabled,
        **context)


@app.route("/profile/change-email/", methods=['POST'])
@login_required
def change_email():
    new_email = request.form['email']
    task_login.email_change(session['username'], new_email)
    return {'success': True}

@app.route("/profile/change-username/", methods=['POST'])
@login_required
def change_username():
    new_username = request.form['username']
    current_username = session['username']

    if new_username == current_username:
        error = f"{current_username} is already your username..."
        return {'success' : False, 'error': error}

    change_username_result = task_login.username_change(current_username, new_username)
    change_username_result_task_account = username_change(current_username, new_username)

    if change_username_result == True and change_username_result_task_account == True:
        session['username'] = new_username
        return {'success' : True}

    return {'success': False, 'error': change_username_result}

@app.route("/profile/change-password/", methods=['POST'])
@login_required
def change_password():
    username = session['username']
    new_password = request.form['new_password']

    if new_password == '':
        return {'success': False, 'error' : 'Password cannot be empty.'}
    change_password = task_login.change_password(username, new_password)
    if change_password[0]:
        return {'success' : True}
    if not change_password[0]:
        return {'success' : False, 'error' : change_password[1]}

    return {'success' : False, 'error' : 'An error occurred!'}


# AJAX route to change LMS status
@app.route("/profile/change-lms-status/", methods=['POST'])
@login_required
def change_lms_status():
    username = session['username']
    data = request.form['lms_status']
    data = False if data == 'false' else True
    lms_status_change(username, data)
    return {'success' : True}

# AJAX route to change offical status
@app.route("/profile/change-official/", methods=['POST'])
@login_required
def change_official_status():
    username = session['username']
    official_status_change(username)
    return {'success' : True}

if __name__ == "__main__":
    if (isProd):
        app.run(host='0.0.0.0')
    else:
        app.run(host="0.0.0.0", port=5001)
