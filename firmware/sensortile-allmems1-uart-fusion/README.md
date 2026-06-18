# README – PERSEUS DAQ Board – UART Fusion Stream

## 📖 Présentation du projet

Ce dépôt contient le **firmware** du **PERSEUS DAQ board** basé sur le MCU **STM32L476JG** (SensorTile). L’objectif principal est de transmettre, via **UART5**, un flux binaire de télémétrie (quaternion, accéléromètre, gyroscope, magnétomètre, température, pression, …) décodable en temps réel par un script Python.

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

## 📄 Licence
Ce projet est publié sous la licence **BSD‑3‑Clause**. Voir le fichier `LICENSE` pour les détails.

---

## 👨‍💻 Contributeurs
- **Maxenslecam** – développeur principal (firmware, script Python).
- Contributions externes bienvenues ! Veuillez ouvrir une *pull‑request* et suivre les conventions de codage du projet.

---

*© 2026 PERSEUS DAQ Board – Tous droits réservés.*
