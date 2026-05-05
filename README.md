# ⛓ ElectrumShield

**Verifica l'autenticità dell'AppImage di Electrum in pochi click — senza toccare il terminale.**

![Python](https://img.shields.io/badge/Python-3.8%2B-blue?logo=python&logoColor=white)
![Platform](https://img.shields.io/badge/Platform-Linux-orange?logo=linux&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)
![GPG](https://img.shields.io/badge/GPG-Verified-brightgreen?logo=gnu-privacy-guard)

---

## 🔐 Cos'è ElectrumShield?

ElectrumShield è un'applicazione desktop con interfaccia grafica (Tkinter) che automatizza completamente la verifica delle **firme GPG** dell'AppImage di [Electrum](https://electrum.org) per Linux.

Electrum è uno dei wallet Bitcoin più usati e rispettati al mondo. Prima di eseguirlo, è fondamentale verificare che il file scaricato sia **autentico e non manomesso**. Questa operazione normalmente richiede diversi comandi da terminale — ElectrumShield la rende accessibile a tutti con un'interfaccia semplice e guidata.

---

## ✨ Funzionalità

- **Download automatico** dell'AppImage e del file firma `.asc` direttamente da `electrum.org`
- **Importazione automatica** delle chiavi GPG dei 4 sviluppatori ufficiali di Electrum da GitHub
- **Verifica con un click** — nessun comando da terminale necessario
- **Risultato chiaro** — popup ✅ FIRMA VALIDA o ❌ FIRMA NON VALIDA
- **Log in tempo reale** colorato e dettagliato
- **Supporto multilingua** per gpg (italiano, inglese e altri)
- **Compatibile con file già scaricati** — puoi selezionare un AppImage esistente e lo script scarica automaticamente il `.asc` nella stessa cartella

---

## 🛡️ Sviluppatori verificati

Lo script importa e verifica le chiavi GPG ufficiali di:

| Sviluppatore | Fingerprint chiave primaria |
|---|---|
| ThomasV | `6694 D8DE 7BE8 EE56 31BE D950 2BD5 824B 7F94 70E6` |
| SomberNight | `0EED CFD5 CAFB 4590 6734 9B23 CA9E EEC4 3DF9 11DC` |
| Emzy | `9EDA FF80 E080 6596 04F4 A76B 2EBB 056F D847 F8A7` |
| felixb_f321x | `AA0B C682 4B39 7BBA 9977 6E15 7ED8 D82B 3719 2688` |

> Le chiavi vengono scaricate direttamente dal repository ufficiale di Electrum su GitHub e importate nel keyring GPG del tuo utente (`~/.gnupg/`).

---

## 📋 Requisiti

- Linux (qualsiasi distribuzione)
- Python 3.8 o superiore
- `python3-tk` (Tkinter)
- `gnupg` (gpg)

---

## 🚀 Installazione e avvio

### 1. Installa le dipendenze

```bash
sudo apt install python3-tk gnupg
```

> Su Fedora/RHEL: `sudo dnf install python3-tkinter gnupg2`  
> Su Arch: `sudo pacman -S tk gnupg`

### 2. Clona il repository

```bash
git clone https://github.com/tuousername/electrumshield.git
cd electrumshield
```

### 3. Avvia lo script

```bash
python3 electrum_shield.py
```

---

## 🖥️ Come si usa

Il tool guida l'utente in **4 passi**:

**Passo 1 — Cartella di salvataggio**  
Scegli dove salvare i file scaricati (default: `~/Downloads`).

**Passo 2 — Scarica i file**  
Clicca *"Scarica AppImage + .asc"* per scaricare automaticamente entrambi i file da `electrum.org`.  
Oppure clicca *"Usa file già presenti"* se hai già l'AppImage: il `.asc` verrà trovato o scaricato automaticamente nella stessa cartella.

**Passo 3 — Importa le chiavi GPG**  
Clicca *"Importa tutte le chiavi"*: le 4 chiavi ufficiali vengono scaricate da GitHub e salvate nel tuo keyring GPG. Questa operazione va fatta **una sola volta** per sistema.

**Passo 4 — Verifica**  
Clicca *"Verifica ora"* e attendi il risultato:
- ✅ **FIRMA VALIDA** → il file è autentico, puoi usarlo in sicurezza
- ❌ **FIRMA NON VALIDA** → il file è sospetto, non eseguirlo

---

## ⚠️ Note sulla sicurezza

- Il warning GPG *"questa chiave non è certificata con una firma fidata"* è **completamente normale** e non indica alcun problema. Significa solo che non hai firmato personalmente quelle chiavi con il web of trust.
- La verifica si basa sul **return code di gpg** (universale) e non sul testo dell'output, quindi funziona correttamente in qualsiasi lingua di sistema.
- Per la massima sicurezza, puoi verificare manualmente le fingerprint mostrate nel log confrontandole con quelle pubblicate su [electrum.org](https://electrum.org).
- ElectrumShield scarica i file esclusivamente da `electrum.org` e `raw.githubusercontent.com/spesmilo/electrum` — mai da fonti di terze parti.

---

## 📁 Struttura del progetto

```
electrumshield/
├── electrum_shield.py   # Script principale
└── README.md            # Questa guida
```

---

## 📄 Licenza

Distribuito sotto licenza **MIT**. Vedi il file `LICENSE` per i dettagli.

---

## 🙏 Crediti

- [Electrum](https://electrum.org) — il wallet Bitcoin che questo tool protegge
- Sviluppatori Electrum: ThomasV, SomberNight, Emzy, felixb_f321x

---

> **Disclaimer:** ElectrumShield è un tool indipendente, non affiliato al progetto Electrum. Usalo sempre scaricando i file originali da `electrum.org`.
