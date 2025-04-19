import psycopg
import logging
logger = logging.getLogger(__name__)

class PostgreSQL:
    def __init__(self, dbname, schema, user, password, host='localhost', port=5432):
        self.schema = schema
        self.connection = psycopg.connect(
            dbname=dbname,
            user=user,
            password=password,
            host=host,
            port=port
        )
        logger.info("Connected to PostgreSQL")

    def insert_ret_idelab(self, table, data):
        try:
            columns = ', '.join(data.keys())
            values = ', '.join(f'%({key})s' for key in data.keys())
            query = f'INSERT INTO {self.schema}.{table} ({columns}) VALUES ({values}) RETURNING id_elab'
            with self.connection.cursor() as cursor:
                cursor.execute(query, data)
                id_elab = cursor.fetchone()[0]
            self.connection.commit()
            logger.info(f"Inserted data into {table} and data: {data}")
            return id_elab, 0
        except Exception as e:
            logger.error(f"Error inserting data into {table}: {e}")
            self.connection.rollback()  # Ripristina la connessione
            return id_elab, 8

    def insert(self, table, data):
        try:
            columns = ', '.join(data.keys())
            values = ', '.join(f'%({key})s' for key in data.keys())
            query = f'INSERT INTO {self.schema}.{table} ({columns}) VALUES ({values})'
            with self.connection.cursor() as cursor:
                cursor.execute(query, data)
            self.connection.commit()
            logger.info(f"Inserted data into {table} and data: {data}")
            return 0
        except Exception as e:
            logger.error(f"Error inserting data into {table}: {e}")
            self.connection.rollback()  # Ripristina la connessione
            return 8


    def read(self, table, conditions=None):
        query = f'SELECT * FROM {self.schema}.{table}'
        if conditions:
            condition_str = ' AND '.join(f"{key} = %({key})s" for key in conditions.keys())
            query += f' WHERE {condition_str}'
        with self.connection.cursor() as cursor:
            cursor.execute(query, conditions)
            result = cursor.fetchall()
        logger.info(f"Read data from {table}")
        return result

    def update(self, table, data, conditions):
        try:
            set_str = ', '.join(f"{key} = %({key})s" for key in data.keys())
            condition_str = ' AND '.join(f"{key} = %({key})s" for key in conditions.keys())
            query = f'UPDATE {self.schema}.{table} SET {set_str} WHERE {condition_str}'
            logger.info(f"Updating data: {query}")
            with self.connection.cursor() as cursor:
                cursor.execute(query, {**data, **conditions})
            self.connection.commit()
            logger.info(f"Updated data in {table} with conditions: {conditions} and data: {data}")
            return 0
        except Exception as e:
            logger.error(f"Error updating data in {table}: {e}")
            self.connection.rollback()  # Ripristina la connessione
            return 8

    def delete(self, table, conditions):
        condition_str = ' AND '.join(f"{key} = %({key})s" for key in conditions.keys())
        query = f'DELETE FROM {self.schema}.{table} WHERE {condition_str}'
        with self.connection.cursor() as cursor:
            cursor.execute(query, conditions)
        self.connection.commit()
        logger.info(f"Deleted data from {table}")

    def close(self):
        self.connection.close()
        logger.info("Disconnected from PostgreSQL")
