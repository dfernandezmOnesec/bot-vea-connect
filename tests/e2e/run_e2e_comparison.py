#!/usr/bin/env python3
"""
Script de ejecución para comparación end-to-end de bots.

Uso:
    python run_e2e_comparison.py [--config test_data.json] [--output report.html]
"""

import argparse
import sys
from pathlib import Path
from bot_comparison_tool import BotComparisonTool


def main():
    """Función principal del script."""
    parser = argparse.ArgumentParser(
        description="Ejecutar comparación end-to-end entre bot original y refactorizado"
    )
    parser.add_argument(
        "--config",
        default="tests/e2e/test_data.json",
        help="Ruta al archivo de configuración de tests (default: tests/e2e/test_data.json)"
    )
    parser.add_argument(
        "--output",
        default="bot_comparison_report.html",
        help="Ruta del reporte de salida (default: bot_comparison_report.html)"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Mostrar información detallada durante la ejecución"
    )
    
    args = parser.parse_args()
    
    # Verificar que el archivo de configuración existe
    config_path = Path(args.config)
    if not config_path.exists():
        print(f"❌ Error: Archivo de configuración no encontrado: {config_path}")
        sys.exit(1)
    
    try:
        print("🚀 Iniciando comparación end-to-end de bots...")
        print(f"📁 Configuración: {config_path}")
        print(f"📄 Reporte: {args.output}")
        print("-" * 50)
        
        # Crear herramienta de comparación
        tool = BotComparisonTool(str(config_path))
        
        # Ejecutar comparación
        report = tool.run_comparison()
        
        # Generar reporte
        report_path = tool.generate_report(report, args.output)
        
        # Mostrar resumen
        print("\n" + "="*60)
        print("📊 RESUMEN DE COMPARACIÓN END-TO-END")
        print("="*60)
        print(f"📈 Total de tests: {report.total_tests}")
        print(f"✅ Tests exitosos: {report.passed_tests}")
        print(f"❌ Regresiones: {report.failed_tests}")
        print(f"🚨 Fallos críticos: {report.critical_failures}")
        print(f"📊 Similitud promedio: {report.average_similarity:.2%}")
        print(f"⏱️  Tiempo promedio bot original: {report.average_original_time:.1f}ms")
        print(f"⏱️  Tiempo promedio bot refactorizado: {report.average_refactored_time:.1f}ms")
        print(f"📄 Reporte generado: {report_path}")
        
        # Mostrar detalles si hay regresiones
        if report.regressions:
            print("\n🚨 REGRESIONES DETECTADAS:")
            for regression in report.regressions:
                status = "🚨 CRÍTICA" if regression.critical else "⚠️  NO CRÍTICA"
                print(f"  {status} - Test {regression.test_id}: {regression.regression_reason}")
        
        # Código de salida
        if report.critical_failures > 0:
            print("\n❌ ATENCIÓN: Se detectaron fallos críticos que requieren atención inmediata.")
            return 1
        elif report.failed_tests > 0:
            print("\n⚠️  ADVERTENCIA: Se detectaron regresiones no críticas.")
            return 0
        else:
            print("\n✅ Todos los tests pasaron exitosamente.")
            return 0
            
    except Exception as e:
        print(f"❌ Error en comparación end-to-end: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main()) 