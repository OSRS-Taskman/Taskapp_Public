from http import HTTPStatus

from flask import request

from app_setup import app
from task_database import get_task_progress, get_taskCurrent
import logging

logger = logging.getLogger(__name__)


@app.route('/command/<username>', methods=['GET'])
def command_get_task_progress(username: str):
    try:
        task = get_taskCurrent(username)
        progress = get_task_progress(username)
        curr_tier = _get_current_tier(progress)
        return {
            "task": task,
            "tier": curr_tier,
            "progressPercentage": progress[curr_tier]["percent_complete"]
        }
    except Exception:
        logger.exception("Error on retrieving command information")
        return {
            'error': 'Something went wrong when retrieving command information'
        }, HTTPStatus.NOT_FOUND


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