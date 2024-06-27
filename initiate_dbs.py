import sqlite3


def create_sqlite_database(filename):
    """ create a database connection to an SQLite database """
    conn = None
    try:
        conn = sqlite3.connect(filename)
        print(sqlite3.sqlite_version)
        create_tables()
    except sqlite3.Error as e:
        print(e)
    finally:
        if conn:
            conn.close()


def create_tables():
    sql_statements = [
        """CREATE TABLE IF NOT EXISTS event (
                ID INTEGER PRIMARY KEY, 
                TYPE text NOT NULL, 
                EVENT_CREATED TIMESTAMP, 
                REPO_FK TEXT NOT NULL,
                OWNER_FK TEXT NOT NULL,
                FOREIGN KEY (REPO_FK, OWNER_FK) REFERENCES repo (REPO, OWNER)
        );""",
        """CREATE TABLE IF NOT EXISTS repo (
                REPO TEXT NOT NULL, 
                OWNER TEXT NOT NULL, 
                LAST_MODIFIED TEXT NOT NULL,
                PRIMARY KEY (REPO, OWNER)
        );"""]

    # create a database connection
    try:
        with sqlite3.connect('my.db') as conn:
            cursor = conn.cursor()
            for statement in sql_statements:
                cursor.execute(statement)

            conn.commit()
            conn.close()
    except sqlite3.Error as e:
        print(e)