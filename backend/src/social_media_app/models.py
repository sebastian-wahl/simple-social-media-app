from datetime import datetime

from sqlmodel import Field, SQLModel


class Post(SQLModel, table=True):
    """
    Simple post entity stored in a table named 'post'.
    """

    id: int | None = Field(default=None, primary_key=True)
    image_path: str  # path since I would like to use Minio for files
    text: str
    user: str
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)
