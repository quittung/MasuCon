# MasuCon Treiber 2.0
Verbindet sich über serielle Kommunikation mit dem Arduino im MasuCon. Die empfangenen Zustandsinformationen werden dann in entsprechende Tastenanschläge umgewandelt.

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