# Deploy Persicup su Google Cloud Run

Guida passo-passo per fare il deploy e aggiornare l'app **Persicup** su Google Cloud Run.

- **Progetto GCP**: `persicup-a49df`
- **Region**: `europe-west1`
- **Service**: `persicup`
- **URL**: https://persicup-214688066540.europe-west1.run.app
- **Service Account runtime**: `persicup-runtime@persicup-a49df.iam.gserviceaccount.com`

---

## 1. Setup iniziale (UNA SOLA VOLTA)

Questi comandi sono già stati eseguiti. Non rifarli, sono qui solo come riferimento se mai dovessi ricreare da zero il progetto.

### 1.1 Login e selezione progetto

```powershell
gcloud auth login
gcloud config set project persicup-a49df
gcloud auth application-default set-quota-project persicup-a49df
```

### 1.2 Abilita le API GCP

```powershell
gcloud services enable run.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com firestore.googleapis.com storage.googleapis.com secretmanager.googleapis.com
```

### 1.3 Crea il service account runtime

```powershell
gcloud iam service-accounts create persicup-runtime --display-name="Persicup Cloud Run"
```

### 1.4 Dai i permessi al service account

```powershell
gcloud projects add-iam-policy-binding persicup-a49df --member="serviceAccount:persicup-runtime@persicup-a49df.iam.gserviceaccount.com" --role="roles/datastore.user"
gcloud projects add-iam-policy-binding persicup-a49df --member="serviceAccount:persicup-runtime@persicup-a49df.iam.gserviceaccount.com" --role="roles/storage.objectAdmin"
gcloud projects add-iam-policy-binding persicup-a49df --member="serviceAccount:persicup-runtime@persicup-a49df.iam.gserviceaccount.com" --role="roles/iam.serviceAccountTokenCreator"
```

Cosa fanno:
- `datastore.user` → lettura/scrittura Firestore (utenti, partite, classifiche)
- `storage.objectAdmin` → upload/delete file nel bucket GCS
- `serviceAccountTokenCreator` → firmare i signed URL delle immagini

### 1.5 Crea il secret per SECRET_KEY

```powershell
$bytes = New-Object byte[] 32
[Security.Cryptography.RandomNumberGenerator]::Create().GetBytes($bytes)
$key = [Convert]::ToBase64String($bytes)
$tmp = [System.IO.Path]::GetTempFileName()
[System.IO.File]::WriteAllText($tmp, $key)
gcloud secrets create flask-secret-key --data-file=$tmp
Remove-Item $tmp
```

Dai accesso al service account:

```powershell
gcloud secrets add-iam-policy-binding flask-secret-key --member="serviceAccount:persicup-runtime@persicup-a49df.iam.gserviceaccount.com" --role="roles/secretmanager.secretAccessor"
```

### 1.6 Primo deploy (lungo, ~10 minuti)

```powershell
gcloud run deploy persicup --source . --region europe-west1 --platform managed --allow-unauthenticated --service-account persicup-runtime@persicup-a49df.iam.gserviceaccount.com --set-env-vars "FLASK_CONFIG=prod,FIREBASE_PROJECT_ID=persicup-a49df,GCS_BUCKET_NAME=persicup-a49df.firebasestorage.app" --set-secrets SECRET_KEY=flask-secret-key:latest --memory 512Mi --cpu 1 --min-instances 0 --max-instances 5
```

**IMPORTANTE — in PowerShell le virgole vanno DENTRO le virgolette**: `"FLASK_CONFIG=prod,FIREBASE_PROJECT_ID=..."`. Altrimenti PowerShell le interpreta come array e gcloud riceve tutto come un'unica variabile.

---

## 2. Aggiornare l'app dopo una modifica al codice (USO QUOTIDIANO)

### Comando unico, sempre lo stesso

Dalla cartella `PC/` (quella con il `Dockerfile`):

```powershell
gcloud run deploy persicup --source . --region europe-west1
```

Cloud Run **ricorda** env vars, secret, service account, scaling. Non serve ripassarli.

### Tempi tipici

| Tipo di modifica | Tempo |
|---|---|
| Solo template HTML / CSS | ~1 minuto |
| Solo codice Python | ~1-2 minuti |
| Modifica `requirements.txt` | ~3-5 minuti |

### Dopo il deploy

Apri il sito in **incognito** (`Ctrl+Shift+N`) per evitare cache del browser:

https://persicup-214688066540.europe-west1.run.app

---

## 3. Cosa succede dietro le quinte quando deployi

Quando lanci `gcloud run deploy ... --source .`, succedono 7 cose in ordine:

### Atto 1 — Upload del codice
gcloud comprime la cartella in un `.tar.gz` e la carica in un bucket privato di Cloud Build. **Esclude** tutto quello che è in `.gcloudignore` (credenziali, venv, cache, ecc.).

### Atto 2 — Build del container
Cloud Build accende una VM temporanea e legge il [Dockerfile](Dockerfile):
1. `FROM python:3.11-slim` → scarica Python
2. `COPY requirements.txt` + `pip install` → installa le dipendenze (questo layer viene cachato)
3. `COPY . .` → copia il tuo codice
4. `CMD gunicorn ...` → comando d'avvio

> Se modifichi solo codice/template (non `requirements.txt`), il layer pip viene riusato dalla cache → build velocissima.

### Atto 3 — Crea l'immagine
Genera un'immagine container di ~500 MB con Python + dipendenze + tuo codice.

### Atto 4 — Push su Artifact Registry
L'immagine viene salvata nel repo `cloud-run-source-deploy` con un tag univoco (hash). Le versioni vecchie restano lì.

### Atto 5 — Nuova revision
Cloud Run crea una nuova **revision** (es. `persicup-00003-abc`) accanto a quella precedente. Ogni revision è uno snapshot immutabile di: immagine + env + secret + risorse.

### Atto 6 — Health check
Cloud Run avvia un container della nuova revision e aspetta che gunicorn risponda su `:8080`. **Se l'app crasha all'avvio, la revision viene rifiutata** e la vecchia continua a servire tutto il traffico.

### Atto 7 — Switch traffico
Se l'health check passa, il 100% del traffico va alla nuova revision. La vecchia si spegne dopo qualche minuto (zero-downtime).

---

## 4. Comandi utili per la gestione

### Leggere i log degli ultimi minuti

```powershell
gcloud run services logs read persicup --region europe-west1 --limit 100
```

### Vedere lo stato attuale del servizio

```powershell
gcloud run services describe persicup --region europe-west1
```

### Vedere solo le env vars correnti

```powershell
gcloud run services describe persicup --region europe-west1 --format="value(spec.template.spec.containers[0].env)"
```

### Aggiungere o cambiare una env var (senza ribuild)

```powershell
gcloud run services update persicup --region europe-west1 --update-env-vars "NUOVA_VAR=valore"
```

Più env vars insieme (ricorda le virgolette!):

```powershell
gcloud run services update persicup --region europe-west1 --update-env-vars "VAR1=a,VAR2=b"
```

### Aggiornare il valore del secret (es. ruotare SECRET_KEY)

```powershell
$bytes = New-Object byte[] 32
[Security.Cryptography.RandomNumberGenerator]::Create().GetBytes($bytes)
$key = [Convert]::ToBase64String($bytes)
$tmp = [System.IO.Path]::GetTempFileName()
[System.IO.File]::WriteAllText($tmp, $key)
gcloud secrets versions add flask-secret-key --data-file=$tmp
Remove-Item $tmp
```

Poi forza una nuova revision per fargli leggere la nuova versione:

```powershell
gcloud run services update persicup --region europe-west1
```

### Lista delle revisions (per rollback)

```powershell
gcloud run revisions list --service persicup --region europe-west1
```

### Rollback istantaneo a una revision precedente

```powershell
gcloud run services update-traffic persicup --to-revisions=persicup-00002-xyz=100 --region europe-west1
```

(sostituisci `persicup-00002-xyz` con il nome della revision a cui vuoi tornare)

Il rollback è immediato (~5 secondi) perché l'immagine vecchia è già su Artifact Registry.

### Spegnere completamente il servizio

```powershell
gcloud run services delete persicup --region europe-west1
```

---

## 5. Troubleshooting

### Sintomo: "Service Unavailable" dopo il deploy

L'app crasha all'avvio. Leggi i log:

```powershell
gcloud run services logs read persicup --region europe-west1 --limit 50
```

Cerca righe `Traceback`, `Error`, `KeyError`, `ImportError`.

### Sintomo: `KeyError` su una env var

Probabilmente le virgole in `--set-env-vars` non sono state quotate in PowerShell. Verifica:

```powershell
gcloud run services describe persicup --region europe-west1 --format="value(spec.template.spec.containers[0].env)"
```

Devi vedere ogni env var come entry separata. Se ne vedi una sola con tutto dentro, fixala:

```powershell
gcloud run services update persicup --region europe-west1 --update-env-vars "FLASK_CONFIG=prod,FIREBASE_PROJECT_ID=persicup-a49df,GCS_BUCKET_NAME=persicup-a49df.firebasestorage.app"
```

### Sintomo: deploy non parte / errore di credenziali

Re-autentica:

```powershell
gcloud auth login
gcloud config set project persicup-a49df
```

### Sintomo: errori 403 su Firestore o GCS dall'app

Il service account non ha i permessi giusti. Verifica:

```powershell
gcloud projects get-iam-policy persicup-a49df --flatten="bindings[].members" --filter="bindings.members:persicup-runtime@persicup-a49df.iam.gserviceaccount.com" --format="value(bindings.role)"
```

Dovresti vedere almeno: `roles/datastore.user`, `roles/storage.objectAdmin`, `roles/iam.serviceAccountTokenCreator`.

### Sintomo: i miei `.pyc` finiscono nel container

Verifica che `.gcloudignore` contenga `__pycache__/` e `*.pyc`. Già configurato in questo progetto.

---

## 6. Costi

Con il setup attuale (`min-instances 0`, `max-instances 5`, `512 Mi`, `1 CPU`) stai nel **free tier** di Cloud Run per traffico medio-basso:

- Cloud Run: 2 milioni di richieste/mese gratis
- Cloud Build: 120 minuti di build/giorno gratis
- Artifact Registry: 0,5 GB gratis (sufficiente per ~10-20 versioni dell'immagine)
- Secret Manager: 6 secret + 10.000 accessi/mese gratis
- Firestore: 1 GB storage + 50k letture/giorno gratis
- Cloud Storage: 5 GB gratis

Per stare tranquillo imposta un **budget alert** su Billing → Budgets (es. 5 EUR/mese): ti manda mail se sfori.

---

## 7. Flusso tipico nella vita reale

```
1. Modifichi un file (es. app/templates/public/landing.html)
2. Salvi
3. Apri PowerShell nella cartella PC/
4. Lanci:  gcloud run deploy persicup --source . --region europe-west1
5. Aspetti ~1-2 minuti
6. Apri il sito in incognito (Ctrl+Shift+N) per evitare la cache
7. Vedi le modifiche live
```

Se il deploy fallisce per un bug, **il sito vecchio continua a girare** finché non sistemi e ri-deployi. Zero panico.
