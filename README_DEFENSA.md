<div align="center">
  <img src="app/static/img/logos/fifa-hub.svg" alt="FIFAHub Logo" width="300">
  
  # FIFAHub - Documentación Técnica Completa
  
  **Repositorio de Datasets de Jugadores FIFA**
  
  [![CI/CD](https://github.com/EGCproyecto/fifahub/actions/workflows/ci-cd-prod.yml/badge.svg)](https://github.com/EGCproyecto/fifahub/actions)
</div>

---

## 📋 Índice

1. [Descripción del Proyecto](#-descripción-del-proyecto)
2. [Arquitectura del Sistema](#-arquitectura-del-sistema)
3. [Estructura del Proyecto](#-estructura-del-proyecto)
4. [Módulos y Funcionalidades](#-módulos-y-funcionalidades)
5. [Modelo de Datos](#-modelo-de-datos)
6. [Servicios y Lógica de Negocio](#-servicios-y-lógica-de-negocio)
7. [Flujo de Validación CSV](#-flujo-de-validación-csv)
8. [Sistema de Recomendaciones](#-sistema-de-recomendaciones)
9. [Sistema de Notificaciones](#-sistema-de-notificaciones)
10. [CI/CD Pipeline](#-cicd-pipeline)
11. [Comandos Esenciales](#-comandos-esenciales)
12. [Variables de Entorno](#-variables-de-entorno)
13. [Testing](#-testing)
14. [Despliegue](#-despliegue)

---

## 🎯 Descripción del Proyecto

**FIFAHub** es una plataforma web para compartir y explorar datasets de jugadores de videojuegos FIFA/EA Sports FC. Los usuarios pueden:

- 📤 **Subir datasets** CSV con validación automática de esquema FIFA
- 🔍 **Explorar y buscar** datasets disponibles
- 📊 **Visualizar estadísticas** de jugadores y métricas de calidad
- 👥 **Organizar datasets** en comunidades
- 🔐 **Autenticación segura** con 2FA opcional (TOTP)
- 📦 **Integración con Zenodo** para DOIs
- 🔔 **Notificaciones por email** al seguir autores/comunidades
- 💡 **Recomendaciones inteligentes** de datasets similares
- 📜 **Versionado semántico** de datasets

### Stack Tecnológico

| Componente | Tecnología | Uso |
|------------|------------|-----|
| **Backend** | Python 3.12, Flask | Framework web principal |
| **Base de Datos** | MariaDB | Almacenamiento persistente |
| **ORM** | SQLAlchemy + Alembic | Mapeo objeto-relacional y migraciones |
| **Frontend** | Jinja2 Templates, Bootstrap 5 | Renderizado de vistas |
| **Testing** | pytest | Tests unitarios e integración |
| **CI/CD** | GitHub Actions | Automatización de pipelines |
| **Contenedores** | Docker, Docker Compose | Desarrollo y producción |
| **Despliegue** | Render | Hosting de producción |
| **2FA** | pyotp + QRCode | Autenticación de dos factores |
| **Email** | SMTP (Flask-Mail) | Notificaciones asíncronas |

---

## 🏗 Arquitectura del Sistema

```
┌─────────────────────────────────────────────────────────────────────┐
│                        CLIENTE (Browser)                            │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        FLASK APPLICATION                            │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │                      CAPA DE PRESENTACIÓN                       ││
│  │   Routes (Blueprints)  │  Templates (Jinja2)  │  Forms (WTForms)││
│  └─────────────────────────────────────────────────────────────────┘│
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │                      CAPA DE SERVICIOS                          ││
│  │  AuthenticationService │ NotificationService │ RecommendationSvc││
│  │  FollowService         │ VersioningService   │ TabularIngestor  ││
│  └─────────────────────────────────────────────────────────────────┘│
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │                      CAPA DE DATOS                              ││
│  │       Models (SQLAlchemy)  │  Repositories  │  Migrations       ││
│  └─────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                          MariaDB Database                           │
└─────────────────────────────────────────────────────────────────────┘
```

### Patrón de Diseño

El proyecto sigue una **arquitectura en capas**:

1. **Capa de Presentación**: Routes (Blueprints Flask), Templates Jinja2, Forms WTForms
2. **Capa de Servicios**: Lógica de negocio encapsulada en clases Service
3. **Capa de Datos**: Models SQLAlchemy con herencia polimórfica, Repositories

---

## 📁 Estructura del Proyecto

```
fifahub/
├── app/                              # Aplicación principal Flask
│   ├── __init__.py                   # Factory de la aplicación
│   ├── modules/                      # Módulos funcionales (18 módulos)
│   │   ├── auth/                     # Autenticación y 2FA
│   │   │   ├── models.py             # User, RecoveryCodes, Follow*
│   │   │   ├── routes.py             # Endpoints de login/signup/2FA
│   │   │   ├── services.py           # AuthenticationService, FollowService
│   │   │   ├── forms.py              # LoginForm, SignupForm, 2FAForms
│   │   │   └── templates/            # Vistas de auth
│   │   ├── dataset/                  # Gestión de datasets
│   │   │   ├── models.py             # BaseDataset, UVLDataset, DSMetaData
│   │   │   ├── routes.py             # CRUD, download, stats
│   │   │   └── services/             # Servicios de dataset
│   │   │       ├── services.py       # DataSetService
│   │   │       ├── notification_service.py  # Notificaciones async
│   │   │       └── versioning_service.py    # Versionado semántico
│   │   ├── tabular/                  # Carga y validación CSV
│   │   │   ├── models.py             # TabularDataset, TabularMetaData
│   │   │   ├── routes.py             # Upload, my_tabular, detail
│   │   │   ├── forms.py              # Validación esquema FIFA
│   │   │   ├── ingest.py             # TabularIngestor
│   │   │   └── utils/parser.py       # Parsing y análisis CSV
│   │   ├── explore/                  # Búsqueda y exploración
│   │   ├── profile/                  # Perfiles de usuario
│   │   ├── zenodo/                   # Integración DOI
│   │   ├── webhook/                  # Deploy automático
│   │   ├── recommendation/           # Sistema de recomendaciones
│   │   │   └── service.py            # RecommendationService (Jaccard)
│   │   └── ...
│   ├── static/                       # Archivos estáticos (CSS, JS, imágenes)
│   └── templates/                    # Plantillas Jinja2 base
├── core/                             # Configuración y utilidades core
│   ├── configuration/configuration.py
│   └── services/
│       ├── BaseService.py            # Clase base para servicios
│       ├── email_service.py          # Envío de emails
│       └── encryption.py             # Encriptación AES para 2FA secrets
├── docker/                           # Configuración Docker
│   └── images/
│       └── Dockerfile.render         # Dockerfile para producción
├── migrations/                       # Migraciones Alembic
│   └── versions/                     # Scripts de migración
├── scripts/                          # Scripts de utilidad
│   ├── git_update.sh                 # Actualización via webhook
│   └── wait-for-db.sh                # Esperar MariaDB
├── .github/workflows/                # Pipelines CI/CD
│   ├── ci-cd-dev.yml                 # Pipeline desarrollo (PRs)
│   └── ci-cd-prod.yml                # Pipeline producción (main)
├── requirements.txt                  # Dependencias Python
└── docker-compose.yml                # Configuración Docker Compose
```

---

## 📦 Módulos y Funcionalidades

### 🔐 Módulo `auth` - Autenticación

**Ubicación:** `app/modules/auth/`

**Funcionalidades:**
- **Registro e inicio de sesión** con validación de email único
- **Autenticación de Dos Factores (2FA)** con códigos TOTP
- **Códigos de recuperación** (8 códigos encriptados con AES)
- **Rate limiting** para prevenir ataques de fuerza bruta
- **Seguimiento de autores y comunidades** (follow/unfollow)

**Rutas principales:**
| Ruta | Método | Descripción |
|------|--------|-------------|
| `/signup` | GET/POST | Registro de nuevo usuario |
| `/login` | GET/POST | Inicio de sesión |
| `/login/two-factor` | GET/POST | Verificación 2FA |
| `/logout` | GET | Cerrar sesión |
| `/two-factor/settings` | GET | Configuración 2FA |
| `/two-factor/setup` | GET/POST | Activar 2FA con QR |
| `/two-factor/verify-setup` | POST | Verificar código 2FA |
| `/two-factor/regenerate-codes` | POST | Regenerar códigos recuperación |
| `/two-factor/disable` | POST | Desactivar 2FA |
| `/follow/author/<id>` | POST | Seguir un autor |
| `/unfollow/author/<id>` | POST | Dejar de seguir autor |
| `/follow/community/<id>` | POST | Seguir una comunidad |
| `/unfollow/community/<id>` | POST | Dejar de seguir comunidad |

**Modelos:**

```python
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(256), unique=True, nullable=False)
    password = db.Column(db.String(256), nullable=False)  # Hasheado con Werkzeug
    two_factor_enabled = db.Column(db.Boolean, default=False)
    two_factor_secret = db.Column(db.String(512))  # Encriptado AES
    
class UserTwoFactorRecoveryCode(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    encrypted_code = db.Column(db.String(512))  # Encriptado AES
    
class UserFollowAuthor(db.Model):
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    author_id = db.Column(db.Integer, db.ForeignKey("author.id"))
    
class UserFollowCommunity(db.Model):
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    community_id = db.Column(db.String(255))  # ID externo
```

**Flujo de 2FA:**

```
1. Usuario activa 2FA en /two-factor/setup
2. Se genera secret TOTP con pyotp
3. Se muestra QR code para Google Authenticator
4. Usuario verifica con código de 6 dígitos
5. Se generan 8 códigos de recuperación
6. En futuros logins: email/password → código TOTP
```

---

### 📊 Módulo `dataset` - Gestión de Datasets

**Ubicación:** `app/modules/dataset/`

**Funcionalidades:**
- **CRUD completo** de datasets
- **Descarga** en formato ZIP
- **Estadísticas** de visualizaciones y descargas
- **Gestión de autores** y metadatos
- **Datasets trending** (ordenados por descargas)
- **Integración con DOI** (Digital Object Identifier)

**Rutas principales:**
| Ruta | Método | Descripción |
|------|--------|-------------|
| `/dataset/upload` | GET/POST | Subir nuevo dataset UVL |
| `/dataset/list` | GET | Listar mis datasets |
| `/dataset/view/<id>` | GET | Ver detalle de dataset |
| `/dataset/download/<id>` | GET | Descargar dataset (ZIP) |
| `/dataset/delete` | POST | Eliminar dataset |
| `/dataset/stats/<id>` | GET | Estadísticas del dataset |
| `/doi/<doi>` | GET | Acceso por DOI |
| `/authors` | GET | Lista de todos los autores |
| `/author/<id>` | GET | Detalle de autor |
| `/communities` | GET | Lista de comunidades |
| `/community/<id>` | GET | Detalle de comunidad |

**Modelos principales:**

```python
class BaseDataset(db.Model):
    """Clase base con herencia polimórfica"""
    __tablename__ = "data_set"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    type = db.Column(db.String(50))  # Discriminador: 'uvl' o 'tabular'
    created_at = db.Column(db.DateTime)
    download_count = db.Column(db.Integer, default=0)
    view_count = db.Column(db.Integer, default=0)
    ds_meta_data_id = db.Column(db.Integer, db.ForeignKey("ds_meta_data.id"))
    
    __mapper_args__ = {"polymorphic_on": type}

class UVLDataset(BaseDataset):
    """Dataset de tipo UVL (feature models)"""
    __mapper_args__ = {"polymorphic_identity": "uvl"}
    feature_models = db.relationship("FeatureModel", ...)

class DSMetaData(db.Model):
    """Metadatos compartidos por todos los datasets"""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=False)
    publication_type = db.Column(Enum(PublicationType))
    publication_doi = db.Column(db.String(120))
    dataset_doi = db.Column(db.String(120))
    tags = db.Column(db.String(120))  # CSV separado por comas
    authors = db.relationship("Author", ...)

class Author(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    affiliation = db.Column(db.String(120))
    orcid = db.Column(db.String(120))
    ds_meta_data_id = db.Column(db.Integer, db.ForeignKey("ds_meta_data.id"))
```

---

### 📋 Módulo `tabular` - Datasets CSV

**Ubicación:** `app/modules/tabular/`

**Funcionalidades:**
- **Carga de archivos CSV** con validación de esquema FIFA
- **Ingesta automática** de datos tabulares
- **Análisis de metadatos** (filas, columnas, tipos)
- **Cálculo de métricas** de calidad (null_ratio, cardinalidad)
- **Re-subida** de datasets con versionado automático
- **Selección/creación** de autores

**Rutas principales:**
| Ruta | Método | Descripción |
|------|--------|-------------|
| `/tabular/upload` | GET/POST | Subir CSV |
| `/tabular/my` | GET | Mis datasets tabulares |
| `/tabular/<id>` | GET | Ver detalle tabular |

**Modelos:**

```python
class TabularDataset(BaseDataset):
    """Dataset tabular (hereda de BaseDataset)"""
    __mapper_args__ = {"polymorphic_identity": "tabular"}
    rows_count = db.Column(db.Integer)
    schema_json = db.Column(db.Text)
    
    meta_data = db.relationship("TabularMetaData", uselist=False, ...)
    metrics = db.relationship("TabularMetrics", uselist=False, ...)

class TabularMetaData(db.Model):
    """Metadatos del CSV (1-a-1 con TabularDataset)"""
    id = db.Column(db.Integer, primary_key=True)
    delimiter = db.Column(db.String(5))      # ",", ";", "\t"
    encoding = db.Column(db.String(20))      # "utf-8", "latin1"
    has_header = db.Column(db.Boolean)
    n_rows = db.Column(db.Integer)
    n_cols = db.Column(db.Integer)
    sample_rows = db.Column(db.JSON)         # Primeras N filas
    columns = db.relationship("TabularColumn", ...)

class TabularColumn(db.Model):
    """Metadatos de cada columna (N-a-1 con TabularMetaData)"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    dtype = db.Column(db.String(50))         # "int", "float", "string"
    null_count = db.Column(db.Integer)
    unique_count = db.Column(db.Integer)
    stats = db.Column(db.JSON)               # {min, max, mean, median}

class TabularMetrics(db.Model):
    """Métricas de calidad (1-a-1 con TabularDataset)"""
    id = db.Column(db.Integer, primary_key=True)
    null_ratio = db.Column(db.Float)         # % de nulos total
    avg_cardinality = db.Column(db.Float)    # Promedio de únicos por columna
```

---

## 🔄 Flujo de Validación CSV

El módulo `tabular` implementa un flujo completo de validación:

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  1. FORMULARIO  │────▶│  2. VALIDACIÓN  │────▶│  3. INGESTA     │
│  TabularDataset │     │  Esquema FIFA   │     │  TabularIngestor│
│  Form           │     │                 │     │                 │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                                                        │
                                                        ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  6. RESPUESTA   │◀────│  5. NOTIFIC.    │◀────│  4. ANÁLISIS    │
│  Redirect a     │     │  Async a        │     │  parse_csv_     │
│  detail         │     │  followers      │     │  metadata()     │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

### Paso 1: Formulario

```python
# forms.py
FIFA_REQUIRED_COLUMNS = [
    "ID", "Name", "Age", "Nationality", "Overall", "Potential",
    "Club", "Value", "Wage", "Preferred Foot", "Weak Foot",
    "Skill Moves", "Position", "Height", "Weight",
]

def validate_fifa_schema(form, field):
    """Valida que el CSV tenga todas las columnas requeridas"""
    # Lee la primera línea (header)
    # Compara con FIFA_REQUIRED_COLUMNS
    # Lanza ValidationError si faltan columnas
```

### Paso 2: Validación de Esquema

```python
# Al subir el formulario:
if not form.validate_on_submit():
    return render_template("upload_tabular.html", form=form), 400
```

### Paso 3: Ingesta (TabularIngestor)

```python
# ingest.py
class TabularIngestor:
    def ingest(self, *, dataset_id, file_path, delimiter, has_header, sample_rows):
        # 1. Parsear CSV
        parsed = parse_csv_metadata(file_path, delimiter, has_header, sample_rows)
        
        # 2. Crear TabularMetaData
        meta = TabularMetaData(
            dataset_id=dataset_id,
            n_rows=parsed["n_rows"],
            n_cols=parsed["n_cols"],
            encoding=parsed["encoding"],
            ...
        )
        
        # 3. Crear TabularColumn por cada columna
        for col in parsed["columns"]:
            db.session.add(TabularColumn(
                name=col["name"],
                dtype=col["dtype"],  # "int", "float", "string"
                null_count=col["null_count"],
                unique_count=col["unique_count"],
                stats=col["stats"],  # {min, max, mean, median}
            ))
        
        # 4. Calcular métricas de calidad
        null_ratio = total_nulls / total_cells
        metrics = TabularMetrics(null_ratio=null_ratio, avg_cardinality=...)
```

### Paso 4: Parser CSV

```python
# utils/parser.py
def parse_csv_metadata(file_path, delimiter, has_header, sample_rows):
    """
    Analiza un CSV y extrae:
    - n_rows, n_cols, file_size, encoding, delimiter
    - columns: [{name, dtype, null_count, unique_count, stats}]
    - sample_rows: primeras N filas
    """
    
    # Detectar encoding automáticamente
    encoding = _detect_encoding(file_path)  # utf-8, latin1, cp1252
    
    # Leer y analizar hasta 10,000 filas
    for i, row in enumerate(reader):
        # Contar nulos: "", "NA", "null", "N/A", "nan"
        # Acumular valores por columna
    
    # Por cada columna:
    for idx in range(n_cols):
        dtype = _infer_dtype_specific(values)  # int, float, string
        stats = _calculate_numeric_stats(values, dtype)  # min, max, mean, median
```

### Esquema CSV Requerido

| Columna | Tipo | Descripción | Ejemplo |
|---------|------|-------------|---------|
| `ID` | int | Identificador único del jugador | `158023` |
| `Name` | string | Nombre del jugador | `L. Messi` |
| `Age` | int | Edad del jugador | `36` |
| `Nationality` | string | Nacionalidad | `Argentina` |
| `Overall` | int | Rating global (0-99) | `90` |
| `Potential` | int | Potencial (0-99) | `90` |
| `Club` | string | Club actual | `Inter Miami` |
| `Value` | string | Valor de mercado | `€16M` |
| `Wage` | string | Salario semanal | `€150K` |
| `Preferred Foot` | string | Pie preferido | `Left` |
| `Weak Foot` | int | Rating pie débil (1-5) | `4` |
| `Skill Moves` | int | Regates (1-5) | `4` |
| `Position` | string | Posición | `RW` |
| `Height` | string | Altura | `170cm` |
| `Weight` | string | Peso | `72kg` |

> **Nota:** Se aceptan columnas adicionales (Pace, Shooting, etc.) que serán preservadas.

---

## 💡 Sistema de Recomendaciones

**Ubicación:** `app/modules/recommendation/service.py`

El sistema recomienda datasets similares usando un **algoritmo de scoring ponderado**:

### Fórmula de Relevancia

```python
WEIGHTS = {
    "tags": 0.40,        # 40% - Etiquetas compartidas
    "communities": 0.30, # 30% - Misma comunidad
    "authors": 0.20,     # 20% - Mismo autor
    "downloads": 0.05,   # 5%  - Popularidad
    "recency": 0.05,     # 5%  - Frescura
}
```

### Algoritmo

```python
class RecommendationService:
    def get_related_datasets(dataset_id, limit=5):
        # 1. Cargar dataset base y crear perfil
        base_profile = _collect_profile(base_dataset)
        
        # 2. Buscar candidatos que compartan atributos
        candidates = _fetch_candidates(base_profile)
        
        # 3. Calcular score para cada candidato
        for candidate in candidates:
            score = 0.0
            
            # Índice de Jaccard para tags
            score += jaccard(base.tags, candidate.tags) * 0.40
            
            # Jaccard para autores
            score += jaccard(base.authors, candidate.authors) * 0.20
            
            # Jaccard para comunidades  
            score += jaccard(base.communities, candidate.communities) * 0.30
            
            # Popularidad (log10 normalizado)
            score += log10(downloads + 1) / 5.0 * 0.05
            
            # Frescura (decae a 0 en 365 días)
            score += max(1.0 - days_old / 365, 0) * 0.05
        
        # 4. Ordenar por score descendente
        return top_5_candidates
```

### Índice de Jaccard

```
Jaccard(A, B) = |A ∩ B| / |A ∪ B|
```

Mide la similitud entre dos conjuntos (0.0 = disjuntos, 1.0 = idénticos).

---

## 🔔 Sistema de Notificaciones

**Ubicación:** `app/modules/dataset/services/notification_service.py`

El sistema envía emails cuando se publica un nuevo dataset a los seguidores.

### Flujo Asíncrono

```python
class NotificationService:
    def trigger_new_dataset_notifications_async(self, dataset):
        """Lanza un hilo para enviar notificaciones sin bloquear"""
        
        def _worker():
            with app.app_context():
                # Notificar a seguidores del autor
                self._notify_author_followers(dataset)
                
                # Notificar a seguidores de la comunidad
                self._notify_community_followers(dataset)
        
        thread = threading.Thread(target=_worker, daemon=True)
        thread.start()
```

### Tipos de Notificación

1. **Nuevo dataset de autor seguido:**
   ```
   Subject: [fifahub] New dataset from L. Messi
   Body: You are following this author...
   ```

2. **Nuevo dataset en comunidad seguida:**
   ```
   Subject: [fifahub] New dataset in community fifa24
   Body: You are following this community...
   ```

---

## 📜 Sistema de Versionado

**Ubicación:** `app/modules/dataset/services/versioning_service.py`

Implementa **versionado semántico** (SemVer) para datasets.

```python
class VersioningService:
    def _next_version(self, dataset):
        """Genera versión semántica: 1.0.0 → 1.0.1 → 1.0.2..."""
        last = DatasetVersion.query.filter_by(dataset_id=dataset.id).first()
        if not last:
            return "1.0.0"
        
        major, minor, patch = map(int, last.version.split("."))
        patch += 1
        return f"{major}.{minor}.{patch}"
    
    def create_version(self, dataset, author_id, change_note, strategy):
        """Crea snapshot del estado actual del dataset"""
        snapshot = strategy.snapshot(dataset)
        version = DatasetVersion(
            dataset_id=dataset.id,
            version=self._next_version(dataset),
            change_note=change_note,
            snapshot=snapshot,
        )
        db.session.add(version)
```

---

## 💾 Modelo de Datos

```mermaid
erDiagram
    User ||--o{ BaseDataset : owns
    User ||--o| UserProfile : has
    User ||--o{ UserTwoFactorRecoveryCode : has
    User ||--o{ UserFollowAuthor : follows
    User ||--o{ UserFollowCommunity : follows
    
    BaseDataset ||--o| DSMetaData : has
    DSMetaData ||--o{ Author : has
    
    BaseDataset <|-- UVLDataset : extends
    BaseDataset <|-- TabularDataset : extends
    
    TabularDataset ||--o| TabularMetaData : has
    TabularDataset ||--o| TabularMetrics : has
    TabularMetaData ||--o{ TabularColumn : has
    
    BaseDataset ||--o{ DSDownloadRecord : tracks
    BaseDataset ||--o{ DSViewRecord : tracks
    BaseDataset ||--o{ DatasetVersion : versions
    
    UserFollowAuthor }o--|| Author : references
```

### Herencia Polimórfica (Single Table Inheritance)

```python
# data_set table tiene columna 'type' como discriminador
class BaseDataset(db.Model):
    __tablename__ = "data_set"
    type = db.Column(db.String(50))
    __mapper_args__ = {"polymorphic_on": type}

class UVLDataset(BaseDataset):
    __mapper_args__ = {"polymorphic_identity": "uvl"}

class TabularDataset(BaseDataset):
    __mapper_args__ = {"polymorphic_identity": "tabular"}
```

**Ventajas:**
- Una sola tabla para todos los datasets
- Consultas polimórficas: `BaseDataset.query.all()` devuelve UVL y Tabular
- Campos comunes compartidos (user_id, created_at, view_count, etc.)

---

## 🔄 CI/CD Pipeline

### Pipeline de Desarrollo (`ci-cd-dev.yml`)

Se ejecuta en **pull requests** hacia `main`:

```yaml
jobs:
  commits:     # Validar Conventional Commits
  style:       # black + isort
  pytest:      # Tests con MariaDB service
```

### Pipeline de Producción (`ci-cd-prod.yml`)

Se ejecuta en **push a `main`**:

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Conventional  │────▶│     Style       │────▶│     Pytest      │
│   Commits       │     │   black/isort   │     │   + MariaDB     │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                                                        │
                                                        ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Deploy to     │◀────│   Docker Hub    │◀────│    Release      │
│   Render        │     │   Publish       │     │   SemVer Auto   │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

### Versionado Semántico Automático

Basado en **Conventional Commits**:

| Tipo de Commit | Incremento | Ejemplo |
|----------------|------------|---------|
| `BREAKING CHANGE` o `!:` | **MAJOR** | `2.0.0` |
| `feat:` | **MINOR** | `1.1.0` |
| `fix:`, `perf:`, `refactor:` | **PATCH** | `1.0.1` |

### Estructura del Job `release_automation`

```yaml
- name: Determine release type
  run: |
    # Analizar commits desde último tag
    COMMITS=$(git log ${LAST_TAG}..HEAD --pretty=format:'%s%n%b')
    
    # Buscar BREAKING CHANGE → major
    # Buscar feat: → minor
    # Buscar fix/perf/refactor → patch

- name: Create GitHub Release
  uses: softprops/action-gh-release@v2
  with:
    tag_name: v1.2.3
    generate_release_notes: true
```

---

## ⚡ Comandos Esenciales

### 🐳 Desarrollo con Docker

```bash
# Copiar configuración
cp .env.docker.example .env

# Iniciar contenedores
docker compose up --build -d

# Ver logs en tiempo real
docker compose logs -f web

# Acceder al contenedor
docker compose exec web bash

# Parar contenedores
docker compose down

# Limpiar todo (incluyendo volúmenes y BD)
docker compose down -v
```

### 🗃️ Base de Datos y Migraciones

```bash
# Crear nueva migración
flask db migrate -m "Descripción del cambio"

# Aplicar migraciones pendientes
flask db upgrade

# Revertir última migración
flask db downgrade

# Ver estado de migraciones
flask db current
flask db history

# Marcar como actualizada sin ejecutar
flask db stamp head
```

### 🧪 Testing

```bash
# Ejecutar todos los tests
pytest app/modules/ --ignore-glob='*selenium*'

# Tests con cobertura
pytest app/modules/ --cov=app --cov-report=html

# Test de un módulo específico
pytest app/modules/tabular/tests/ -v

# Test de un archivo específico
pytest app/modules/auth/tests/test_unit_auth.py -v

# Test de una función específica
pytest app/modules/tabular/tests/test_tabular_ingest.py::test_ingest_valid_csv -v
```

### 🎨 Formateo y Linting

```bash
# Formatear código con black
black app rosemary core

# Ordenar imports con isort
isort --profile black app rosemary core

# Verificar sin modificar
black --check app rosemary core
isort --check-only --profile black app rosemary core
```

### 🖥️ Servidor de Desarrollo

```bash
# Activar entorno virtual
source env/bin/activate

# Instalar dependencias
pip install -r requirements.txt

# Ejecutar servidor de desarrollo
flask run --debug

# Con host específico
flask run --host=0.0.0.0 --port=5000
```

### 🔧 Git y Conventional Commits

```bash
# Ejemplos de commits válidos
git commit -m "feat(tabular): add CSV schema validation"
git commit -m "fix(auth): resolve 2FA rate limiting issue"
git commit -m "docs: update README with deployment instructions"
git commit -m "refactor(dataset)!: change download endpoint"  # BREAKING CHANGE

# Ver historial con formato
git log --oneline -20
```

---

## 🔐 Variables de Entorno

### Variables Obligatorias

| Variable | Descripción | Ejemplo |
|----------|-------------|---------|
| `SECRET_KEY` | Clave para encriptar sesiones y 2FA secrets | `tu-clave-secreta-muy-larga` |
| `MARIADB_HOSTNAME` | Host de MariaDB | `db` (Docker) / `localhost` |
| `MARIADB_DATABASE` | Nombre de la BD | `fifahubdb` |
| `MARIADB_USER` | Usuario de BD | `fifahub_user` |
| `MARIADB_PASSWORD` | Contraseña de BD | `tu-password-seguro` |

### Variables Opcionales

| Variable | Descripción | Default |
|----------|-------------|---------|
| `MARIADB_PORT` | Puerto de MariaDB | `3306` |
| `FLASK_ENV` | Entorno Flask | `development` |
| `UPLOAD_FOLDER` | Carpeta de uploads | `./uploads` |
| `WEBHOOK_TOKEN` | Token para deploy webhook | - |
| `DOMAIN` | Dominio para URLs absolutas | `localhost:5000` |

### Variables de Email (SMTP)

| Variable | Descripción |
|----------|-------------|
| `MAIL_SERVER` | Servidor SMTP (ej: `smtp.gmail.com`) |
| `MAIL_PORT` | Puerto SMTP (ej: `587`) |
| `MAIL_USERNAME` | Usuario SMTP |
| `MAIL_PASSWORD` | Contraseña SMTP |
| `MAIL_USE_TLS` | Usar TLS (`True`/`False`) |
| `MAIL_DEFAULT_SENDER` | Email remitente por defecto |

---

## 🧪 Testing

### Estructura de Tests

```
app/modules/<modulo>/tests/
├── conftest.py           # Fixtures específicos del módulo
├── test_unit_<modulo>.py # Tests unitarios
├── test_<feature>.py     # Tests de funcionalidad
└── locustfile.py         # Tests de carga (opcional)
```

### Fixtures Globales

En `app/modules/conftest.py`:

```python
@pytest.fixture(scope="session")
def app():
    """Crea instancia de la aplicación para testing"""
    app = create_app()
    app.config["TESTING"] = True
    return app

@pytest.fixture
def client(app):
    """Cliente de test Flask"""
    return app.test_client()

@pytest.fixture
def logged_in_client(client):
    """Cliente con sesión iniciada"""
    client.post("/login", data={"email": "test@test.com", "password": "test"})
    return client
```

### Ejemplo de Test

```python
# app/modules/tabular/tests/test_tabular_ingest.py
def test_ingest_valid_csv(app, client, sample_csv_path):
    """Test que la ingesta de CSV válido funciona correctamente"""
    with app.app_context():
        ingestor = TabularIngestor()
        result = ingestor.ingest(
            dataset_id=1,
            file_path=sample_csv_path,
            delimiter=",",
            has_header=True,
        )
        
        assert result["status"] == "ok"
        assert result["n_rows"] > 0
        assert result["n_cols"] == 15  # Columnas FIFA
```

---

## 🚀 Despliegue

### Producción en Render

1. **Push a `main`** dispara GitHub Actions
2. Pipeline ejecuta tests
3. Se crea release con versión semántica
4. Se construye imagen Docker
5. Se publica en Docker Hub: `sergiogar/fifahub:v1.2.3`
6. Se triggerea webhook de Render
7. Render descarga nueva imagen y reinicia

### Dockerfile de Producción

```dockerfile
# docker/images/Dockerfile.render
FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Entrypoint aplica migraciones y arranca gunicorn
ENTRYPOINT ["./docker/scripts/render_entrypoint.sh"]
```

### Webhook de Deploy Manual

```bash
curl -X POST \
  -H "Authorization: Bearer $WEBHOOK_TOKEN" \
  https://fifahub.onrender.com/webhook/deploy
```

---

## 📝 Convención de Commits

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

**Tipos:**
| Tipo | Descripción | Versión |
|------|-------------|---------|
| `feat` | Nueva funcionalidad | MINOR |
| `fix` | Corrección de bug | PATCH |
| `docs` | Documentación | PATCH |
| `style` | Formateo | PATCH |
| `refactor` | Refactorización | PATCH |
| `test` | Tests | PATCH |
| `chore` | Mantenimiento | PATCH |
| `ci` | CI/CD | PATCH |

**Ejemplos:**
```bash
feat(tabular): add automatic encoding detection
fix(auth): prevent race condition in 2FA verification
docs: add API endpoint documentation
refactor(dataset)!: rename download endpoint  # BREAKING CHANGE
```

---

## 🔗 Enlaces Útiles

- **Repositorio:** https://github.com/EGCproyecto/fifahub
- **Producción:** https://fifahub.onrender.com
- **Docker Hub:** https://hub.docker.com/r/sergiogar/fifahub
- **Proyecto Base:** [UVLHub](https://github.com/diverso-lab/uvlhub)

---

<div align="center">
  
  **FIFAHub** - Desarrollado para EGC 2024/2025
  
  ¡Buena suerte en la defensa! 🎯
  
</div>
