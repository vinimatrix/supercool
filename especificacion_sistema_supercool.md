# Especificación Técnica y Arquitectura del Sistema: SuperCool - AI Cinematic Studio

## 1. Visión General del Sistema

**SuperCool** es un estudio cinematográfico virtual impulsado por Inteligencia Artificial diseñado para transformar la producción audiovisual independiente. La arquitectura permite pasar de un concepto, guion o prompt inicial a un largometraje o serie terminada en **resolución 4K, con audio profesional, doblaje multilingüe y publicación en plataformas digitales** desde un único entorno de chat.

---

## 2. Arquitectura General y Flujo de Datos

[ Usuario (Chat Prompt) ]
│
▼
[ Story Bible & Inyector de Contexto ] ──► (Rostros Ancla, Lore, Estilo)
│
▼
[ Middleware / Enrutador Dinámico ]
├──► Motores Atmósfera/Cine (ej. Flow)
└──► Motores Acción/Físicas (ej. Seedance)
│
▼
[ Director de Arte Autónomo (QA Agent) ]
──► (Rechazo / Re-renderizado)
│ (Aprobado)
▼
[ Computadora Virtual (Headless NLE Engine) ]
├── FFmpeg + NVENC (Concatenación y Stream Copy)
├── Clonación de Voz + Lip-Sync
└── Mezcla de Audio & Ducking
│
▼
[ Pipeline de Distribución y Analíticas ]
├── YouTube Data API v3 / Prime Video Direct
└── Tablero de Control de Monetización (Prometheus/Grafana)

---

## 3. Módulos Principales de la Arquitectura

### 3.1. Story Bible e Inyector de Contexto

- **Propósito**: Garantizar la consistencia visual y narrativa a lo largo de toda la producción.
- **Mecanismo**:
  - Extrae y almacena entidades (personajes, atuendos, utilería, escenarios).
  - Bloquea atributos clave mediante **Rostros Ancla** (ID de referencia visual).
  - Inyecta los tokens de referencia en cada prompt técnico en segundo plano, evitando desviaciones en el actor entre toma y toma.

### 3.2. Enrutador Dinámico de Motores AI (Middleware)

- **Propósito**: Asignar cada plano al motor de generación de video ideal según la naturaleza de la escena.
- **Reglas de Enrutamiento**:
  - **Escenas Contemplativas / Paisajes / Diálogos**: Enrutado a motores optimizados para composición atmosférica (ej. *Flow*).
  - **Escenas de Acción / Combate / Taijutsu / Efectos Especiales**: Enrutado a motores con físicas de movimiento avanzadas y seguimiento de cámara (ej. *Seedance*).

### 3.3. Director de Arte Autónomo (Control de Calidad - QA)

- **Propósito**: Eliminar la revisión e iteración manual de tomas defectuosas.
- **Funcionalidad**:
  - Inspecciona los fotogramas generados tras cada render.
  - Compara la consistencia del rostro contra el Rostro Ancla de la *Story Bible*.
  - Detecta artefactos visuales, deforma de extremidades o pérdida de rasgos.
  - Asigna estado `approved_for_edit` o fuerza un re-renderizado en segundo plano (`rejected_by_art_director`).

### 3.4. Computadora Virtual & Motor NLE (FFmpeg)

- **Propósito**: Reemplazar editores de video externos (ej. DaVinci Resolve) ensamblando automáticamente los clips sueltos en una secuencia unificada.
- **Capacidades**:
  - **Concatenación de Video**: Une archivos `.mp4` en secuencia exacta.
  - **Estandarización**: Convierte framerates (24fps) y resoluciones (1080p/4K).
  - **Ingeniería de Audio**:
    - Sincronización labial (*Lip-Sync*) con voces clonadas.
    - Mezcla multicanal (diálogo + efectos foley + banda sonora).
  - **Atenuación Automática (*Ducking*)**: Reduce el volumen de la música de fondo al 20% cuando hay diálogos activos.

---

## 4. Optimización de Rendimiento y Escalabilidad

Para procesar películas completas en tiempos de renderizado eficientes:

1. **Aceleración por GPU (NVIDIA CUDA / NVENC)**: Delegación del procesamiento de video al hardware dedicado (`h264_nvenc`).
2. **Unión sin Recodificación (*Stream Copying*)**: Concatenación mediante `-c:v copy` para reducir el ensamblado de secuencias a milisegundos.
3. **Procesamiento en RAM Disk (`/dev/shm`)**: Operaciones de archivos temporales directamente en memoria para eliminar latencia de I/O en disco.
4. **Renderizado en Paralelo (Celery Chord)**: Procesamiento distribuido de múltiples escenas en paralelo.

---

## 5. Infraestructura y Despliegue

El sistema se despliega como una arquitectura de microservicios contenedorizada:

- **FastAPI**: API principal con soporte WebSockets para progreso en tiempo real.
- **Celery + Redis**: Cola de tareas asíncronas para procesamiento pesados.
- **Prometheus + Grafana**: Monitoreo de telemetría (uso de VRAM con NVML, latencia por escena, FPS y tasa de errores).
- **Docker Compose**: Orquestador del stack completo de microservicios.

---

## 6. Módulo de Publicación, Monetización y Analíticas

- **Publicación Automática**: Carga resumible (*Resumable Upload*) de archivos máster mediante YouTube Data API v3 y preparación de paquetes para Prime Video Direct.
- **Generador de Material Promocional**: Creación de pósters en alta resolución y miniaturas optimizadas para CTR basadas en el personaje ancla.
- **Tablero de Control de Monetización**:
  - Seguimiento de Vistas, Horas de Reproducción, CPM e Ingresos Estimados.
  - Módulo de **Proyecciones Financieras** a 6 meses basado en tasas de crecimiento compuesto.

---

## 7. Caso de Estudio: Live-Action "Boruto: Two Blue Vortex"

| Fase | Acción en el Sistema |
|:--- |:--- |
| **1. Guion & Personajes** | Carga del guion en chat; la *Story Bible* bloquea el Rostro Ancla de Boruto (cicatriz, capa negra, espada). |
| **2. Escenas Tranquilas** | El Middleware enruta la entrada a la aldea al motor tipo *Flow*. |
| **3. Escenas de Acción** | El combate de taijutsu y activación del *Rasengan Uzuhiko* se enruta a *Seedance*. |
| **4. Control de Calidad** | El Director de Arte valida la consistencia de la cicatriz y vestuario en ambas tomas. |
| **5. Montaje y Voz** | La Computadora Virtual une las escenas, clona la voz, sincroniza el lip-sync y atenúa la música en los diálogos. |
| **6. Miniatura y Estreno** | Se genera el póster promocional 16:9 y se programa el estreno automático en YouTube/Prime Video. |

---

## 8. Inventario de Archivos del Sistema Generados

- `docker-compose.yml`: Orquestador de servicios (API, Celery, Redis, Prometheus, Grafana).
- `Dockerfile`: Imagen base con CUDA 12.2, FFmpeg y librerías de soporte.
- `test_pipeline.py`: Script de prueba E2E (Story Bible -> QA -> NLE Master).
- `youtube_publisher.py`: Módulo de publicación automatizada con soporte para miniaturas.
- `analytics_dashboard_v2.py`: Tablero de analíticas con proyecciones financieras a 6 meses.
- `boruto_tbv_thumbnail.jpg`: Muestra de póster promocional en alta resolución.
