# 💊 Charla de Dispensación Hospitalaria

Webapp interactiva en **Streamlit** para repasar la charla
*«Dispensación Hospitalaria: Procesos, Seguridad y el Valor Humano»*,
del **Hospital General de la Plaza de la Salud (HGPS) · Gerencia de Farmacia**.

Cada tema de la presentación es un **módulo** con preguntas de opción múltiple, intentos,
rachas y una pantalla final con certificado descargable.

| | |
|---|---|
| Módulos | 11 (uno por bloque temático) |
| Preguntas | 36 de opción múltiple, con explicación y referencia a la diapositiva |
| Intentos | 3 (o modo práctica sin límite) |
| Duración | 20–30 minutos |
| Cierre | Certificado PNG + informe PDF de 2 páginas (certificado y seguimiento) |
| Sonidos | Acierto, error y finalización, con opción de silencio |
| Dispositivos | Escritorio, tableta y smartphone |

## Diseño institucional

La interfaz usa la paleta oficial del HGPS tomada de <https://hgps.org.do/es/>:

| Color | Uso |
|---|---|
| `#32477B` | Azul institucional: títulos, botones de descarga y textos principales |
| `#00BCD4` | Cyan HGPS: acentos, botones primarios, barra de avance y logo |
| `#BABF33` | Lima HGPS: detalles, estrellas y filete superior |
| `#FFFFFF` / `#F7FBFC` | Fondos claros y tarjetas |
| `#30414F` | Texto de lectura |

La tipografía sigue la línea del sitio del hospital: **Titillium Web** para títulos y
**Open Sans** para el cuerpo. Los contrastes se revisaron para que los textos pequeños
se lean bien sobre fondos claros.

El logo institucional se usa en la cabecera y como favicon desde `assets/`; se embebe
en la app para que no dependa de enlaces externos.

## Arrancar en local

```powershell
pip install -r requirements.txt
streamlit run app.py
```

Se abre en <http://localhost:8501>. En Windows puedes usar el lanzador incluido, que
reutiliza las dependencias de `.pylibs` si existen:

```bat
run.cmd              :: http://127.0.0.1:8501
run.cmd 8600         :: otro puerto
run.cmd 8501 lan     :: expone la app a la red local, para que los asistentes
                     :: entren desde sus teléfonos con http://SU-IP:8501
```

> Si usas PowerShell y la política de ejecución bloquea scripts, `run.cmd` funciona
> igual porque es un archivo por lotes.

## Si cambias el tema o los estilos

Streamlit lee `.streamlit/config.toml` **al arrancar**. Si cambias el tema de oscuro a
claro y solo refrescas el navegador, el servidor antiguo conserva el tema anterior y la
página puede mostrar un parpadeo: los estilos nuevos aparecen un instante y luego vuelve
el fondo viejo.

Para evitarlo:

1. Detén el servidor anterior con `Ctrl+C` en su terminal.
2. Vuelve a arrancar con `run.cmd` o `streamlit run app.py`.
3. Confirma que `.streamlit/config.toml` tenga `base = "light"`.
4. Abre una sola instancia; si tienes otra en el puerto `8501`, ciérrala o usa `8502`.

Un `Ctrl+F5` solo ayuda si el servidor ya se reinició.

Si después de reiniciar el servidor el navegador sigue mostrando el tema anterior, es
porque Streamlit guardó la preferencia de tema en `localStorage`. Bórrala una sola vez
desde la consola del navegador (F12 → Console) en la URL de la app:

```js
Object.keys(localStorage)
  .filter(k => k.startsWith("stActiveTheme"))
  .forEach(k => localStorage.removeItem(k));
location.reload();
```

Esto no borra contraseñas ni cookies de otros sitios; solo la preferencia de tema de
Streamlit para esa ruta. También puedes usar una ventana de incógnito para confirmar que
el servidor ya sirve el tema claro.

## Publicarla gratis (GitHub + Streamlit Community Cloud)

1. Crea un repositorio en GitHub y sube el contenido de esta carpeta.
   **No subas** `.pylibs/` ni `.tmp/`: ya están en `.gitignore`.
2. Verifica que el repositorio incluya `app.py`, `certificate.py`, `quiz_data.py`,
   `requirements.txt` y `.streamlit/config.toml`.
3. Entra en <https://share.streamlit.io> con tu cuenta de GitHub y elige **New app**.
4. Selecciona el repositorio, la rama (`main`) y el archivo principal `app.py`.
5. En *Advanced settings*, elige Python 3.12 (o 3.11) si te lo pide.
   La evaluación funciona sin secretos. Para el panel de administradores, agrega los
   secrets que se explican más abajo.
6. Pulsa **Deploy**. Streamlit instala solo lo indicado en `requirements.txt`
   (`streamlit` y `pillow`).
7. Comparte el enlace con los asistentes; cada uno participa desde su propio navegador y
   la interfaz se adapta a escritorio, tableta y móvil.

La app no depende de archivos locales ni de `.pylibs` para funcionar en la nube: todo
lo necesario está en los archivos versionados.

## Panel de administradores

Los charlistas pueden entrar desde el enlace **“Acceso administradores”** al pie de la
portada, o directamente en `.../?admin=1`. El acceso está protegido por una clave.

El panel muestra la tabla de participantes, permite filtrar por modo (evaluación o
práctica), y al elegir una persona muestra sus métricas, el certificado, la página de
seguimiento y todas sus respuestas. Incluye el botón **“Ver ejemplo”**, que abre la
vista de ejemplo sin salir del contexto administrativo; al volver, regresa al panel.

El **Resumen general** aparece encima de la tabla de participantes y calcula promedios
ponderados de todos los registros filtrados: precisión global (aciertos totales /
preguntas respondidas), puntuación y tiempo promedio, porcentaje con 90 % o más,
precisión por módulo y distribución por rango. También destaca los módulos por debajo
del 70 %.

### Crear la clave de administración

Crea `.streamlit/secrets.toml` en la carpeta del proyecto (no se sube a GitHub):

```toml
admin_password = "una-clave-larga-y-unica"
```

Puedes generar una clave segura con:

```bash
python -c "import secrets; print(secrets.token_urlsafe(24))"
```

Guárdala en un gestor de contraseñas y no la compartas. En Streamlit Cloud, agrégala
en **App settings → Secrets**. Después de crear el archivo, reinicia Streamlit.

### Opción recomendada: Google Sheets (gratis y persistente)

1. Crea una hoja de cálculo de Google y ábrela.
2. Ve a **Extensiones → Apps Script**.
3. Copia el contenido de [`google_apps_script.gs`](google_apps_script.gs).
   **No pongas el token en el código.**
4. En Apps Script: **Configuración del proyecto → Propiedades del script**.
   Agrega `TOKEN` con una cadena larga y aleatoria.
5. Implementar → **Nueva implementación** → **Aplicación web**:
   - Ejecutar como: **yo**
   - Quién tiene acceso: **cualquier persona**
6. Copia la URL terminada en `/exec`.
7. Crea `.streamlit/secrets.toml` a partir de
   [`.streamlit/secrets.toml.example`](.streamlit/secrets.toml.example) y completa:
   ```toml
   admin_password = "una-clave-larga"
   results_webhook = "https://script.google.com/macros/s/.../exec"
   results_token = "el-mismo-valor-de-la-propiedad-TOKEN"
   ```
   En Streamlit Cloud, agrégalos en **App settings → Secrets**.
8. La hoja debe quedar privada: compártela solo con el equipo administrativo.

Si no configuras `results_webhook`, la app usa un archivo local
`data/results.json` (útil para probar en tu equipo). Ese archivo **no persiste** en
Streamlit Cloud, así que para la nube usa Google Sheets.

> **Privacidad:** los nombres, puntuaciones y respuestas son datos de los participantes.
> Mantén la hoja y los secrets restringidos al equipo responsable.

## Seguridad antes de publicar

- **Nunca subas** `.streamlit/secrets.toml`, `data/results.json` ni tokens reales.
  Ya están en `.gitignore`; verifica antes de hacer `git push`.
- Usa una **contraseña de administración larga** y un **TOKEN largo** en las
  propiedades del script de Google. No los escribas en el código.
- Mantén la hoja de Google **privada** y activa **2FA** en GitHub y Google.
- La sesión de administración expira a los **30 minutos** y bloquea temporalmente
  tras **5 intentos** fallidos.
- El webhook debe ser **HTTPS**; los redirects se limitan a dominios de Google.
- La tabla del panel oculta su barra de exportación para reducir el riesgo de
  exportar datos personales a CSV/Excel.
- Los nombres y respuestas son **datos personales**: informa a los participantes,
  limita el acceso y define una política de retención/borrado.
- Si un secreto se filtra, **rota la contraseña y el TOKEN**, revisa la hoja y
  vuelve a desplegar la aplicación.
- Las dependencias están fijadas en `requirements.txt` para despliegues
  reproducibles. Revisa actualizaciones de Streamlit/Pillow con regularidad.

Detalles y lista de verificación: [SECURITY.md](SECURITY.md).

## Cómo funciona

1. **Ficha del participante:** nombre y modo (normal o práctica).
2. **Ideas clave:** antes de cada módulo se muestran las ideas clave del tema.
3. **Pregunta:** cuatro opciones; un clic responde.
4. **Retroalimentación:** acierto/error, puntos, respuesta correcta y *por qué*,
   con la diapositiva de origen.
5. **Intentos y racha:** un fallo cuesta un intento y reinicia la racha; los aciertos
   encadenados valen más (100 + 20 por nivel de racha).
6. **Cierre:** rango, precisión, mapa de módulos con estrellas, repaso de respuestas,
   certificado PNG y un informe PDF de dos páginas: certificado landscape + seguimiento
   con mapa y áreas de mejora.
7. **Sonidos:** tono ascendente al acertar, descendente al fallar y arpegio al completar.
   Se pueden desactivar desde la ficha del participante.

## Estrellas y rangos

Las **estrellas del certificado** dependen de la precisión global:

| Estrellas | Precisión |
|---|---|
| 3 ★ | 90 % o más |
| 2 ★ | 70 % – 89,9 % |
| 1 ★ | 50 % – 69,9 % |
| Sin estrellas | Menos de 50 % |

Los **rangos** son independientes de las estrellas:

| Rango | Precisión |
|---|---|
| Excelencia en Dispensación | 95 % o más |
| Guardián de la Seguridad | 85 % – 94,9 % |
| Especialista en Formación | 70 % – 84,9 % |
| Aprendiz Comprometido | Menos de 70 % |

Por eso un certificado de **3 estrellas** puede ser Guardián (90–94,9 %) o Excelencia
(95 % o más). Las estrellas del **mapa de módulos** son otra escala: 3 = módulo al
100 %, 2 = entre 50 % y 99 %, 1 = menos de 50 %.

Puedes ver un ejemplo sin completar la evaluación desde el enlace
**“Ver ejemplo del certificado”** al pie de la portada, o en `.../?ejemplo=1`.

## Estructura

```
app.py                     # interfaz, estado de la evaluación y estilos
quiz_data.py               # 11 módulos, 36 preguntas, explicaciones y rangos
certificate.py             # certificado PNG con Pillow
report.py                  # página de seguimiento + PDF de 2 páginas
analytics.py               # promedios ponderados y resumen general
audio.py                   # tonos WAV de acierto, error y finalización
storage.py                 # persistencia local o Google Sheets
google_apps_script.gs      # endpoint para guardar/leer resultados en Sheets
test_app.py                # pruebas funcionales (streamlit.testing.AppTest)
requirements.txt
.streamlit/config.toml     # tema claro y color primario HGPS
.streamlit/secrets.toml.example  # plantilla de secrets (sin credenciales reales)
assets/hgps-logo.png       # logo oficial usado en la cabecera
assets/hgps-favicon.png    # favicon cuadrado del HGPS
shots/cert_preview.png     # vista previa del certificado
```

## Editar el contenido

Todo el texto vive en `quiz_data.py`: cada módulo tiene `name`, `icon`, `subtitle`,
`briefing` (ideas clave del módulo), `tip` y una lista de `questions` con
`q`, `options`, `answer` (índice correcto), `why` y `source`.

Para validar los cambios:

```powershell
python test_app.py
```

El script recorre la evaluación completa, comprueba los 11 módulos, la pérdida de intentos,
el modo práctica y la integridad del contenido.

## Nota sobre el contenido

Las preguntas se derivan de las 17 diapositivas originales (conceptos, propósito,
tipos de dispensación, receta, 7 correctos, los 6 pasos, LASA, Decreto 246-06,
Ley 50-88, farmacéutico, auxiliar, sinergia y cierre). Las diapositivas 6 y 7 eran
imágenes de recetas (con y sin errores); su contenido se convirtió en preguntas
sobre los requisitos de una orden médica válida.
