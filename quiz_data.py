"""Contenido de la evaluación simplificada: 11 módulos, 11 preguntas de opción múltiple.

Una pregunta por módulo. Todo el material proviene de la charla "Dispensación Hospitalaria:
Procesos, Seguridad y el Valor Humano".
"""

LETTERS = ["A", "B", "C", "D"]

LEVELS = [
    {
        "id": 1,
        "icon": "🚪",
        "name": "El Umbral",
        "subtitle": "Dispensar no es entregar",
        "briefing": [
            "La <b>dispensación farmacológica</b> es el acto profesional de entregar un medicamento "
            "<b>incluyendo información para su uso y seguimiento</b>.",
            "Incluye validación de la prescripción, preparación de dosis unitarias y asesoramiento clínico "
            "(administración, efectos adversos, interacciones).",
            "En el hospital se entrega a <b>enfermería y médicos</b>: exige un <b>rigor absoluto</b>.",
        ],
        "tip": "Entregar es un traspaso. Dispensar es un acto profesional con información y seguimiento.",
        "questions": [
            {
                "q": "¿Qué distingue a la dispensación de una simple entrega de medicamento?",
                "options": [
                    "Que solo se realiza en farmacias comunitarias",
                    "Que incluye información para el uso y el seguimiento del tratamiento",
                    "Que obliga al paciente a firmar la receta",
                    "Que solo aplica a medicamentos controlados",
                ],
                "answer": 1,
                "why": "Dispensar suma información y seguimiento al acto de entregar: por eso es un acto profesional y no un simple traspaso de producto.",
                "source": "Diapositiva 3",
            }
        ],
    },
    {
        "id": 2,
        "icon": "🎯",
        "name": "El Propósito",
        "subtitle": "Efectividad máxima, riesgo mínimo",
        "briefing": [
            "Propósito: <b>efectividad máxima con riesgo mínimo</b>.",
            "<b>Uso correcto y seguro:</b> que el paciente reciba el producto exacto y la información vital.",
            "<b>Uso hospitalario:</b> entrega controlada y trazable dentro del recinto, con dosis personalizadas y acompañamiento continuo.",
        ],
        "tip": "Cada paso del proceso existe para mover una sola aguja: más efectividad, menos riesgo.",
        "questions": [
            {
                "q": "¿Cuál resume mejor el propósito fundamental de la dispensación?",
                "options": [
                    "Vender la mayor cantidad de medicamentos posible",
                    "Lograr la efectividad máxima con el riesgo mínimo",
                    "Reducir la cantidad de personal de farmacia",
                    "Acelerar el alta del paciente",
                ],
                "answer": 1,
                "why": "La charla lo sintetiza en una frase: efectividad máxima, riesgo mínimo. Todo lo demás (validación, dosis unitarias, seguimiento) sirve a ese fin.",
                "source": "Diapositiva 4",
            }
        ],
    },
    {
        "id": 3,
        "icon": "💊",
        "name": "Las Tres Puertas",
        "subtitle": "Tipos de dispensación",
        "briefing": [
            "<b>Hospitalizados:</b> ciclo de 24 horas (dosis unitarias o totales), con validación previa del farmacéutico y/o auxiliar.",
            "<b>Ambulatorios:</b> tratamientos complejos no disponibles en farmacias comunitarias (trasplantados, quimioterapia oral, diálisis).",
            "<b>Controlados:</b> estupefacientes y psicotrópicos, con cumplimiento estricto de la Ley 50-88 y entrega exclusiva a personal autorizado.",
        ],
        "tip": "Tres puertas, tres niveles de control. La puerta equivocada es un error de seguridad.",
        "questions": [
            {
                "q": "¿Cuál es el ciclo habitual de dispensación para un paciente hospitalizado?",
                "options": [
                    "Una sola entrega al mes",
                    "Un período de 24 horas, en dosis unitarias o totales",
                    "Cada 7 días, en dosis totales",
                    "Solo cuando el paciente lo solicita",
                ],
                "answer": 1,
                "why": "El ciclo es de 24 horas, con dosis unitarias o totales y validación previa de la prescripción.",
                "source": "Diapositiva 5",
            }
        ],
    },
    {
        "id": 4,
        "icon": "📝",
        "name": "La Receta Perfecta",
        "subtitle": "Componentes clave y errores de prescripción",
        "briefing": [
            "Una orden médica completa permite <b>validar</b>: paciente, medicamento, dosis, vía, frecuencia, fecha y <b>firma/sello del prescriptor</b>.",
            "La receta correcta es <b>legible y completa</b>: sin datos faltantes no hay dispensación segura.",
            "Ante una receta con errores (dosis, vía, interacción): <b>no se dispensa</b>, se notifica al farmacéutico.",
        ],
        "tip": "Una receta incompleta no es un trámite: es una alerta de seguridad.",
        "questions": [
            {
                "q": "¿Cuál de estos elementos es imprescindible en toda orden médica?",
                "options": [
                    "El color del papel de la receta",
                    "La marca del hospital",
                    "La firma y el sello del prescriptor",
                    "El precio del medicamento",
                ],
                "answer": 2,
                "why": "Sin firma y sello del prescriptor no hay orden válida: es la garantía de que la prescripción es auténtica y responsable.",
                "source": "Diapositivas 6 y 7",
            }
        ],
    },
    {
        "id": 5,
        "icon": "🛡️",
        "name": "Los 7 Correctos",
        "subtitle": "El escudo de la seguridad",
        "briefing": [
            "<b>Paciente · Medicamento · Dosis · Vía · Momento · Motivo · Documentación.</b>",
            "Siete verificaciones que se cruzan antes de que el medicamento llegue al paciente.",
            "Se sostienen con identificación rigurosa, protocolos de higiene y seguimiento clínico continuo.",
        ],
        "tip": "Los 7 correctos no son una lista para memorizar: son un ritual de verificación.",
        "questions": [
            {
                "q": "¿Cuál de estos NO es uno de los 7 correctos de la dispensación?",
                "options": [
                    "Paciente correcto",
                    "Precio correcto",
                    "Vía correcta",
                    "Momento correcto",
                ],
                "answer": 1,
                "why": "Los siete son: paciente, medicamento, dosis, vía, momento, motivo y documentación. El precio no forma parte del escudo de seguridad.",
                "source": "Diapositiva 8",
            }
        ],
    },
    {
        "id": 6,
        "icon": "🔗",
        "name": "La Cadena",
        "subtitle": "Los 6 pasos del flujo operativo",
        "briefing": [
            "<b>1.</b> Ingresar las órdenes de medicamentos e insumos.",
            "<b>2.</b> Solicitar por el sistema los insumos y medicamentos de cada paciente.",
            "<b>3.</b> Consultar el aplicativo, dosificar cantidades, descargar inventario y enviar a facturación.",
            "<b>4.</b> Alistar los medicamentos e insumos.",
            "<b>5.</b> Verificar contra lo ordenado y entregar al Jefe de Enfermería de piso.",
            "<b>6.</b> Enfermería recibe, verifica contra la orden médica y firma el recibido.",
        ],
        "tip": "La cadena se rompe en el eslabón que se salta. Ningún paso es opcional.",
        "questions": [
            {
                "q": "¿Cuál es el Paso 1 del flujo operativo de la cadena de suministro?",
                "options": [
                    "Alistar los medicamentos e insumos",
                    "Ingresar las órdenes de medicamentos e insumos",
                    "Enviar a facturación",
                    "Firmar el recibido",
                ],
                "answer": 1,
                "why": "Todo comienza con la orden: ingresar las órdenes de medicamentos e insumos en el sistema.",
                "source": "Diapositiva 9",
            }
        ],
    },
    {
        "id": 7,
        "icon": "⚠️",
        "name": "Territorio LASA",
        "subtitle": "Nombres y apariencias que engañan",
        "briefing": [
            "<b>LASA</b> (Look-Alike / Sound-Alike): medicamentos que se parecen en nombre, fonética o envase.",
            "<b>Cefalosporinas:</b> CefaLEXINA · CefaLOTINA · CefoTAXIMA.",
            "<b>Vasoactivos:</b> DOBUTamina vs. DOPamina.",
            "<b>Emergencia:</b> Adrenalina/EPINEFRINA vs. ATROPINA.",
            "<b>Fonética:</b> HidroCLOROTIAZIDA vs. HidroCORTISONA.",
        ],
        "tip": "Si dos nombres se parecen, la salvación está en la etiqueta, no en la memoria.",
        "questions": [
            {
                "q": "¿Qué significa LASA?",
                "options": [
                    "Lotes de alta seguridad asistencial",
                    "Medicamentos de nombre o apariencia similares (Look-Alike, Sound-Alike)",
                    "Lista de antibióticos de suministro anual",
                    "Logística de almacenamiento sanitario",
                ],
                "answer": 1,
                "why": "LASA agrupa los medicamentos que se parecen al oído o a la vista: el riesgo es la confusión, no la potencia del fármaco.",
                "source": "Diapositiva 10",
            }
        ],
    },
    {
        "id": 8,
        "icon": "⚖️",
        "name": "La Ley",
        "subtitle": "Decreto 246-06 y Ley 50-88",
        "briefing": [
            "El <b>Decreto No. 246-06</b> regula fabricación, almacenamiento, dispensación y control de medicamentos.",
            "Incluye la <b>Sección IV: Farmacias Hospitalarias</b> y la <b>Sección V: Suministro de Medicamentos</b> (hospitalizados y urgencias).",
            "Capítulos sobre prescripción y dispensación, uso racional de medicamentos, y deberes y derechos del ciudadano.",
            "La <b>Ley 50-88</b> rige los estupefacientes y psicotrópicos.",
        ],
        "tip": "La ley no es un adorno: es la estructura que hace exigible la seguridad.",
        "questions": [
            {
                "q": "¿Qué regula el Decreto No. 246-06?",
                "options": [
                    "Solo los precios de los medicamentos",
                    "La fabricación, almacenamiento, dispensación y control de medicamentos",
                    "Únicamente la publicidad farmacéutica",
                    "Los horarios de las farmacias comunitarias",
                ],
                "answer": 1,
                "why": "Es el reglamento que cubre el ciclo completo del medicamento: fabricación, almacenamiento, dispensación y control.",
                "source": "Diapositiva 11",
            }
        ],
    },
    {
        "id": 9,
        "icon": "🧪",
        "name": "El Farmacéutico",
        "subtitle": "Autoridad clínica",
        "briefing": [
            "<b>A. Validación</b> de interacciones e idoneidad · <b>B. Preparación individualizada</b> en entornos estériles.",
            "<b>C. Conciliación</b> ingreso/alta · <b>D. Asesoramiento</b> a pacientes, enfermeras y médicos.",
            "<b>E. Control y seguimiento</b> farmacoterapéutico · <b>F. Gestión de stock</b>.",
            "<b>G. Prevención de errores</b>: reenvase y alertas electrónicas.",
        ],
        "tip": "El farmacéutico diseña las barreras; no solo las usa.",
        "questions": [
            {
                "q": "¿Cuál es una función clínica del farmacéutico hospitalario?",
                "options": [
                    "Validar interacciones e idoneidad de la prescripción",
                    "Cobrar la factura del paciente",
                    "Transportar los medicamentos entre pisos",
                    "Archivar las recetas vencidas",
                ],
                "answer": 0,
                "why": "La validación clínica (interacciones, idoneidad) es el primer filtro profesional del farmacéutico sobre la prescripción.",
                "source": "Diapositiva 12",
            }
        ],
    },
    {
        "id": 10,
        "icon": "🧰",
        "name": "El Auxiliar",
        "subtitle": "Operaciones tácticas, valor humano",
        "briefing": [
            "<b>Filtro de seguridad:</b> identificar errores en recetas (dosis, interacciones, vías) y notificar al farmacéutico.",
            "<b>Preparación y etiquetado:</b> procedimientos estrictos de identificación y suministro.",
            "<b>Control de normativas:</b> estándares legales y protocolos de almacenamiento.",
            "<b>Soporte técnico y administrativo:</b> información precisa, inventario, pedidos y confidencialidad absoluta.",
        ],
        "tip": "El auxiliar es la primera y la última mirada sobre el medicamento.",
        "questions": [
            {
                "q": "El rol del auxiliar como «filtro de seguridad» consiste en…",
                "options": [
                    "Identificar errores en las recetas y notificarlos al farmacéutico",
                    "Modificar la prescripción cuando hay dudas",
                    "Autorizar la entrega de controlados",
                    "Decidir el alta del paciente",
                ],
                "answer": 0,
                "why": "El auxiliar detecta (dosis, interacciones, vías) y escala al farmacéutico. Detectar y notificar, no corregir por cuenta propia.",
                "source": "Diapositiva 13",
            }
        ],
    },
    {
        "id": 11,
        "icon": "🤝",
        "name": "Sinergia Final",
        "subtitle": "Sinergia y corazón de farmacia",
        "briefing": [
            "<b>Farmacéutico:</b> enfoque clínico y estratégico — validación, preparación estéril, asesoramiento avanzado, diseño de barreras.",
            "<b>Auxiliar:</b> enfoque operativo y táctico — verificación técnica preliminar, etiquetado, normas de almacenamiento, detección primaria.",
            "Juntos garantizan la seguridad absoluta del paciente.",
            "Y detrás de cada dosis verificada late el compromiso por la vida humana: empatía, actitud positiva, disposición, atención.",
        ],
        "tip": "La ciencia guía, la ley estructura, el corazón cura.",
        "questions": [
            {
                "q": "¿Qué aporta el auxiliar en la sinergia con el farmacéutico?",
                "options": [
                    "El diseño de las barreras de seguridad",
                    "La verificación técnica preliminar, el etiquetado y la detección primaria de errores",
                    "La validación clínica de interacciones",
                    "La prescripción de tratamientos",
                ],
                "answer": 1,
                "why": "El auxiliar aporta el enfoque operativo y táctico: verificación preliminar, etiquetado, cumplimiento de almacenamiento y detección primaria de errores.",
                "source": "Diapositiva 14",
            }
        ],
    },
]

TOTAL_QUESTIONS = sum(len(level["questions"]) for level in LEVELS)

RANKS = [
    (0.95, "EXCELENCIA EN DISPENSACIÓN", "🏆", "Dominio total del proceso, la ley y el factor humano."),
    (0.85, "GUARDIÁN DE LA SEGURIDAD", "🥇", "Rigor de nivel experto: el paciente está en buenas manos."),
    (0.70, "ESPECIALISTA EN FORMACIÓN", "🥈", "Base sólida. Repasa LASA y los 7 correctos para mejorar tu resultado."),
    (0.00, "APRENDIZ COMPROMETIDO", "🥉", "El primer paso ya está dado. Repasa los módulos y vuelve a intentarlo."),
]


def rank_for(accuracy: float):
    for threshold, title, icon, message in RANKS:
        if accuracy >= threshold:
            return title, icon, message
    # Corrección para desempaquetar correctamente la tupla del último rango
    threshold, title, icon, message = RANKS[-1]
    return title, icon, message
