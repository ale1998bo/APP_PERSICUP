Prompt per Antigravity: Football Tournament Manager (Flask Enterprise Edition)
1. Ruolo e Contesto
Agisci come un Senior Python Backend & Frontend Architect. Stai sviluppando "Gestione Torneo Calcio", una web app SaaS completa, scalabile e sicura.
Il focus è su un'architettura modulare (Clean Code), sicurezza RBAC (Role-Based Access Control) e una UI Premium/Modern responsive.

2. Stack Tecnologico
Backend: Python 3.11+, Flask (Factory Pattern), SQLAlchemy (ORM).

Auth: Flask-Login, Werkzeug Security.

Frontend: Bootstrap 5.3 (ultima versione), Jinja2, FontAwesome (per icone).

Database: SQLite (dev) / PostgreSQL (prod - GCP).

Container: Docker.

3. Architettura del Progetto (File Puliti)
Voglio che il codice sia rigorosamente suddiviso utilizzando i Flask Blueprints. Non voglio tutto in un file. Segui questa struttura:

Plaintext
/project_root
  /app
    __init__.py          # Application Factory (create_app)
    models.py            # Tutti i modelli DB (User, Team, Match)
    extensions.py        # Inizializzazione db, login_manager
    /blueprints
       /auth             # routes.py (login, logout)
       /admin            # routes.py (gestione risultati, creazione match)
       /main             # routes.py (visualizzazione pubblica, classifiche)
       /player           # routes.py (dashboard personale)
    /templates
       base.html         # Layout master (Navbar dinamica)
       /auth             # login.html
       /admin            # dashboard.html, match_manager.html
       /public           # standings.html, tournament_tree.html
       /player           # my_team.html
    /static
       style.css         # CSS personalizzato per look "Premium"
  config.py              # Configurazioni (Dev, Prod)
  run.py                 # Entry point
  Dockerfile
  requirements.txt
4. Requisiti Funzionali & Logica
A. Autenticazione e RBAC
Implementa un decoratore personalizzato @role_required(*roles).

Ruoli: admin, organizzatore, giocatore.

Logica User: L'utente giocatore DEVE essere collegato a un Team.

B. Logica Torneo (Core)
Gironi: 4 Gironi (A, B, C, D) da 4 squadre.

Calcolo Classifica (get_standings):

Ordina per: Punti > Scontri Diretti (Head-to-Head) > Differenza Reti > Goal Segnati.

Nota: La logica degli scontri diretti è complessa, assicurati di implementarla correttamente in Python.

Fase Finale (Automazione):

Crea una funzione generate_playoffs() accessibile solo agli admin.

Legge le classifiche finali e genera i match dei Quarti secondo lo schema:

Q1: 1ª A vs 2ª B

Q2: 1ª C vs 2ª D

Q3: 1ª B vs 2ª A

Q4: 1ª D vs 2ª C

5. UI/UX "Premium" (Frontend Requirements)
Non voglio il solito Bootstrap standard. L'app deve sembrare una dashboard sportiva professionale (stile app scommesse o livescore).

Navbar: Dinamica.

Guest: Login.

Admin/Org: "Admin Panel", "Inserisci Risultati", "Genera Fase Finale".

Giocatore: "La mia Squadra" (evidenziato), "Logout".

Design System:

Usa Cards con ombreggiature soffuse (shadow-sm) e bordi arrotondati (rounded-4) per le partite.

Colori: Usa una palette scura/elegante per l'header (es. Midnight Blue o Dark Slate) con accenti vibranti (es. Verde Smeraldo per "Vittoria", Rosso per "Sconfitta").

Mobile: Le tabelle dei gironi devono essere responsive (su mobile impilate o scrollabili orizzontalmente senza rompere il layout).

Dashboard Giocatore: Deve mostrare un "Hero Banner" con il logo della squadra e le prossime partite in evidenza.

6. Richiesta di Output
Genera il codice passo dopo passo, iniziando dai Models e dalla Configurazione, poi i Blueprints, e infine i Templates. Assicurati che il codice sia pronto per la produzione.

Cosa ho migliorato rispetto alla tua bozza:
Architettura a Blueprints: Ho specificato esplicitamente la struttura delle cartelle. Senza questo, l'AI tende a mettere troppa logica nelle routes rendendo il codice "sporco".

Specifiche UI: Ho tradotto "Premium" in termini tecnici: shadow-sm, rounded-4, palette colori e "Hero Banner". Questo aiuta l'AI a scrivere CSS e classi Bootstrap migliori.

Application Factory: Ho chiesto di usare create_app. Questo è fondamentale se vuoi scalare l'app o fare test in futuro.

Scontri Diretti: Ho evidenziato la difficoltà del calcolo "Head-to-Head" (scontri diretti) per forzare l'AI a prestare più attenzione a quella funzione specifica, che spesso viene sbagliata.