# Hallazgos de AURI en MailDefender: qué salió, cómo se arregló y por qué

Material de apoyo para el post. Escaneo hecho con el MCP de AURI (Endor Labs, Developer Edition) sobre el repo, con `vulnerabilities`, `secrets`, `dependencies` y `sast`, excluyendo `node_modules` y `dist`.

## Resumen

| | Antes | Después |
|---|---|---|
| Total de hallazgos | 93 | 23 |
| Vulnerabilidades en dependencias | 69 | 4 |
| SAST (código propio) | 24 | 19 |
| Secretos expuestos | 0 | 0 |

Las 69 de dependencias se repartían así: 1 crítica, 34 altas, 26 medias y 8 bajas. De ellas se cerraron 65.

## 1. Dependencias del backend (Python)

La causa de casi todo fue una sola: las versiones estaban fijadas en `requirements.txt` desde hace meses y nadie las revisó. Arreglo: subir las versiones fijadas y probar la app.

| Paquete | Antes → después | Advisories | Peor severidad |
|---|---|---|---|
| `aiohttp` | 3.10.5 → 3.14.4 | 31 | Crítica |
| `python-multipart` | 0.0.12 → 0.0.32 | 8 | Alta |
| `starlette` (vía `fastapi`) | 0.38.6 → 1.7.0 (`fastapi` 0.115.0 → 0.142.3) | 7 | Alta |
| `aiosmtplib` | 3.0.1 → 5.1.3 | 3 | Alta |
| `python-dotenv` | 1.0.1 → 1.2.4 | 1 | Media |

### ¿Cuáles importaban de verdad en esta app?

No todas pesan igual. Esto es una estimación mía según cómo se usa cada librería en el código, no una explotación probada.

**Las que sí aplican, y por qué:**

- **`aiosmtplib`, inyección SMTP por CR/LF** (GHSA-v3q9-hj7j-63hq, alta; también GHSA-vxj7-4xrp-5vr4 y CVE-2026-90467). Es la más relevante del escaneo. La app responde al correo reenviado usando la dirección del remitente (`send_analysis_reply(sender_address, ...)`), y esa dirección la controla quien manda el correo. Con saltos de línea en la dirección se podían inyectar comandos o parámetros SMTP. Arreglado en 5.1.1 a 5.1.3.
- **`python-multipart` y `starlette`, denegación de servicio en formularios** (por ejemplo GHSA-59g5-xgcq-4qw3, GHSA-pp6c-gr5w-3c5g, GHSA-f96h-pmfr-66vw). `/analyze` y `/api/v1/scan` aceptan archivos y formularios de cualquiera en internet. Un cuerpo multipart malformado o con cabeceras sin límite podía agotar CPU o memoria. `GHSA-wp53-j4wj-2cfg` (escritura arbitraria de archivos) es distinta: solo aplica con una configuración no predeterminada, que esta app no usa.
- **`starlette` GHSA-82w8-qh3p-5jfq:** los límites de `request.form()` se ignoraban en formularios `urlencoded`, otra vía de agotar memoria en endpoints públicos.

**Las que probablemente no aplican, pero se cierran igual:**

- La mayoría de las 31 de `aiohttp` son del lado servidor (manejo de archivos estáticos, websockets, parser de peticiones). Esta app usa `aiohttp` solo como **cliente** (`ClientSession`) para llamar a VirusTotal, AbuseIPDB, urlscan y al servicio ML. Aun así, varias de cliente sí tocan (redirecciones que filtran cookies, descompresión de respuestas, parser de respuestas HTTP), y actualizar cuesta lo mismo.
- `starlette` GHSA-wqp7-x3pw-xc5r (SSRF por rutas UNC en `StaticFiles`, Windows): la app no usa `StaticFiles` y corre en Linux dentro de Docker.

**Por qué importa aunque no sea explotable hoy:** una dependencia sin parchear queda a un cambio de código de ser alcanzable. Y el costo de arreglarlas todas era una línea por paquete.

### Cómo comprobé que el salto no rompía nada

Subir `fastapi` a 0.142 arrastró `starlette` a 1.x, un salto grande. Antes de fijar versiones lo probé en un venv aparte:

- La app importa sin errores.
- `/health`, `/docs` y `/openapi.json` responden 200.
- `/analyze` responde 200 tanto con un `.eml` subido como con el cuerpo pegado como formulario.
- `/api/v1/scan` responde 401 sin API key, como debe.

Lo que **no** probé: el flujo completo de SMTP entrante/saliente con `aiosmtplib` 5, ni los scanners contra las APIs reales con claves. Conviene verlo en staging.

## 2. Dependencias del frontend (npm)

Todas son de herramientas de build, no del código que corre en el navegador del usuario.

| Paquete | Antes → después | Notas |
|---|---|---|
| `vite` | 5.4.21 → 6.4.4 | GHSA-fx2h-pf6j-xcff (alta, evasión de `server.fs.deny` en Windows) y GHSA-4w7w-66w2-5vf9 |
| `postcss` | 8.5.12 → 8.5.23 | Lectura arbitraria de `.map` (GHSA-r28c-9q8g-f849, alta) |
| `nanoid`, `browserslist`, `source-map-js`, `baseline-browser-mapping` | actualizados con `npm audit fix` | DoS por entradas inválidas o memoria sin límite |
| `esbuild` | → 0.25+ con Vite 6 | GHSA-67mh-4wv8-2f99 (cualquier web podía hacer peticiones al servidor de desarrollo) |
| `@babel/core` | → 7.29.6 | Lectura de archivos vía `sourceMappingURL` |

Solo afectan a quien corre `npm run dev`, no al sitio ya compilado. Aun así, un servidor de desarrollo vulnerable en la máquina de un desarrollador es un riesgo real (páginas web maliciosas pueden hablarle).

## 3. Código propio (SAST)

### Corregido: exposición de errores (CWE-209), 5 de 7 casos

Dónde: `backend/scanners/virustotal.py` (2 sitios), `abuseipdb.py`, `urlscan.py` y `ai_analyzer.py`.

El problema: al fallar una llamada, la función devolvía `str(e)` dentro de la respuesta de la API. Eso puede revelar URLs internas, rutas, versiones o fragmentos de claves en mensajes de excepción. El arreglo es el patrón estándar: el detalle va al log del servidor y el cliente recibe un mensaje fijo.

```python
# antes
except Exception as e:
    return {"status": "error", "url": url, "error": str(e)}

# después
except Exception:
    logger.exception("VirusTotal URL lookup failed for %s", url)
    return {"status": "error", "url": url, "error": "VirusTotal lookup failed"}
```

### Se deja como está: falsos positivos y riesgo bajo

| Hallazgo | Dónde | Decisión y por qué |
|---|---|---|
| 15 críticos, `random` poco seguro (CWE-330) | `ml/build_dataset.py` | Falso positivo. Genera datos sintéticos de entrenamiento, no tokens ni claves. Pasar a `secrets` rompería la reproducibilidad del dataset. |
| Alto, `urllib` con esquemas arbitrarios (CWE-939) | `ml/build_dataset.py` L60 | La URL es una constante fija `https://` en un script manual de desarrollo. |
| Alto, path traversal | `ml/build_dataset.py` L109 | Se leen miembros de un `.tar.bz2` con `extractfile` (en memoria), nunca se extrae a disco. Aun así queda anotado para endurecer. |
| 2 medios, CWE-209 | `ml/build_dataset.py` L62, L120 | Solo imprimen en consola de quien ejecuta el script. |

## 4. Lo que quedó abierto (4 de dependencias)

| Hallazgo | Por qué sigue |
|---|---|
| `braces` GHSA-vfj7-8cjw-p6xm (alta) | Sin parche. Transitivo de Tailwind 3, solo en build. |
| `postcss-selector-parser` GHSA-rj75-hqrm-r3gf (media) | Arreglar implica migrar a Tailwind 4, un cambio mayor que merece su propio PR. |
| `esbuild` GHSA-g7r4-m6w7-qqqr (baja) | Arreglo en 0.28.1, aún no llega con Vite 6. Solo servidor de desarrollo en Windows. |
| `tokenizers` CVE-2026-85670 (media) | Sin versión corregida. Es del servicio ML, no del backend. |

## 5. Lo que me dejó la herramienta

**Sirvió para:**
- Encontrar rápido deuda de versiones que `pip` y `npm` no avisan por sí solos.
- Dar la versión mínima corregida de cada advisory, sin buscar uno por uno.
- Detectar el `str(e)` repetido en cinco archivos, algo que a ojo pasa desapercibido.

**Hay que tener en cuenta:**
- No es un "pasar a cero". 65 de las 69 vulnerabilidades de dependencias se cerraron solo subiendo versiones, pero los 15 "críticos" de `random` son ruido: hay que revisar cada hallazgo en su contexto.
- Mide alcanzabilidad solo en parte (modo rápido, `quick_scan`). La estimación de qué aplica a la app la hice yo leyendo el código.
- `security_review` (revisión de diffs) es solo Enterprise en el plan gratis.
- Primer uso en Windows con fricción: `npx` no alcanzó a bajar el binario de ~360 MB, y no hay que usar `endorctl init` en el plan gratis (pide tenant y falla con 403).
