# 📊 PostgreSQL Configuration

To use this system, you must have an active **PostgreSQL database**. Make sure it is running and that you have credentials.

## 📌 Prepare the database

Run the following **DML commands** to set up your database. You must have privileges to create schemas and tables.

### 1. Create schema

Default schema is `py_monitor`, but you can change it (update `config.json` accordingly).

```sql
CREATE SCHEMA IF NOT EXISTS py_monitor
    AUTHORIZATION admin;
```

### 2. Create sequence

```sql
CREATE SEQUENCE IF NOT EXISTS py_monitor.id_elab_s
    INCREMENT 1
    START 1
    MINVALUE 1
    MAXVALUE 9223372036854775807
    CACHE 1;

ALTER SEQUENCE py_monitor.id_elab_s
    OWNER TO admin;
```

### 3. Create table `elaborazioni`

```sql
CREATE TABLE IF NOT EXISTS py_monitor.elaborazioni (
    id_elab integer NOT NULL DEFAULT nextval('py_monitor.id_elab_s'::regclass),
    script_name text,
    data_iniz timestamp,
    data_fine timestamp,
    esito text,
    note text,
    CONSTRAINT elaborazioni_pkey PRIMARY KEY (id_elab)
);

ALTER TABLE IF EXISTS py_monitor.elaborazioni
    OWNER to admin;
```

### 4. Create table `elaborazioni_size`

```sql
CREATE TABLE IF NOT EXISTS py_monitor.elaborazioni_size (
    id_elab integer NOT NULL,
    zip_name text NOT NULL,
    size numeric NOT NULL,
    CONSTRAINT elaborazioni_size_pkey PRIMARY KEY (id_elab, zip_name),
    CONSTRAINT elaborazioni_size_id_elab_fkey FOREIGN KEY (id_elab)
        REFERENCES py_monitor.elaborazioni (id_elab)
        ON DELETE CASCADE
);
ALTER TABLE IF EXISTS py_monitor.elaborazioni_size
    OWNER to admin;
```

## ⚠️ Notes

- If you rename the schema, update the `schema` field in `config.json`.
- Sequence and table names must stay the same.
- Ensure you have database privileges to create schemas/tables.