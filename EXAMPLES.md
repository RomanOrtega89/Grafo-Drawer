# 📚 Ejemplos de Uso - Grafo Drawer

Este documento proporciona ejemplos prácticos de cómo usar Grafo Drawer para diferentes escenarios.

## Ejemplo 1: Crear un Grafo Simple

### Objetivo
Crear un grafo con 4 nodos (A, B, C, D) y conectarlos.

### Pasos
1. **Iniciar la aplicación**: Ejecuta `python main.py`
2. **Activar modo Dibujar**: Presiona `D` o haz clic en el icono de lápiz
3. **Crear nodos**:
   - Haz clic en el lienzo
   - Ingresa "A" como etiqueta
   - Repite para crear nodos B, C y D
4. **Conectar nodos**:
   - Presiona `E` para activar modo Aristas
   - Haz clic en nodo A, luego en nodo B
   - Ingresa "5" como peso
   - Repite para crear más aristas

### Resultado
Un grafo con 4 nodos conectados que puedes guardar como `ejemplo1.json`

---

## Ejemplo 2: Visualizar Algoritmos de Rutas

### Objetivo
Crear un grafo para demostrar el algoritmo de Dijkstra.

### Pasos
1. Crea 6 nodos representando ciudades: Madrid, Barcelona, Valencia, Sevilla, Bilbao, Zaragoza
2. Conéctalos con aristas que representen distancias:
   - Madrid → Barcelona: 620
   - Madrid → Valencia: 350
   - Madrid → Sevilla: 530
   - Barcelona → Zaragoza: 300
   - Zaragoza → Valencia: 320
   - Valencia → Sevilla: 650
3. Activa la matriz de adyacencia (`M`) para ver las distancias
4. Exporta la imagen para presentaciones

### Aplicaciones
- Enseñanza de algoritmos de camino más corto
- Planificación de rutas
- Análisis de redes de transporte

---

## Ejemplo 3: Grafos de Dependencias

### Objetivo
Modelar dependencias entre tareas de un proyecto.

### Configuración
1. Crea nodos para cada tarea: Diseño, Programación, Testing, Documentación, Deployment
2. Conecta las tareas según sus dependencias:
   - Diseño → Programación
   - Programación → Testing
   - Programación → Documentación
   - Testing → Deployment
   - Documentación → Deployment
3. Usa los pesos para indicar tiempo estimado en días

### Análisis
- Identifica tareas críticas viendo la matriz
- Detecta dependencias circulares
- Planifica el orden de ejecución

---

## Ejemplo 4: Red Social

### Objetivo
Modelar conexiones en una red social pequeña.

### Implementación
1. Crea nodos para usuarios: Alice, Bob, Charlie, Diana, Eve
2. Crea aristas dirigidas que representen "sigue a":
   - Alice → Bob
   - Alice → Charlie
   - Bob → Charlie
   - Charlie → Diana
   - Diana → Eve
   - Eve → Alice (forma un ciclo)
3. Analiza la matriz para ver:
   - Quién tiene más seguidores
   - Detectar comunidades
   - Identificar nodos influyentes

---

## Ejemplo 5: Flujo de Procesos

### Objetivo
Documentar un proceso de negocio o workflow.

### Pasos
1. Cada nodo representa un estado o actividad
2. Las aristas representan transiciones
3. Los pesos pueden indicar probabilidad o tiempo
4. Ejemplo - Proceso de pedido:
   - Inicio → Recibir Pedido
   - Recibir Pedido → Validar Inventario
   - Validar Inventario → Procesar Pago (si hay stock)
   - Validar Inventario → Reordenar (si no hay stock)
   - Procesar Pago → Enviar
   - Reordenar → Validar Inventario (ciclo)
   - Enviar → Fin

### Beneficios
- Documentación visual clara
- Identificación de cuellos de botella
- Detección de procesos redundantes

---

## Ejemplo 6: Grafo con Imagen de Fondo

### Objetivo
Usar un mapa como contexto para un grafo de rutas.

### Pasos
1. Prepara una imagen de mapa (PNG/JPG) de tu región
2. En Grafo Drawer: Ver → Cargar Imagen de Fondo
3. Selecciona tu imagen
4. Ajusta el zoom para ver el mapa
5. Crea nodos sobre ubicaciones importantes
6. Conecta con aristas que sigan las rutas reales
7. Usa pesos para distancias o tiempos

### Casos de Uso
- Planificación urbana
- Logística y distribución
- Turismo y rutas turísticas
- Análisis geográfico

---

## Ejemplo 7: Exportar para Presentaciones

### Objetivo
Crear visualizaciones profesionales para exposiciones.

### Flujo de Trabajo
1. Crea tu grafo con colores y disposición estética
2. Usa `F` para ajustar la vista perfectamente
3. Oculta pesos si no son necesarios: Ver → Mostrar Pesos de Aristas
4. Exporta como imagen PNG:
   - Archivo → Exportar → Dibujo a Imagen
   - Elige PNG para mejor calidad
5. Exporta la matriz como CSV:
   - Cambia a pestaña Matriz (`M`)
   - Archivo → Exportar → Matriz a CSV
6. Importa la imagen en PowerPoint/Google Slides
7. Importa el CSV en Excel para análisis

---

## Ejemplo 8: Análisis con Matriz de Adyacencia

### Objetivo
Usar la matriz para análisis cuantitativo.

### Pasos
1. Crea tu grafo con pesos numéricos significativos
2. Activa la pestaña Matriz (`M`)
3. Marca "Mostrar Heatmap" para visualización de colores
4. Observa las estadísticas automáticas:
   - **Promedio**: Peso medio de las aristas
   - **Mediana**: Valor central de los pesos
   - **Min/Max**: Rango de pesos
   - **Desv. Estándar**: Dispersión de valores
5. Exporta a CSV para análisis avanzado en Python/R/Excel

### Interpretación
- Heatmap rojo: Conexiones fuertes/costosas
- Heatmap azul: Conexiones débiles/baratas
- Ceros: Sin conexión directa
- Diagonal: Auto-bucles

---

## Ejemplo 9: Colaboración en Equipo

### Objetivo
Compartir grafos con compañeros o profesores.

### Proceso
1. Crea tu grafo y guárdalo: `Ctrl+S`
2. El archivo JSON se puede compartir por:
   - Email
   - Drive/Dropbox
   - USB
   - GitHub (si es público)
3. Tu compañero/profesor:
   - Descarga Grafo Drawer
   - Abre el archivo: `Ctrl+O`
   - Puede editar y agregar comentarios
   - Guarda con nuevo nombre
4. Pueden iterar hasta tener la versión final

### Ventajas
- Formato estándar JSON (legible y portable)
- Historial con Git si subes a GitHub
- Fácil de revisar cambios

---

## Ejemplo 10: Ejercicios Académicos

### Escenario
Resolver problemas típicos de Teoría de Grafos.

### Problema 1: ¿Es el grafo conexo?
1. Crea un grafo aleatorio
2. Observa la matriz de adyacencia
3. Verifica si hay nodos aislados (fila/columna toda en ceros)

### Problema 2: Encontrar ciclos
1. Crea un grafo
2. Identifica ciclos visualmente
3. Verifica: si puedes volver al nodo de inicio, hay un ciclo

### Problema 3: Grado de entrada/salida
1. En la matriz, cuenta valores por fila (grado salida)
2. Cuenta valores por columna (grado entrada)
3. Exporta a CSV para calcular en Excel

### Problema 4: Camino más corto
1. Crea un grafo con pesos
2. Identifica el camino más corto manualmente
3. Suma los pesos de las aristas
4. Exporta para verificar con algoritmos en Python

---

## Tips y Trucos

### ⚡ Atajos Rápidos
- `P` → `D` → Clic → `E` → Clic-Clic: Flujo rápido para crear nodo y conectar
- `Ctrl+A` → `Del`: Limpiar todo el lienzo
- `F`: Centrar vista después de mover muchos nodos
- `M`: Alternar rápido entre vista y matriz

### 🎨 Estética
- Usa la cuadrícula para alinear nodos simétricamente
- Ajusta el tamaño de nodos según la cantidad de texto
- Usa imágenes de fondo sutiles (con transparencia baja)
- Distribuye nodos en círculo para grafos cíclicos

### 💾 Organización
- Nombra archivos descriptivamente: `grafo_dijkstra_ejemplo.json`
- Guarda versiones: `proyecto_v1.json`, `proyecto_v2.json`
- Exporta imágenes con mismo nombre base: `proyecto_v1.png`
- Mantén una carpeta de proyectos organizada

### 🔍 Debugging
- Si un nodo desaparece, usa `Ctrl+Z` (si lo implementas)
- Para nodos superpuestos, usa modo Mover para separarlos
- Si la matriz está vacía, presiona "Refrescar Matriz"
- Guarda frecuentemente: `Ctrl+S`

---

## Recursos para Aprender Más

### Teoría de Grafos
- [Graph Theory - Khan Academy](https://www.khanacademy.org/computing/computer-science/algorithms)
- [Visualizing Algorithms](https://visualgo.net/en/graphds)

### Algoritmos
- Dijkstra
- Floyd-Warshall
- Bellman-Ford
- Kruskal (Árboles de expansión mínima)
- Prim

### Aplicaciones Reales
- Redes de computadoras
- Sistemas de recomendación
- Análisis de redes sociales
- Logística y optimización de rutas
- Análisis de dependencias en software

---

**¿Tienes más ideas de ejemplos? ¡Contribuye al proyecto en GitHub! 🚀**
