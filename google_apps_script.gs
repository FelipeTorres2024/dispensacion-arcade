/**
 * Endpoint de resultados para la webapp de la Charla de Dispensación Hospitalaria.
 *
 * INSTALACIÓN
 * 1. Crea una hoja de cálculo de Google (por ejemplo: "Resultados Charla HGPS").
 * 2. En esa hoja: Extensiones → Apps Script.
 * 3. Pega este archivo completo (no pongas el token aquí).
 * 4. En el editor de Apps Script: Configuración del proyecto → Propiedades del script.
 *    Agrega TOKEN con una cadena larga y aleatoria. Ese valor no se publica.
 * 5. Implementar → Nueva implementación → Aplicación web.
 *    - Ejecutar como: yo
 *    - Quién tiene acceso: cualquier persona
 * 6. Copia la URL /exec. En Streamlit usa:
 *      results_webhook = "https://script.google.com/macros/s/.../exec"
 *      results_token   = "el mismo valor de la propiedad TOKEN"
 * 7. La hoja debe quedar privada; compártela solo con el equipo administrativo.
 */

const TOKEN = PropertiesService.getScriptProperties().getProperty("TOKEN") || "";
const SHEET_NAME = "Resultados";

function json_(obj) {
  return ContentService.createTextOutput(JSON.stringify(obj))
    .setMimeType(ContentService.MimeType.JSON);
}

function getSheet_() {
  const ss = SpreadsheetApp.getActive();
  let sheet = ss.getSheetByName(SHEET_NAME);
  if (!sheet) {
    sheet = ss.insertSheet(SHEET_NAME);
    sheet.appendRow([
      "id", "fecha", "nombre", "modo", "puntos", "aciertos", "total",
      "precision", "mejor_racha", "duracion_seg", "rango", "respuestas_json"
    ]);
    sheet.setFrozenRows(1);
  }
  return sheet;
}

function safeCell_(value) {
  // Evita inyección de fórmulas en Google Sheets (=, +, -, @, tab, CR).
  if (typeof value !== "string") return value;
  return /^[=+\-@\t\r]/.test(value) ? "'" + value : value;
}

function rowFor_(r) {
  return [
    safeCell_(r.id),
    safeCell_(r.created_at),
    safeCell_(r.name),
    r.training ? "Práctica" : "Evaluación",
    r.score,
    r.correct,
    r.total,
    r.accuracy,
    r.best_streak,
    r.elapsed,
    safeCell_(r.rank),
    safeCell_(JSON.stringify(r.answers || []))
  ];
}

function recordFromRow_(row) {
  let answers = [];
  try { answers = JSON.parse(row[11] || "[]"); } catch (err) { answers = []; }
  return {
    id: String(row[0]),
    created_at: String(row[1]),
    name: String(row[2]),
    training: String(row[3]) === "Práctica",
    score: Number(row[4]),
    correct: Number(row[5]),
    total: Number(row[6]),
    accuracy: Number(row[7]),
    best_streak: Number(row[8]),
    elapsed: Number(row[9]),
    rank: String(row[10]),
    answers: answers
  };
}

function doGet() {
  return json_({ ok: true, service: "HGPS · resultados de la charla" });
}

function doPost(e) {
  try {
    if (!e || !e.postData || !e.postData.contents) {
      return json_({ ok: false, error: "sin datos" });
    }
    const body = JSON.parse(e.postData.contents);
    if (!TOKEN || body.token !== TOKEN) {
      return json_({ ok: false, error: "token inválido" });
    }

    const sheet = getSheet_();

    if (body.action === "list") {
      const values = sheet.getDataRange().getValues();
      if (values.length < 2) return json_({ ok: true, records: [] });
      const headers = values.shift();
      const records = values
        .filter(function (row) { return row[0]; })
        .map(recordFromRow_);
      return json_({ ok: true, records: records });
    }

    const r = body.record;
    if (!r || !r.id) return json_({ ok: false, error: "registro inválido" });

    const values = sheet.getDataRange().getValues();
    let rowIndex = -1;
    for (let i = 1; i < values.length; i++) {
      if (String(values[i][0]) === String(r.id)) { rowIndex = i + 1; break; }
    }

    const row = rowFor_(r);
    if (rowIndex > 0) {
      sheet.getRange(rowIndex, 1, 1, row.length).setValues([row]);
    } else {
      sheet.appendRow(row);
    }
    return json_({ ok: true });
  } catch (err) {
    return json_({ ok: false, error: String(err) });
  }
}
