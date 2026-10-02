# Publicación 1 en LinkedIn

Carrusel: [`carrusel_linkedin.pdf`](carrusel_linkedin.pdf) (6 láminas de
1080 × 1350 px). Se regenera con `python -m proyecto.carrusel`.

| Lámina | Contenido |
|---|---|
| 1 | La pregunta: ¿cuánto contrata el Estado colombiano sin competencia? |
| 2 | Hallazgo 1: 51,6 % del valor por contratación directa; Antioquia 71,7 % |
| 3 | Hallazgo 2: el top 10 nacional suma 12,2 %, pero 824 entidades están concentradas |
| 4 | Hallazgo 3: diciembre, 27,4 billones; noviembre, 69 % directa |
| 5 | Dashboard de Power BI: Resumen, Entidades y Alertas |
| 6 | Método y enlace al repositorio |

Si guardas las capturas del dashboard en `docs/capturas/` (`01_resumen.png`,
`02_entidades.png`, `03_alertas.png`), la lámina 5 las muestra en lugar de la
descripción. Vuelve a ejecutar `python -m proyecto.carrusel`.

## Cómo publicarlo

En LinkedIn: **Empezar una publicación → Añadir documento** (el ícono de
documento, no el de imagen), sube el PDF y ponle título: *Contratación pública
en Colombia: 3 hallazgos*. Pega el texto de abajo. El enlace va en el texto
porque los enlaces dentro del PDF no se pueden pulsar.

## Texto

> ¿Cuánto contrata el Estado colombiano sin competencia?
>
> Descargué los 1,05 millones de contratos firmados en 2025 en SECOP II y los
> analicé con Python, SQL (DuckDB) y Power BI. Tres hallazgos:
>
> 1️⃣ La contratación directa es la regla: se lleva el 51,6 % del valor y el
> 77,3 % de los contratos. En Antioquia llega al 71,7 %.
>
> 2️⃣ La concentración es local: los 10 mayores proveedores del país suman solo
> el 12,2 % del valor, pero 824 entidades entregan más de la mitad de su
> presupuesto a 5 proveedores.
>
> 3️⃣ El calendario pesa: diciembre concentra 27,4 billones de pesos y en
> noviembre, antes de la ley de garantías, el 69 % del valor fue por
> contratación directa.
>
> Son patrones para priorizar la revisión, no pruebas de irregularidad.
>
> El código, las consultas SQL y el dashboard están aquí:
> https://github.com/alexgomez-gif/secop-contratacion
>
> ¿Qué otra pregunta le harías a estos datos?
>
> #DataAnalytics #SQL #PowerBI #Python #DatosAbiertos #Colombia
