import sqlite3
from tools import setup_logger

logger = setup_logger(__name__)


def data_magic(repo, owner):
    variables = (repo, owner)
    sql = '''

    WITH time_diffs AS (
        SELECT 
            type, 
            repo_fk,
            owner_fk,
            (julianday(event_created) - julianday(LAG(event_created) OVER (PARTITION BY type ORDER BY event_created))) * 24 * 60 * 60 AS diff_seconds
        FROM event
        WHERE repo_fk = ? and owner_fk = ?
    )
    SELECT 
        type, 
        repo_fk,
        owner_fk,
        AVG(diff_seconds)
    FROM 
        time_diffs
    WHERE 
        diff_seconds IS NOT NULL
    GROUP BY
        REPO_FK, OWNER_FK, TYPE
    '''
    with sqlite3.connect('my.db') as conn:
        cur = conn.cursor()
        cur.execute(sql, variables)
        row = cur.fetchall()
    conn.close()
    return row
