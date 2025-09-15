# API de Procesamiento de Mensajes

## Descripción General

API RESTful desarrollada en Python con FastAPI para el procesamiento de mensajes de chat. 
La aplicación recibe, valida, procesa y almacena mensajes con funcionalidades de filtrado de palabras, generación de metadatos y recuperación de mensajes con filtros.

## Características Principales

- **Procesamiento de Mensajes**: Validación, filtrado y almacenamiento
- **Filtrado de Contenido**: Detección de palabras prohibidas con similitud fuzzy
- **Metadatos Automáticos**: Conteo de palabras, caracteres y timestamps
- **Recuperación Avanzada**: Paginación y filtrado por remitente
- **Autenticación**: API Key authentication
- **Rate Limiting**: Limitación de tasa por endpoint
- **Manejo de Errores**: Formato de error consistente
- **Documentación Interactiva**: Swagger UI
- **Cobertura de Pruebas**: Tests unitarios e integración

## Stack Tecnológico

- **Framework**: FastAPI 0
- **Base de Datos**: SQLite con SQLAlchemy ORM
- **Validación**: Pydantic schemas
- **Testing**: Pytest con fixtures
- **Rate Limiting**: Slowapi
- **Filtrado**: FuzzyWuzzy para similitud de strings

## Instalación y Configuración

### 1. Clonar el Repositorio
```bash
git clone https://github.com/steven-galindo/API-procesamiento-de-mensajes.git
cd API-procesamiento-de-mensajes
```

### 2. Crear Entorno Virtual
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

### 3. Instalar Dependencias
```bash
pip install -r src/requirements.txt
```

### 4. Configurar Variables de Entorno
Crear el archivo `.env` con los siguientes valores por defecto:
```env
API_KEY=xxxxxxxxxx #Clave de API para autenticación
API_VERSION=1.0.0 #Versión de la API
API_TIMEZONE=America/Mexico_City #Zona horaria para timestamps
CORPUS_FILE_PATH=data/corpus_filter.json #Ruta al archivo de palabras prohibidas
```

### 5. Ejecutar la Aplicación
```bash
cd src
python -m uvicorn main:app --reload
```
## Docker (Recomendado)

Si se desea usar docker:
- Crear el archivo `.env`
- Construir y ejecutar el contenedor:
```bash
# Construir imagen
cd src
docker build -t api-procesamiento-mensajes:v1.0.0 .

# Ejecutar contenedor
docker run -p 8000:8000 api-procesamiento-mensajes:v1.0.0
```

La API estará disponible en: `http://localhost:8000`

## Documentación de la API
### Endpoints Principales
#### Autenticación
Todos los endpoints (excepto health check) requieren el header:
```
X-API-Key: xxxxxxxxxx
```
#### POST `/api/messages/`
Procesa y almacena un nuevo mensaje.

**Rate Limit**: 100 requests/hora

**Request Body**:
```json
{
  "message_id": "msg-123456",
  "session_id": "session-abcdef",
  "content": "Hola, ¿cómo puedo ayudarte hoy?",
  "timestamp": "2023-06-15T14:30:00Z",
  "sender": "system"
}
```

**Response Success (200)**:
```json
{
  "status": "success",
  "data": {
    "message_id": "msg-123456",
    "session_id": "session-abcdef",
    "content": "Hola, ¿cómo puedo ayudarte hoy?",
    "timestamp": "2023-06-15T14:30:00Z",
    "sender": "system",
    "metadata": {
      "word_count": 5,
      "character_count": 31,
      "processed_at": "2023-06-15T14:30:01Z"
    }
  }
}
```

#### GET `/api/messages/{session_id}`
Recupera mensajes de una sesión específica.

**Rate Limit**: 500 requests/hora

**Query Parameters**:
- `limit` (int, default=100): Número máximo de mensajes
- `offset` (int, default=0): Desplazamiento para paginación
- `sender` (str, optional): Filtrar por remitente ("user" o "system")

**Response Success (200)**:
```json
{
  "messages": [
    {
      "status": "success",
      "data": {
        "message_id": "msg-123456",
        "session_id": "session-abcdef",
        "content": "Hola, ¿cómo puedo ayudarte hoy?",
        "timestamp": "2023-06-15T14:30:00Z",
        "sender": "system",
        "metadata": {
          "word_count": 5,
          "character_count": 31,
          "processed_at": "2023-06-15T14:30:01Z"
        }
      }
    }
  ],
  "total": 1,
  "count": 1
}
```

#### GET `/`
Health check del servicio.

**Rate Limit**: 60 requests/minuto

### Respuestas de Error

#### Formato Estándar de Error:
```json
{
  "status": "error",
  "error": {
    "code": "ERROR_CODE",
    "message": "Descripción del error",
    "details": "Información adicional del error"
  }
}
```

#### Códigos de Error Comunes:
- **400**: `BANNED_WORD_DETECTED` - Contenido inapropiado detectado
- **401**: `INVALID_API_KEY` - API key inválida o faltante
- **404**: `MESSAGES_NOT_FOUND` - No se encontraron mensajes
- **422**: `VALIDATION_ERROR` - Datos de entrada inválidos
- **429**: `RATE_LIMIT_EXCEEDED` - Límite de tasa excedido
- **500**: `DATABASE_ERROR` - Error interno del servidor al interactuar con la base de datos

## Ejecutar Pruebas
### Script para ejecutar las pruebas:
```bash
# Todos los tests
python run_tests.py

# Solo tests unitarios
python run_tests.py --unit-only

# Solo tests de integración  
python run_tests.py --integration-only

# Tests con cobertura completa
python run_tests.py --coverage
```

### Comandos Manuales:
#### Pruebas de Integración
```bash
cd src # Navegar al directorio src
python -m pytest ../tests/test_integration/test_messages_endpoint.py -v
```

####  Pruebas Unitarias
```bash
# Desde el directorio raíz del proyecto
python -m pytest tests/test_auth/ -v #pruebas unitarias de autenticación
python -m pytest tests/test_services/ -v #pruebas unitarias de servicios
```

### Cobertura de Pruebas
La cobertura de pruebas se midió con el paquete [coverage] (https://pypi.org/project/coverage/).
```bash
coverage report --include="src/*"
```
Name                                    Stmts   Miss  Cover
-----------------------------------------------------------
src\controllers\__init__.py                 0      0   100%
src\controllers\message_controller.py      26      9    65%
src\core\__init__.py                        0      0   100%
src\core\auth.py                           14      0   100%
src\core\database.py                       11      4    64%
src\core\exceptions.py                     34     13    62%
src\dependencies\__init__.py                0      0   100%
src\dependencies\auth.py                    4      1    75%
src\dependencies\services.py               10      3    70%
src\main.py                                27      2    93%
src\models\__init__.py                      0      0   100%
src\models\message_model.py                12      0   100%
src\schemas\__init__.py                     0      0   100%
src\schemas\message_schema.py              33      1    97%
src\services\__init__.py                    0      0   100%
src\services\message_service.py            82      1    99%
-----------------------------------------------------------
TOTAL                                     253     34    87%

donde:
Stmts: número de sentencias ejecutables.
Miss: sentencias no ejecutadas durante los tests.
Cover: porcentaje de cobertura de cada archivo.

Las pruebas incluyen: 

** Casos de Éxito:**
- Procesamiento exitoso de mensajes
- Mensajes de usuario y sistema
- Caracteres especiales y Unicode
- Contenido vacío y mensajes largos
- Múltiples mensajes por sesión
- Persistencia de datos

** Casos de Error:**
- Autenticación fallida
- API keys inválidas
- Validación de campos
- Filtrado de contenido
- Formatos incorrectos

** Casos Especiales:**
- Rendimiento (< 2 segundos)
- Caracteres Unicode
- Mensajes largos o vacíos

##  Arquitectura del Proyecto

```
pytest.ini                  # Configuración de pytest 
run_tests.py                # Script para ejecutar pruebas unitarias e integración
src/
├── main.py                # Punto de entrada FastAPI
├── controllers/           # Controladores de endpoints
├── services/              # Lógica de negocio
├── models/                # Modelos SQLAlchemy
├── schemas/               # Esquemas Pydantic
├── dependencies/          # Inyección de dependencias (auth y servicios)
├── core/                  # Configuración y utilidades
└── data/                  # Base de datos y corpus

tests/
├── conftest.py            # Configuración pytest
├── test_integration/      # Tests de endpoints
└── test_services/            # Tests de logica de negocio
```


## Configuración Avanzada

### Personalizar Rate Limits:
Editar en `src/main.py` y `src/controllers/message_controller.py`:
```python
@limiter.limit("100/hour")  # Cambiar según necesidades
```

## Uso Rápido

### Ejemplo con cURL:

```bash
# Crear mensaje
curl -X POST "http://localhost:8000/api/messages/" \
     -H "X-API-Key: api-key-default-123" \
     -H "Content-Type: application/json" \
     -d '{
       "message_id": "msg-001",
       "session_id": "session-abc",
       "content": "Hola mundo",
       "timestamp": "2023-06-15T14:30:00Z",
       "sender": "user"
     }'

# Obtener mensajes
curl -X GET "http://localhost:8000/api/messages/session-abc?limit=10&sender=user" \
     -H "X-API-Key: api-key-default-123"
```


## Documentación Interactiva

Una vez que el servidor esté ejecutándose, visita:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`


---

Steven Galindo - [GitHub](https://github.com/steven-galindo)