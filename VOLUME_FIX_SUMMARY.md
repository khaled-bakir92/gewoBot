# Volume-Fehler Fix - Zusammenfassung

## Das Problem

Der Scheduler zeigte einen neuen Fehler:
```
error creating exec: API error (500): invalid volume specification
```

**Ursache:** Ofelia unterstützt bei `job-run` Labels mit mehrfachen Volumes nicht in der Form:
```yaml
ofelia.job-run.job.volume: "vol1,vol2,vol3"
```

Außerdem können YAML-Labels mit demselben Key nicht mehrfach definiert werden (YAML überschreibt).

## Die Lösung

Wir haben von **Label-basierter Konfiguration** auf **Config-Datei** umgestellt:

### Vorher (Labels in docker-compose.yml):
```yaml
labels:
  ofelia.job-run.job.volume: "vol1,vol2,vol3"  # ❌ Funktioniert nicht
```

### Nachher (Config-Datei ofelia-config.ini):
```ini
[job-run "gewobag-bot-job"]
volume = /root/gewoBot/user_data.json:/app/user_data.json:ro
volume = /root/gewoBot/filter_config.json:/app/filter_config.json:ro
volume = /root/gewoBot/gewobag_wohnungen.db:/app/gewobag_wohnungen.db
...
```

## Geänderte Dateien

### 1. docker-compose.yml
- Scheduler lädt jetzt Config-Datei: `--config=/etc/ofelia/config.ini`
- Volume für Config-Datei hinzugefügt: `./ofelia-config.ini:/etc/ofelia/config.ini:ro`
- Alle Labels entfernt

### 2. ofelia-config.ini (NEU!)
- Vollständige Job-Konfiguration
- Alle Volumes einzeln definiert (mit absoluten Pfaden)
- Kommentare für alternative Zeitpläne

### 3. VPS_DEPLOYMENT_FIX.md
- Schritt 3 hinzugefügt: Pfade in ofelia-config.ini prüfen
- Schritt-Nummerierung aktualisiert

### 4. QUICK_FIX.sh
- Pfad-Prüfung am Anfang (Warnung wenn nicht /root/gewoBot)
- Prüfung ob ofelia-config.ini existiert
- Anzeige der ersten Volume-Zeile zur Verifikation

## Deployment-Schritte (Kurzfassung)

```bash
# 1. Auf lokalem Rechner
scp docker-compose.yml ofelia-config.ini QUICK_FIX.sh root@vmd181811.contaboserver.net:~/gewoBot/

# 2. Auf VPS
ssh root@vmd181811.contaboserver.net
cd ~/gewoBot

# 3. WICHTIG: Pfade prüfen und ggf. anpassen
pwd  # Sollte /root/gewoBot sein
# Wenn anders: nano ofelia-config.ini und alle Pfade anpassen

# 4. Fix-Script ausführen
bash QUICK_FIX.sh

# 5. Logs überwachen
docker-compose logs -f gewobag-scheduler
```

## Erwartete Ausgabe (Erfolg)

**Scheduler-Logs:**
```
New job registered "gewobag-bot-job" - "python main.py --full" - "@every 15m"
[Job "gewobag-bot-job"] Started - python main.py --full
[Job "gewobag-bot-job"] Found locally image gewobot-gewobag-bot:latest
[Job "gewobag-bot-job"] Finished in "42s"
```

**Keine Fehler mehr!** ✅

## Wichtige Hinweise

1. **Absolute Pfade verwenden**: Die Pfade in `ofelia-config.ini` müssen absolut sein (nicht relativ)
2. **Arbeitsverzeichnis prüfen**: Standardmäßig `/root/gewoBot` - wenn anders, Pfade anpassen
3. **Alle Dateien müssen existieren**: user_data.json, filter_config.json, logs/, documents/, etc.
4. **Scheduler neu starten nach Config-Änderungen**: `docker-compose restart gewobag-scheduler`

## Zeitplan anpassen

Bearbeiten Sie `ofelia-config.ini` auf dem VPS:

```ini
# Alle 30 Minuten statt 15
schedule = @every 30m

# Stündlich
schedule = @hourly

# Täglich um 9:00 Uhr
schedule = 0 9 * * *

# Mo-Fr, 9-18 Uhr, alle 15 Min
schedule = */15 9-18 * * 1-5
```

Dann Scheduler neu starten:
```bash
docker-compose restart gewobag-scheduler
```

## Troubleshooting

### "No such file or directory: /root/gewoBot/user_data.json"
→ Pfade in ofelia-config.ini falsch. Mit `pwd` prüfen und anpassen.

### "network gewobot_default not found"
→ Web-Service zuerst starten: `docker-compose up -d gewobag-web`

### "No such image: gewobot-gewobag-bot:latest"
→ Image neu bauen: `docker-compose build gewobag-bot`

### Scheduler läuft, aber keine Jobs
→ Config-Datei prüfen: `docker exec gewobag-scheduler cat /etc/ofelia/config.ini`

## Vorteile der Config-Datei

✅ Übersichtlicher als YAML-Labels
✅ Einfacher zu bearbeiten (keine Escape-Zeichen)
✅ Mehrere Volumes problemlos möglich
✅ Kommentare für Dokumentation
✅ Einfacher zu debuggen

## Nächste Schritte

1. ✅ Dateien auf VPS hochladen
2. ✅ Pfade in ofelia-config.ini prüfen/anpassen
3. ✅ QUICK_FIX.sh ausführen
4. ✅ 15 Minuten warten
5. ✅ Logs prüfen
6. ✅ Bei Erfolg: Zeitplan nach Bedarf anpassen
