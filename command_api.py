from http import HTTPStatus

from flask import request

from app_setup import app
from task_database import get_task_progress, get_taskCurrent
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

    username_by_rsn_cache[rsn] = user.username

    logger.debug(
        "Storing RSN mapping: username=%s, rsn=%s, body=%s",
        user.username,
        rsn,
        body
    )

    return '', HTTPStatus.NO_CONTENT


@app.route('/command/<rsn>', methods=['GET'])
def command_get_task_progress(rsn: str):
    logger.debug("Looking up RSN in cache: rsn=%s, cache=%s",rsn, username_by_rsn_cache)

    try:
        username = username_by_rsn_cache.get(rsn)

        if username is None:
            logger.debug("No username found in cache for rsn=%s", rsn)
            return {
                "error": "Unknown RSN"
            }, HTTPStatus.NOT_FOUND

        logger.debug("Found username for RSN: rsn=%s, username=%s", rsn, username)
        task = get_taskCurrent(username)
        progress = get_task_progress(username)
        curr_tier = _get_current_tier(progress)

        return {
            "task": task,
            "tier": curr_tier,
            "progressPercentage": progress[curr_tier]["percent_complete"]
        }

    except Exception as e:
        logger.exception(
            "Error retrieving command information for rsn=%s",
            rsn
        )

        return {
            'error': f'Error: {e}'
        }, HTTPStatus.INTERNAL_SERVER_ERROR


def _get_current_tier(progress):
    if progress["easy"]["total_complete"] < progress["easy"]["total"]:
        return "easy"
    elif progress["medium"]["total_complete"] < progress["medium"]["total"]:
        return "medium"
    elif progress["hard"]["total_complete"] < progress["hard"]["total"]:
        return "hard"
    elif progress["elite"]["total_complete"] < progress["elite"]["total"]:
        return "elite"
    elif progress["master"]["total_complete"] < progress["master"]["total"]:
        return "master"
    else:
        return "extra"