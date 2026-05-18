# BlenderProjectorsFork – Property Update Guidelines & Abhängigkeiten

## Property-Update-Guidelines

- **Vektor-Properties (z.B. dimensions):**
  - Setze immer das gesamte Tupel, nicht einzelne Komponenten:
    ```python
    obj.dimensions = (w, h, d)
    ```
  - Einzelne Zuweisungen wie `obj.dimensions[0] = ...` funktionieren nicht zuverlässig.

- **Property-Callbacks:**
  - Callbacks für verschiedene Properties dürfen sich nicht gegenseitig überschreiben, außer explizit gewünscht.
  - Beispiel: `projector_w` (Gehäusebreite) und `w_projection` (Bildbreite) sind unabhängig und beeinflussen sich nicht gegenseitig.
  - Wenn eine Kopplung gewünscht ist, muss sie explizit im Callback codiert werden.

- **Update-Logik:**
  - Die Update-Funktionen für die Projektor-Dimensionen (`update_projector_width`, `update_projector_height`, `update_projector_depth`) rufen immer `update_projector_dimensions` auf, das die Cube-Dimensionen setzt.
  - Die Update-Funktionen für die Projektion (`update_projection_by_width`, ...) ändern ausschließlich die Projektionseigenschaften, nicht die Gehäusegröße.

- **Debugging:**
  - Für die Fehlersuche in Callbacks: Debug-Prints einbauen, um zu prüfen, ob und wann sie getriggert werden.

## Abhängigkeiten und Pattern aus dieser Session

- **projector_w, projector_h, projector_d**
  - Steuern ausschließlich die Größe des Gehäuses (Cube).
  - Werden in der UI und in `update_projector_dimensions` verwendet.

- **w_projection, h_projection, d_projection**
  - Steuern ausschließlich die Bildprojektion.
  - Werden in der UI und in den Projection-Update-Callbacks verwendet.

- **Keine gegenseitige Beeinflussung**
  - Es gibt keine automatische Kopplung zwischen Gehäuse- und Bildwerten.
  - Änderungen an `projector_w` beeinflussen nicht `w_projection` und umgekehrt.

- **Initialisierung**
  - Bei der Initialisierung werden alle Properties explizit gesetzt und die Update-Funktionen einmal aufgerufen.

- **UI**
  - Es gibt getrennte Slider für Gehäuse und Projektion.

- **Sonstiges**
  - Wenn weitere Properties oder Abhängigkeiten hinzukommen, immer explizit dokumentieren, wie sie sich gegenseitig beeinflussen (oder nicht).

---
Letztes Update: 2026-05-18
