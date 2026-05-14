from app.database import get_connection, setup


if __name__ == "__main__":
    conn = get_connection()
    setup(conn)
    conn.close()
