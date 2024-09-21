import os

import mysql.connector.pooling

# Configure MySQL connection pool
db_config = {
    "host": os.getenv("DB_HOST"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_NAME"),
}

# Create a MySQL connection pool
connection_pool = mysql.connector.pooling.MySQLConnectionPool(
    pool_size=5, **db_config
)


# Function to get a connection from the pool
def get_connection():
    return connection_pool.get_connection()


# Function to close the connection
def close_connection(connection):
    connection.close()


# Function to execute a query
def execute_query(query, params=None, jsonformat=True):
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute(query, params)
    column_names = [column[0] for column in cursor.description]
    rows = cursor.fetchall()
    if jsonformat:
        result = [dict(zip(column_names, row)) for row in rows]
    else:
        result = column_names, rows
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
            FROM Events e
            JOIN Sections s on e.id = s.event_id
            GROUP BY e.id, e.date_created, e.name, e.event_date, e.location, e.lap_count, e.completed
            ORDER BY e.event_date ASC;
        """
    ),
    "UPCOMING_EVENTS": lambda: execute_query(
        """
            SELECT e.*, COUNT(s.section_number) AS section_count
            FROM Events e
            JOIN Sections s on e.id = s.event_id
            WHERE completed = 0
            GROUP BY e.id, e.date_created, e.name, e.event_date, e.location, e.lap_count, e.completed
            ORDER BY e.event_date ASC;
        """
    ),
    "COMPLETED_EVENTS": lambda: execute_query(
        """
            SELECT e.*, COUNT(s.section_number) AS section_count
            FROM Events e
            JOIN Sections s on e.id = s.event_id
            WHERE completed = 1
            GROUP BY e.id, e.date_created, e.name, e.event_date, e.location, e.lap_count, e.completed
            ORDER BY e.event_date ASC;
        """
    ),
    "COMPLETE_EVENT": lambda event_id: insert_query(
        """
            UPDATE Events
            SET completed = 1
            WHERE id = %s;
        """,
        (event_id,),
    ),
    "DELETE_EVENT": lambda event_id: insert_query(
        """
            DELETE FROM Events
            WHERE id = %s;
        """,
        (event_id,),
    ),
    "EVENT": lambda event_id: execute_query(
        """
            SELECT id, name, event_date, location, lap_count
            FROM Events
            WHERE id = %s;
        """,
        (event_id,),
    ),
    # Sections
    "ALL_SECTIONS": lambda event_id: execute_query(
        """
            SELECT section_number
            FROM Sections
            WHERE event_id = %s;
        """,
        (event_id,),
    ),
    # Riders
    "ALL_RIDERS": lambda event_id: execute_query(
        """
            SELECT rider_number, rider_name, c.name AS class
            FROM Riders r
            JOIN Classes c ON r.class_id = c.id
            WHERE event_id = %s
            ORDER BY rider_number ASC;
        """,
        (event_id,),
    ),
    "GET_SCORES": lambda event_id, section_number, rider_number: execute_query(
        """
            SELECT lap_number, score
            FROM Scores
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
            INSERT INTO Scores (event_id, section_number, rider_number, lap_number, score)
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
    "UPDATE_SCORE": lambda event_id, section_number, rider_number, lap_number, score: insert_query(
        """
            UPDATE Scores
            SET score = %s
            WHERE event_id = %s AND section_number = %s AND rider_number = %s AND lap_number = %s;
        """,
        (
            score,
            event_id,
            section_number,
            rider_number,
            lap_number,
        ),
    ),
    "CREATE_EVENT": lambda event_name, event_location, event_date, laps, password: insert_query(
        """
            INSERT INTO Events (name, location, event_date, lap_count, password)
            VALUES (%s, %s, %s, %s, %s);
        """,
        (
            event_name,
            event_location,
            event_date,
            laps,
            password,
        ),
    ),
    "CREATE_SECTION": lambda event_id, section_number: insert_query(
        """
            INSERT INTO Sections (event_id, section_number)
            VALUES (%s, %s);
        """,
        (
            event_id,
            section_number,
        ),
    ),
    "CREATE_RIDERS": lambda query: insert_query(
        f"""
            INSERT INTO Riders (event_id, rider_number, rider_name, class_id)
            VALUES {query};
        """,
    ),
    
    "GET_SCORES_SUMMARY_BY_EVENTID": lambda event_id: execute_query(
        """
            SELECT s.rider_number, rider_name, c.name as class_name, SUM(score) as total_score
            FROM trials_db.Events e
            JOIN Sections sec ON e.id = sec.event_id
            JOIN Scores s ON e.id = s.event_id AND s.section_number = sec.section_number
            JOIN Riders r ON e.id = r.event_id AND s.rider_number = r.rider_number
            JOIN Classes c ON r.class_id = c.id
            WHERE e.id = %s
            GROUP BY rider_number, rider_name, class_name
            ORDER BY
            CASE class_name
                WHEN 'M' THEN 1
                WHEN 'E' THEN 2
                WHEN 'I' THEN 3
                WHEN 'C' THEN 4
            END,
            total_score ASC;
        """,
        (event_id,),
    ),
    "GET_SCORES_SUMMARY_BY_EVENTID_EXCEL": lambda event_id: execute_query(
        """
            SELECT s.rider_number, rider_name, c.name as class_name, SUM(score) as total_score
            FROM trials_db.Events e
            JOIN Sections sec ON e.id = sec.event_id
            JOIN Scores s ON e.id = s.event_id AND s.section_number = sec.section_number
            JOIN Riders r ON e.id = r.event_id AND s.rider_number = r.rider_number
            JOIN Classes c ON r.class_id = c.id
            WHERE e.id = %s
            GROUP BY rider_number, rider_name, class_name
            ORDER BY
            CASE class_name
                WHEN 'M' THEN 1
                WHEN 'E' THEN 2
                WHEN 'I' THEN 3
                WHEN 'C' THEN 4
            END,
            total_score ASC;
        """,
        (event_id,),
        False
    ),
    "EVENT_HAS_PASSWORD": lambda event_id: execute_query(
        """
            SELECT password
            FROM Events
            WHERE id = %s;
        """,
        (event_id,),
    ),
    "VERIFY_EVENT_PASSWORD": lambda event_id, password: execute_query(
        """
            SELECT id
            FROM Events
            WHERE id = %s AND password = %s;
        """,
        (event_id, password),
    ),
}
