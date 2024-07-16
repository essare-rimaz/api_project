# https://www.reddit.com/r/learnpython/comments/x10ezo/fastapi_how_do_i_cross_call_another_endpoint/
from tools import setup_logger
import httpx
from fastapi import APIRouter, FastAPI, Depends
from schemas import RepoIdentity
from sqlmodel import Session, select
import uvicorn
from pathlib import Path
from models import Repository, GithubEvent
from initiate_db import init_db, get_session
from contextlib import asynccontextmanager

logger = setup_logger(__name__)


# creates an object that is initiated before the app starts
@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app = FastAPI(lifespan=lifespan)
github_callback_router = APIRouter()


#TODO actually only returns 30 items, have to implement pagination
@github_callback_router.get("https://api.github.com/repos/{$request.body.owner}/{$request.body.repo}/events")
def github_repo_public_events(repo, owner, last_modified):
    """
    Pooling from GitHub API. In order to keep calls at minimum header "last_modified" is used
    for potential 304 code response.
    """
    headers = {'if-modified-since': last_modified} if last_modified else None
    logger.debug(f"my header {headers}")
    callback_url = f"https://api.github.com/repos/{owner}/{repo}/events"
    response = httpx.get(callback_url, headers=headers)
    logger.debug(response.status_code)
    logger.debug(response.headers.get("Last-Modified"))
    return response


@app.get("/", callbacks=github_callback_router.routes)
def get_repo_statistics(repo_identity: RepoIdentity, session: Session = Depends(get_session)):
    """
    Get average time (in seconds) between consecutive events (grouped by event type) for given GitHub repository.

    Is returned as a list of lists.
    """
    repo = session.get(Repository, (repo_identity.repo, repo_identity.owner))
    # handle whether the repository already was called in the past
    if repo:
        logger.debug(f"repo exists")
        logger.debug(f"at start repo has {repo.last_modified} as last modified")
        last_modified = repo.last_modified
    else:
        logger.debug(f"repo DOES NOT exist")

        repo_data = Repository(name=repo_identity.repo, owner=repo_identity.owner)
        session.add(repo_data)
        session.flush()
        last_modified = None

    repo = repo_identity.repo
    owner = repo_identity.owner

    response = github_repo_public_events(repo, owner, last_modified)
    process_github_response(response, repo, owner, session)

    statement = select(GithubEvent).where(GithubEvent.repo_name_fk == repo and GithubEvent.repo_owner_fk == owner)
    results = session.exec(statement)
    result = results.all()
    logger.debug(f"{len(result)}")
    return result


# is it ok that the session is not used as a dependent?
def process_github_response(response, repo, owner, session):
    status_code = response.status_code
    response_headers = response.headers
    last_modified = response_headers.get('Last-Modified')
    logger.debug(f"status code = {status_code}")
    if status_code == 304:
        statement = select(Repository).where(Repository.name == repo and Repository.owner == owner)
        result = session.exec(statement)
        repository = result.one()
        repository.last_modified = last_modified

    elif status_code == 200:
        last_modified = response_headers.get('Last-Modified')
        statement = select(Repository).where(Repository.name == repo and Repository.owner == owner)
        result = session.exec(statement)
        repository = result.one()
        logger.debug(repository)

        repository.last_modified = last_modified
        session.add(repository)
        session.flush()
        session.refresh(repository)
        logger.debug(repository)

        events = extract_from_response(response.json(), repo, owner)
        #TODO implement a check for each row if it already is in DB until I learn how to do it in bulk...
        # I would definetly prefer if it wasnt taken by index...
        # it does seem that upsert exists in sqlmodel, best solution so far looks like
        # https://github.com/tiangolo/sqlmodel/issues/59#issuecomment-2085514089
        for event in events:
            github_event = GithubEvent(id=event[0],
                                       type=event[1],
                                       created_at=event[2],
                                       repo_name_fk=event[3],
                                       repo_owner_fk=event[4])
            session.add(github_event)
        #TODO rollback in case of errors
        session.commit()

    else:
        print(status_code)
        raise ValueError


def extract_from_response(github_response, repo, owner):
    data = github_response
    extracted_data = [(item["id"], item["type"], item["created_at"], repo, owner) for item in data]
    return extracted_data


if __name__ == "__main__":
    # https://github.com/tiangolo/fastapi/issues/1495
    uvicorn.run(f"{Path(__file__).stem}:app", host="127.0.0.1", port=8000, reload=True, log_level="debug")
