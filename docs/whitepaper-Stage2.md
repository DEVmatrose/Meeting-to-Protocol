# DreamMall Stage2 - BigBlueButton (BBB) Integration

## Überblick

In der Stage2-Version von DreamMall wurde erfolgreich die Integration mit BigBlueButton (BBB) implementiert, um die "Tische"-Funktionalität zu realisieren. Diese Integration ermöglicht es Benutzern, direkt aus der DreamMall-Plattform heraus Videokonferenzen zu erstellen und zu nutzen.

## Implementierte Funktionalität

### Backend-Komponenten

1. **BBBService**: Eine zentrale Serviceklasse, die die Kommunikation mit dem BBB-Server verwaltet
   - Erstellen von Meetings
   - Generieren von Join-URLs für verschiedene Benutzerrollen
   - Abrufen von Meeting-Informationen
   - Beenden von Meetings

2. **BBBController**: API-Controller, der die HTTP-Endpunkte für BBB-Funktionen bereitstellt
   - POST `/api/bbb/meetings`: Erstellt ein neues Meeting
   - GET `/api/bbb/meetings/:meetingId`: Ruft Meeting-Informationen ab
   - GET `/api/bbb/meetings/:meetingId/join`: Generiert Join-URLs für ein Meeting
   - POST `/api/bbb/meetings/:meetingId/end`: Beendet ein Meeting
   - GET `/api/bbb/server-info`: Testet die BBB-Server-Verbindung

3. **Konfiguration und Sicherheit**:
   - Sichere Speicherung der BBB-API-URL und des Secret nur im Backend
   - JWT-Authentifizierung für alle BBB-bezogenen API-Endpunkte

### Frontend-Komponenten

1. **BBB-Diagnose-Tool**: Eine Admin-Komponente zum Testen der BBB-Verbindung
   - Direkte Überprüfung der Verbindung zum BBB-Server
   - Erstellung von Test-Meetings
   - Anzeige detaillierter BBB-Server-Informationen
   - Beitreten zu Test-Meetings als Moderator

2. **BBB-Meeting-Integration**: 
   - Erstellung und Beitritt zu BBB-Meetings aus Projektkontexten heraus
   - Rollenbasierter Zugang (Moderator/Viewer)
   - Nahtlose Einbettung in die DreamMall-Benutzeroberfläche

## Technische Umsetzung

### API-Sicherheit

- Alle BBB-Anfragen werden über das Backend geleitet
- Keine direkten Anfragen vom Frontend zum BBB-Server
- API-Geheimnisse werden ausschließlich im Backend gespeichert
- Rollenbasierte Zugriffskontrolle für Meeting-Verwaltung

### Integration mit dem Projektsystem

- Meetings werden mit Projekten verknüpft über die `projectId`
- Automatische Generierung eindeutiger Meeting-IDs basierend auf Projekt-IDs
- Rollenverteilung basierend auf Projektberechtigungen

## Skalierbarkeit

Die BBB-Integration wurde mit Blick auf zukünftige Skalierung konzipiert:
- Vorbereitung für Load-Balancing mit b3scale
- Flexible Konfiguration für den Einsatz mehrerer BBB-Server

## Nächste Schritte

Die aktuelle Implementation bildet die Grundlage für weitere Funktionen:
- Erweiterte Meeting-Verwaltung (Aufzeichnungen, Präsentationen)
- Integration mit dem Matching-System für thematische Tische
- Automatisierte Transkription und Zusammenfassung von Meetings