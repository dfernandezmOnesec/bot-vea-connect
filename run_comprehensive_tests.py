#!/usr/bin/env python3
"""
Script para ejecutar tests exhaustivos de la Fase 3.

Este script ejecuta todos los tests unitarios, de integración y de performance,
generando un reporte completo del estado del sistema.
"""

import os
import sys
import time
import subprocess
import json
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
import argparse


class TestRunner:
    """Ejecutor de tests con reportes detallados."""
    
    def __init__(self, output_dir: str = "test_reports"):
        self.output_dir = output_dir
        self.results = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "summary": {},
            "unit_tests": {},
            "integration_tests": {},
            "performance_tests": {},
            "coverage": {},
            "errors": []
        }
        
        # Crear directorio de reportes si no existe
        os.makedirs(output_dir, exist_ok=True)
    
    def run_command(self, command: List[str], test_type: str) -> Dict[str, Any]:
        """Ejecutar comando y capturar resultados."""
        print(f"\n{'='*60}")
        print(f"Ejecutando: {' '.join(command)}")
        print(f"{'='*60}")
        
        start_time = time.time()
        
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=300  # 5 minutos de timeout
            )
            
            end_time = time.time()
            duration = end_time - start_time
            
            return {
                "command": command,
                "return_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "duration": duration,
                "success": result.returncode == 0
            }
            
        except subprocess.TimeoutExpired:
            return {
                "command": command,
                "return_code": -1,
                "stdout": "",
                "stderr": "Timeout después de 5 minutos",
                "duration": 300,
                "success": False
            }
        except Exception as e:
            return {
                "command": command,
                "return_code": -1,
                "stdout": "",
                "stderr": str(e),
                "duration": 0,
                "success": False
            }
    
    def run_unit_tests(self) -> Dict[str, Any]:
        """Ejecutar tests unitarios."""
        print("\n🔬 Ejecutando Tests Unitarios...")
        
        # Tests de interfaces
        interface_result = self.run_command(
            ["python", "-m", "pytest", "tests/unit/test_interfaces.py", "-v"],
            "interfaces"
        )
        
        # Tests del contenedor de dependencias
        container_result = self.run_command(
            ["python", "-m", "pytest", "tests/unit/test_dependency_container.py", "-v"],
            "dependency_container"
        )
        
        # Tests del manejador de errores
        error_handler_result = self.run_command(
            ["python", "-m", "pytest", "tests/unit/test_error_handler.py", "-v"],
            "error_handler"
        )
        
        # Tests del procesador de mensajes
        message_processor_result = self.run_command(
            ["python", "-m", "pytest", "tests/unit/test_message_processor.py", "-v"],
            "message_processor"
        )
        
        # Tests de todos los servicios
        services_result = self.run_command(
            ["python", "-m", "pytest", "tests/unit/", "-v", "--tb=short"],
            "all_services"
        )
        
        return {
            "interfaces": interface_result,
            "dependency_container": container_result,
            "error_handler": error_handler_result,
            "message_processor": message_processor_result,
            "all_services": services_result
        }
    
    def run_integration_tests(self) -> Dict[str, Any]:
        """Ejecutar tests de integración."""
        print("\n🔗 Ejecutando Tests de Integración...")
        
        # Tests de integración del sistema completo
        complete_system_result = self.run_command(
            ["python", "-m", "pytest", "tests/integration/test_integration_complete_system.py", "-v"],
            "complete_system"
        )
        
        # Tests de integración existentes
        existing_integration_result = self.run_command(
            ["python", "-m", "pytest", "tests/integration/", "-v", "--tb=short"],
            "existing_integration"
        )
        
        return {
            "complete_system": complete_system_result,
            "existing_integration": existing_integration_result
        }
    
    def run_performance_tests(self) -> Dict[str, Any]:
        """Ejecutar tests de performance."""
        print("\n⚡ Ejecutando Tests de Performance...")
        
        # Tests de benchmarks de performance
        performance_result = self.run_command(
            ["python", "-m", "pytest", "tests/performance/test_performance_benchmarks.py", "-v"],
            "performance_benchmarks"
        )
        
        return {
            "performance_benchmarks": performance_result
        }
    
    def run_coverage_analysis(self) -> Dict[str, Any]:
        """Ejecutar análisis de cobertura."""
        print("\n📊 Ejecutando Análisis de Cobertura...")
        
        # Cobertura de tests unitarios
        unit_coverage_result = self.run_command(
            ["python", "-m", "pytest", "tests/unit/", "--cov=shared_code", "--cov-report=term-missing"],
            "unit_coverage"
        )
        
        # Cobertura de tests de integración
        integration_coverage_result = self.run_command(
            ["python", "-m", "pytest", "tests/integration/", "--cov=shared_code", "--cov-report=term-missing"],
            "integration_coverage"
        )
        
        # Cobertura completa
        full_coverage_result = self.run_command(
            ["python", "-m", "pytest", "tests/", "--cov=shared_code", "--cov-report=html", "--cov-report=term-missing"],
            "full_coverage"
        )
        
        return {
            "unit_coverage": unit_coverage_result,
            "integration_coverage": integration_coverage_result,
            "full_coverage": full_coverage_result
        }
    
    def run_type_validation(self) -> Dict[str, Any]:
        """Ejecutar validación de tipos."""
        print("\n🔍 Ejecutando Validación de Tipos...")
        
        # Validación con mypy
        mypy_result = self.run_command(
            ["python", "validate_types.py"],
            "mypy_validation"
        )
        
        return {
            "mypy_validation": mypy_result
        }
    
    def analyze_results(self) -> Dict[str, Any]:
        """Analizar resultados de todos los tests."""
        print("\n📈 Analizando Resultados...")
        
        # Contar tests exitosos y fallidos
        total_tests = 0
        successful_tests = 0
        failed_tests = 0
        
        # Analizar tests unitarios
        for test_name, result in self.results["unit_tests"].items():
            if result["success"]:
                successful_tests += 1
            else:
                failed_tests += 1
                self.results["errors"].append(f"Unit test failed: {test_name}")
            total_tests += 1
        
        # Analizar tests de integración
        for test_name, result in self.results["integration_tests"].items():
            if result["success"]:
                successful_tests += 1
            else:
                failed_tests += 1
                self.results["errors"].append(f"Integration test failed: {test_name}")
            total_tests += 1
        
        # Analizar tests de performance
        for test_name, result in self.results["performance_tests"].items():
            if result["success"]:
                successful_tests += 1
            else:
                failed_tests += 1
                self.results["errors"].append(f"Performance test failed: {test_name}")
            total_tests += 1
        
        # Calcular métricas
        success_rate = (successful_tests / total_tests * 100) if total_tests > 0 else 0
        
        self.results["summary"] = {
            "total_tests": total_tests,
            "successful_tests": successful_tests,
            "failed_tests": failed_tests,
            "success_rate": success_rate,
            "overall_status": "PASS" if success_rate >= 90 else "FAIL"
        }
        
        return self.results["summary"]
    
    def generate_report(self) -> str:
        """Generar reporte completo."""
        print("\n📋 Generando Reporte...")
        
        # Analizar resultados
        summary = self.analyze_results()
        
        # Generar reporte en formato JSON
        report_file = os.path.join(self.output_dir, f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        
        # Generar reporte en formato texto
        text_report_file = os.path.join(self.output_dir, f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
        
        with open(text_report_file, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("REPORTE COMPLETO DE TESTS - FASE 3\n")
            f.write("=" * 80 + "\n")
            f.write(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Timestamp: {self.results['timestamp']}\n\n")
            
            # Resumen
            f.write("RESUMEN EJECUTIVO\n")
            f.write("-" * 40 + "\n")
            f.write(f"Total de tests: {summary['total_tests']}\n")
            f.write(f"Tests exitosos: {summary['successful_tests']}\n")
            f.write(f"Tests fallidos: {summary['failed_tests']}\n")
            f.write(f"Tasa de éxito: {summary['success_rate']:.2f}%\n")
            f.write(f"Estado general: {summary['overall_status']}\n\n")
            
            # Tests Unitarios
            f.write("TESTS UNITARIOS\n")
            f.write("-" * 40 + "\n")
            for test_name, result in self.results["unit_tests"].items():
                status = "✅ PASÓ" if result["success"] else "❌ FALLÓ"
                f.write(f"{test_name}: {status} ({result['duration']:.2f}s)\n")
            f.write("\n")
            
            # Tests de Integración
            f.write("TESTS DE INTEGRACIÓN\n")
            f.write("-" * 40 + "\n")
            for test_name, result in self.results["integration_tests"].items():
                status = "✅ PASÓ" if result["success"] else "❌ FALLÓ"
                f.write(f"{test_name}: {status} ({result['duration']:.2f}s)\n")
            f.write("\n")
            
            # Tests de Performance
            f.write("TESTS DE PERFORMANCE\n")
            f.write("-" * 40 + "\n")
            for test_name, result in self.results["performance_tests"].items():
                status = "✅ PASÓ" if result["success"] else "❌ FALLÓ"
                f.write(f"{test_name}: {status} ({result['duration']:.2f}s)\n")
            f.write("\n")
            
            # Cobertura
            f.write("ANÁLISIS DE COBERTURA\n")
            f.write("-" * 40 + "\n")
            for test_name, result in self.results["coverage"].items():
                status = "✅ PASÓ" if result["success"] else "❌ FALLÓ"
                f.write(f"{test_name}: {status} ({result['duration']:.2f}s)\n")
            f.write("\n")
            
            # Errores
            if self.results["errors"]:
                f.write("ERRORES DETECTADOS\n")
                f.write("-" * 40 + "\n")
                for error in self.results["errors"]:
                    f.write(f"• {error}\n")
                f.write("\n")
            
            # Recomendaciones
            f.write("RECOMENDACIONES\n")
            f.write("-" * 40 + "\n")
            if summary['success_rate'] >= 90:
                f.write("✅ El sistema está listo para producción\n")
                f.write("✅ Todos los componentes principales están funcionando correctamente\n")
                f.write("✅ La arquitectura modular está validada\n")
            elif summary['success_rate'] >= 70:
                f.write("⚠️  El sistema necesita mejoras antes de producción\n")
                f.write("⚠️  Revisar los tests fallidos y corregir los problemas\n")
                f.write("⚠️  Considerar refactorización de componentes problemáticos\n")
            else:
                f.write("❌ El sistema no está listo para producción\n")
                f.write("❌ Se requieren correcciones significativas\n")
                f.write("❌ Revisar la arquitectura y implementación\n")
            
            f.write("\n" + "=" * 80 + "\n")
        
        return text_report_file
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Ejecutar todos los tests."""
        print("🚀 Iniciando Ejecución Completa de Tests - Fase 3")
        print(f"Directorio de reportes: {self.output_dir}")
        
        start_time = time.time()
        
        try:
            # Ejecutar tests unitarios
            self.results["unit_tests"] = self.run_unit_tests()
            
            # Ejecutar tests de integración
            self.results["integration_tests"] = self.run_integration_tests()
            
            # Ejecutar tests de performance
            self.results["performance_tests"] = self.run_performance_tests()
            
            # Ejecutar análisis de cobertura
            self.results["coverage"] = self.run_coverage_analysis()
            
            # Ejecutar validación de tipos
            type_validation = self.run_type_validation()
            self.results["type_validation"] = type_validation
            
            # Generar reporte
            report_file = self.generate_report()
            
            end_time = time.time()
            total_duration = end_time - start_time
            
            print(f"\n✅ Ejecución completada en {total_duration:.2f} segundos")
            print(f"📄 Reporte generado: {report_file}")
            
            # Mostrar resumen en consola
            summary = self.results["summary"]
            print(f"\n📊 RESUMEN:")
            print(f"   Total de tests: {summary['total_tests']}")
            print(f"   Tests exitosos: {summary['successful_tests']}")
            print(f"   Tests fallidos: {summary['failed_tests']}")
            print(f"   Tasa de éxito: {summary['success_rate']:.2f}%")
            print(f"   Estado general: {summary['overall_status']}")
            
            return self.results
            
        except Exception as e:
            print(f"\n❌ Error durante la ejecución: {e}")
            self.results["errors"].append(f"Error de ejecución: {e}")
            return self.results


def main():
    """Función principal."""
    parser = argparse.ArgumentParser(description="Ejecutar tests exhaustivos de la Fase 3")
    parser.add_argument(
        "--output-dir",
        default="test_reports",
        help="Directorio para guardar reportes (default: test_reports)"
    )
    parser.add_argument(
        "--unit-only",
        action="store_true",
        help="Ejecutar solo tests unitarios"
    )
    parser.add_argument(
        "--integration-only",
        action="store_true",
        help="Ejecutar solo tests de integración"
    )
    parser.add_argument(
        "--performance-only",
        action="store_true",
        help="Ejecutar solo tests de performance"
    )
    
    args = parser.parse_args()
    
    runner = TestRunner(args.output_dir)
    
    if args.unit_only:
        print("🔬 Ejecutando solo tests unitarios...")
        runner.results["unit_tests"] = runner.run_unit_tests()
        runner.results["integration_tests"] = {}
        runner.results["performance_tests"] = {}
        runner.results["coverage"] = {}
    elif args.integration_only:
        print("🔗 Ejecutando solo tests de integración...")
        runner.results["unit_tests"] = {}
        runner.results["integration_tests"] = runner.run_integration_tests()
        runner.results["performance_tests"] = {}
        runner.results["coverage"] = {}
    elif args.performance_only:
        print("⚡ Ejecutando solo tests de performance...")
        runner.results["unit_tests"] = {}
        runner.results["integration_tests"] = {}
        runner.results["performance_tests"] = runner.run_performance_tests()
        runner.results["coverage"] = {}
    else:
        # Ejecutar todos los tests
        runner.run_all_tests()
    
    # Generar reporte
    report_file = runner.generate_report()
    print(f"\n📄 Reporte generado: {report_file}")
    
    # Retornar código de salida basado en el éxito
    summary = runner.results["summary"]
    if summary.get("success_rate", 0) >= 90:
        sys.exit(0)  # Éxito
    else:
        sys.exit(1)  # Fallo


if __name__ == "__main__":
    main() 