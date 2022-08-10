# MasuCon Treiber 2.0
Verbindet sich über serielle Kommunikation mit dem Arduino im MasuCon. Die empfangenen Zustandsinformationen werden dann in entsprechende Tastenanschläge umgewandelt.

## Abhängigkeiten
Der Treiber ist von zwei Modulen abhängig:
 - pyserial für serielle Kommunikation
 - pynput für Simulation von Tastenanschlägen

Beide können mit diesem Befehl in der Kommandozeile installiert werden:
```python -m pip install pyserial, pynput```
