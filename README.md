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

**This component will set up the following platforms.**

Platform | Beschreibung
-- | --
`sensor` | Sensor Daten des Microwechselrichters
'binary' | Binär Daten des Microwechselrichters
'switch' | Schalter zum Ein- / Ausschalten des Wechselrichters

## Einführung

### Was ist der Unterschied dieser Integration zur Sonnenladen Integration, die nativ in HA Core enthalten ist.

1. Über die Zeit haben sich einige Problemchen mit der ursprünglichen Integration angesammelt, die wohl nur sehr stückweise angegangen werden.
2. Die WLAN-API des EZ1-M Wechselrichters ist nicht immer sehr stabil. Oft werden Logs mit Fehlermeldungen überschüttet. Diese Integration minimiert die Log-Einträge
3. Ein sehr ärgerlicher Überlauf in den Energiezählers für Port 1 und Port 2 (P1 und P2) sorgt für ein regelmäßiges Durcheinander im HA Energie-Dashboard. Diese Integration ermöglicht bei der Konfiguration eine Eingabe eines Energieoffsets für bisher stattgefundene Overruns. Wenn nichts eingegeben wird, wird kein Offset hinzugerechnet.
4. Detektiert selbstständig weitere Overruns (passiert immer so um die 540kWh) und errechnet dann einen neuen Offset, der auch Persistent in HA gespeichert wird. Dieser Offset wird an die Seriennummer des Wechselrichters verbunden, so dass auch mehrere Wechelrichter unterstützt werden können.
5. Auch nach einem Neustart bleibt der Offset erhalten und man hat keine Rücksprünge mehr und HA errechnet den tatsächlichen erzeugten Energiewert, obwohl der WR wieder bei 0 zum zählen beginnt.
6. Microrückzähler anhand von Rundungsproblemen werden mit gespeicherten Werten korrigiert. Es gibt keine HA Warnungen mehr wegen Rücksprünge bei den Energiewerten.
7. Der Tagereset des Tageszähler war falsch implementiert. Diese Integration korrigiert es.
8. Neuere Firmware-Versionen speichern nicht mehr die Maximal-Leistung des Wechselrichters. Über HA wird dies gerne zur Regelung im Zusammenhang eines Akkus genutzt. Diese Integration schreibt den letzten gültigen Maximal-Wert entweder beim Aufwachen am Morgen oder beim Wiedereinschalten. Das Schreiben wird nur dann ausgeführt, wenn der WR selbst die letzten Werte vergessen hat. Bei den alten WR wird kein Schreibzyklus ausgelöst, um dessen Flash-Speicher zu schonen.
9. Die Alarminformationen werden nicht bei jedem Update-Zyklus gelesen, um die Updaterate zu verbessern.
10. Die Updaterate kann wieder im Konfigurations-Dialog eingegeben werden. Die Integration unterstützt jetzt auch ein Reconfigure, damit kann man die Konfiguration ohne Löschen und neu anlegen korrigieren.





https://www.home-assistant.io/integrations/apsystems/
