# MasuCon Treiber 2.0
Dieses Skript verbindet einen modifizierten Controller für "Densha de Go!" (Fahr-Brems-Hebel TCPP-20001) mit auf PC emulierten Simulatoren wie "The Keihin Kyuukou - Train Simulator Real". Es verbindet sich über serielle Kommunikation mit dem Arduino im MasuCon. Die empfangenen Zustandsinformationen werden dann in entsprechende Tastenanschläge umgewandelt.

## Abhängigkeiten
Der Treiber ist von zwei Modulen abhängig:
 - pyserial für serielle Kommunikation
 - pynput für Simulation von Tastenanschlägen

Beide können mit diesem Befehl in der Kommandozeile installiert werden:
```python -m pip install pyserial, pynput```

## Datenfluss
Der aktuelle Fahrstufe wird vom MasuCon als Zahl zwischen ??? und ??? als String empfangen. Der String endet mit ```\r\n``` und wird zuerst zu einem Integer umgewandelt.
Dann wird die Fahrstufe auf den vom Simulator unterstützen Bereich angepasst:
 - Werte größer als maximale Fahrstufe wird auf maximale Fahrstufe begrenzt
 - Werte zwischen der maximalen Betriebsbremsstufe und dem Schnellbremsschwellenwert werden zu maximaler Betriebsbremsung
 - Werte nach dem Schnellbremsschwellenwert werden auf die Schnellbremsstufe begrenzt 

 Nicht jede Stufe kann direkt im Simulator eingestellt werden, die meisten müssen über mehrmaliges Drücken von D-Pad Up oder D-Pad Down schrittweise erreicht werden. Ohne Feedback vom Simulator muss das Skript deswegen den vermuteten aktuellen Zustand des Fahr-Brems-Hebels im Simulator mitverfolgen. 
 
 Nachdem eine neue Zielstufe empfangen wurde, wird diese mit der vermuteten aktuellen Stufe verglichen. Eine Liste von allen Stufen dazwischen wird erzeugt, hier am Beispiel ```P1 -> B2```:
 ```
 Stufen:  P1 N B1 B2
 ```

 Hier könnte nun 3 mal D-Pad Down gesendet werden:
```
Stufen:  P1 N B1 B2
Befehle:    D D  D
```

In "Trainsim Real" können jedoch bestimmte Stufen direkt angefahren werden:
```
Stufen:  P1 N B1 B2
Befehle:    N B1 D
```

Man kann also von der Zielstufe beim nächsten absoluten Befehl anfangen:
```
Stufen:  P1 N B1 B2
Befehle:      B1 D
```

So kann man teilweise die Zahl der benötigten Tastendrücke deutlich reduzieren. 

Absolute Befehle ermöglichen auch einen relativ sicheren Rückschluss auf die tatsächlich eingestellte Stufe im Simulator, die sonst nur mit einer gewissen Unsicherheit ermittelt werden kann. Bei Treiber- oder Simulatorstart ist sie komplett unbekannt, aber auch danach besteht die Gefahr, dass z.B. ein gesendeter Befehl vom Simulator nicht verarbeitet wurde. Das wird einerseits in Kauf genommen, andererseits aber durch einstellbare Verzögerungen beim Tastenanschlag unwahrscheinlicher gemacht. 

## Einstellungen
### JR EAST Train Simulator
```
"lever_max_power": 5,
"lever_max_service_brake": -8,
"lever_thresh_emergency_brake": -9,
"buttons": {
    "up": "m_scrolldown",
    "down": "m_scrollup",
    "n": "m_middle"
},
```

### The Keihin Kyuukou - Train Simulator Real (PCSX2)
```
"lever_max_power": 5,
"lever_max_service_brake": -5,
"lever_thresh_emergency_brake": -6,
"buttons": {
    "up": "u",
    "down": "d",
    "n": "n",
    "b1": "b",
    "eb": "e"
},
```