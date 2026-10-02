# Publicación en NovyPro

NovyPro no recibe el archivo de Power BI: muestra el informe a partir de un
enlace público de **Publicar en la web** de Power BI Service. Este documento
reúne los pasos, el texto listo para pegar y las capturas que faltan.

## Antes de empezar

- **Windows con Power BI Desktop** (noviembre de 2025 o posterior), para abrir
  `powerbi/SECOP.pbip` y publicarlo. Desktop no existe para Linux; sirve otro
  equipo, una máquina virtual o un escritorio en la nube.
- **Cuenta de Power BI Service.** El registro exige un correo de trabajo o de
  institución educativa; no acepta cuentas personales como Gmail u Outlook.
- **Publicar en la web habilitado** por el administrador del inquilino
  (*Configuración de inquilino → Exportación y uso compartido → Publicar en la web*).

Publicar en la web deja el informe **público para cualquiera con el enlace**.
Los datos son abiertos (datos.gov.co) y el modelo ya reemplaza los nombres de
personas naturales por "(persona natural)".

## Pasos

1. Abre `powerbi/SECOP.pbip`, ajusta el parámetro `RutaDatos` y actualiza (ver
   [`powerbi/README.md`](../../powerbi/README.md)). Comprueba las cifras de la
   tabla de comprobación.
2. Toma las capturas (sección siguiente).
3. **Inicio → Publicar** a "Mi área de trabajo".
4. En Power BI Service abre el informe: **Archivo → Insertar informe →
   Publicar en la web (público)** y copia el **enlace** (el primero, no el código
   HTML).
5. En NovyPro: logo verde junto a tu foto → **Publish Project**. Llena los
   campos con el texto de abajo, sube `docs/publicacion/portada.png` como
   portada y, en **Add Interactive Sample → Power BI**, pega el enlace.
6. Añade el enlace de NovyPro al [README](../../README.md) y avísame para hacer
   el commit.

## Texto para el formulario

**Título**

> Contratación pública en Colombia: contratación directa y concentración de proveedores (SECOP II 2025)

**Descripción**

> Dashboard de tres páginas sobre 1,05 millones de contratos firmados en 2025 en
> SECOP II, la plataforma de compras públicas de Colombia.
>
> - **Resumen:** 177,6 billones de pesos contratados; el 51,6 % del valor va por
>   contratación directa. Diciembre concentra el mayor valor del año.
> - **Entidades:** qué entidades contratan más por vía directa frente a las de su
>   mismo orden y cuánto pesan sus 5 mayores proveedores.
> - **Alertas:** 824 entidades entregan más del 50 % de su valor a 5 proveedores;
>   933 parejas entidad–empresa firman contratos directos encadenados a menos de
>   30 días; 1.546 personas tuvieron 4 o más contratos de servicios simultáneos.
>   Son patrones para revisar, no pruebas de irregularidad.
>
> Pipeline: descarga de la API de datos.gov.co con Python, limpieza documentada y
> modelo estrella en DuckDB/SQL, y modelo semántico con 33 medidas DAX
> (inteligencia de tiempo, TOPN, USERELATIONSHIP). Filtros por departamento,
> modalidad y mes.
>
> Código y documentación: https://github.com/alexgomez-gif/secop-contratacion

**Etiquetas**

> Power BI, DAX, SQL, DuckDB, Python, Contratación pública, Colombia, Open Data

**Portada:** `docs/publicacion/portada.png` (1020 × 730 px, la misma proporción
510 × 365 que pide NovyPro; 64 KB).

## Capturas

Guárdalas en `docs/capturas/` con estos nombres. En Desktop, pon la vista en
*Ajustar a la página*, oculta los paneles laterales y captura solo el lienzo
(Win + Shift + S).

| Archivo | Qué mostrar |
|---|---|
| `01_resumen.png` | Página Resumen sin filtros |
| `02_entidades.png` | Página Entidades sin filtros |
| `03_alertas.png` | Página Alertas sin filtros |
| `04_filtro_departamento.png` | Resumen con un departamento seleccionado (p. ej., Antioquia) |
| `05_modelo.png` | Vista de modelo (tablas y relaciones) |

Cuando estén, esta sección va en el README principal:

```markdown
## Dashboard

![Resumen](docs/capturas/01_resumen.png)
![Entidades](docs/capturas/02_entidades.png)
![Alertas](docs/capturas/03_alertas.png)
```
