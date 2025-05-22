# 🪟 **Borderless Manager**

**Borderless Manager** es una utilidad ligera para **Windows** que te permite convertir cualquier ventana visible en modo ***borderless*** (sin bordes ni barra de título), ideal para videojuegos, herramientas o aplicaciones que no lo soportan de forma nativa.

## ✨ Características principales

✅ Lista todas las ventanas visibles del sistema.
🖼️ Aplica o revierte el modo *borderless* con un solo clic.
📝 Guarda un registro de las ventanas modificadas para su fácil restauración.
🧩 Interfaz gráfica minimalista con soporte para **bandeja del sistema**.

## ⚙️ Instalación

🔽 Descarga la última versión desde la sección de [📦 Releases](https://github.com/Tiobilito/Borderless_Manager/releases) del repositorio.
📁 Ejecuta el instalador o el `.exe` directamente (no requiere instalación adicional).

## 🧪 Uso básico

1. Abre **Borderless Manager**.
2. Selecciona una ventana en la lista **Ventanas disponibles**.
3. Haz clic en **"→ Aplicar"** para ponerla en modo *borderless*.
4. Para revertir, selecciona la ventana en **Borderless activas** y haz clic en **"← Revertir"**.
5. Desde el icono de la bandeja del sistema puedes:

   * Restaurar la ventana principal.
   * Cerrar el programa (se restauran automáticamente todas las ventanas modificadas).

## 🛠️ Entorno virtual con Conda

Crea un entorno virtual con todas las dependencias necesarias usando el archivo `environment.yml` incluido:

```bash
conda env create -f environment.yml
```

## 🏗️ Compilación del ejecutable

Puedes generar tu propio ejecutable con el script `build.bat` (requiere tener **PyInstaller** instalado).

## 📦 Crear instalador con Inno Setup

1. Instala [Inno Setup](https://jrsoftware.org/isinfo.php).
2. Verifica que la variable de entorno `ISCC` apunte al ejecutable `ISCC.exe` (normalmente se configura automáticamente).
3. Asegúrate de haber compilado el ejecutable antes.
4. Ejecuta en la raíz del proyecto:

```bash
ISCC installer.iss
```

🔧 Esto generará un instalador `.exe` en la carpeta `Output` (o la configurada en el script `installer.iss`).
