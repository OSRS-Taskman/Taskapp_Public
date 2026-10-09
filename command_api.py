from http import HTTPStatus

from flask import Response, request

from app_setup import app
from task_database import get_user
import logging
from task_api import token_required_v2
from user_dao import UserDatabaseObject
import os

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO")
)
logger = logging.getLogger(__name__)

username_by_rsn_cache = {}


@app.route('/api/v2/command/rsn', methods=['POST'])
@token_required_v2
def store_rsn_by_username(user: UserDatabaseObject):
    body = request.json
    rsn = body['rsn']

    logger.debug("Storing RSN mapping: username=%s, rsn=%s", user.username, rsn)
    username_by_rsn_cache[rsn] = user.username

    return Response(status=HTTPStatus.NO_CONTENT)


@app.route('/api/v2/command/<rsn>', methods=['GET'])
def command_get_task_progress(rsn: str):
    logger.debug('Looking up RSN in cache: rsn=%s, cache=%s',rsn, username_by_rsn_cache)

    try:
        username = username_by_rsn_cache.get(rsn)

        if username is None:
            logger.debug('No username found in cache for rsn=%s', rsn)
            return { 'error': 'Unknown RSN' }, HTTPStatus.NOT_FOUND

        user = get_user(username)
        if user is None:
            return { 'error': 'Unknown user' }, HTTPStatus.NOT_FOUND

        logger.debug('Found username for RSN: rsn=%s, username=%s', rsn, username)
        task_id = user.current_task_id()
        curr_tier = user.current_rollable_tier()
        progress = user.get_tier_progress(curr_tier)

        return {
            'task_id': task_id,
            'tier': curr_tier,
            'progress': progress.percent_complete
        }

    except Exception as e:
        logger.exception('Error retrieving command information for rsn=%s', rsn)
        return { 'error': str(e) }, HTTPStatus.INTERNAL_SERVER_ERROR