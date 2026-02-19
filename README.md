# ⚽ Torneo Calcio Manager

**Gestione Torneo Calcio** è una web app per gestire un torneo di calcio completo: gironi, classifiche, fase ad eliminazione diretta, rose dei giocatori e certificati medici. È costruita con **Python / Flask** e ha un look moderno in stile dashboard sportiva.

---

## 📋 Indice

1. [Prerequisiti — Cosa installare prima](#-prerequisiti--cosa-installare-prima)
2. [Scaricare il progetto da GitHub](#-scaricare-il-progetto-da-github)
3. [Aprire il progetto nel tuo editor (IDE)](#-aprire-il-progetto-nel-tuo-editor-ide)
4. [Preparare l'ambiente Python](#-preparare-lambiente-python)
5. [Popolare il database con dati di esempio](#-popolare-il-database-con-dati-di-esempio)
6. [Avviare l'applicazione in locale](#-avviare-lapplicazione-in-locale)
7. [Come navigare nell'app — Mappa completa delle pagine](#-come-navigare-nellapp--mappa-completa-delle-pagine)
8. [Utenti di prova (seed)](#-utenti-di-prova-seed)
9. [Struttura completa dei file del progetto](#-struttura-completa-dei-file-del-progetto)
10. [Tecnologie utilizzate](#-tecnologie-utilizzate)
11. [Risoluzione problemi comuni](#-risoluzione-problemi-comuni)

---

## 🛠 Prerequisiti — Cosa installare prima

Prima di tutto devi installare alcuni programmi sul tuo PC. Se li hai già, puoi saltare questo passaggio.

### 1. Python 3.11 o superiore

Python è il linguaggio con cui gira il backend dell'app.

1. Vai su 👉 [https://www.python.org/downloads/](https://www.python.org/downloads/)
2. Scarica l'ultima versione (3.11 o superiore)
3. **IMPORTANTE:** durante l'installazione **spunta la casella "Add Python to PATH"** (è in basso nella prima schermata dell'installer)
4. Clicca "Install Now"

**Verifica** — Apri il **Terminale** (su Windows cerca "Prompt dei comandi" o "PowerShell" nel menu Start) e scrivi:

```
python --version
```

Dovresti vedere qualcosa come `Python 3.11.x` o `Python 3.12.x`. Se non funziona, prova con `python3 --version`.

### 2. Git

Git serve per scaricare il codice dal repository GitHub.

1. Vai su 👉 [https://git-scm.com/downloads](https://git-scm.com/downloads)
2. Scarica la versione per il tuo sistema operativo
3. Installa con le opzioni di default (clicca sempre "Next")

**Verifica:**

```
git --version
```

### 3. Un editor di codice (IDE)

Ti consiglio **Visual Studio Code** (VS Code), è gratuito e facilissimo da usare.

1. Vai su 👉 [https://code.visualstudio.com/](https://code.visualstudio.com/)
2. Scarica e installa
3. **(Opzionale ma consigliato)** — Installa l'estensione **Python** di Microsoft: apri VS Code → clicca sull'icona dei quadratini a sinistra (Extensions) → cerca "Python" → clicca "Install"

---

## 📥 Scaricare il progetto da GitHub

### Opzione A — Da terminale (consigliata)

1. Apri il **Terminale** (Prompt dei comandi, PowerShell, oppure il terminale integrato di VS Code)
2. Vai nella cartella dove vuoi salvare il progetto. Per esempio, per metterlo sul Desktop:
   ```
   cd Desktop
   ```
3. Clona (scarica) il repository:
   ```
   git clone <URL_DEL_REPOSITORY>
   ```
   > ⚠️ Sostituisci `<URL_DEL_REPOSITORY>` con il link reale del progetto su GitHub. Lo trovi sulla pagina GitHub del progetto cliccando il bottone verde **"Code"** e copiando il link HTTPS.
4. Entra nella cartella del progetto:
   ```
   cd <NOME_CARTELLA>
   ```

### Opzione B — Download ZIP (per chi non vuole usare Git)

1. Vai sulla pagina GitHub del progetto
2. Clicca il bottone verde **"Code"**
3. Clicca **"Download ZIP"**
4. Estrai lo ZIP nella cartella che preferisci
5. Apri il terminale e naviga nella cartella estratta

---

## 💻 Aprire il progetto nel tuo editor (IDE)

### Visual Studio Code

1. Apri VS Code
2. Clicca su **File → Apri Cartella...** (oppure `Ctrl + K` poi `Ctrl + O`)
3. Seleziona la cartella del progetto (quella che contiene `run.py`, `requirements.txt`, ecc.)
4. Clicca **"Seleziona cartella"**

Ora nella barra laterale sinistra vedrai tutti i file del progetto! 🎉

**Aprire il terminale integrato in VS Code:**
- Vai su **Terminale → Nuovo Terminale** (oppure premi `` Ctrl + ` ``)
- Si apre un terminale nella parte bassa dello schermo, già posizionato nella cartella del progetto

---

## 🐍 Preparare l'ambiente Python

Tutti i comandi seguenti vanno eseguiti nel **terminale**, dalla **cartella del progetto** (quella dove si trova `run.py`).

### Passo 1 — Creare un ambiente virtuale

L'ambiente virtuale serve a isolare le librerie di questo progetto dal resto del tuo PC.

```bash
python -m venv venv
```

Questo crea una cartella `venv/` dentro il progetto. Non devi modificarla né caricarla su GitHub.

### Passo 2 — Attivare l'ambiente virtuale

**Windows (PowerShell):**

```powershell
.\venv\Scripts\Activate.ps1
```

> ⚠️ Se ricevi un errore sulla **Execution Policy**, esegui prima:
> ```powershell
> Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
> ```
> poi riprova il comando di attivazione.

**Windows (Prompt dei comandi / cmd):**

```cmd
venv\Scripts\activate.bat
```

**macOS / Linux:**

```bash
source venv/bin/activate
```

Quando l'ambiente è attivo, vedrai `(venv)` all'inizio della riga del terminale. **Devi attivare l'ambiente ogni volta che apri un nuovo terminale.**

### Passo 3 — Installare le dipendenze

```bash
pip install -r requirements.txt
```

Questo installa tutte le librerie necessarie: Flask, SQLAlchemy, Flask-Login, ecc.

---

## 🌱 Popolare il database con dati di esempio

Il file `seed.py` crea automaticamente il database SQLite con dati di prova: squadre, gironi, partite e utenti.

```bash
python seed.py
```

Output atteso:

```
[OK] Database resettato.
[OK] Creati 16 squadre in 4 gironi.
[OK] Creati 24 partite dei gironi.
[OK] Rose: Roma (5 giocatori), Juventus (5 giocatori)
[OK] Utenti: admin/admin, org/org, caproma/caproma, capjuve/capjuve
[OK] Seed completato! Esegui: python run.py
```

> ⚠️ **Ogni volta che esegui `seed.py` il database viene RESETTATO completamente.** Tutti i dati precedenti vengono cancellati.

---

## 🚀 Avviare l'applicazione in locale

```bash
python run.py
```

Vedrai nel terminale:

```
 * Running on http://0.0.0.0:5000
 * Debug mode: on
```

**Apri il browser** e vai su:

### 👉 [http://localhost:5000](http://localhost:5000)

L'app è ora raggiungibile! 🎉

Per **fermare il server**, torna nel terminale e premi `Ctrl + C`.

---

## 🗺 Come navigare nell'app — Mappa completa delle pagine

L'app ha 4 aree principali, ognuna con le sue pagine. Qui sotto trovi la descrizione dettagliata di ciascuna.

```
📦 Pagine dell'Applicazione
│
├── 🌍 AREA PUBBLICA (visibile da tutti, anche senza login)
│   ├── Classifiche Gironi ........... /
│   ├── Dettaglio Girone ............. /group/A  (o B, C, D)
│   ├── Dettaglio Partita Pubblica ... /match/<id>
│   └── Tabellone Fase Finale ....... /tournament
│
├── 🔐 AUTENTICAZIONE
│   ├── Login ........................ /auth/login
│   └── Logout ....................... /auth/logout
│
├── 🛡️ AREA ADMIN (solo admin e organizzatore)
│   ├── Dashboard Admin .............. /admin/
│   ├── Gestione Partite ............. /admin/matches
│   ├── Dettaglio Partita Admin ...... /admin/match/<id>
│   ├── Gestione Rose ................ /admin/roster  e  /admin/roster/<id>
│   └── Gestione Utenti .............. /admin/users
│
└── 👤 AREA GIOCATORE (solo capitano)
    └── Gestione Rosa Squadra ........ /player/roster
```

---

### 🌍 AREA PUBBLICA

Queste pagine sono accessibili da **chiunque**, senza bisogno di effettuare il login.

---

#### 📊 Classifiche Gironi — `http://localhost:5000/`

- È la **homepage** dell'applicazione
- Mostra le classifiche dei **4 gironi** (A, B, C, D)
- Per ogni girone viene visualizzata una tabella con:
  - Nome squadra
  - Partite giocate (G)
  - Vittorie (V), Pareggi (P), Sconfitte (S)
  - Goal fatti (GF), Goal subiti (GS), Differenza reti (DR)
  - Punti (Pt)
- Le squadre sono ordinate automaticamente secondo le regole ufficiali: **Punti** → **Scontri diretti** → **Differenza reti** → **Goal segnati**
- Cliccando sul nome di un girone si può accedere al **dettaglio del girone**

---

#### 📋 Dettaglio Girone — `http://localhost:5000/group/A`

- Mostra la classifica dettagliata di un **singolo girone** (A, B, C o D)
- Sotto la classifica elenca **tutte le partite** di quel girone
- Per ogni partita si vedono:
  - Le due squadre
  - Il risultato (se la partita è stata giocata)
  - Lo stato (da giocare / giocata)
- Cliccando su una partita si accede al **dettaglio partita pubblica**

---

#### ⚽ Dettaglio Partita Pubblica — `http://localhost:5000/match/<id>`

- Mostra il **dettaglio completo** di una singola partita
- Visualizza:
  - Le due squadre con il risultato finale
  - L'elenco dei **marcatori** con il minuto del gol (per ciascuna squadra)
  - Il **Man of the Match** (MVP), se assegnato
- È una vista di sola lettura (nessuna modifica possibile)

---

#### 🏆 Tabellone Fase Finale — `http://localhost:5000/tournament`

- Mostra il **bracket** (tabellone) della fase ad eliminazione diretta
- Visualizza:
  - **Quarti di finale** (4 partite)
  - **Semifinali** (2 partite)
  - **Finale** (1 partita)
- Le partite dei quarti vengono generate automaticamente dall'admin dopo la fine dei gironi seguendo lo schema:
  - Q1: 1ª del Girone A vs 2ª del Girone B
  - Q2: 1ª del Girone C vs 2ª del Girone D
  - Q3: 1ª del Girone B vs 2ª del Girone A
  - Q4: 1ª del Girone D vs 2ª del Girone C
- Se la fase finale non è ancora stata generata, la pagina sarà vuota

---

### 🔐 AUTENTICAZIONE

---

#### 🔑 Login — `http://localhost:5000/auth/login`

- Schermata di accesso con **username** e **password**
- Dopo il login verrai reindirizzato alla homepage
- La navbar in alto cambia dinamicamente in base al tuo ruolo
- Se sei già loggato e provi ad accedere alla pagina di login, verrai reindirizzato automaticamente alla homepage

---

#### 🚪 Logout — `http://localhost:5000/auth/logout`

- Effettua il logout e ti riporta alla homepage
- Si accede dal pulsante **"Logout"** nella navbar

---

### 🛡️ AREA ADMIN

Queste pagine sono accessibili solo da utenti con ruolo **admin** o **organizzatore**. Se provi ad accedervi senza i permessi giusti, verrai reindirizzato alla homepage con un messaggio di errore.

---

#### 📊 Dashboard Admin — `http://localhost:5000/admin/`

- Pannello di controllo principale per admin e organizzatori
- Mostra le **statistiche rapide** del torneo:
  - Numero totale di squadre
  - Numero totale di partite
  - Partite giocate vs partite da giocare
  - Partite dei gironi vs partite della fase finale
- Contiene il **pulsante "Genera Fase Finale"** (solo per admin) per creare automaticamente i quarti di finale quando tutti i gironi sono completati

---

#### 📝 Gestione Partite — `http://localhost:5000/admin/matches`

- Elenco di **tutte le partite** del torneo
- Suddivise in:
  - **Partite dei gironi** (raggruppate per girone A, B, C, D)
  - **Partite della fase finale** (quarti, semifinali, finale)
- Per ogni partita si vedono le squadre , il risultato e lo stato
- Cliccando su una partita si accede al **dettaglio partita admin** per inserire risultati

---

#### ⚙️ Dettaglio Partita Admin — `http://localhost:5000/admin/match/<id>`

- Pagina centrale per **inserire i risultati** di una partita
- Funzionalità disponibili:
  - **Aggiungere un gol**: selezionare il marcatore dalla rosa della squadra, indicare la squadra e il minuto
  - **Rimuovere un gol**: cancellare un gol inserito per errore
  - **Assegnare MVP** (Man of the Match): selezionare il miglior giocatore della partita
  - **Segnare come giocata (0-0)**: per registrare uno 0-0 senza inserire marcatori
- Il punteggio viene **ricalcolato automaticamente** in base ai gol inseriti
- Le liste dei giocatori per i gol e l'MVP sono prese dalla **rosa** di ciascuna squadra

---

#### 👥 Gestione Rose (Admin) — `http://localhost:5000/admin/roster`

- Permette all'admin di gestire le **rose dei giocatori** di **tutte** le squadre
- **Prima schermata** (`/admin/roster`): lista di tutte le squadre, clicca su una per gestirla
- **Schermata di dettaglio** (`/admin/roster/<team_id>`): mostra i giocatori della squadra selezionata con:
  - Nome e cognome
  - Data di scadenza della visita medica
  - File del certificato medico (se caricato)
  - Stato della visita (valida ✅ / scaduta ❌)
- L'admin può:
  - **Aggiungere** un nuovo giocatore con nome, cognome, scadenza visita e certificato (PDF o immagine)
  - **Eliminare** un giocatore dalla rosa (viene cancellato anche il file caricato)

---

#### 👤 Gestione Utenti — `http://localhost:5000/admin/users`

- Pagina riservata **esclusivamente all'admin**
- Permette di:
  - **Creare nuovi utenti**: indicando username, password, ruolo e (per i giocatori/capitani) la squadra di appartenenza
  - **Eliminare utenti** esistenti
- Mostra la lista di tutti gli utenti con il loro ruolo e la squadra assegnata
- Ruoli disponibili:
  - **admin** — accesso completo
  - **organizzatore** — può gestire partite e risultati
  - **capitano** — può gestire la rosa della propria squadra
  - **giocatore** — ruolo base, può solo visualizzare

---

### 👤 AREA GIOCATORE (Capitano)

---

#### 📋 Gestione Rosa Squadra — `http://localhost:5000/player/roster`

- Accessibile solo dagli utenti con ruolo **capitano**
- Mostra la rosa della **propria squadra** (quella associata al proprio account)
- Il capitano può:
  - **Aggiungere giocatori** con: nome, cognome, scadenza visita medica, file del certificato medico
  - **Rimuovere giocatori** dalla rosa
- Per ogni giocatore nella rosa si vede:
  - Nome e cognome
  - Scadenza della visita medica
  - Stato della visita (valida / scaduta)
  - Download del certificato medico (se caricato)

---

## 👥 Utenti di prova (seed)

Dopo aver eseguito `python seed.py`, puoi accedere con questi account:

| Username    | Password    | Ruolo          | Squadra    | Cosa può fare                              |
|-------------|-------------|----------------|------------|--------------------------------------------|
| `admin`     | `admin`     | Admin          | —          | Tutto: utenti, rose, partite, fase finale  |
| `org`       | `org`       | Organizzatore  | —          | Dashboard admin, inserire risultati        |
| `caproma`   | `caproma`   | Capitano       | Roma       | Gestire la rosa della Roma                 |
| `capjuve`   | `capjuve`   | Capitano       | Juventus   | Gestire la rosa della Juventus             |

> 💡 **Consiglio**: per esplorare tutte le funzionalità, inizia con l'utente **admin**.

---

## 📁 Struttura completa dei file del progetto

```
📦 project_root/
│
├── 📄 run.py                    # 👉 Punto di ingresso: avvia il server Flask
├── 📄 config.py                 # Configurazioni (dev con SQLite, prod con PostgreSQL)
├── 📄 seed.py                   # Popola il DB con dati di esempio
├── 📄 requirements.txt          # Lista delle librerie Python necessarie
├── 📄 Dockerfile                # Per il deploy con Docker (non serve per uso locale)
├── 📄 .gitignore                # File ignorati da Git
│
├── 📂 app/                      # 🏗️ Cartella principale dell'applicazione
│   ├── 📄 __init__.py           # Application Factory (crea l'app Flask)
│   ├── 📄 models.py             # Modelli del database (User, Team, Match, Goal, RosterPlayer)
│   ├── 📄 extensions.py         # Inizializzazione database e login manager
│   │
│   ├── 📂 blueprints/           # 🔀 Moduli separati per ogni area dell'app
│   │   ├── 📂 auth/             # Autenticazione (login, logout)
│   │   │   └── routes.py        # Route di login/logout + decoratore @role_required
│   │   ├── 📂 admin/            # Pannello amministratore
│   │   │   └── routes.py        # Dashboard, gestione partite, rose utenti, generazione playoff
│   │   ├── 📂 main/             # Area pubblica
│   │   │   └── routes.py        # Homepage, classifiche, tabellone, dettaglio partite
│   │   └── 📂 player/           # Area giocatore / capitano
│   │       └── routes.py        # Gestione rosa della propria squadra
│   │
│   ├── 📂 templates/            # 🎨 Pagine HTML (Jinja2)
│   │   ├── 📄 base.html         # Layout master con navbar dinamica e footer
│   │   ├── 📂 auth/
│   │   │   └── login.html       # Pagina di login
│   │   ├── 📂 public/
│   │   │   ├── standings.html       # Classifiche dei 4 gironi (homepage)
│   │   │   ├── group_detail.html    # Dettaglio singolo girone
│   │   │   ├── match_detail.html    # Dettaglio partita (vista pubblica)
│   │   │   └── tournament_tree.html # Tabellone fase finale
│   │   ├── 📂 admin/
│   │   │   ├── dashboard.html       # Dashboard admin con statistiche
│   │   │   ├── match_manager.html   # Lista partite da gestire
│   │   │   ├── match_detail.html    # Inserimento risultati partita
│   │   │   ├── roster.html          # Gestione rose di tutte le squadre
│   │   │   └── users.html           # Gestione utenti
│   │   └── 📂 player/
│   │       ├── my_team.html         # (Info squadra del giocatore)
│   │       └── roster.html          # Gestione rosa (lato capitano)
│   │
│   └── 📂 static/
│       └── 📄 style.css         # CSS personalizzato (look premium/dark mode)
│
├── 📂 instance/
│   └── 📄 torneo.db             # Database SQLite (creato automaticamente)
│
└── 📂 uploads/                  # File caricati (certificati medici)
```

---

## 🧰 Tecnologie utilizzate

| Tecnologia         | Utilizzo                                         |
|--------------------|--------------------------------------------------|
| **Python 3.11+**   | Linguaggio backend                               |
| **Flask**          | Framework web (con Application Factory Pattern)  |
| **SQLAlchemy**     | ORM per il database                              |
| **Flask-Login**    | Gestione sessioni e autenticazione               |
| **SQLite**         | Database locale (file `torneo.db`)               |
| **Jinja2**         | Template engine per le pagine HTML                |
| **Bootstrap 5.3**  | Framework CSS per il design responsive            |
| **FontAwesome**    | Icone nella UI                                   |
| **Google Fonts**   | Font "Inter" per un look moderno                  |

---

## 🆘 Risoluzione problemi comuni

### ❌ `python` non viene riconosciuto come comando

- Assicurati di aver installato Python **con l'opzione "Add to PATH"** selezionata
- Su Windows prova con `py` al posto di `python`
- Su macOS/Linux prova con `python3`

### ❌ Errore di Execution Policy su PowerShell

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### ❌ `ModuleNotFoundError: No module named 'flask'`

- Assicurati di aver **attivato l'ambiente virtuale** (devi vedere `(venv)` nel terminale)
- Se non lo vedi, esegui di nuovo il comando di attivazione (vedi sezione sopra)

### ❌ L'app non si apre nel browser

- Controlla che il server sia avviato (nel terminale devi vedere `Running on http://...`)
- Prova a navigare su `http://127.0.0.1:5000` (invece di `localhost`)

### ❌ Errore di porta già in uso

Se la porta 5000 è già occupata, puoi cambiarla modificando `run.py`:

```python
app.run(debug=True, host='0.0.0.0', port=8080)
```

### ❌ Il database è vuoto o non funziona

- Esegui `python seed.py` per ricreare il database da zero con i dati di esempio

---

## 🤝 Flusso di lavoro consigliato

1. **Clona** il repository da GitHub
2. **Apri** la cartella in VS Code
3. **Crea e attiva** l'ambiente virtuale
4. **Installa** le dipendenze con `pip install -r requirements.txt`
5. **Popola** il database con `python seed.py`
6. **Avvia** il server con `python run.py`
7. **Apri** `http://localhost:5000` nel browser
8. **Accedi** con `admin / admin` per esplorare tutte le funzionalità
9. **Modifica** i file HTML in `app/templates/` per cambiare l'interfaccia
10. **Modifica** il CSS in `app/static/style.css` per personalizzare il look
11. Il server si **ricarica automaticamente** quando salvi un file (grazie al debug mode) 🔄

---

> 💬 **Hai bisogno di aiuto?** Apri una **Issue** su GitHub descrivendo il problema che hai riscontrato.
