# AutoMSR
[![Linters](https://github.com/Crissal1995/auto_msrewards/actions/workflows/linters.yaml/badge.svg)](https://github.com/Crissal1995/auto_msrewards/actions/workflows/linters.yaml)
[![Tests](https://github.com/Crissal1995/auto_msrewards/actions/workflows/tests.yaml/badge.svg)](https://github.com/Crissal1995/auto_msrewards/actions/workflows/tests.yaml)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

README languages: [EN](README.md) **IT**

## Descrizione
**AutoMSR** è uno strumento di automazione creato a scopo educativo, con 
l'intenzione di mostrare come utilizzare Selenium come driver di automazione
per il servizio Microsoft Rewards.

## Cosa fa
Questo strumento ha lo scopo di mostrare come raccogliere automaticamente
i punti giornalieri disponibili su Microsoft Rewards.

Cosa fa:
- Completa le attività giornaliere
- Completa altre attività
- Completa le schede punti gratuite 
- Ricerche con uno User Agent desktop (Edge su Windows)
- Ricerche con un User Agent mobile (Chrome su Android)

### Attenzione
Prima di utilizzare questo software, leggere attentamente i 
[Termini di servizio Microsoft][1], sezione Microsoft Rewards.

## Utilizzo
### Chromedriver
Scarica il [Chromedriver][2] corretto corrispondente alla tua versione di Chrome.

### Credenziali e profili
Crea il tuo `credentials.json` seguendo il file di esempio. 
Il file è strutturato come una lista di record, dove ogni record
rappresenta un diverso profilo da utilizzare con AutoMSR.

Ci sono due tipi di utilizzo: via Login e via Profiles.

#### Login
*Questo è il vecchio metodo, disponibile per coerenza.*

Ogni voce deve fornire `email` e `password`, e il login
verrà eseguito in una nuova sessione di Chrome.

#### Profiles
*Questo è il nuovo metodo.*

Ogni voce deve fornire `email` e `profile`, e poi verrà utilizzato
il profilo Chrome corrispondente.

**Questo metodo presuppone che il tuo profilo sia impostato correttamente**, quindi che:

- Sei loggato nella [homepage di Rewards][rewards];
- Sei loggato nella [homepage di Bing][bing]
(l'angolo in alto a destra dovrebbe riportare il tuo nome, non Accedi);
- Hai accettato tutti i cookies popup trovati sia nella homepage di Rewards che nelle pagine di Bing.

Per ottenere il nome del tuo profilo, devi andare in [chrome://version](chrome://version)
e controllare *Percorso Profilo*.

È stato sviluppato un metodo di utility per controllare facilmente i tuoi profili: 
controlla la sezione [Mostra Profili][showProfiles].

Se entrambi `profile` che `password` vengono trovati, verrà utilizzato questo metodo.

### Configurazione
Tutti i parametri di configurazione sono elencati di seguito in modo più dettagliato. 
Tuttavia, ci sono alcuni elementi che vale la pena notare, ovvero:
1. `email/recipient`: Email (o lista di email separate da virgola) dove
ricevere lo stato di esecuzione di AutoMSR.
2. `selenium/headless`: Visualizza (`false`) o no (`true`) la finestra di Chrome
durante l'esecuzione. È stato empiricamente provato che un valore `false`
dia maggiore stabilità al sistema. 
3. `selenium/path`: Percorso completo dell'eseguibile di Chromedriver, se
non si trova nella variabile d'ambiente PATH. 
4. `selenium/profile_root`: Se usato con Profiles (invece di Login), deve
puntare al percorso dei profili di Chrome.

### Python
La versione di Python deve essere 3.7+.

È necessario installare i requisiti con il comando:
```bash
python3 -m pip install -r requirements.txt
```

### Esecuzione
Una volta che hai finito la configurazione, puoi eseguire AutoMSR con il comando:
```bash
python3 main.py
```

*Si noti che, quando si esegue con Profiles, tutti i processi di Chrome
dovrebbero essere terminati. Mentre si esegue AutoMSR si possono comunque usare altri browser Chromium, come Edge.*

#### <a name="show-profiles"></a> Mostra Profili
Per mostrare i profili Chrome disponibili, si può eseguire il seguente comando:
```bash
python3 main.py --show-profiles
```
Per ogni profilo Chrome trovato verrà mostrato un set di attributi:
- `display_name`, il nome del profilo mostrato su Chrome;
- `folder_name`, il nome della cartella del Profilo nel filesystem
(diventa `profile` nel file `credentials.json`);
- `profile_root`, la root dei profili Chrome (diventa `profile_root` nel file 
`automsr.cfg`).

## Configurazione
Il comportamento dello strumento può essere configurato all'interno di `automsr.cfg`.

Il file di configurazione è diviso in tre sezioni:  **automsr**, **email** e **selenium**.

### automsr
#### credentials
Il file json delle credenziali (dovrebbe essere una lista di oggetti; 
vedi file di esempio).

Il valore predefinito è `credentials.json`.

#### skip
AutoMSR può saltare le attività Rewards o le ricerche di Bing (o entrambe). 

Questo valore può essere uno tra 
`no` (non saltare nulla), 
`yes`, `all` (saltare tutto), 
`search`, `searches` (saltare le ricerche Bing), 
`activity`, `activities` (saltare le attività Rewards),
`punchcard`, `punchcards` (saltare le schede punti Rewards).

Il valore predefinito è `no`.

#### retry
Il numero di volte che AutoMSR dovrebbe riprovare le attività Rewards mancanti o fallite.

Il valore predefinito è 3.

#### search_type
Come eseguire le ricerche di Bing. 
Può essere `random` (genera una parola casuale e poi esegue una ricerca 
rimuovendo un carattere alla fine della stringa alla volta) o 
`takeout` (usa le ricerche di Google, ottenute da una Takeout Action).

Il valore predefinito è `random`.

#### verbose
Se aumentare o meno la verbosità dell'output della console; la verbosità dei file di log è immutabile.

Il valore predefinito è `false`.

### email
#### send
Abilita o disabilita l'invio dell'email di stato alla fine dell'esecuzione
per tutti gli account usati con AutoMSR.

Il valore predefinito è `true`.

#### recipient
L'indirizzo email del destinatario dove ricevere l'email di stato. 
Può essere un singolo indirizzo email o una lista separata da virgole d'indirizzi email.

#### strategy
La strategia usata per decidere quale mittente usare per inviare l'email di stato
al destinatario specificato. 
Può essere uno dei seguenti:
- `first`: sarà usato il primo indirizzo email nel file di credenziali fornito;
- `last`: verrà usato l'ultimo indirizzo email nel file di credenziali fornito;
- `random`: verrà usato un indirizzo email casuale nel file di credenziali fornito;
- `gmail`: verrà usato un indirizzo email Gmail (mittente e password devono essere configurati);
- `custom`: verrà usato un indirizzo email generico (mittente, password, host e porta devono essere configurati).

Il valore predefinito è `first`.

#### sender
Se la strategia è `gmail` o `custom`, specifica l'indirizzo email del mittente.

#### password
Se la strategia è `gmail` o `custom`, specifica la password del mittente.

#### host
Se la strategia è `custom`, specifica il nome dell'host SMTP.

#### porta
Se la strategia è `custom`, specifica la porta SMTP.

#### tls
Se la strategia è `custom`, specifica se usare o meno TLS.

### selenium
#### env
Se l'ambiente sta usando un eseguibile chromedriver trovato in PATH (`local`), 
o un hub Selenium in ascolto su una porta, di default 4444 (`remote`).

Il valore predefinito è `local`.

#### headless
Scegliere se avviare o meno la sessione di Chrome in modalità headless.

Il valore predefinito è `false`.

#### path
Ignorato quando env è `remote`. Il percorso dell'eseguibile di chromedriver.

Se manca, Selenium cercherà il chromedriver nel PATH.

#### url
Ignorato quando env è `local`. Sovrascrive l'url dell'hub di Selenium.

Il valore predefinito è `http://localhost:4444/wd/hub`.

#### logging
Abilita o disabilita i log di Selenium server.

Il valore predefinito è `true`.

#### profile_root
Radice della directory dei dati utente di Chromium (cioè dove sono memorizzati
i profili). Un esempio è:
```
C:\Users\<USER>\AppData\Local\Google\Chrome\User Data
```
Il valore predefinito è nullo.


[1]: https://www.microsoft.com/servicesagreement
[2]: https://chromedriver.chromium.org/downloads
[rewards]: https://rewards.microsoft.com/
[bing]: https://www.bing.com/
[showProfiles]: #show-profiles