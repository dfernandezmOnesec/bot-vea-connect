"""
Herramienta de comparación end-to-end para bots de WhatsApp.

Este script envía mensajes de prueba a ambos bots (original y refactorizado)
y compara sus respuestas para detectar regresiones.
"""

import json
import time
import difflib
import statistics
from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime, timezone
from dataclasses import dataclass
import logging
from pathlib import Path

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class TestResult:
    """Resultado de un test individual."""
    test_id: str
    description: str
    critical: bool
    original_response: str
    refactored_response: str
    original_time_ms: float
    refactored_time_ms: float
    similarity_score: float
    is_regression: bool
    regression_reason: Optional[str] = None


@dataclass
class ComparisonReport:
    """Reporte completo de comparación."""
    total_tests: int
    passed_tests: int
    failed_tests: int
    critical_failures: int
    average_similarity: float
    average_original_time: float
    average_refactored_time: float
    regressions: List[TestResult]
    test_results: List[TestResult]
    timestamp: str


class BotComparisonTool:
    """Herramienta para comparar respuestas de bots."""
    
    def __init__(self, test_data_path: str = "tests/e2e/test_data.json"):
        """Inicializar herramienta de comparación."""
        self.test_data_path = Path(test_data_path)
        self.test_data = self._load_test_data()
        self.config = self.test_data.get("test_config", {})
        
    def _load_test_data(self) -> Dict[str, Any]:
        """Cargar datos de prueba desde JSON."""
        try:
            with open(self.test_data_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error cargando datos de prueba: {e}")
            raise
    
    def send_message_to_bot(self, message: Dict[str, Any], bot_type: str) -> Tuple[str, float]:
        """
        Enviar mensaje a un bot específico y medir tiempo de respuesta.
        
        Args:
            message: Mensaje a enviar
            bot_type: 'original' o 'refactored'
            
        Returns:
            Tuple[str, float]: (respuesta, tiempo_en_ms)
        """
        start_time = time.time()
        
        try:
            if bot_type == "original":
                response = self._send_to_original_bot(message)
            elif bot_type == "refactored":
                response = self._send_to_refactored_bot(message)
            else:
                raise ValueError(f"Tipo de bot no válido: {bot_type}")
            
            end_time = time.time()
            response_time = (end_time - start_time) * 1000  # Convertir a ms
            
            return response, response_time
            
        except Exception as e:
            logger.error(f"Error enviando mensaje a {bot_type} bot: {e}")
            return f"ERROR: {str(e)}", 0.0
    
    def _send_to_original_bot(self, message: Dict[str, Any]) -> str:
        """Enviar mensaje al bot original."""
        # TODO: Implementar conexión al bot original
        # Por ahora, simulamos una respuesta
        import random
        responses = [
            "¡Hola! Gracias por contactarnos. ¿En qué puedo ayudarte?",
            "Bienvenido a VEA Connect. Estoy aquí para servirte.",
            "Hola, soy tu asistente pastoral. ¿Cómo estás?"
        ]
        time.sleep(random.uniform(0.1, 0.5))  # Simular latencia
        return random.choice(responses)
    
    def _send_to_refactored_bot(self, message: Dict[str, Any]) -> str:
        """Enviar mensaje al bot refactorizado."""
        # TODO: Implementar conexión al bot refactorizado
        # Por ahora, simulamos una respuesta
        import random
        responses = [
            "¡Hola! Gracias por contactarnos. ¿En qué puedo ayudarte?",
            "Bienvenido a VEA Connect. Estoy aquí para servirte.",
            "Hola, soy tu asistente pastoral. ¿Cómo estás?"
        ]
        time.sleep(random.uniform(0.1, 0.5))  # Simular latencia
        return random.choice(responses)
    
    def calculate_similarity(self, text1: str, text2: str) -> float:
        """
        Calcular similitud entre dos textos usando difflib.
        
        Args:
            text1: Primer texto
            text2: Segundo texto
            
        Returns:
            float: Puntuación de similitud (0.0 - 1.0)
        """
        if not text1 or not text2:
            return 0.0
        
        # Normalizar textos
        text1_norm = text1.lower().strip()
        text2_norm = text2.lower().strip()
        
        if text1_norm == text2_norm:
            return 1.0
        
        # Usar difflib para calcular similitud
        similarity = difflib.SequenceMatcher(None, text1_norm, text2_norm).ratio()
        return similarity
    
    def detect_regression(self, test_result: TestResult) -> bool:
        """
        Detectar si hay una regresión en el test.
        
        Args:
            test_result: Resultado del test
            
        Returns:
            bool: True si hay regresión
        """
        similarity_threshold = self.config.get("similarity_threshold", 0.7)
        max_response_time = self.config.get("max_response_time_ms", 5000)
        
        # Verificar similitud
        if test_result.similarity_score < similarity_threshold:
            test_result.is_regression = True
            test_result.regression_reason = f"Similitud baja: {test_result.similarity_score:.2f} < {similarity_threshold}"
            return True
        
        # Verificar tiempo de respuesta
        if test_result.refactored_time_ms > max_response_time:
            test_result.is_regression = True
            test_result.regression_reason = f"Tiempo de respuesta alto: {test_result.refactored_time_ms:.2f}ms > {max_response_time}ms"
            return True
        
        # Verificar si la respuesta original es exitosa pero la refactorizada no
        if test_result.original_response and not test_result.original_response.startswith("ERROR") and \
           test_result.refactored_response.startswith("ERROR"):
            test_result.is_regression = True
            test_result.regression_reason = "Bot refactorizado falló mientras el original funcionó"
            return True
        
        return False
    
    def run_comparison(self) -> ComparisonReport:
        """
        Ejecutar comparación completa entre ambos bots.
        
        Returns:
            ComparisonReport: Reporte de comparación
        """
        logger.info("Iniciando comparación end-to-end de bots...")
        
        test_messages = self.test_data.get("test_messages", [])
        test_results = []
        regressions = []
        
        for test_case in test_messages:
            test_id = test_case["id"]
            description = test_case["description"]
            message = test_case["message"]
            critical = test_case.get("critical", False)
            
            logger.info(f"Ejecutando test {test_id}: {description}")
            
            # Enviar mensaje a ambos bots
            original_response, original_time = self.send_message_to_bot(message, "original")
            refactored_response, refactored_time = self.send_message_to_bot(message, "refactored")
            
            # Calcular similitud
            similarity = self.calculate_similarity(original_response, refactored_response)
            
            # Crear resultado del test
            test_result = TestResult(
                test_id=test_id,
                description=description,
                critical=critical,
                original_response=original_response,
                refactored_response=refactored_response,
                original_time_ms=original_time,
                refactored_time_ms=refactored_time,
                similarity_score=similarity,
                is_regression=False
            )
            
            # Detectar regresiones
            if self.detect_regression(test_result):
                regressions.append(test_result)
                logger.warning(f"REGRESIÓN detectada en test {test_id}: {test_result.regression_reason}")
            
            test_results.append(test_result)
            
            # Pausa entre tests para no sobrecargar
            time.sleep(0.5)
        
        # Generar estadísticas
        total_tests = len(test_results)
        passed_tests = len([r for r in test_results if not r.is_regression])
        failed_tests = len(regressions)
        critical_failures = len([r for r in regressions if r.critical])
        
        similarities = [r.similarity_score for r in test_results]
        original_times = [r.original_time_ms for r in test_results]
        refactored_times = [r.refactored_time_ms for r in test_results]
        
        report = ComparisonReport(
            total_tests=total_tests,
            passed_tests=passed_tests,
            failed_tests=failed_tests,
            critical_failures=critical_failures,
            average_similarity=statistics.mean(similarities) if similarities else 0.0,
            average_original_time=statistics.mean(original_times) if original_times else 0.0,
            average_refactored_time=statistics.mean(refactored_times) if refactored_times else 0.0,
            regressions=regressions,
            test_results=test_results,
            timestamp=datetime.now(timezone.utc).isoformat()
        )
        
        logger.info(f"Comparación completada. {passed_tests}/{total_tests} tests pasaron.")
        return report
    
    def generate_report(self, report: ComparisonReport, output_path: str = "bot_comparison_report.html") -> str:
        """
        Generar reporte HTML detallado.
        
        Args:
            report: Reporte de comparación
            output_path: Ruta del archivo de salida
            
        Returns:
            str: Ruta del archivo generado
        """
        html_content = self._generate_html_report(report)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        logger.info(f"Reporte generado: {output_path}")
        return output_path
    
    def _generate_html_report(self, report: ComparisonReport) -> str:
        """Generar contenido HTML del reporte."""
        html = f"""
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Reporte de Comparación de Bots - VEA Connect</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ background-color: #f0f0f0; padding: 20px; border-radius: 5px; }}
        .summary {{ margin: 20px 0; }}
        .test-result {{ margin: 10px 0; padding: 10px; border: 1px solid #ddd; border-radius: 5px; }}
        .passed {{ background-color: #d4edda; border-color: #c3e6cb; }}
        .failed {{ background-color: #f8d7da; border-color: #f5c6cb; }}
        .critical {{ border-left: 5px solid #dc3545; }}
        .regression {{ background-color: #fff3cd; border-color: #ffeaa7; }}
        .metrics {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 20px 0; }}
        .metric {{ background-color: #e9ecef; padding: 15px; border-radius: 5px; text-align: center; }}
        .metric-value {{ font-size: 2em; font-weight: bold; }}
        .response-comparison {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin: 10px 0; }}
        .response-box {{ background-color: #f8f9fa; padding: 10px; border-radius: 3px; }}
        .response-label {{ font-weight: bold; margin-bottom: 5px; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Reporte de Comparación de Bots - VEA Connect</h1>
        <p>Generado el: {report.timestamp}</p>
    </div>
    
    <div class="summary">
        <h2>Resumen Ejecutivo</h2>
        <div class="metrics">
            <div class="metric">
                <div class="metric-value">{report.passed_tests}/{report.total_tests}</div>
                <div>Tests Exitosos</div>
            </div>
            <div class="metric">
                <div class="metric-value">{report.failed_tests}</div>
                <div>Regresiones</div>
            </div>
            <div class="metric">
                <div class="metric-value">{report.critical_failures}</div>
                <div>Fallos Críticos</div>
            </div>
            <div class="metric">
                <div class="metric-value">{report.average_similarity:.2%}</div>
                <div>Similitud Promedio</div>
            </div>
        </div>
    </div>
    
    <div class="summary">
        <h2>Métricas de Performance</h2>
        <div class="metrics">
            <div class="metric">
                <div class="metric-value">{report.average_original_time:.1f}ms</div>
                <div>Tiempo Promedio Bot Original</div>
            </div>
            <div class="metric">
                <div class="metric-value">{report.average_refactored_time:.1f}ms</div>
                <div>Tiempo Promedio Bot Refactorizado</div>
            </div>
        </div>
    </div>
    
    <div class="summary">
        <h2>Detalle de Tests</h2>
        {self._generate_test_details_html(report.test_results)}
    </div>
    
    {self._generate_regressions_html(report.regressions) if report.regressions else ''}
</body>
</html>
        """
        return html
    
    def _generate_test_details_html(self, test_results: List[TestResult]) -> str:
        """Generar HTML para detalles de tests."""
        html = ""
        for result in test_results:
            css_class = "test-result"
            if result.is_regression:
                css_class += " failed regression"
            else:
                css_class += " passed"
            
            if result.critical:
                css_class += " critical"
            
            html += f"""
        <div class="{css_class}">
            <h3>Test {result.test_id}: {result.description}</h3>
            <p><strong>Crítico:</strong> {'Sí' if result.critical else 'No'}</p>
            <p><strong>Similitud:</strong> {result.similarity_score:.2%}</p>
            <p><strong>Tiempos:</strong> Original: {result.original_time_ms:.1f}ms, Refactorizado: {result.refactored_time_ms:.1f}ms</p>
            
            <div class="response-comparison">
                <div class="response-box">
                    <div class="response-label">Bot Original:</div>
                    <div>{result.original_response}</div>
                </div>
                <div class="response-box">
                    <div class="response-label">Bot Refactorizado:</div>
                    <div>{result.refactored_response}</div>
                </div>
            </div>
            
            {f'<p><strong>REGRESIÓN:</strong> {result.regression_reason}</p>' if result.is_regression else ''}
        </div>
            """
        return html
    
    def _generate_regressions_html(self, regressions: List[TestResult]) -> str:
        """Generar HTML para sección de regresiones."""
        html = """
    <div class="summary">
        <h2>Regresiones Detectadas</h2>
        <p style="color: #dc3545; font-weight: bold;">⚠️ ATENCIÓN: Se detectaron regresiones que requieren atención inmediata.</p>
        """
        
        for regression in regressions:
            html += f"""
        <div class="test-result failed critical">
            <h3>Test {regression.test_id}: {regression.description}</h3>
            <p><strong>Razón de la regresión:</strong> {regression.regression_reason}</p>
            <p><strong>Similitud:</strong> {regression.similarity_score:.2%}</p>
            
            <div class="response-comparison">
                <div class="response-box">
                    <div class="response-label">Bot Original:</div>
                    <div>{regression.original_response}</div>
                </div>
                <div class="response-box">
                    <div class="response-label">Bot Refactorizado:</div>
                    <div>{regression.refactored_response}</div>
                </div>
            </div>
        </div>
            """
        
        html += "</div>"
        return html


def main():
    """Función principal para ejecutar la comparación."""
    try:
        # Crear herramienta de comparación
        tool = BotComparisonTool()
        
        # Ejecutar comparación
        report = tool.run_comparison()
        
        # Generar reporte
        report_path = tool.generate_report(report)
        
        # Mostrar resumen en consola
        print("\n" + "="*60)
        print("RESUMEN DE COMPARACIÓN END-TO-END")
        print("="*60)
        print(f"Total de tests: {report.total_tests}")
        print(f"Tests exitosos: {report.passed_tests}")
        print(f"Regresiones: {report.failed_tests}")
        print(f"Fallos críticos: {report.critical_failures}")
        print(f"Similitud promedio: {report.average_similarity:.2%}")
        print(f"Tiempo promedio bot original: {report.average_original_time:.1f}ms")
        print(f"Tiempo promedio bot refactorizado: {report.average_refactored_time:.1f}ms")
        print(f"Reporte generado: {report_path}")
        
        if report.critical_failures > 0:
            print("\n⚠️  ATENCIÓN: Se detectaron fallos críticos que requieren atención inmediata.")
            return 1
        elif report.failed_tests > 0:
            print("\n⚠️  ADVERTENCIA: Se detectaron regresiones no críticas.")
            return 0
        else:
            print("\n✅ Todos los tests pasaron exitosamente.")
            return 0
            
    except Exception as e:
        logger.error(f"Error en comparación end-to-end: {e}")
        return 1


if __name__ == "__main__":
    exit(main()) 