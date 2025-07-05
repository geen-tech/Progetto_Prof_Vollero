# Distributed Key-Value Store with Fault Tolerance (EnergyGuard)

## Descrizione del Progetto

**EnergyGuard** è un sistema distribuito per l’archiviazione di misurazioni energetiche con replica dei dati, tolleranza ai guasti e gestione delle soglie di allerta. Il sistema fornisce un'API RESTful costruita con Flask per eseguire operazioni CRUD e monitorare lo stato dei nodi. Include test automatici di resilienza e prestazioni.

## Obiettivi del Progetto

- Garantire alta disponibilità e integrità dei dati.
- Fornire tolleranza ai guasti per i nodi di storage.
- Offrire un sistema scalabile con strategie di replica configurabili.
- Generare allerte automatiche per superamento soglie dei sensori.

## Funzionalità Principali

- **Strategie di replica**: `full` e `consistent hashing`.
- **Operazioni CRUD** su misurazioni energetiche.
- **Gestione nodi**: simulazione di guasti, recupero, stato nodi.
- **Allerte automatiche**: superamento soglie personalizzate per sensori.
- **Test di tolleranza ai guasti e benchmark prestazionali**.

## Struttura del Progetto

### 1. `app.py` (o `__init__.py`)
Avvia l'applicazione Flask. Carica la configurazione e registra le route tramite `register_routes()`.

### 2. `routes.py`
Definisce gli endpoint REST:
- `/ingest`, `/measurement/<key>`, `/delete/<key>`, `/set_threshold`
- `/alerts`, `/measurements`, `/sensor/<sensor_id>/history`
- `/configure_replication`, `/nodes_status`, `/fail_node/<id>`, `/recover_node/<id>`, `/replica_nodes/<key>`

Supporta autenticazione tramite API Token (`Authorization: Bearer <token>`).

### 3. `models.py`
Contiene le classi principali:
- **StorageNode**: nodo individuale con DB SQLite locale.
- **MeasurementReplicationManager**: gestore della replica, strategia, gestione fallimenti, consistenza.
- **AlertManager**: gestione delle soglie e allerte.

### 4. `energyguardring.py`
Implementa il **Consistent Hashing** per assegnare chiavi ai nodi responsabili in modo bilanciato.

### 5. `client.py`
Script CLI per:
- Scrittura, lettura, cancellazione chiavi.
- Configurazione strategia di replica.
- Simulazione fail/recover.
- Recupero nodi per chiavi specifiche.
- Visualizzazione stato nodi.

### 6. `run.py`
Permette di:
- Avviare l'app Flask (`python run.py`)
- Eseguire i test (`python run.py test`)

### 7. `test_per.py`
Testa:
- Performance con replica full e consistent.
- Tempi di `write`, `read`, `fail`, `recover`.

### 8. `plot_result.py`
Genera grafici comparativi tra strategie di replica (es. tempo medio operazioni).

### 9. `requirements.txt`
Librerie necessarie:
```
Flask~=2.1.1
requests~=2.31.0
unittest2~=1.1.0
```

## Come Iniziare

### Installazione

```bash
git clone https://github.com/<tuo-utente>/energyguard-distributed-kv.git
cd energyguard-distributed-kv
pip install -r requirements.txt
```

### Esecuzione

```bash
python run.py
```
L’applicazione sarà disponibile su: `http://127.0.0.1:5000`

### Test

```bash
python run.py test
```

## Esempio di chiamate API

```bash
# Ingest misura
curl -X POST http://localhost:5000/ingest \
  -H "Authorization: Bearer martina123456" \
  -H "Content-Type: application/json" \
  -d '{"sensor_id": "sensor1", "timestamp": "2025-07-05T18:00:00", "value": 75.5}'

# Recupera alert
curl -X GET http://localhost:5000/alerts \
  -H "Authorization: Bearer martina123456"
```

## Risultati Test di Fail/Recover

| Strategia        | Fail   | Recover | Read   | Write   |
|------------------|--------|---------|--------|---------|
| **Full**         | 0.000s | 0.227s  | 0.000s | 0.112s  |
| **Consistent**   | 0.020s | 0.010s  | 0.010s | 0.170s  |

Totale test: 6 — **durata complessiva ~1.09s**

## Conclusioni

Il sistema è in grado di:
- Garantire l’integrità dei dati.
- Gestire dinamicamente guasti e recuperi.
- Supportare strategie di replica configurabili.
- Generare allerte automatiche su condizioni anomale.

Prossimi sviluppi possibili:
- Aggiunta di un broker come Kafka o MQTT per ingestion asincrona.
- Interfaccia web per il monitoraggio del sistema.

