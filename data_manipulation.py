import sqlite3
from tools import setup_logger

logger = setup_logger(__name__)


def check_state(repo, owner):
    sql = '''SELECT * FROM repo WHERE repo=? and owner=?'''
    variables = (repo, owner)
    with sqlite3.connect('my.db') as conn:
        cur = conn.cursor()
        cur.execute(sql, variables)
        row = cur.fetchone()
        conn.close()
    logger.debug(row)
    return row


def get_last_modified(repo, owner):
    sql = '''SELECT last_modified FROM repo WHERE repo=? and owner=?'''
    variables = (repo, owner)
    with sqlite3.connect('my.db') as conn:
        cur = conn.cursor()
        cur.execute(sql, variables)
        row = cur.fetchone()
    if row is None:
        logger.debug(row)
        conn.close()
        return row
    else:
        logger.debug(row)
        conn.close()
        return row[0]


def update_repo_combo(repo, owner, last_modified):
    sql = ''' UPDATE repo SET last_modified=? WHERE repo=? and owner=?'''
    variables = (last_modified, repo, owner)
    with sqlite3.connect('my.db') as conn:
        cur = conn.cursor()
        cur.execute(sql, variables)
        conn.commit()
    conn.close()


def check_repo_combo(repo, owner) -> bool:
    with sqlite3.connect('my.db') as conn:
        cur = conn.cursor()
        cur.execute('select count(*) as count from repo where repo = ? and owner = ?', (repo, owner,))
        row = cur.fetchone()[0]
    if row == 0:
        conn.close()
        return False
    elif row == 1:
        conn.close()
        return True
    else:
        conn.close()
        raise ValueError


def add_repo_combo(repo, owner, last_modified):
    sql = ''' INSERT OR IGNORE INTO repo(repo,owner,last_modified)
              VALUES(?,?,?) '''
    variables = (repo, owner, last_modified)
    with sqlite3.connect('my.db') as conn:
        cur = conn.cursor()
        cur.execute(sql, variables)
        conn.commit()
    conn.close()


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


def write_github_events(events):
    sql = ''' INSERT OR IGNORE INTO event(ID, TYPE, EVENT_CREATED, REPO_FK, OWNER_FK)
              VALUES(?,?,?,?,?) '''
    with sqlite3.connect('my.db') as conn:
        cur = conn.cursor()
        cur.executemany(sql, events)
        conn.commit()
    return cur.lastrowid