import mysql.connector.pooling

# Configure MySQL connection pool
db_config = {
    "host": "localhost",
    "user": "root",
    "password": "31656072",
    "database": "trails_db",
}

# Create a MySQL connection pool
connection_pool = mysql.connector.pooling.MySQLConnectionPool(
    pool_name="my_pool", pool_size=5, **db_config
)


# Function to get a connection from the pool
def get_connection():
    return connection_pool.get_connection()


# Function to close the connection
def close_connection(connection):
    connection.close()


# Function to execute a query
def execute_query(query, params=None):
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute(query, params)
    column_names = [column[0] for column in cursor.description]
    rows = cursor.fetchall()
    result = [dict(zip(column_names, row)) for row in rows]
    cursor.close()
    close_connection(connection)
    return result


def insert_query(query, params=None):
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute(query, params)
    connection.commit()
    inserted_id = cursor.lastrowid
    cursor.close()
    close_connection(connection)
    return inserted_id


# Standard Queries
QUERIES = {
    # Events
    "ALL_EVENTS": lambda: execute_query(
        """
            SELECT e.*, COUNT(s.section_number) AS section_count
            FROM events e
            JOIN sections s on e.id = s.event_id
            GROUP BY e.id, e.date_created, e.name, e.event_date, e.location, e.lap_count, e.completed
            ORDER BY e.event_date ASC;
        """
    ),
    "UPCOMING_EVENTS": lambda: execute_query(
        """
            SELECT e.*, COUNT(s.section_number) AS section_count
            FROM events e
            JOIN sections s on e.id = s.event_id
            WHERE completed = 0
            GROUP BY e.id, e.date_created, e.name, e.event_date, e.location, e.lap_count, e.completed
            ORDER BY e.event_date ASC;
        """
    ),
    "COMPLETED_EVENTS": lambda: execute_query(
        """
            SELECT e.*, COUNT(s.section_number) AS section_count
            FROM events e
            JOIN sections s on e.id = s.event_id
            WHERE completed = 1
            GROUP BY e.id, e.date_created, e.name, e.event_date, e.location, e.lap_count, e.completed
            ORDER BY e.event_date ASC;
        """
    ),
    "COMPLETE_EVENT": lambda event_id: insert_query(
        """
            UPDATE events
            SET completed = 1
            WHERE id = %s;
        """,
        (event_id,),
    ),
    "DELETE_EVENT": lambda event_id: insert_query(
        """
            DELETE FROM events
            WHERE id = %s;
        """,
        (event_id,),
    ),
    "EVENT": lambda event_id: execute_query(
        """
            SELECT id, name, event_date, location, lap_count
            FROM events
            WHERE id = %s;
        """,
        (event_id,),
    ),
    # Sections
    "ALL_SECTIONS": lambda event_id: execute_query(
        """
            SELECT section_number
            FROM sections
            WHERE event_id = %s;
        """,
        (event_id,),
    ),
    # Riders
    "ALL_RIDERS": lambda event_id: execute_query(
        """
            SELECT rider_number, rider_name, c.name AS class
            FROM riders r
            JOIN classes c ON r.class_id = c.id
            WHERE event_id = %s;
        """,
        (event_id,),
    ),
    "GET_SCORES": lambda event_id, section_number, rider_number: execute_query(
        """
            SELECT lap_number, score
            FROM scores
            WHERE event_id = %s AND section_number = %s AND rider_number = %s;
        """,
        (
            event_id,
            section_number,
            rider_number,
        ),
    ),
    "POST_SCORE": lambda event_id, section_number, rider_number, lap_number, score: insert_query(
        """
            INSERT INTO scores (event_id, section_number, rider_number, lap_number, score)
            VALUES (%s, %s, %s, %s, %s);
        """,
        (
            event_id,
            section_number,
            rider_number,
            lap_number,
            score,
        ),
    ),
    "CREATE_EVENT": lambda event_name, event_location, event_date, laps: insert_query(
        """
            INSERT INTO events (name, location, event_date, lap_count)
            VALUES (%s, %s, %s, %s);
        """,
        (
            event_name,
            event_location,
            event_date,
            laps,
        ),
    ),
    "CREATE_SECTION": lambda event_id, section_number: insert_query(
        """
            INSERT INTO sections (event_id, section_number)
            VALUES (%s, %s);
        """,
        (
            event_id,
            section_number,
        ),
    ),
    "CREATE_RIDERS": lambda query: insert_query(
        f"""
            INSERT INTO riders (event_id, rider_number, rider_name, class_id)
            VALUES {query};
        """,
    ),
}
