# 🕒 Automating Backup Container Start from Home Assistant (Docker)

If you're using **Home Assistant** in a Docker environment, you can configure an automation to **automatically start the backup container**, for example **twice a day**, at **02:00** and **18:00**.

> ⚠️ This guide assumes you have access to your Docker host and are running Home Assistant in Supervised or Container mode (not Home Assistant OS).

---

## 🔧 1. Mount the Docker Socket

To allow Home Assistant to control other containers, you must give it access to the Docker socket.

In your Home Assistant `docker-compose.yml`, add:

```yaml
homeassistant:
  image: homeassistant/home-assistant:latest
  volumes:
    - /var/run/docker.sock:/var/run/docker.sock
```

> 💡 This allows Home Assistant to run `docker` commands directly.

---

## 🛠️ 2. Define the Command in `configuration.yaml`

Add a `shell_command` to start the backup container:

```yaml
shell_command:
  start_docker_container: "docker start automated-backup"
```

---

## ▶️ 3. Create a Script to Trigger the Command

Also in your `configuration.yaml`, add:

```yaml
script:
  start_backup_container:
    alias: Start backup container
    sequence:
      - service: shell_command.start_docker_container
```

---

## 📆 4. Automation to Schedule Two Daily Starts

Add the following automation in your `configuration.yaml` or via the UI:

```yaml
automation:
  - alias: Start backup container at 02:00 and 18:00
    trigger:
      - platform: time
        at: "02:00:00"
      - platform: time
        at: "18:00:00"
    action:
      - service: script.start_backup_container
```

---

## ✅ Check and Restart

After editing `configuration.yaml`:

1. Go to **Settings → Check Configuration**
2. Restart Home Assistant to apply changes

---

With this setup, your backup container will be automatically started twice a day, ensuring reliable scheduling.

# 🕒 Alternative – Automate with Node-RED (Docker)

If you're using **Node-RED as a standalone Docker container**, you can easily set up a flow to **automatically start another Docker container**, e.g. **twice a day**, at **02:00** and **18:30**.

---

## 📦 1. Prerequisites

### A. Node-RED Container Must Access Docker Socket

In your `docker-compose.yml`, mount the Docker socket:

```yaml
nodered:
  image: nodered/node-red:latest
  volumes:
    - /var/run/docker.sock:/var/run/docker.sock
  ports:
    - "1880:1880"
```

> 🎯 This allows Node-RED to control other local containers.

---

### B. Install the `node-red-contrib-dockerode` Node

1. Access Node-RED Web UI
2. Click the top-right menu → **Manage palette**
3. Go to **Install**
4. Search for `node-red-contrib-dockerode`
5. Click **Install**

This module provides the necessary Docker nodes.

---

## 🧩 2. Import the Scheduling Flow

Copy and paste the following JSON into Node-RED (Menu → Import → Paste):

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

## 🚀 3. Deploy the Flow

After importing the flow:
- Click **Deploy** in the top right
- The `inject` triggers will automatically run the container at the scheduled times

---

With this setup, the `automated-backup` container will be automatically started **every day at 02:00 and 18:30** via Node-RED.