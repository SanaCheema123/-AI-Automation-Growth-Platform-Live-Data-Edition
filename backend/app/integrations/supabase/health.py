from sqlalchemy import text
from sqlalchemy.orm import Session


def test_connection(db: Session) -> bool:
    db.execute(text("select 1"))
    return True
