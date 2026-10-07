# Escaneé mi detector de phishing con AURI (Endor Labs): 93 hallazgos, 23 después de arreglar

Mi proyecto, **MailDefender / PhishGuard**, analiza correos sospechosos (FastAPI + React + un clasificador ML). Ironía: una herramienta de seguridad con dependencias viejas. Usé el MCP de **AURI** (Endor Labs, plan gratis Developer Edition) desde Claude Code para escanear el repo y arreglar lo que saliera.

## Setup (y los tropiezos)

El plan gratis no requiere cuenta ni tenant: el propio servidor MCP abre el login en el navegador (GitHub, GitLab o Google) la primera vez.

```bash
claude mcp add endor-cli-tools -- npx -y endorctl ai-tools mcp-server
```

Tres lecciones:

1. **En Windows, `npx` no alcanzó a bajar el binario** (~360 MB, se descarga en el postinstall) y el servidor aparecía como "Failed to connect". Solución: `npm i -g endorctl` y apuntar el MCP directo al `.exe`.
2. **No uses `endorctl init`** para el plan gratis. Me pidió un tenant, falló con 403 y terminé en "No authorized tenant found". Esa ruta es para el plan Enterprise.
3. **No mates el proceso `endorctl` mientras espera el login**: es el propio MCP con el puerto 30000 abierto esperando el callback.

## Qué encontró (93 hallazgos)

| Tipo | Cantidad | Dónde |
|---|---|---|
| Dependencias (SCA) | 69 | `aiohttp 3.10.5` (31), `python-multipart` (8), `starlette` (7), `aiosmtplib`, vite/postcss en frontend |
| SAST crítico | 15 | `ml/build_dataset.py`, uso de `random` |
| SAST alto | 2 | `ml/build_dataset.py`, `urllib` y path traversal |
| SAST medio | 7 | `str(e)` devuelto al cliente en 5 scanners |
| Secretos | 0 | |

## Qué arreglé

**Dependencias.** Fijé versiones corregidas en `requirements.txt`: fastapi 0.115 → 0.142.3 (arrastra starlette a 1.x), aiohttp → 3.14.4, python-multipart → 0.0.32, aiosmtplib 3 → 5.1.3, python-dotenv → 1.2.4. Antes de commitear probé la app en un venv aparte: import, `/health`, `/docs` y `/analyze` con un `.eml` real y con form data, todo 200. En el frontend, `npm audit fix` y Vite 5 → 6.4.3. El build pasa.

**Fuga de información (CWE-209).** Los scanners de VirusTotal, AbuseIPDB, urlscan y el analizador AI devolvían `str(e)` en la respuesta. Ahora el detalle va al log y el cliente recibe un mensaje genérico:

```python
except Exception:
    logger.exception("VirusTotal URL lookup failed for %s", url)
    return {"status": "error", "url": url, "error": "VirusTotal lookup failed"}
```

## Qué NO arreglé (y por qué)

- **15 "críticos" por `random`**: falso positivo. Es el generador de datos sintéticos de entrenamiento del ML, no genera tokens ni claves. Cambiarlo a `secrets` rompería la reproducibilidad del dataset. Un escáner no distingue el propósito: hay que triar.
- **`urllib` y path traversal en `build_dataset.py`**: script offline de desarrollo, con URL fija y sin extraer a disco. Riesgo bajo, pendiente de endurecer.
- **7 avisos en Tailwind 3** (`braces`, `postcss-selector-parser`): transitivos de herramientas de build, sin parche. El arreglo implica migrar a Tailwind 4, que es un cambio mayor aparte.

## Resultado

**93 → 23 hallazgos.** De los 23 restantes, 15 son el falso positivo de `random`; los demás son dev-only, scripts offline o sin parche upstream (por ejemplo `tokenizers`, CVE sin versión corregida). Todas las vulnerabilidades de `aiohttp`, `python-multipart`, `starlette` y `aiosmtplib` quedaron cerradas.

## Conclusiones

- El valor real estuvo en las dependencias: 69 de 93, casi todas por no haber actualizado `aiohttp` en un año.
- Un escáner SAST da falsos positivos; hay que revisar cada uno, no "poner a cero".
- Prueba el upgrade antes de fijar versiones: saltos de starlette 0.38 → 1.x y aiosmtplib 3 → 5 no rompieron nada aquí, pero eso se verifica, no se asume.
- `security_review` de AURI es solo Enterprise; `scan` cubre el plan gratis.
