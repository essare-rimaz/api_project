# https://www.reddit.com/r/learnpython/comments/x10ezo/fastapi_how_do_i_cross_call_another_endpoint/
from typing import Union, AnyStr
from tools import setup_logger
import httpx
from fastapi import APIRouter, FastAPI
from pydantic import BaseModel
import uvicorn
from pathlib import Path
from initiate_dbs import create_sqlite_database
from data_manipulation import data_magic, update_repo_combo, add_repo_combo, \
    check_repo_combo, get_last_modified, write_github_events

logger = setup_logger(__name__)

app = FastAPI()
github_callback_router = APIRouter()


@app.get("/", callbacks=github_callback_router.routes)
def get_repo_statistics(owner: AnyStr, repo: AnyStr):
    """
    Get average time (in seconds) between consecutive events (grouped by event type) for given GitHub repository.

    Is returned as a list of lists.
    """
    repo_combo_in_db = check_repo_combo(repo, owner)
    last_modified = get_last_modified(repo, owner)
    response = github_repo_public_events(owner, repo, last_modified)

    return process_github_response(response, repo, owner, repo_combo_in_db)


@github_callback_router.get(
"https://api.github.com/repos/{$owner}/{$repo}/events")
def github_repo_public_events(owner, repo, last_modified=None):
    owner = owner
    repo = repo
    headers = {'if-modified-since': last_modified} if last_modified else None
    callback_url = f"https://api.github.com/repos/{owner}/{repo}/events"
    response = httpx.get(callback_url, headers=headers)

    return response


def process_github_response(response, repo, owner, repo_combo_in_db):
    status_code = response.status_code
    response_headers = response.headers

    if status_code == 304:
        logger.debug(f"status code = {status_code}, repo_combo_in_db = {repo_combo_in_db}")
        return data_magic(repo, owner)

    elif status_code == 200 and repo_combo_in_db:
        logger.debug(f"status code = {status_code}, repo_combo_in_db = {repo_combo_in_db}")
        last_modified = response_headers.get('last-modified')
        update_repo_combo(repo, owner, last_modified)
        return data_magic(repo, owner)

    elif status_code == 200 and not repo_combo_in_db:
        logger.debug(f"status code = {status_code}, repo_combo_in_db = {repo_combo_in_db}")
        last_modified = response_headers.get('last-modified')
        add_repo_combo(repo, owner, last_modified)
        events = extract_from_response(response.json(), repo, owner)
        write_github_events(events)
        return data_magic(repo, owner)
    else:
        print(status_code)
        raise ValueError


def extract_from_response(github_response, repo, owner):
    data = github_response
    extracted_data = [(item["id"], item["type"], item["created_at"], repo, owner) for item in data]
    return extracted_data


if __name__ == "__main__":
    create_sqlite_database("my.db")
    # https://github.com/tiangolo/fastapi/issues/1495
    uvicorn.run(f"{Path(__file__).stem}:app", host="127.0.0.1", port=8000, reload=True, log_level="debug")