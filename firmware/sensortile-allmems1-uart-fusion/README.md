# README – PERSEUS DAQ Board – UART Fusion Stream

## 📖 Présentation du projet

Ce dépôt contient le **firmware** du **PERSEUS DAQ board** basé sur le MCU **STM32L476JG** (SensorTile). L’objectif principal est de transmettre, via **UART5**, un flux binaire de télémétrie (quaternion, accéléromètre, gyroscope, magnétomètre, température, pression, …) décodable en temps réel par un script Python. Le terme **DAQ** signifie *Data Acquisition* – acquisition de données en temps réel depuis les capteurs.

### Fonctionnalités clés
- Envoi périodique d’une trame UART de **72 octets** de données utiles.
- CRC‑CCITT (polynôme 0x1021) pour la détection d’erreurs.
- Transmission **non bloquante** grâce à `HAL_UART_Transmit_IT`.
- Décodage côté PC via `scripts/uart_fusion_decoder.py`.

---

## 🛠️ Prérequis

| Élément | Version recommandée |
|---------|-------------------|
| **STM32CubeIDE** | 1.14.0 ou plus (contient GNU‑ARM) |
| **Make** (optionnel) | GNU make 4.4 |
| **Python** | 3.10 (géré avec `pyenv`) |
| **pyserial** | `pip install pyserial` |
| **ST‑Link** (ou programmateur équivalent) | pour flasher le MCU |

---

## 📂 Structure du dépôt
```
├─ Projects/STM32L476JG-SensorTile/Applications/ALLMEMS1/   # Firmware C
│   ├─ Inc/                     # headers
│   └─ Src/                     # sources
│       └─ uart_fusion_stream.c   # implémentation UART Fusion
├─ scripts/                     # outils côté PC
│   └─ uart_fusion_decoder.py   # script de décodage
├─ .cubeide-workspace/…        # configuration CubeIDE (ignorée dans le repo)
├─ Makefile (optionnel)        # build simple en ligne de commande
└─ README.md                   # <‑‑ ce fichier (global)
```

---

## 🚀 Compilation du firmware

### 1️⃣ Via STM32CubeIDE (recommandé)
1. Ouvrez **CubeIDE** (`open /Applications/STM32CubeIDE.app`).
2. *File → Open Projects from File System* → pointez sur le répertoire `Projects/STM32L476JG-SensorTile/Applications/ALLMEMS1`.
3. Sélectionnez la configuration **Debug** (ou **Release**) et cliquez **Build** (⌘ B).
4. Le binaire `STM32L476JG-SensorTile_ALLMEMS1.elf` apparaît dans le sous‑dossier `Debug/`.

### 2️⃣ En ligne de commande (Makefile)
```bash
cd /Users/maxenslecam/Documents/perseus-daq-board/firmware/sensortile-allmems1-uart-fusion
make      # génère .elf, .bin et .map
```
> Le Makefile utilise `arm-none-eabi-gcc` fourni par CubeIDE ; assurez‑vous que le répertoire `bin` est dans votre `$PATH`.

### 3️⃣ Flash du binaire
```bash
# avec ST‑Link (ou via CubeIDE → Run)
st-flash write Debug/STM32L476JG-SensorTile_ALLMEMS1.bin 0x8000000
```
Redémarrez la carte (bouton Reset) après le flash.

---

## 📡 Activation du flux UART Fusion
1. Ouvrez `ALLMEMS1_config.h` et assurez‑vous que la macro est activée :
   ```c
   #define ALLMEMS1_ENABLE_UART_FUSION_STREAM 1
   ```
2. (Facultatif) Ajoutez un appel périodique dans `main.c` pour tester :
   ```c
   UART_FusionStream_SendFrame(...);
   ```
3. Re‑compilez et re‑flashez.

---

## 🐍 Décodage côté PC avec le script Python
### Installation des dépendances
```bash
/Users/maxenslecam/.pyenv/versions/3.10.13/bin/python -m pip install --upgrade pip
/Users/maxenslecam/.pyenv/versions/3.10.13/bin/python -m pip install pyserial
```
### Exécution
```bash
/Users/maxenslecam/.pyenv/versions/3.10.13/bin/python \
    /Users/maxenslecam/Documents/perseus-ddaq-board/firmware/sensortile-allmems1-uart-fusion/scripts/uart_fusion_decoder.py \
    --port /dev/cu.usbserial-FT82BWWY   # <-- adaptez le nom du périphérique
```
Le script affichera chaque trame décodée :
```
--- Frame ---
ID: 12, time: 5243 ms, dt: 100 ms
Quaternion: (0, 0, 0, 0)
Accel (mg): (0, 0, 0)
Gyro (mdps): (0, 0, 0)
Mag (mgauss): (0, 0, 0)
Temp: 25.0 °C
Pressure: 1013.00 hPa
Calib status: 0x1F, flags: 0x00
```
---

## 🎨 Design & bonnes pratiques
- **Modularité** : le code UART est isolé derrière `uart_fusion_stream.h` ; il suffit d’inclure le header et d’appeler `UART_FusionStream_Init()` et `UART_FusionStream_SendFrame()`.
- **Robustesse** : le CRC‑CCITT garantit l’intégrité du flux.
- **Non‑bloquant** : l’usage de `HAL_UART_Transmit_IT` laisse l’application principale poursuivre son exécution.
- **Extensible** : on peut augmenter la trame (nouveaux capteurs) en modifiant `UART_FUSION_FRAME_PAYLOAD_LEN` et le décodage côté Python.

---

## 📡 Format brut de la trame UART (RS422)

Le MCU transmet les données sur le port **UART5 (RS422)**. Chaque trame possède la structure suivante (en **little‑endian**) :

- **Header (6 octets)**
  - Octet 0‑1 : `0xA5 0x5A` – séquence de synchronisation.
  - Octet 2    : version (`0x01`).
  - Octet 3    : type (`0x01` – télémétrie).
  - Octet 4‑5 : longueur du payload (`0x48` = 72 octets).

- **Payload (72 octets)**

| Octets | Taille | Type | Champ | Description |
|--------|--------|------|-------|-------------|
| 0‑3    | 4 | `uint32_t` | `frame_id` | Identifiant séquentiel du trame. |
| 4‑7    | 4 | `uint32_t` | `t_ms` | Horodatage en millisecondes depuis le démarrage. |
| 8‑11   | 4 | `uint32_t` | `dt_ms` | Δt depuis la trame précédente. |
| 12‑15  | 4 | `int32_t`  | `q0` | Quaternion w × 10000. |
| 16‑19  | 4 | `int32_t`  | `q1` | Quaternion x × 10000. |
| 20‑23  | 4 | `int32_t`  | `q2` | Quaternion y × 10000. |
| 24‑27  | 4 | `int32_t`  | `q3` | Quaternion z × 10000. |
| 28‑31  | 4 | `int32_t`  | `ax` | Accélération X en **mg** (1 mg = 0.001 g). |
| 32‑35  | 4 | `int32_t`  | `ay` | Accélération Y en mg. |
| 36‑39  | 4 | `int32_t`  | `az` | Accélération Z en mg. |
| 40‑43  | 4 | `int32_t`  | `gx` | Gyro X en **mdps** (milli‑deg/s). |
| 44‑47  | 4 | `int32_t`  | `gy` | Gyro Y en mdps. |
| 48‑51  | 4 | `int32_t`  | `gz` | Gyro Z en mdps. |
| 52‑55  | 4 | `int32_t`  | `mx` | Champ magnétique X en **mgauss**. |
| 56‑59  | 4 | `int32_t`  | `my` | Champ magnétique Y en mgauss. |
| 60‑63  | 4 | `int32_t`  | `mz` | Champ magnétique Z en mgauss. |
| 64‑65  | 2 | `int16_t`  | `temp_c_x10` | Température × 10 (°C). |
| 66‑69  | 4 | `int32_t`  | `pressure_hpa_x100` | Pression × 100 (hPa). |
| 70     | 1 | `uint8_t`  | `calib_status` | Statut de calibration du capteur. |
| 71     | 1 | `uint8_t`  | `status_flags` | Flags divers (ex. 0x0F = données valides). |

- **CRC (2 octets)**
  - Calculé sur le header (à partir du byte 2) + payload, avec le polynôme `0x1021` et le seed `0xFFFF` (CRC‑16‑CCITT).

Cette structure occupe **80 octets** au total : 6 octets d’en‑tête, 72 octets de payload et 2 octets de CRC. Le protocole RS422 assure une transmission fiable sur de longues distances avec blindage.

---

## 📄 Licence
Ce projet est publié sous la licence **BSD‑3‑Clause**. Voir le fichier `LICENSE` pour les détails.

---

## 👨‍💻 Contributeurs
- **Maxenslecam** – développeur principal (firmware, script Python).
- Contributions externes bienvenues ! Veuillez ouvrir une *pull‑request* et suivre les conventions de codage du projet.

---

*© 2026 PERSEUS DAQ Board – Tous droits réservés.*
