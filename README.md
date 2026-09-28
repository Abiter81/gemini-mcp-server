# Gemini MCP Server für LM Studio

Ein kleiner MCP-Server auf Basis von **Python MCP SDK / FastMCP**, der Fragen über die
Google-Gemini-REST-API `generateContent` beantwortet. Der Server läuft lokal über
**stdio** und stellt das Tool `ask_gemini` bereit.

> Nicht von Google oder LM Studio bereitgestellt. Prompts werden an Google gesendet;
> beachte die Datenschutz- und Nutzungsbedingungen deines Kontos.

## Voraussetzungen

- Python 3.10 oder neuer (Python 3.11+ empfohlen)
- LM Studio mit MCP-Unterstützung
- Gemini-API-Schlüssel aus einer für dein Konto verfügbaren Google-Gemini-API-Quelle
- Internetzugriff vom Rechner, auf dem der Server läuft

## Installation

```bash
cd /pfad/zu/gemini-mcp-server
python3 -m venv .venv
. .venv/bin/activate                 # Windows: .venv\Scripts\activate
python -m pip install -r requirements.txt
```

## Schlüssel sicher konfigurieren

Bevorzugt als Umgebungsvariable (nicht in Git einchecken):

```bash
export GEMINI_API_KEY='DEIN_SCHLUESSEL'
```

Alternativ kann `GEMINI_API_KEY_FILE` auf eine Datei zeigen, die nur eine Schlüsselzeile
enthält. Der Pfad kann absolut oder `~`-bezogen sein:

```bash
chmod 600 ~/.config/gemini/api_key
export GEMINI_API_KEY_FILE="$HOME/.config/gemini/api_key"
```

Wenn beide gesetzt sind, hat `GEMINI_API_KEY` Vorrang. Der Server schreibt den Schlüssel
nicht in Logs oder Antworten. Die Datei `user_self_host_config_example.json` ist nur ein
Beispiel mit Platzhaltern und kein Geheimnisspeicher.

## LM Studio konfigurieren

LM Studio verwendet für lokale MCP-Server eine `mcp.json`. Öffne in LM Studio die MCP-
Einstellungen bzw. die Datei `mcp.json` und füge den Inhalt aus der Beispieldatei ein.
Ersetze **alle** Platzhalter durch absolute Pfade. Für die Umgebungsvariable ist diese
Form möglich:

```json
{
  "mcpServers": {
    "gemini-mcp": {
      "command": "/ABSOLUTER/PFAD/gemini-mcp-server/.venv/bin/python",
      "args": ["/ABSOLUTER/PFAD/gemini-mcp-server/ask_gemini_server.py"],
      "env": {"GEMINI_API_KEY": "DEIN_SCHLUESSEL_NUR_LOKAL"}
    }
  }
}
```

Sicherer ist es, `env` wegzulassen und `GEMINI_API_KEY_FILE` zu verwenden:

```json
"env": {"GEMINI_API_KEY_FILE": "/home/du/.config/gemini/api_key"}
```

Aktiviere in LM Studio die Option, die das Aufrufen von Servern aus `mcp.json` erlaubt,falls deine Version dies verlangt. Starte/verbinde den Server anschließend und erlaube
nur das Tool `ask_gemini`, sofern LM Studio eine Tool-Auswahl anbietet. Die Einstellung
ist versionsabhängig; die offizielle Übersicht steht unter
<https://lmstudio.ai/docs/developer/core/mcp>.

## Nutzung und Optionen

Das Tool akzeptiert `prompt` sowie optional `model` (Standard `gemini-2.5-flash`),
`temperature` (0–2, Standard 0,2) und `max_output_tokens` (1–65536, Standard 2048).
Der Timeout beträgt 60 Sekunden. Netzwerk-, HTTP-, Authentifizierungs-, Timeout- und
ungültige-Antwort-Fehler werden als verständliche Tool-Fehler zurückgegeben.

Der Server prüft Eingaben, begrenzt Prompts auf 100.000 Zeichen und verwendet keine
Datei- oder Shell-Tools. Das ist keine umfassende Sicherheitsgarantie: Prüfe weiterhin
MCP-Berechtigungen, Prompts und die Daten, die du an einen externen API-Dienst sendest.

## Offline-Test

Ohne API-Aufruf können Syntax und Import geprüft werden:

```bash
python -m py_compile ask_gemini_server.py
python -m pip install -r requirements.txt
```

Ein echter Funktionstest benötigt einen gültigen Schlüssel und erzeugt eine externe
Google-API-Anfrage; er ist in diesem Paket nicht automatisch enthalten.

## Dateien und Lizenz

- `ask_gemini_server.py` – FastMCP-Server und REST-Aufruf
- `requirements.txt` – Python-Abhängigkeit  
- `user_self_host_config_example.json` – gültiges Konfigurationsbeispiel
- `.gitignore` – Ausschluss lokaler Geheimnisse und Build-Dateien
- `LICENSE` – mitgelieferte MIT-Lizenz

Keine Garantie, keine Zusicherung von Verfügbarkeit oder Richtigkeit der Gemini-Antworten.

---

## Sicherheitshinweise

1. DO NOT COMMIT API KEYS TO VCS - Keep credentials in your local .gemini_config.json file
2. The implementation itself contains no secrets or hardcoded keys
3. Users should only copy this server template and paste their own configuration
4. Never share or commit your personal .gemini_config.json to any public repository

This license allows commercial use while maintaining a clear separation between 
the documentation package and the self-hosted API key management that users must 
do themselves for security reasons.