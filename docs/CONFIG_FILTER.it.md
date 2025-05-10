### 🧰 CONFIG: Come funzionano `include` e `exclude`

Per ogni percorso specificato in `backups`, puoi definire dei **filtri** per scegliere quali file o cartelle includere o escludere nel file `.zip`.

Il sistema utilizza **pattern stile Unix** (come `*.txt`, `data/*`, ecc.) per filtrare:

- I **file** vengono inclusi solo se corrispondono ad almeno un pattern in `include` **e** non corrispondono a nessun pattern in `exclude`.
- Le **cartelle** vengono esplorate ricorsivamente, ma le sottocartelle escluse vengono ignorate.

#### ✅ Esempi pratici
**Esempio per Windows:**
```json
{
  "path": "C:\\my_data",
  "zip_name": "backup_my_data",
  "filters": {
    "include": ["*", "data/*"],
    "exclude": ["data/*/*", "*.log"]
  }
}
```

**Esempio per Linux:**
```json
{
  "path": "/srv/docker-projects/my_data/",
  "zip_name": "backup_my_data",
  "filters": {
    "include": ["*", "data/*"],
    "exclude": ["data/*/*", "*.log"]
  }
}
```

| Pattern         | Significato                                                             |
|----------------|-------------------------------------------------------------------------|
| `*`            | Includi tutti i file nella directory di primo livello                   |
| `data/*`       | Includi tutti i file nella cartella `data/` (non ricorsivamente)        |
| `data/*/*`     | Escludi sottocartelle di `data/` e il loro contenuto                    |
| `*.log`        | Escludi tutti i file con estensione `.log`                              |

#### 🧪 Suggerimenti

- Se non specifichi `include`, verranno presi **tutti i file** per impostazione predefinita.
- Se non specifichi `exclude`, non verrà escluso nulla.
- I percorsi nei filtri sono **relativi alla cartella specificata in `path`**.
- Usa `/` anche su Windows per evitare problemi di compatibilità.

