# 📊 Configurazione PostgreSQL

Per utilizzare il sistema, è necessario avere un **database PostgreSQL attivo**. Assicurati che il tuo database sia in esecuzione e che tu abbia le credenziali di accesso. Se non hai ancora creato il database, fallo prima di procedere.

## 📌 Prepara il database

Esegui i seguenti comandi **DML (Data Manipulation Language)** per predisporre il tuo database. Assicurati di avere i privilegi necessari per creare uno schema e tabelle nel database PostgreSQL.

### 1. Creazione dello schema

Lo schema di default per il monitoraggio è chiamato `py_monitor`, ma puoi cambiarlo a tuo piacimento. Se decidi di farlo, ricorda di aggiornare anche il nome dello schema nel file di configurazione `config.json`.

```sql
-- SCHEMA: py_monitor

-- DROP SCHEMA IF EXISTS py_monitor ;

CREATE SCHEMA IF NOT EXISTS py_monitor
    AUTHORIZATION admin;
```

### 2. Creazione della sequenza

La sequenza `py_monitor.id_elab_s` viene utilizzata per generare i valori per la colonna `id_elab` nella tabella `elaborazioni`. Puoi lasciarla invariata.

```sql
-- SEQUENCE: py_monitor.id_elab_s

-- DROP SEQUENCE IF EXISTS py_monitor.id_elab_s;

CREATE SEQUENCE IF NOT EXISTS py_monitor.id_elab_s
    INCREMENT 1
    START 1
    MINVALUE 1
    MAXVALUE 9223372036854775807
    CACHE 1;

ALTER SEQUENCE py_monitor.id_elab_s
    OWNER TO admin;
```

### 3. Creazione della tabella `elaborazioni`

Questa tabella tiene traccia delle elaborazioni eseguite, inclusi i dati di inizio e fine, l'esito e le note.

```sql
-- Table: py_monitor.elaborazioni 

-- DROP TABLE IF EXISTS py_monitor.elaborazioni;

CREATE TABLE IF NOT EXISTS py_monitor.elaborazioni
(
    id_elab integer NOT NULL DEFAULT nextval('py_monitor.id_elab_s'::regclass),
    script_name text COLLATE pg_catalog."default",
    data_iniz timestamp without time zone,
    data_fine timestamp without time zone,
    esito text COLLATE pg_catalog."default",
    note text COLLATE pg_catalog."default",
    CONSTRAINT elaborazioni_pkey PRIMARY KEY (id_elab)
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS py_monitor.elaborazioni
    OWNER to admin;
```

### 4. Creazione della tabella `elaborazioni_size`

Questa tabella contiene informazioni sul nome dei file ZIP e la loro dimensione, collegandosi alla tabella `elaborazioni`.

```sql
-- Table: py_monitor.elaborazioni_size

-- DROP TABLE IF EXISTS py_monitor.elaborazioni_size;

CREATE TABLE IF NOT EXISTS py_monitor.elaborazioni_size
(
    id_elab integer NOT NULL,
    zip_name text COLLATE pg_catalog."default" NOT NULL,
    size numeric NOT NULL,
    CONSTRAINT elaborazioni_size_pkey PRIMARY KEY (id_elab, zip_name),
    CONSTRAINT elaborazioni_size_id_elab_fkey FOREIGN KEY (id_elab)
        REFERENCES py_monitor.elaborazioni (id_elab) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE CASCADE
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS py_monitor.elaborazioni_size
    OWNER to admin;
```

## ⚠️ Considerazioni

- Lo **schema `py_monitor`** è il nome predefinito, ma puoi cambiarlo a tuo piacimento. Se modifichi il nome dello schema, **aggiorna anche il campo `schema` nel file `config.json`**.
- La sequenza `id_elab_s` e le tabelle `elaborazioni` ed `elaborazioni_size` devono rimanere invariati.
- Se non hai familiarità con PostgreSQL, assicurati di avere le giuste credenziali di accesso e i privilegi per creare e gestire lo schema e le tabelle.

