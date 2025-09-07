import psycopg
import logging
from psycopg import sql
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

    import logging

    def check_and_create_instance_column_py(self):
        try:
            cursor = self.connection.cursor()

            # Usa i parametri (%s) per i valori nella clausola WHERE
            select_query = """
                SELECT 1
                FROM information_schema.columns
                WHERE table_schema = %s AND table_name = %s AND column_name = %s
            """
            cursor.execute(select_query, (self.schema, 'elaborazioni_size', 'instance'))

            column_exists = cursor.fetchone()

            if not column_exists:
                logging.info("Column 'instance' does not exist. Creating it now...")

                # Per gli identificatori (schemi, tabelle), usa psycopg2.sql per comporre la query in modo sicuro
                alter_query = sql.SQL("ALTER TABLE {}.{} ADD COLUMN {} TEXT NOT NULL DEFAULT {}").format(
                    sql.Identifier(self.schema),
                    sql.Identifier('elaborazioni_size'),
                    sql.Identifier('instance'),
                    sql.Literal('default')
                )

                cursor.execute(alter_query)
                self.connection.commit()
                logging.info("Column 'instance' successfully created.")
            else:
                logging.info("Column 'instance' already exists. No action needed.")

        except Exception as e:
            self.connection.rollback()
            logging.critical(f"Error during database operation: {e}")
        finally:
            if 'cursor' in locals() and cursor:
                cursor.close()

    def check_and_update_primary_key_py(self):
        constraint_name = "elaborazioni_size_pkey"
        table_name = "elaborazioni_size"
        desired_pk_columns = sorted(['id_elab', 'zip_name', 'instance'])

        try:
            cursor = self.connection.cursor()

            get_pk_columns_query = """
                SELECT a.attname
                FROM   pg_constraint c
                JOIN   pg_namespace n ON n.oid = c.connamespace
                JOIN   pg_class t ON t.oid = c.conrelid
                JOIN   pg_attribute a ON a.attrelid = t.oid
                WHERE  n.nspname = %s
                AND    t.relname = %s
                AND    c.contype = 'p'
                AND    a.attnum = ANY(c.conkey)
                ORDER BY a.attname;
            """

            cursor.execute(get_pk_columns_query, (self.schema, table_name))

            current_pk_records = cursor.fetchall()
            current_pk_columns = sorted([rec[0] for rec in current_pk_records])

            if not current_pk_columns:
                logging.warning(f"Primary key '{constraint_name}' not found on table '{table_name}'. Creating it now.")
                add_pk_query = f"""
                    ALTER TABLE {self.schema}.{table_name}
                    ADD CONSTRAINT {constraint_name} PRIMARY KEY (id_elab, zip_name, instance)
                """
                cursor.execute(add_pk_query)
                logging.info(
                    f"Primary key '{constraint_name}' created successfully on {', '.join(desired_pk_columns)}.")

            elif current_pk_columns == desired_pk_columns:
                None #logging.info(f"Primary key '{constraint_name}' is already correct. No action needed.")

            else:
                logging.warning(
                    f"Primary key '{constraint_name}' is on ({', '.join(current_pk_columns)}). Recreating it on ({', '.join(desired_pk_columns)}).")

                drop_pk_query = f"ALTER TABLE {self.schema}.{table_name} DROP CONSTRAINT {constraint_name}"
                cursor.execute(drop_pk_query)

                add_pk_query = f"""
                    ALTER TABLE {self.schema}.{table_name}
                    ADD CONSTRAINT {constraint_name} PRIMARY KEY (id_elab, zip_name, instance)
                """
                cursor.execute(add_pk_query)
                logging.info(f"Primary key '{constraint_name}' successfully recreated.")

            self.connection.commit()

        except Exception as e:
            self.connection.rollback()
            logging.critical(f"Error during primary key check/update for '{table_name}': {e}")
        finally:
            if 'cursor' in locals() and cursor:
                cursor.close()
