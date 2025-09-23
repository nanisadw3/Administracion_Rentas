# Administración de Rentas

Una aplicación web simple desarrollada con Flask para la gestión de alquiler de propiedades.

## Características

-   Gestión de Propiedades (Crear, Editar, Ver, Borrar)
-   Gestión de Inquilinos y Administradores
-   Creación y seguimiento de Contratos de alquiler
-   Registro de Pagos mensuales
-   Panel de control para administradores y para inquilinos

## Tecnologías Utilizadas

-   **Backend:** Python, Flask
-   **Base de Datos:** PostgreSQL (utilizando Flask-SQLAlchemy)
-   **Servidor de Producción:** Gunicorn

## Instalación y Ejecución Local

Sigue estos pasos para ejecutar el proyecto en tu máquina local.

### 1. Prerrequisitos

-   Git
-   Python 3.8+ y `pip`

### 2. Clonar el Repositorio

```bash
git clone https://github.com/nanisadw3/Administracion_Rentas.git
cd Administracion_Rentas
```

### 3. Crear un Entorno Virtual

Es una buena práctica usar un entorno virtual para aislar las dependencias del proyecto.

-   **En macOS/Linux:**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```
-   **En Windows:**
    ```bash
    python -m venv venv
    .\venv\Scripts\activate
    ```

### 4. Instalar Dependencias

Instala todas las librerías necesarias que se encuentran en `requirements.txt`.

```bash
pip install -r requirements.txt
```

### 5. Configurar la Base de Datos

La aplicación está configurada para conectarse a una base de datos PostgreSQL.

-   **Para producción (en Railway):** La aplicación usará la variable de entorno `DATABASE_URL` automáticamente.
-   **Para desarrollo local:** La aplicación intentará usar las credenciales que están en `app.py`. Asegúrate de que tu base de datos sea accesible con esas credenciales o modifica el archivo para apuntar a tu base de datos local.

**Importante:** La primera vez que ejecutes la aplicación, las tablas de la base de datos deberían crearse automáticamente si no existen.

### 6. Crear el Usuario Administrador

Antes de iniciar sesión, crea el usuario administrador inicial ejecutando el siguiente comando en tu terminal:

```bash
flask create-admin
```

Las credenciales por defecto son:
-   **Usuario:** `admin`
-   **Contraseña:** `admin`

### 7. Ejecutar la Aplicación

Inicia el servidor de desarrollo de Flask:

```bash
flask run
```

Abre tu navegador y ve a `http://127.0.0.1:5000`.

## Despliegue

Este proyecto está listo para ser desplegado en [Railway](https://railway.app).

1.  Sube tu código a un repositorio de GitHub.
2.  En el panel de Railway, crea un "New Project" y selecciona "Deploy from GitHub repo".
3.  Elige tu repositorio. Railway se encargará del resto.
