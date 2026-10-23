# Seguridad

Webapp de la **Charla de Dispensación Hospitalaria (HGPS)**. Este documento resume
las medidas implementadas y la lista de verificación antes de publicar en GitHub y
Streamlit Community Cloud.

## Modelo de acceso

- **Participante:** no requiere credenciales. Se identifica con el nombre que escribe
  (texto libre, máximo 40 caracteres). No hay conexión con bases de datos del hospital.
- **Administrador/charlista:** entra por `.../?admin=1` o por el enlace al pie de la
  portada, con una contraseña guardada en Streamlit Secrets.
- La sesión de administración expira tras **30 minutos** de inactividad.
- Tras **5 intentos fallidos** se bloquea el acceso durante **60 segundos**.
- El panel no permite modificar ni borrar resultados; solo consultarlos.

## Secretos

Nunca deben subirse al repositorio:

- `admin_password`
- `results_webhook`
- `results_token`
- Cualquier archivo `.streamlit/secrets.toml`
- `data/results.json` (resultados locales con datos personales)

`.gitignore` excluye `.streamlit/secrets.toml`, `data/`, `.pylibs/`, `.tmp/` y
`__pycache__/`. El archivo de ejemplo solo contiene marcadores de posición.

En Streamlit Cloud, los secretos se configuran en **App settings → Secrets**.

## Google Sheets / Apps Script

- El **TOKEN vive en las propiedades del script**, no en `google_apps_script.gs`.
- El webhook debe usar **HTTPS**. La app rechaza URLs no HTTPS.
- Los redirects de Apps Script se limitan a `script.google.com` y
  `*.googleusercontent.com`.
- La hoja debe ser privada y compartirse solo con el equipo administrativo.
- Los nombres se escriben con protección contra **inyección de fórmulas**
  (`=`, `+`, `-`, `@`, tabulación, retorno de carro).
- El endpoint de Apps Script está protegido por el TOKEN; usa una cadena larga y
  aleatoria y rótala si se filtra.

## Datos personales

- Se almacenan nombre, fecha, modo, puntuación, respuestas y un ID interno.
- Son datos personales: informa a los participantes y define una política de
  retención y borrado.
- El archivo local `data/results.json` se crea con permisos `600` cuando el sistema
  operativo lo permite y **no debe subirse** al repositorio.
- La tabla del panel oculta su barra de exportación para reducir el riesgo de
  descargar los datos a CSV/Excel.
- El certificado y el informe se generan en memoria; no se guardan como archivos
  permanentes en el servidor.

## Dependencias

`requirements.txt` fija versiones exactas:

```
streamlit==1.66.1
pillow==13.0.0
```

Revisa periódicamente si hay actualizaciones de seguridad. Si actualizas, ejecuta de
nuevo `python test_app.py` (325 comprobaciones) y prueba el panel.

Auditoría de dependencias con `pip-audit` sobre `requirements.txt`: **sin
vulnerabilidades conocidas** en las versiones fijadas (22/10/2026).

## Lista de verificación antes del `git push`

- [ ] No existe `.streamlit/secrets.toml` en el repositorio.
- [ ] No existe `data/results.json` real en el repositorio.
- [ ] `google_apps_script.gs` no contiene el TOKEN real.
- [ ] El repositorio no incluye `.pylibs/`, `.tmp/` ni `__pycache__/`.
- [ ] La contraseña de administración es larga y única.
- [ ] El TOKEN de Apps Script es largo y está en Script Properties.
- [ ] La hoja de Google es privada.
- [ ] La app está desplegada con HTTPS (Streamlit Cloud lo hace).
- [ ] Los secretos están cargados en Streamlit Cloud, no en el código.
- [ ] Se probó el panel con una cuenta/clave de prueba y se cerró sesión.
- [ ] Se revisó la hoja y no hay datos de prueba reales.
- [ ] GitHub y Google tienen 2FA activo.

## Limitaciones conocidas

- El nombre del participante **no está verificado**; alguien puede escribir otro nombre.
  Si se requiere identidad formal, habría que integrar un directorio o un código único.
- La contraseña de administración no sustituye un sistema de identidad corporativo
  (SSO/MFA). Para un uso institucional amplio, se recomienda poner el panel detrás del
  SSO del hospital o de un proxy autenticado.
- Streamlit Community Cloud es un servicio público; la protección del panel es la
  contraseña + los secretos.
- No hay conexión con la base de datos clínica del hospital; no se debe introducir
  información de pacientes.

## Respuesta ante incidentes

Si sospechas que se filtró la contraseña o el TOKEN:

1. Cambia `admin_password` en Streamlit Secrets.
2. Cambia la propiedad `TOKEN` del script y `results_token` en Secrets.
3. Vuelve a desplegar la aplicación web de Apps Script.
4. Revisa la hoja y los accesos compartidos.
5. Si hay datos reales expuestos, aplica el protocolo de privacidad de la institución.
