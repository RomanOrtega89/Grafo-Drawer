# 📋 Guía para Subir el Proyecto a GitHub

## Paso 1: Crear el Repositorio en GitHub

1. Ve a [GitHub.com](https://github.com) e inicia sesión
2. Haz clic en el botón **"+"** en la esquina superior derecha
3. Selecciona **"New repository"**
4. Configura el repositorio:
   - **Repository name**: `mi-grafos-desktop` (o el nombre que prefieras)
   - **Description**: "Herramienta de visualización de grafos dirigidos - Proyecto de Servicio Social UAQ"
   - **Visibility**: Selecciona **Public** o **Private** según tu preferencia
   - **NO marques** "Initialize this repository with a README" (ya tienes uno)
   - Haz clic en **"Create repository"**

## Paso 2: Conectar tu Repositorio Local con GitHub

Una vez creado el repositorio en GitHub, verás una página con instrucciones. Copia la URL del repositorio (algo como `https://github.com/TU_USUARIO/mi-grafos-desktop.git`)

Luego, ejecuta estos comandos en PowerShell desde la carpeta del proyecto:

```powershell
# Agregar el repositorio remoto (reemplaza TU_USUARIO con tu usuario de GitHub)
git remote add origin https://github.com/TU_USUARIO/mi-grafos-desktop.git

# Verificar que se agregó correctamente
git remote -v

# Subir el código a GitHub (primera vez)
git push -u origin master
```

Si prefieres usar SSH en lugar de HTTPS:
```powershell
git remote add origin git@github.com:TU_USUARIO/mi-grafos-desktop.git
git push -u origin master
```

## Paso 3: Verificar la Subida

1. Actualiza la página de tu repositorio en GitHub
2. Deberías ver todos tus archivos incluyendo el README.md
3. El README se mostrará automáticamente en la página principal del repositorio

## Comandos Útiles para el Futuro

### Hacer cambios y subirlos
```powershell
# Ver archivos modificados
git status

# Agregar cambios al staging
git add .

# Hacer commit con mensaje descriptivo
git commit -m "Descripción de los cambios"

# Subir cambios a GitHub
git push
```

### Ver el historial
```powershell
# Ver historial de commits
git log --oneline

# Ver cambios específicos
git diff
```

### Crear una rama (branch)
```powershell
# Crear y cambiar a una nueva rama
git checkout -b nombre-rama

# Subir la rama a GitHub
git push -u origin nombre-rama

# Volver a la rama principal
git checkout master
```

## Configuración Inicial de Git (si aún no lo has hecho)

Si es la primera vez que usas Git en tu computadora:

```powershell
# Configurar tu nombre
git config --global user.name "Román Ortega Muñoz"

# Configurar tu email (usa el mismo que en GitHub)
git config --global user.email "tu-email@ejemplo.com"

# Verificar configuración
git config --global --list
```

## Consejos de Seguridad

- ✅ Nunca subas contraseñas, tokens o información sensible
- ✅ Revisa el `.gitignore` para asegurar que archivos temporales no se suban
- ✅ Si subes archivos JSON de ejemplo, asegúrate de que no contengan datos privados
- ✅ Considera usar un archivo `.env` para configuraciones sensibles (y agregarlo al .gitignore)

## Personalizar el README

No olvides actualizar estas secciones en el README.md:

1. **Línea 86**: Reemplaza `TU_USUARIO` con tu usuario real de GitHub en la URL del clone
2. **Capturas de pantalla**: Agrega imágenes de tu aplicación en funcionamiento
3. **Sección de Contacto**: Agrega tu información de contacto si lo deseas

## Recursos Adicionales

- [Documentación de Git](https://git-scm.com/doc)
- [GitHub Guides](https://guides.github.com/)
- [Pro Git Book (Español)](https://git-scm.com/book/es/v2)

---

**¡Tu proyecto está listo para compartirse con el mundo! 🎉**
