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
    result = cursor.fetchall()
    cursor.close()
    close_connection(connection)
    return result
