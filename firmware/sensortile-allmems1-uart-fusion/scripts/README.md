# UART Fusion Decoder

Ce répertoire contient le script Python **`uart_fusion_decoder.py`** qui décode les flux UART provenant du capteur SensorTile.

## Prérequis
- Python 3.8+ installé. Nous recommandons d’utiliser l’interpréteur fourni par **pyenv** : `/Users/maxenslecam/.pyenv/versions/3.10.13/bin/python` (ou le chemin correspondant à votre version).
- Bibliothèque Python requise : `pyserial`.

Installez la dépendance :
```bash
pip install pyserial
```

## Utilisation
Exécutez le script depuis ce répertoire :

### Exemple avec le chemin complet de l’interpréteur (macOS / Linux)

```bash
/Users/maxenslecam/.pyenv/versions/3.10.13/bin/python \
    /Users/maxenslecam/Documents/perseus-daq-board/firmware/sensortile-allmems1-uart-fusion/scripts/uart_fusion_decoder.py \
    --port /dev/cu.usbserial-FT82BWWY \
    --baud 115200 \
    --output decoded.csv
```

### Exemple sous Windows (chemin complet vers `python.exe`)

```bat
rem Utiliser le chemin pyenv‑win vers python.exe
C:\Users\maxenslecam\.pyenv\pyenv-win\versions\3.10.13\python.exe ^
    C:\Users\maxenslecam\Documents\perseus-daq-board\firmware\sensortile-allmems1-uart-fusion\scripts\uart_fusion_decoder.py ^
    --port COM3 ^
    --baud 115200 ^
    --output decoded.csv
```

## Options courantes
- `-p <port>` : périphérique série (`/dev/cu.*` sous macOS/Linux, `COMx` sous Windows).
- `-b <baud>` : vitesse de transmission (défaut : 115200).
- `-o <output>` : fichier où écrire les données décodées.

## Trouver le nom du port série

### Sur Windows
1. Ouvrez le **Gestionnaire de périphériques**.
2. Déroulez la section **Ports (COM et LPT)** et repérez le port attribué (ex. `COM3`).
3. Vous pouvez également lister les ports avec PowerShell :
   ```powershell
   Get-CimInstance Win32_SerialPort | Select-Object DeviceID, Description
   ```

### Sur macOS / Linux
1. Ouvrez un terminal.
2. Listez les ports disponibles :
   ```bash
   ls /dev/cu.*    # macOS
   ls /dev/ttyUSB* # Linux
   ```
3. Vous pouvez aussi obtenir la liste avec Python :
   ```bash
   python -c "import serial.tools.list_ports as lp; print([p.device for p in lp.comports()])"
   ```

## Commandes complètes d’exemple
Remplacez `<PORT>` par le nom du port trouvé précédemment, `<BAUD>` par la vitesse souhaitée et `<OUTPUT>` par le fichier de sortie.

```bash
# macOS / Linux (exemple avec le chemin pyenv)
/Users/maxenslecam/.pyenv/versions/3.10.13/bin/python \
    /Users/maxenslecam/Documents/perseus-daq-board/firmware/sensortile-allmems1-uart-fusion/scripts/uart_fusion_decoder.py \
    --port /dev/cu.usbserial-FT82BWWY --baud 9600 --output decoded.csv

# Windows (exemple)
C:\Users\maxenslecam\.pyenv\pyenv-win\versions\3.10.13\python.exe ^
    C:\Users\maxenslecam\Documents\perseus-daq-board\firmware\sensortile-allmems1-uart-fusion\scripts\uart_fusion_decoder.py ^
    --port COM3 --baud 9600 --output decoded.csv
```

## Script de lancement rapide
Un script d’exécution (`run_decoder.sh` pour macOS/Linux ou `run_decoder.bat` pour Windows) est fourni pour lancer le décodage avec les paramètres par défaut. Vous pouvez le modifier selon vos besoins.

---
*Ce README a été mis à jour pour inclure des exemples de lignes de commande détaillées avec le chemin complet de l’interpréteur Python.*

---

## Format brut du trame UART Fusion

Le capteur envoie des trames binaires de **72 octets** (payload) encapsulées dans un en‑tête de 6 octets et un CRC‑16‑CCITT de 2 octets. Tous les champs sont en **little‑endian**.

| Offset (octets) | Taille | Type | Nom du champ | Description |
|-----------------|--------|------|--------------|-------------|
| 0‑3   | 4 | `uint32_t` | `frame_id` | Identifiant séquentiel du trame. |
| 4‑7   | 4 | `uint32_t` | `t_ms` | Horodatage en millisecondes depuis le démarrage. |
| 8‑11  | 4 | `uint32_t` | `dt_ms` | Δt depuis la trame précédente. |
| 12‑15 | 4 | `int32_t`  | `q0` | composante w du quaternion (Q0 * 10000). |
| 16‑19 | 4 | `int32_t`  | `q1` | composante x du quaternion. |
| 20‑23 | 4 | `int32_t`  | `q2` | composante y du quaternion. |
| 24‑27 | 4 | `int32_t`  | `q3` | composante z du quaternion. |
| 28‑31 | 4 | `int32_t`  | `ax` | Accélération X en **mg** (1 mg = 0.001 g). |
| 32‑35 | 4 | `int32_t`  | `ay` | Accélération Y en mg. |
| 36‑39 | 4 | `int32_t`  | `az` | Accélération Z en mg. |
| 40‑43 | 4 | `int32_t`  | `gx` | Gyro X en **mdps** (milli‑deg/s). |
| 44‑47 | 4 | `int32_t`  | `gy` | Gyro Y en mdps. |
| 48‑51 | 4 | `int32_t`  | `gz` | Gyro Z en mdps. |
| 52‑55 | 4 | `int32_t`  | `mx` | Champ magnétique X en **mgauss**. |
| 56‑59 | 4 | `int32_t`  | `my` | Champ magnétique Y en mgauss. |
| 60‑63 | 4 | `int32_t`  | `mz` | Champ magnétique Z en mgauss. |
| 64‑65 | 2 | `int16_t`  | `temp_c_x10` | Température en décicelsius (°C × 10). |
| 66‑69 | 4 | `int32_t`  | `pressure_hpa_x100` | Pression en centi‑hPa (hPa × 100). |
| 70    | 1 | `uint8_t`  | `calib_status` | Statut de calibration du capteur. |
| 71    | 1 | `uint8_t`  | `status_flags` | Flags divers (ex : 0x0F = données valides). |

Le **header** (6 octets) est : `0xA5 0x5A` (sync), version = `0x01`, type = `0x01`, longueur du payload = `72`. Le **CRC‑16‑CCITT** (2 octets) suit le payload.

---
