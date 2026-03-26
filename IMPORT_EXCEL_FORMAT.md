# Formato Correcto para Importar Excel de Licencias

## Columnas Requeridas (EXACTAMENTE así)

| Columna | Tipo | Obligatorio | Ejemplo |
|---------|------|-------------|---------|
| **CEDULA** | Texto | ✅ SÍ | 1234567890 |
| **NOMBRE** | Texto | ✅ SÍ | JUAN MARTINEZ |
| **CARGO** | Texto | ❌ NO | ANALISTA |
| **PROYECTO** | Texto | ❌ NO | PROYECTO A |
| **software_id** | Número | ❌ NO (default=1) | 1, 2, 3, etc |
| **CORREOS PERSONALES** | Email | ❌ NO | juan@email.com |
| **FECHA DE ENVIO DE CORREO** | Fecha DD/MM/YYYY o MM/DD/YYYY | ❌ NO | 2026-03-20 |
| **FECHA DE HABILITACION DE LICENCIA** | Fecha DD/MM/YYYY o MM/DD/YYYY | ❌ NO | 2026-01-15 |
| **FECHA DE VENCIMIENTO LICENCIA** | Fecha DD/MM/YYYY o MM/DD/YYYY | ❌ NO | 2027-01-15 |
| **VERIFICACIÓN CEDULA** | Sí/No o 1/0 | ❌ NO | No |
| **VERIFICACIÓN LICENCIA** | Sí/No o 1/0 | ❌ NO | Sí |
| **VERIFICACION NOMINA** | Sí/No o 1/0 | ❌ NO | No |
| **OBSERVACIONES** | Texto largo | ❌ NO | Notas sobre la licencia |

## Pasos para Arreglarlo

### 1. Abre tu Excel
- Verifica que tengas EXACTAMENTE estas columnas (mayúsculas, sin acentos variados)
- **IMPORTANTE**: Agrega la columna `software_id` si no la tienes

### 2. Columnas Faltantes
Si te faltan estas columnas, agrégalas con valores por defecto:
- `software_id` → Pon **1** para todas las filas (o el ID del software correcto)
- `VERIFICACIÓN CEDULA` → Vacío o False
- `VERIFICACIÓN LICENCIA` → Vacío o False  
- `VERIFICACION NOMINA` → Vacío o False
- `OBSERVACIONES` → Vacío

### 3. Nombres de Columnas
Debe ser EXACTAMENTE:
```
CEDULA | NOMBRE | CARGO | PROYECTO | software_id | CORREOS PERSONALES | FECHA DE ENVIO DE CORREO | FECHA DE HABILITACION DE LICENCIA | FECHA DE VENCIMIENTO LICENCIA | VERIFICACIÓN CEDULA | VERIFICACIÓN LICENCIA | VERIFICACION NOMINA | OBSERVACIONES
```

### 4. Formatos de Datos
- **CEDULA**: Sin espacios `1234567890` 
- **NOMBRE**: Todo mayúsculas `JUAN MARTINEZ`
- **Fechas**: Formato `2026-03-20` o `03/20/2026`
- **Verificaciones**: `Sí`, `No`, `1`, `0` o vacío

### 5. Errores Comunes

❌ **Esto causa error:**
- CÉDULA (con acento) → ✅ Usa CEDULA
- Cedula (minúsculas) → ✅ Usa CEDULA
- CORREO_PERSONALES (con guión) → ✅ Usa CORREOS PERSONALES (con espacio)
- Fila sin CEDULA o NOMBRE → Error: "Falta cedula o nombre"
- CEDULA duplicada → Error: "Cedula {cedula} ya existe"

## Validaciones que Hace el Sistema

El backend rechaza filas si:
1. ❌ CEDULA o NOMBRE están vacíos
2. ❌ CEDULA ya existe en la BD (duplicado)
3. ❌ Formato de fecha inválido
4. ❌ software_id no es número
5. ❌ Exception técnica durante parseo

Cuando hay error, devuelve: `0 creadas, 19 errores` + lista detallada de qué falló en cada fila.

## IDs de Software Disponibles

Ejecuta esto en el backend para ver:
```python
# En Python
from app.db.session import SessionLocal
from app.models.software import Software

db = SessionLocal()
software = db.query(Software).all()
for s in software:
    print(f"ID: {s.id}, Nombre: {s.name}")
```

O consulta la tabla: `SELECT id, name FROM software;`

## Template Excel Correcto

Descarga este template y úsalo:

| CEDULA | NOMBRE | CARGO | PROYECTO | software_id | CORREOS PERSONALES | FECHA DE ENVIO DE CORREO | FECHA DE HABILITACION DE LICENCIA | FECHA DE VENCIMIENTO LICENCIA | VERIFICACIÓN CEDULA | VERIFICACIÓN LICENCIA | VERIFICACION NOMINA | OBSERVACIONES |
|--------|--------|-------|----------|-------------|-------------------|--------------------------|-----------------------------------|-------------------------------|---------------------|----------------------|------------------|-----------------|
| 123456 | JUAN PEREZ | ANALISTA | PROYECTO A | 1 | juan@email.com | 2026-03-20 | 2026-01-15 | 2027-01-15 | No | Sí | No | Usuario nuevo |
| 789012 | MARIA GARCIA | INGENIERO | PROYECTO B | 2 | maria@email.com | 2026-03-20 | 2026-02-01 | 2027-02-01 | Sí | Sí | No | Verificado |

## Mensaje de Éxito

Si configuraste todo bien, verás: `{"created": 19, "errors": []}`
