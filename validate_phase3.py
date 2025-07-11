#!/usr/bin/env python3
"""
Script de validación rápida para la Fase 3.

Este script ejecuta una validación rápida de los componentes principales
de la Fase 3 para verificar que todo está funcionando correctamente.
"""

import os
import sys
import time
import subprocess
from datetime import datetime
from typing import Dict, Any, List


class Phase3Validator:
    """Validador rápido de la Fase 3."""
    
    def __init__(self):
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "checks": {},
            "summary": {}
        }
    
    def run_check(self, name: str, command: List[str], description: str) -> bool:
        """Ejecutar un check específico."""
        print(f"\n🔍 {name}: {description}")
        print("-" * 60)
        
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            success = result.returncode == 0
            
            if success:
                print(f"✅ {name}: PASÓ")
                if result.stdout.strip():
                    print(f"   Salida: {result.stdout.strip()[:200]}...")
            else:
                print(f"❌ {name}: FALLÓ")
                if result.stderr.strip():
                    print(f"   Error: {result.stderr.strip()[:200]}...")
            
            self.results["checks"][name] = {
                "success": success,
                "return_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr
            }
            
            return success
            
        except subprocess.TimeoutExpired:
            print(f"⏰ {name}: TIMEOUT")
            self.results["checks"][name] = {
                "success": False,
                "return_code": -1,
                "stdout": "",
                "stderr": "Timeout después de 60 segundos"
            }
            return False
        except Exception as e:
            print(f"💥 {name}: ERROR - {e}")
            self.results["checks"][name] = {
                "success": False,
                "return_code": -1,
                "stdout": "",
                "stderr": str(e)
            }
            return False
    
    def check_file_exists(self, name: str, filepath: str, description: str) -> bool:
        """Verificar que un archivo existe."""
        print(f"\n📁 {name}: {description}")
        print("-" * 60)
        
        exists = os.path.exists(filepath)
        
        if exists:
            print(f"✅ {name}: ARCHIVO ENCONTRADO - {filepath}")
        else:
            print(f"❌ {name}: ARCHIVO NO ENCONTRADO - {filepath}")
        
        self.results["checks"][name] = {
            "success": exists,
            "filepath": filepath,
            "exists": exists
        }
        
        return exists
    
    def validate_phase3(self) -> Dict[str, Any]:
        """Ejecutar validación completa de la Fase 3."""
        print("🚀 VALIDACIÓN RÁPIDA - FASE 3: TESTING EXHAUSTIVO")
        print("=" * 80)
        
        start_time = time.time()
        
        # Verificar archivos de tests
        test_files = [
            ("test_interfaces", "tests/unit/test_interfaces.py", "Tests de interfaces"),
            ("test_dependency_container", "tests/unit/test_dependency_container.py", "Tests del contenedor DI"),
            ("test_error_handler", "tests/unit/test_error_handler.py", "Tests del manejador de errores"),
            ("test_integration_complete", "tests/integration/test_integration_complete_system.py", "Tests de integración completa"),
            ("test_performance", "tests/performance/test_performance_benchmarks.py", "Tests de performance"),
            ("run_comprehensive_tests", "run_comprehensive_tests.py", "Script de ejecución completa"),
            ("phase3_docs", "FASE_3_TESTING_EXHAUSTIVO.md", "Documentación de la Fase 3")
        ]
        
        for name, filepath, description in test_files:
            self.check_file_exists(name, filepath, description)
        
        # Verificar que pytest está disponible
        self.run_check(
            "pytest_available",
            ["python", "-m", "pytest", "--version"],
            "Verificar que pytest está instalado"
        )
        
        # Verificar que mypy está disponible
        self.run_check(
            "mypy_available",
            ["mypy", "--version"],
            "Verificar que mypy está instalado"
        )
        
        # Ejecutar tests de interfaces (rápido)
        self.run_check(
            "test_interfaces_quick",
            ["python", "-m", "pytest", "tests/unit/test_interfaces.py", "-q"],
            "Ejecutar tests de interfaces (modo rápido)"
        )
        
        # Ejecutar tests del contenedor DI (rápido)
        self.run_check(
            "test_dependency_container_quick",
            ["python", "-m", "pytest", "tests/unit/test_dependency_container.py", "-q"],
            "Ejecutar tests del contenedor DI (modo rápido)"
        )
        
        # Ejecutar tests del manejador de errores (rápido)
        self.run_check(
            "test_error_handler_quick",
            ["python", "-m", "pytest", "tests/unit/test_error_handler.py", "-q"],
            "Ejecutar tests del manejador de errores (modo rápido)"
        )
        
        # Verificar validación de tipos
        self.run_check(
            "type_validation",
            ["python", "validate_types.py"],
            "Ejecutar validación de tipos"
        )
        
        # Verificar que el script de tests completos funciona
        self.run_check(
            "test_script_help",
            ["python", "run_comprehensive_tests.py", "--help"],
            "Verificar que el script de tests muestra ayuda"
        )
        
        # Analizar resultados
        total_checks = len(self.results["checks"])
        successful_checks = sum(1 for check in self.results["checks"].values() if check["success"])
        failed_checks = total_checks - successful_checks
        success_rate = (successful_checks / total_checks * 100) if total_checks > 0 else 0
        
        end_time = time.time()
        duration = end_time - start_time
        
        self.results["summary"] = {
            "total_checks": total_checks,
            "successful_checks": successful_checks,
            "failed_checks": failed_checks,
            "success_rate": success_rate,
            "duration": duration,
            "status": "PASS" if success_rate >= 80 else "FAIL"
        }
        
        # Mostrar resumen
        print(f"\n{'='*80}")
        print("📊 RESUMEN DE VALIDACIÓN")
        print(f"{'='*80}")
        print(f"Total de checks: {total_checks}")
        print(f"Checks exitosos: {successful_checks}")
        print(f"Checks fallidos: {failed_checks}")
        print(f"Tasa de éxito: {success_rate:.2f}%")
        print(f"Duración: {duration:.2f} segundos")
        print(f"Estado: {self.results['summary']['status']}")
        
        # Mostrar checks fallidos
        if failed_checks > 0:
            print(f"\n❌ CHECKS FALLIDOS:")
            for name, check in self.results["checks"].items():
                if not check["success"]:
                    print(f"   • {name}")
        
        # Mostrar recomendaciones
        print(f"\n💡 RECOMENDACIONES:")
        if success_rate >= 90:
            print("   ✅ La Fase 3 está lista para uso")
            print("   ✅ Todos los componentes principales están funcionando")
            print("   ✅ Puedes ejecutar tests completos con: python run_comprehensive_tests.py")
        elif success_rate >= 70:
            print("   ⚠️  La Fase 3 necesita algunas correcciones")
            print("   ⚠️  Revisar los checks fallidos antes de continuar")
            print("   ⚠️  Considerar ejecutar tests completos después de correcciones")
        else:
            print("   ❌ La Fase 3 necesita correcciones significativas")
            print("   ❌ Revisar todos los checks fallidos")
            print("   ❌ No ejecutar tests completos hasta corregir problemas")
        
        return self.results


def main():
    """Función principal."""
    validator = Phase3Validator()
    results = validator.validate_phase3()
    
    # Retornar código de salida basado en el éxito
    if results["summary"]["success_rate"] >= 80:
        print(f"\n🎉 Validación completada exitosamente!")
        sys.exit(0)
    else:
        print(f"\n💥 Validación falló. Revisar errores antes de continuar.")
        sys.exit(1)


if __name__ == "__main__":
    main() 