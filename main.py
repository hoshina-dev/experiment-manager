import sqlite3
from app.database import get_connection, setup


def insert(conn: sqlite3.Connection, name: str, value: str) -> int:
    cursor = conn.execute(
        "INSERT INTO items (name, value) VALUES (?, ?)", (name, value)
    )
    conn.commit()
    assert cursor.lastrowid is not None
    return cursor.lastrowid


def fetch_all(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    return conn.execute("SELECT * FROM items").fetchall()


if __name__ == "__main__":
    conn = get_connection()
    setup(conn)

    insert(conn, "experiment_1", "result=0.92")
    insert(conn, "experiment_2", "result=0.87")
    insert(conn, "experiment_3", "result=0.95")

    rows = fetch_all(conn)
    print(f"{'ID':<5} {'Name':<20} {'Value'}")
    print("-" * 40)
    for row in rows:
        print(f"{row['id']:<5} {row['name']:<20} {row['value']}")

    conn.close()
