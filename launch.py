from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class Launch(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    path: str
    launch_time: Optional[datetime]
    type: bool
