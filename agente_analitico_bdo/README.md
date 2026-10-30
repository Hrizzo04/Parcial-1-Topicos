# Agente Analítico BDO

Proyecto académico en Python que conecta un agente analítico con un Data Mart
de ventas en PostgreSQL/Supabase. Interpreta preguntas gerenciales mediante
reglas, selecciona consultas SQL del catálogo, valida solicitudes, genera una
respuesta y registra pregunta, consulta, resultado y trazabilidad en las tablas
ORM BDOO.

El proyecto contiene una matriz de 12 escenarios de prueba y una consola
interactiva. El esquema esperado del Data Mart incluye `FactVentas` y las
dimensiones `DimTiempo`, `DimCliente`, `DimProducto`, `DimSucursal` y
`DimCanal`.

## Requisitos

- Python 3.10 o posterior.
- Acceso de red a una base PostgreSQL de Supabase.
- Una URL de conexión válida y permisos de lectura para el Data Mart.
- Permisos para crear tablas en el esquema configurado, ya que el arranque
  inicializa las tablas BDOO.

## Instalación e inicio

Ejecuta estos comandos desde la raíz del proyecto:

```bash
# Activar el entorno virtual existente
source venv/bin/activate

# Instalar las dependencias del agente
python -m pip install -r agente_analitico_bdo/requirements.txt

# Crear la configuración local sin sobrescribir un .env existente
if [ ! -f agente_analitico_bdo/.env ]; then
  cp agente_analitico_bdo/.env.example agente_analitico_bdo/.env
fi
```

Edita `agente_analitico_bdo/.env` y sustituye los valores de ejemplo por la URL
de conexión PostgreSQL de Supabase. No compartas ni subas ese archivo.

Inicia el programa desde la raíz:

```bash
python agente_analitico_bdo/main.py
```

Al comenzar, la aplicación crea las tablas BDOO que falten, valida la conexión
al Data Mart, obtiene o crea el usuario gerencial y una sesión activa, ejecuta
la matriz de 12 casos y, después, inicia la consola interactiva. Las
interacciones de prueba también se guardan en la BDOO; usa una base de
desarrollo o ten en cuenta esos registros antes de ejecutar la matriz varias
veces.

Para salir de la consola escribe `salir`, `exit` o `quit`.

## Configuración

El archivo `.env` debe contener, como mínimo:

```env
SUPABASE_DATABASE_URL=postgresql://USUARIO:CONTRASENA@HOST:PUERTO/postgres?sslmode=require
SUPABASE_DB_SCHEMA=public
```

También se acepta `DATABASE_URL` como nombre de la variable de conexión. El
driver PostgreSQL se normaliza a `psycopg2`. Si la contraseña tiene caracteres
especiales, usa la URL copiada desde Supabase o codifícala para URL.

El archivo `.gitignore` de la raíz excluye `.env`, los entornos virtuales y
archivos bytecode. Conserva las credenciales únicamente en el `.env` local y
rota cualquier contraseña que se haya compartido accidentalmente.

## Consultas y escenarios

El catálogo en `queries_catalog.py` contiene:

1. Ingreso neto por mes.
2. Categorías con mayor margen bruto.
3. Ticket promedio por sucursal.
4. Volumen por segmento de clientes.
5. Canal con mayor venta neta.
6. Margen por canal en un rango de meses.
7. Producto líder por categoría.

`agent_logic.py` contiene el enrutamiento y los controles para la matriz de
pruebas y el modo interactivo. Las consultas nuevas deben usar parámetros
SQLAlchemy cuando reciban valores y ejecutarse únicamente contra el catálogo
autorizado.

## Documentación relacionada

- [Ficha técnica](./Fichatecnica.md): componentes, modelo de datos, flujo y
  limitaciones técnicas.
