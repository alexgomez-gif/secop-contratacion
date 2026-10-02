# Guion del video (2 minutos)

Unas 230 palabras de narración (unos 95 segundos de voz; el resto son pausas
y clics). La columna **En pantalla**
indica qué mostrar mientras hablas. Todas las cifras están en el
[README de Power BI](../../powerbi/README.md#comprobación).

**Grabación:** OBS Studio o la Grabadora de pantalla de Windows (Win + Alt + R),
en 1920 × 1080 y con el informe en pantalla completa. Antes de grabar, limpia
todos los segmentadores.

| Tiempo | En pantalla | Narración |
|---|---|---|
| 0:00–0:15 | Página **Resumen**, sin filtros | "¿Cuánto contrata el Estado colombiano sin competencia y qué tan concentrado está en pocos proveedores? Este dashboard lo responde con 1,05 millones de contratos firmados en 2025 en SECOP II." |
| 0:15–0:35 | GitHub: README y carpeta `sql/` | "Descargué los datos de la API de datos abiertos con Python, documenté cada regla de limpieza y construí un modelo estrella en DuckDB. Las consultas SQL y sus hallazgos están en el repositorio." |
| 0:35–1:00 | **Resumen**: tarjetas, luego el gráfico mensual | "En 2025 se contrataron 177,6 billones de pesos, y el 51,6 % fue por contratación directa. El valor se dispara al final del año: diciembre firma pocos contratos, pero los más grandes. La línea naranja es una media móvil de tres meses hecha con inteligencia de tiempo en DAX." |
| 1:00–1:10 | Seleccionar **Antioquia** en Departamento; luego limpiar | "Los filtros de departamento, modalidad y mes se sincronizan entre páginas. En Antioquia, la contratación directa llega al 71,7 % del valor." |
| 1:10–1:30 | **Entidades**: tabla y top 15 | "En Entidades se ve qué entidades mueven más dinero por vía directa y cuánto se alejan del promedio de su orden. Medellín y el Ministerio de Minas encabezan." |
| 1:30–1:52 | **Alertas**: tarjetas y las dos tablas | "Alertas reúne tres patrones: 824 entidades entregan más de la mitad de su valor a cinco proveedores; 933 parejas entidad–empresa firman contratos directos encadenados a menos de 30 días, y 1.546 personas tuvieron cuatro o más contratos de servicios al mismo tiempo. No son pruebas de irregularidad: son puntos de partida para revisar." |
| 1:52–2:00 | Volver a **Resumen** | "Todo el proyecto, del SQL al modelo de Power BI, está en mi GitHub. Gracias." |

## Antes de publicar el video

- Comprueba que las tarjetas muestren las cifras que narras. Si cambian los
  datos, ajusta el guion.
- Súbelo a YouTube (oculto o público) o a LinkedIn y añade el enlace a NovyPro
  y al README.
