# Testing End-to-End para Comparación de Bots

Este directorio contiene herramientas para comparar el comportamiento del bot original con el bot refactorizado, detectando regresiones y validando la funcionalidad.

## Archivos

- `test_data.json` - Mensajes de prueba y configuración
- `bot_comparison_tool.py` - Herramienta principal de comparación
- `run_e2e_comparison.py` - Script de ejecución simplificado
- `README.md` - Esta documentación

## Uso Rápido

### 1. Ejecutar comparación básica
```bash
cd tests/e2e
python run_e2e_comparison.py
```

### 2. Ejecutar con configuración personalizada
```bash
python run_e2e_comparison.py --config mi_config.json --output mi_reporte.html
```

### 3. Ejecutar con información detallada
```bash
python run_e2e_comparison.py --verbose
```

## Configuración

### Archivo test_data.json

El archivo de configuración define los mensajes de prueba y parámetros:

```json
{
  "test_messages": [
    {
      "id": "test_001",
      "description": "Saludo básico",
      "message": {
        "text": {"body": "Hola"},
        "from": "+1234567890",
        "timestamp": "2024-01-01T10:00:00Z"
      },
      "expected_behavior": "Respuesta de saludo cálida y pastoral",
      "critical": true
    }
  ],
  "test_config": {
    "timeout_seconds": 30,
    "max_response_time_ms": 5000,
    "similarity_threshold": 0.7,
    "critical_tests_must_pass": true
  }
}
```

### Parámetros de Configuración

- `timeout_seconds`: Tiempo máximo de espera por respuesta
- `max_response_time_ms`: Tiempo máximo aceptable de respuesta
- `similarity_threshold`: Umbral de similitud entre respuestas (0.0-1.0)
- `critical_tests_must_pass`: Si los tests críticos deben pasar obligatoriamente

## Tipos de Tests

### Tests Críticos (`critical: true`)
- Funcionalidad esencial del bot
- Deben pasar para considerar la migración exitosa
- Ejemplos: saludos, consultas básicas, manejo de errores

### Tests No Críticos (`critical: false`)
- Funcionalidad secundaria o mejoras
- Pueden fallar sin bloquear la migración
- Ejemplos: manejo de emojis, casos edge

## Criterios de Regresión

Una regresión se detecta cuando:

1. **Similitud baja**: Las respuestas son muy diferentes
2. **Tiempo excesivo**: El bot refactorizado es significativamente más lento
3. **Error en refactorizado**: El bot original funciona pero el refactorizado falla
4. **Respuesta vacía**: El bot refactorizado no responde

## Reportes

### Reporte HTML
Se genera automáticamente un reporte HTML con:
- Resumen ejecutivo con métricas
- Detalle de cada test
- Comparación lado a lado de respuestas
- Sección especial para regresiones

### Salida en Consola
- Resumen de resultados
- Lista de regresiones detectadas
- Código de salida (0=éxito, 1=fallo)

## Integración con CI/CD

### GitHub Actions
```yaml
- name: Run E2E Comparison
  run: |
    cd tests/e2e
    python run_e2e_comparison.py --output e2e_report.html
    
- name: Upload E2E Report
  uses: actions/upload-artifact@v2
  with:
    name: e2e-comparison-report
    path: tests/e2e/e2e_report.html
```

### Azure DevOps
```yaml
- script: |
    cd tests/e2e
    python run_e2e_comparison.py
  displayName: 'Run E2E Bot Comparison'
```

## Personalización

### Agregar Nuevos Tests

1. Editar `test_data.json`
2. Agregar nuevo objeto en `test_messages`
3. Definir `id`, `description`, `message`, `expected_behavior`
4. Marcar como `critical` según importancia

### Conectar con Bots Reales

Modificar en `bot_comparison_tool.py`:

```python
def _send_to_original_bot(self, message: Dict[str, Any]) -> str:
    # Implementar conexión real al bot original
    response = requests.post("http://bot-original/api/message", json=message)
    return response.json()["response"]

def _send_to_refactored_bot(self, message: Dict[str, Any]) -> str:
    # Implementar conexión real al bot refactorizado
    response = requests.post("http://bot-refactored/api/message", json=message)
    return response.json()["response"]
```

## Troubleshooting

### Error: "Archivo de configuración no encontrado"
- Verificar que `test_data.json` existe en la ruta especificada
- Usar ruta absoluta si es necesario

### Error: "Error enviando mensaje a bot"
- Verificar conectividad con los bots
- Revisar logs de los servicios
- Usar `--verbose` para más detalles

### Tests fallando consistentemente
- Revisar configuración de `similarity_threshold`
- Ajustar `max_response_time_ms` según performance real
- Verificar que ambos bots estén funcionando correctamente

## Próximos Pasos

1. **Conectar con bots reales**: Implementar conexiones HTTP/WebSocket
2. **Agregar más tests**: Expandir cobertura de casos de uso
3. **Automatización**: Integrar con pipeline de CI/CD
4. **Métricas avanzadas**: Agregar análisis de sentimiento, longitud de respuesta
5. **Reportes mejorados**: Gráficos, tendencias, alertas automáticas 