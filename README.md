# hacs-APsystemsEZ1_local
Modification of popular EZ1 Microinverter to fix a few flaws, APsystems seems not to do
Keywords: Home Assistant HA - APsystem EZ1 EZ1-M - Microinverter - Microwechselrichter

> [!IMPORTANT]
> **This integration is not affiliated with APsystem and is provided as-is and without warranty.**
> **Diese integration ist ohne Hilfe von APsystems erstellt und wird so wie sie ist zur Verfügung gestellt, ohne Garantie und Haftung.**

# APsystems EZ1 local Integration

[![GitHub Release][releases-shield]][releases]
[![GitHub Activity][commits-shield]][commits]
[![License][license-shield]](LICENSE)

> [!NOTE]
>It is assumed this integration is mostly used by German speaker, therefore a translation to English is not provided here. If you need support in English, just raise an issue.

> [!NOTE]
> Diese Integration basiert auf der Home Assistant Core integration von [https://www.home-assistant.io/integrations/apsystems] und dem [EZ1-M Python code von https://github.com/SonnenladenGmbH/APsystems-EZ1-API]. Diese Integration beinhaltet die Python API, ein Requirement und Nachladen ist nicht nötig.

**Diese Integration implementiert folgende HA platforms:**

Platform | Beschreibung
-- | --
`sensor` | Sensor Daten des Microwechselrichters
`binary` | Binär Daten des Microwechselrichters
`switch` | Schalter zum Ein- / Ausschalten des Wechselrichters

## Einführung

### Was ist der Unterschied dieser Integration zur Sonnenladen Integration, die nativ in HA Core enthalten ist.

1. Über die Zeit haben sich einige Problemchen mit der ursprünglichen Integration angesammelt, die wohl nur sehr stückweise angegangen werden.
2. Die WLAN-API des EZ1-M Wechselrichters ist nicht immer sehr stabil. Oft werden Logs mit Fehlermeldungen überschüttet. Diese Integration minimiert die Log-Einträge
3. Ein sehr ärgerlicher Überlauf in den Energiezählern für Port 1 und Port 2 (P1 und P2) sorgt für ein regelmäßiges Durcheinander im HA Energie-Dashboard. Diese Integration ermöglicht bei der Konfiguration eine Eingabe eines Energieoffsets für bisher stattgefundene Overruns. Wenn nichts eingegeben wird, wird kein Offset hinzugerechnet.
4. Detektiert selbstständig weitere Overruns (passiert immer so um die 540kWh) und errechnet dann einen neuen Offset, der auch Persistent in HA gespeichert wird. Dieser Offset wird an die Seriennummer des Wechselrichters verbunden, so dass auch mehrere Wechelrichter unterstützt werden können.
5. Auch nach einem Neustart bleibt der Offset erhalten und man hat keine Rücksprünge mehr und HA errechnet den tatsächlichen erzeugten Energiewert, obwohl der WR wieder bei 0 zum zählen beginnt.
6. Microrücksprünge bei den Energiewerten anhand von Rundungsproblemen werden mit gespeicherten Werten korrigiert. Es gibt keine HA Warnungen mehr wegen Rücksprünge bei den Energiewerten.
7. Der Tagereset des Tageszähler war falsch implementiert. Diese Integration korrigiert es. Die Werte werden jetzt auch zwischengespeichert. Ein Neustart von HA verändert die Tageswerte nun nicht mehr.
8. Neuere Firmware-Versionen speichern nicht mehr die Maximal-Leistung des Wechselrichters. Über HA wird dies gerne zur Regelung im Zusammenhang eines Akkus genutzt. Diese Integration schreibt den letzten gültigen Maximal-Wert entweder beim Aufwachen am Morgen oder beim Wiedereinschalten. Das Schreiben wird nur dann ausgeführt, wenn der WR selbst die letzten Werte vergessen hat. Bei den alten WR wird kein Schreibzyklus ausgelöst, um dessen Flash-Speicher zu schonen.
9. Die Alarminformationen werden nicht bei jedem Update-Zyklus gelesen, um die Updaterate zu verbessern.
10. Die Updaterate kann wieder im Konfigurations-Dialog eingegeben werden. Die Integration unterstützt jetzt auch ein Reconfigure, damit kann man die Konfiguration ohne Löschen und neu anlegen korrigieren.
11. Unterstützt eine neue API um detaillierte Daten (Spannungen, Ströme, Netzfrequenz, Netzspannungen, .. ) anzuzeigen.

## Installation

### Installation mit HACS Repository (Empfohlen)

[![Öffnen Sie Ihr Home Assistant und gehen Sie in das Repository im Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=AndyNew2&repository=hacs-APsystemsEZ1_local&category=integration)

1. Installieren Sie [HACS](https://hacs.xyz/) und führen Sie das zugehörige Setup aus.
2. Gehen Sie in HACS und selektieren "Integrations".
3. Fügen Sie `AndyNew2/hacs-APsystemsEZ1_local` mit der Kathegorie "Integration" als [Benutzer Repository](https://hacs.xyz/docs/faq/custom_repositories/) ein. Oder einfacher, benutzen Sie einfach den Link nach "Installation mit HACS Repository (Empfohlen)".
Falls möglich gleich den "Download" Button nutzen und die aktuelle Version der Integration herunterladen, sonst verschwindet das neue Repository gleich wieder.
4. Wählen Sie "APsystems Local API" von der Liste oder beim Dialog oben klicken auf "Download".
5. Anschließend müssen Sie Home Assistant neu starten, damit die Integration verfügbar wird.

### Installation der Integration APsystems Local API

[![Hinzufügen der Integration zu Home Assistant!](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=apsystemsapi_local)

Die integration erscheint nun wie jede andere Home Assistant integration. Die ursprüngliche HA APsystems Core integration wird durch diese Integration ersetzt.
Sie müssen jedoch wie oben beschrieben Home Assistant einmal neu starten.

Nun können wir unseren Wechselrichter hinzufügen mit dem Konfigurations-Dialog:

1. In der HA GUI gehen Sie zu "Einstellungen" -> "Geräte & Dienste". Unten rechts klicken Sie auf "Integration hinzufügen". Dann suchen Sie nach "APsystems Local API" (nicht die APSystems nehmen). Oder benutzen Sie einfach den Link oben.
2. Gehen Sie durch den Konfig-Dialog, anschließend ist Ihr Wechselrichter in Home Assistant eingerichtet.

### Manuelle Installation

Erzeugen Sie ein Unterverzeichnis in homeassistant/custom_components
1. Ein Unterverzeichnis mit dem Namen "apsystemsapi_local"
2. Kopieren Sie alle Files hier in dieses Verzeichnis auch mit dem Unterverzeichnis translations.
3. Neustart von Home Assistant! Wichtig, nicht vergessen.
4. In den Geräten, suchen Sie nun "APsystems Local API". Konfiguration nach dem Konfig-Dialog, wie unten beschrieben.
 
### Konfiguration mit dem Config-Flow
1. Sie müssen die IP Address Ihres Wechselrichters eingeben. Bitte sorgen Sie für eine statische Adresse. Der Wechselrichter selbst kann es leider nicht, deshalb müssen Sie es mit Hilfe Ihres Routers (z.B. FritzBox) so einrichten, dass der WR immer die gleiche IP-Adresse bekommt. Außerdem muss der WR im Local-Mode arbeiten. Andernfalls können die Daten nicht per HA Integrationen erreicht werden. Den Local-Mode stellen Sie mit der Handy APSystems App ein.
2. Die Port-Nummer sollte 8050 sein und ist schon vorausgefüllt, einfach so lassen.
3. Update-Intervall in Sekunden. Je kleiner der Werte umso öfters werden die Werte aktualisiert. 15 Sekunden sind standard. Weniger wie 5 Sekunden werden nicht empfohlen, weil dies die Integration und HA zu sehr stresst. Auch Ihr Netzwerk und der WR leiden unter zu häufigen Zugriffen.
4. Nun können Sie Basis Werte für Port 1 (P1) und Port 2 eingeben. Sie haben hierfür zwei Eingabefelder. Wenn Sie die Werte leer lassen, wird die Integration versuchen, bereits früher eingegebene Werte zu finden und diese zu benutzen. Wenn Sie noch nie Werte eingegeben haben, wird der Basis Wert 0 für P1 und P2 angenommen. Diese Basiswerte werden zu den Total Energiewerten von P1 und P2 addiert. Der Wechselrichter hat intern keinen Gesamtspeicher für beide Ports, sondern er hat nur getrennte Register für die jeweiligen Ports. Deshalb müssen Sie die Offsets auch getrennt eingeben. Wenn Sie das nicht interessiert, können Sie das Offset auch einfach auf P1 eingeben und P2 leer lassen. Die Summe wird dies nicht verändern. Zukünftige Overflows erhöhen intern automatisch die Basis. Nur wenn etwas furchtbar schief laufen sollte, können Sie den Konfig-Flow wieder aktivieren, und die Werte ggf. korrigieren.

**Fertig! Viel Freude mit der verbesserten Integration.**


## Hinweise
- Diese Integration erneuert (updated) nicht alle Sensoren zur gleichen Zeit. Spannungs-, Strom- und Leistungswerte werden mit der eingegebenen Updaterate erneuert. Andere Werte, wie Ein/Aus Status, Maximalleistungseinstellungen, Alarme, etc. werden weniger häufig geupdated. Bitte nach dem Start der Integration etwas abwarten, es werden alle Sensoren aktiviert.
- Der Persistente (im Flash Speicher) befindliche Maximal-Leistungswert kann in neueren Firmwareversionen nicht mehr häufig geschrieben werden. Dies ist eine Art Schutz, die sehr sinnvoll ist. Leider gibt der Wechelrichter hierzu keine passende Fehlermeldung, wodurch diese Integration nicht unterscheiden kann, warum das Schreiben nicht funktioniert hat. Falls das Schreiben nicht klappt, bitte etwas abwarten (ca. 45 Minuten). Auch wiederholte Versuche zählen als Schreibzugriff, wodurch diese Wartezeit verlängert wird. Also alles in Ruhe lassen und nach der angegebenen Zeit einen Schreibzugriff probieren, dann sollte es auch klappen.
- Diese Integration nutzt standardmäßig die neue API mit genaueren Sensorwerten und dem neuen DefaultMaxPower Flash-Speicher. Sollte Ihr Wechelrichter Probleme mit der neuen API haben (weil Sie z.B. noch eine ältere Firmware <1.7.x) nutzen, können Sie im Konfigurationsdialog die neue API abschalten. Hierzu einfach den entsprechenden Schalter am Ende des Dialogs abwählen.

[commits-shield]: https://img.shields.io/github/commit-activity/y/AndyNew2/hacs-APsystemsEZ1_local.svg?style=for-the-badge
[commits]: https://github.com/AndyNew2/hacs-APsystemsEZ1_local/commits/master
[hacs]: https://github.com/hacs/integration
[hacsbadge]: https://img.shields.io/badge/HACS-Custom-41BDF5.svg?style=for-the-badge
[license-shield]: https://img.shields.io/github/license/AndyNew2/hacs-APsystemsEZ1_local.svg?style=for-the-badge
[releases-shield]: https://img.shields.io/github/release/AndyNew2/hacs-APsystemsEZ1_local.svg?style=for-the-badge
[releases]: https://github.com/AndyNew2/hacs-APsystemsEZ1_local/releases
