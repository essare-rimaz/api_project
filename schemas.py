from pydantic import BaseModel


class RepoIdentity(BaseModel):
    repo: str
    owner: str