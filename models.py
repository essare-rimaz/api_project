from typing import Optional
from sqlmodel import Field, SQLModel
# TODO implement relationships


class Repository(SQLModel, table=True):
    name: str = Field(primary_key=True, nullable=False)
    owner: str = Field(primary_key=True, nullable=False)
    last_modified: Optional[str] = Field(default=None, nullable=True)


class GithubEvent(SQLModel, table=True):
    id: int = Field(primary_key=True)
    type: str = Field()
    created_at: str = Field()
    repo_name_fk: str = Field(foreign_key="repository.name")
    repo_owner_fk: str = Field(foreign_key="repository.owner")
