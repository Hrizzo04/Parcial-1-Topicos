# Ficha técnica — Agente Analítico BDO

## 1. Identificación

| Propiedad | Descripción |
|---|---|
| Nombre | Agente Analítico BDO |
| Tipo | Aplicación académica de línea de comandos |
| Lenguaje | Python |
| Motor de datos | PostgreSQL alojado en Supabase |
| Persistencia de trazabilidad | SQLAlchemy ORM, tablas con prefijo `bdoo_` |
| Entrada principal | `main.py` |

## 2. Propósito y alcance

El sistema recibe preguntas gerenciales sobre ventas, las clasifica mediante
reglas deterministas y las relaciona con consultas SQL predefinidas. Ejecuta
esas consultas contra el Data Mart, construye una respuesta, registra la
trazabilidad en la BDOO y ofrece una matriz de 12 escenarios junto con un modo
interactivo.

El Data Mart esperado contiene la tabla de hechos `FactVentas` y las
dimensiones `DimTiempo`, `DimCliente`, `DimProducto`, `DimSucursal` y
`DimCanal`. Las consultas dependen de sus nombres de tabla y columna, incluidos
los nombres con mayúsculas y acentos entrecomillados.

## 3. Arquitectura y módulos

| Módulo | Responsabilidad |
|---|---|
| `main.py` | Inicializa la BDOO, prepara usuario y sesión, ejecuta los 12 casos y abre la consola interactiva. |
| `agent_logic.py` | Interpreta preguntas, aplica controles, selecciona consultas, mide ejecución y registra resultados y respuesta. |
| `queries_catalog.py` | Define el catálogo de SQL y su mapeo por identificador. |
| `datamart_db.py` | Conecta con el Data Mart, inspecciona tablas y columnas y ejecuta consultas de lectura. |
| `database.py` | Configura la conexión y sesiones ORM de la BDOO; crea las tablas que falten. |
| `models_bdoo.py` | Define las entidades SQLAlchemy y relaciones de persistencia. |
| `crear_session.py` | Script auxiliar para crear un usuario gerencial y una sesión activa. |
| `config.py` | Carga variables de entorno y configuración de la conexión del Data Mart. |

## 4. Flujo de procesamiento

1. `main.py` llama a `inicializar_bdoo()` y crea las tablas BDOO ausentes.
2. Se abre una sesión de base de datos para la BDOO y otra conexión para el
   Data Mart.
3. La aplicación comprueba la conexión al Data Mart y obtiene o crea el usuario
   gerencial y una sesión activa.
4. `AgenteAnaliticoEngine.procesar_pregunta()` registra el texto original.
5. El motor identifica intención, métrica, dimensión, periodo y parámetros;
   rechaza los casos interceptados por sus reglas.
6. La consulta seleccionada se ejecuta en el Data Mart y se mide su duración.
7. El resultado, la respuesta, la fuente y las reglas aplicadas se guardan en
   las entidades BDOO.
8. La matriz inicial ejecuta los escenarios P01–P12 y luego permite preguntas
   adicionales en modo interactivo.

## 5. Modelo de datos BDOO

Las nueve entidades ORM crean estas tablas:

| Entidad | Tabla | Función |
|---|---|---|
| `Usuario` | `bdoo_usuario` | Identidad y rol de quien consulta. |
| `Sesion` | `bdoo_sesion` | Sesión del usuario y estado activo. |
| `Pregunta` | `bdoo_pregunta` | Texto y fecha de cada pregunta. |
| `Intencion` | `bdoo_intencion` | Tipo de análisis, métrica, dimensión, periodo y operación. |
| `ConsultaAnalitica` | `bdoo_consulta_analitica` | SQL ejecutado y parámetros serializados. |
| `ResultadoConsulta` | `bdoo_resultado_consulta` | Filas, datos JSON y tiempo de ejecución. |
| `RespuestaAgente` | `bdoo_respuesta_agente` | Respuesta, interpretación gerencial y advertencias. |
| `FuenteDato` | `bdoo_fuente_dato` | Tabla de hechos y dimensiones consultadas. |
| `ReglaValidacion` | `bdoo_regla_validacion` | Resultado y observaciones de reglas aplicadas. |

Relaciones principales: un usuario tiene varias sesiones; una sesión tiene
varias preguntas; cada pregunta se vincula con una intención; intención,
consulta, resultado y respuesta forman la cadena analítica; cada respuesta
puede registrar fuentes y reglas de validación.

`AgenteAnaliticoEngine` es la clase orquestadora, no una tabla ORM adicional.

## 6. Catálogo analítico

| ID | Análisis |
|---|---|
| Q1 | Ingreso neto agrupado por año y mes. |
| Q2 | Ranking de categorías por margen bruto; recibe límite parametrizado. |
| Q3 | Sucursal con mayor ticket promedio. |
| Q4 | Volumen e ingreso agregados por segmento de cliente. |
| Q5 | Canal con mayor venta neta. |
| Q6 | Margen e ingreso agregados por canal para meses entre dos parámetros. |
| Q7 | Producto con mayor facturación dentro de una categoría. |

### Limitaciones funcionales conocidas

- Q4 actualmente agrega el volumen por segmento, pero no compara dos periodos
  ni calcula la reducción temporal solicitada por el enunciado.
- Q6 acepta `mes_inicio` y `mes_fin`; el enrutamiento actual asigna un rango
  fijo y no busca automáticamente los tres últimos meses disponibles.
- La clasificación de preguntas se basa en palabras clave y categorías
  conocidas; no es un modelo de lenguaje ni un parser general de lenguaje
  natural.
- La respuesta gerencial es una plantilla con conteo e interpretación general;
  no resume los valores individuales de las filas.
- Los 12 casos son procesados en secuencia por `main.py`; su ejecución persiste
  registros de prueba en la BDOO.

## 7. Dependencias

Las dependencias se declaran en `requirements.txt`:

- SQLAlchemy 2.x para conexiones y ORM.
- `psycopg2-binary` como driver PostgreSQL.
- `python-dotenv` para cargar variables desde `.env`.

No se requiere una API key de Supabase para conectarse por PostgreSQL. Se usa
una URL de conexión de base de datos y la contraseña de PostgreSQL.

## 8. Configuración y ejecución

La configuración local se guarda en `agente_analitico_bdo/.env`:

```env
SUPABASE_DATABASE_URL=postgresql://USUARIO:CONTRASENA@HOST:PUERTO/postgres?sslmode=require
SUPABASE_DB_SCHEMA=public
SQL_ECHO=false
```

No guardar credenciales reales en el repositorio. La raíz incluye reglas de
`.gitignore` para `.env`, entornos virtuales y bytecode.

Desde la raíz del proyecto:

```bash
source venv/bin/activate
python -m pip install -r agente_analitico_bdo/requirements.txt
python agente_analitico_bdo/main.py
```

La primera ejecución necesita permiso para crear las nueve tablas BDOO en el
esquema configurado. `create_all()` crea tablas que no existen, pero no es un
sistema de migraciones para actualizar tablas ya existentes. Para una base
compartida o productiva, revisar los cambios de esquema y los permisos antes de
iniciar.

## 9. Seguridad y operación

- Las consultas de negocio están declaradas en el catálogo, no se construyen
  concatenando valores de usuario.
- Los valores variables deben enviarse como parámetros SQLAlchemy.
- La conexión del Data Mart valida que el texto de consulta empiece con
  `SELECT` o `WITH`; esta comprobación básica debe complementarse con permisos
  PostgreSQL de solo lectura y no sustituye un parser SQL.
- Las tablas BDOO contienen preguntas, consultas y resultados; no registrar
  secretos ni datos personales innecesarios en el texto de la pregunta.
- No habilitar `SQL_ECHO` en entornos donde los parámetros o datos puedan ser
  sensibles.
- Mantener `.env` local, rotar secretos expuestos y usar un usuario de base de
  datos con los permisos mínimos necesarios.
