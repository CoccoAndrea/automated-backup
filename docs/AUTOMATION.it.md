# 🕒 Automatizzare l'avvio del container di backup da Home Assistant (Docker)

Se utilizzi **Home Assistant** in un ambiente Docker, puoi configurare un'automazione che **avvia automaticamente il container di backup** ad esempio **due volte al giorno**, alle ore **02:00** e **18:00**.

> ⚠️ Questa guida presuppone che tu abbia accesso al tuo host Docker e che Home Assistant sia in esecuzione in modalità Supervised o Container (non Home Assistant OS puro).

---

## 🔧 1. Montare il socket Docker

Per permettere a Home Assistant di controllare altri container, è necessario concedergli accesso al socket Docker.

Nel tuo `docker-compose.yml` di Home Assistant, aggiungi:

```yaml
homeassistant:
  image: homeassistant/home-assistant:latest
  volumes:
    - /var/run/docker.sock:/var/run/docker.sock
```

> 💡 Questo consente a Home Assistant di eseguire comandi `docker` direttamente.

---

## 🛠️ 2. Definire il comando nel file `configuration.yaml`

Aggiungi un comando `shell_command` che avvia il container di backup:

```yaml
shell_command:
  start_docker_container: "docker start automated-backup"
```

---

## ▶️ 3. Creare uno script per il comando

Sempre nel tuo `configuration.yaml`, aggiungi:

```yaml
script:
  start_backup_container:
    alias: Avvia container di backup
    sequence:
      - service: shell_command.start_docker_container
```

---

## 📆 4. Automazione per schedulare due avvii giornalieri

Aggiungi la seguente automazione al tuo `configuration.yaml` o tramite l’interfaccia grafica:

```yaml
automation:
  - alias: Avvio container di backup alle 02:00 e 18:00
    trigger:
      - platform: time
        at: "02:00:00"
      - platform: time
        at: "18:00:00"
    action:
      - service: script.start_backup_container
```

---

## ✅ Verifica e riavvia

Dopo aver aggiornato il file `configuration.yaml`:

1. Controlla la configurazione in **Impostazioni → Controlla configurazione**
2. Riavvia Home Assistant per applicare le modifiche

---

Con questa configurazione, il tuo container di backup verrà eseguito automaticamente due volte al giorno, garantendo una pianificazione affidabile.

# 🕒 Alternativa - Automatizzare con Node-RED (Docker)

Se utilizzi **Node-RED come container Docker indipendente**, puoi configurare facilmente un flusso per **avviare automaticamente un altro container Docker** per esempio **due volte al giorno**, alle ore **02:00** e **18:30**.

---

## 📦 1. Pre-requisiti

### A. Il container di Node-RED deve avere accesso al socket Docker

Nel tuo `docker-compose.yml`, monta il socket Docker:

```yaml
nodered:
  image: nodered/node-red:latest
  volumes:
    - /var/run/docker.sock:/var/run/docker.sock
  ports:
    - "1880:1880"
```

> 🎯 Questo consente a Node-RED di controllare altri container locali.

---

### B. Installa il nodo `node-red-contrib-dockerode`

1. Accedi all’interfaccia web di Node-RED
2. Clicca sul menu in alto a destra → **Manage palette**
3. Vai su **Install**
4. Cerca `node-red-contrib-dockerode`
5. Clicca su **Install**

Questo modulo fornisce i nodi necessari per interagire con Docker.

---

## 🧩 2. Importare il flow di schedulazione

Copia e incolla il seguente JSON nel tuo Node-RED (Menu → Import → Paste):

```json
[
  {
    "id": "737e308f16a404e4",
    "type": "inject",
    "name": "02:00",
    "crontab": "00 02 * * *",
    "payloadType": "date",
    "wires": [["6587b83b5d81843f"]]
  },
  {
    "id": "877c45fd838dd87c",
    "type": "inject",
    "name": "18:30",
    "crontab": "30 18 * * *",
    "payloadType": "date",
    "wires": [["6587b83b5d81843f"]]
  },
  {
    "id": "6587b83b5d81843f",
    "type": "docker-container-actions",
    "name": "Start - automated-backup",
    "config": "db337e946ad05b5f",
    "container": "automated-backup",
    "action": "start",
    "x": 500,
    "y": 260,
    "wires": [[]]
  },
  {
    "id": "db337e946ad05b5f",
    "type": "docker-configuration",
    "name": "Server",
    "host": "/var/run/docker.sock"
  }
]
```

---

## 🚀 3. Deploy del flow

Dopo aver importato il flusso:
- Clicca su **Deploy** in alto a destra
- I trigger `inject` eseguiranno automaticamente l'avvio del container agli orari specificati

---

Con questa configurazione, il container `automated-backup` sarà avviato **ogni giorno alle 02:00 e alle 18:30** in modo completamente automatico via Node-RED.