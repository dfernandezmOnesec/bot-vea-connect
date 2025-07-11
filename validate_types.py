#!/usr/bin/env python3
"""
Script de validación de tipos para el bot de WhatsApp VEA Connect.

Este script verifica la compatibilidad de tipos entre interfaces e implementaciones
y genera un reporte de errores de tipo encontrados.
"""

import os
import sys
import subprocess
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_mypy_check() -> Dict[str, Any]:
    """
    Ejecutar verificación de tipos con mypy.
    
    Returns:
        Dict[str, Any]: Resultado de la verificación
    """
    try:
        logger.info("Ejecutando verificación de tipos con mypy...")
        
        # Comando para ejecutar mypy
        cmd = [
            sys.executable, "-m", "mypy",
            "shared_code/",
            "whatsapp_bot/",
            "tests/",
            "--ignore-missing-imports",
            "--no-strict-optional",
            "--show-error-codes",
            "--show-column-numbers"
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent
        )
        
        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode
        }
        
    except Exception as e:
        logger.error(f"Error ejecutando mypy: {e}")
        return {
            "success": False,
            "error": str(e),
            "stdout": "",
            "stderr": "",
            "returncode": -1
        }

def run_pyright_check() -> Dict[str, Any]:
    """
    Ejecutar verificación de tipos con pyright.
    
    Returns:
        Dict[str, Any]: Resultado de la verificación
    """
    try:
        logger.info("Ejecutando verificación de tipos con pyright...")
        
        # Comando para ejecutar pyright
        cmd = [
            sys.executable, "-m", "pyright",
            "shared_code/",
            "whatsapp_bot/",
            "tests/",
            "--outputformat=text"
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent
        )
        
        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode
        }
        
    except Exception as e:
        logger.error(f"Error ejecutando pyright: {e}")
        return {
            "success": False,
            "error": str(e),
            "stdout": "",
            "stderr": "",
            "returncode": -1
        }

def validate_service_implementations() -> Dict[str, Any]:
    """
    Validar manualmente las implementaciones de servicios.
    
    Returns:
        Dict[str, Any]: Resultado de la validación
    """
    results = {
        "whatsapp_service": False,
        "user_service": False,
        "openai_service": False,
        "redis_service": False,
        "vision_service": False,
        "blob_storage_service": False,
        "error_handler": False,
        "message_processor": False
    }
    
    try:
        # Importar servicios
        from shared_code.whatsapp_service import WhatsAppService
        from shared_code.user_service import UserService
        from shared_code.openai_service import OpenAIService
        from shared_code.redis_service import RedisService
        from shared_code.error_handler import ErrorHandler
        from shared_code.message_processor import MessageProcessor
        from shared_code.interfaces import (
            IWhatsAppService, IUserService, IOpenAIService, 
            IRedisService, IErrorHandler, IMessageProcessor
        )
        
        # Validar WhatsAppService
        try:
            whatsapp = WhatsAppService(skip_validation=True)
            results["whatsapp_service"] = isinstance(whatsapp, IWhatsAppService)
            logger.info(f"WhatsAppService implements interface: {results['whatsapp_service']}")
        except Exception as e:
            logger.error(f"Error validando WhatsAppService: {e}")
        
        # Validar UserService
        try:
            user_service = UserService()
            results["user_service"] = isinstance(user_service, IUserService)
            logger.info(f"UserService implements interface: {results['user_service']}")
        except Exception as e:
            logger.error(f"Error validando UserService: {e}")
        
        # Validar OpenAIService
        try:
            openai_service = OpenAIService()
            results["openai_service"] = isinstance(openai_service, IOpenAIService)
            logger.info(f"OpenAIService implements interface: {results['openai_service']}")
        except Exception as e:
            logger.error(f"Error validando OpenAIService: {e}")
        
        # Validar RedisService
        try:
            redis_service = RedisService()
            results["redis_service"] = isinstance(redis_service, IRedisService)
            logger.info(f"RedisService implements interface: {results['redis_service']}")
        except Exception as e:
            logger.error(f"Error validando RedisService: {e}")
        
        # Validar ErrorHandler
        try:
            error_handler = ErrorHandler()
            results["error_handler"] = isinstance(error_handler, IErrorHandler)
            logger.info(f"ErrorHandler implements interface: {results['error_handler']}")
        except Exception as e:
            logger.error(f"Error validando ErrorHandler: {e}")
        
        # Validar MessageProcessor (requiere servicios)
        try:
            # Crear mocks para testing
            from unittest.mock import Mock
            mock_whatsapp = Mock(spec=IWhatsAppService)
            mock_user = Mock(spec=IUserService)
            mock_openai = Mock(spec=IOpenAIService)
            mock_error = Mock(spec=IErrorHandler)
            
            message_processor = MessageProcessor(
                whatsapp_service=mock_whatsapp,
                user_service=mock_user,
                openai_service=mock_openai,
                error_handler=mock_error
            )
            results["message_processor"] = isinstance(message_processor, IMessageProcessor)
            logger.info(f"MessageProcessor implements interface: {results['message_processor']}")
        except Exception as e:
            logger.error(f"Error validando MessageProcessor: {e}")
        
        # Servicios opcionales
        try:
            from shared_code.vision_service import VisionService
            from shared_code.azure_blob_storage import AzureBlobStorageService
            from shared_code.interfaces import IVisionService, IBlobStorageService
            
            vision_service = VisionService(skip_validation=True)
            results["vision_service"] = isinstance(vision_service, IVisionService)
            logger.info(f"VisionService implements interface: {results['vision_service']}")
            
            blob_storage_service = AzureBlobStorageService()
            results["blob_storage_service"] = isinstance(blob_storage_service, IBlobStorageService)
            logger.info(f"BlobStorageService implements interface: {results['blob_storage_service']}")
        except Exception as e:
            logger.warning(f"Error validando servicios opcionales: {e}")
        
    except Exception as e:
        logger.error(f"Error en validación de servicios: {e}")
    
    return results

def validate_dependency_container() -> Dict[str, Any]:
    """
    Validar el contenedor de dependencias.
    
    Returns:
        Dict[str, Any]: Resultado de la validación
    """
    try:
        from shared_code.dependency_container import DependencyContainer
        
        container = DependencyContainer()
        
        # Verificar que se pueden obtener servicios principales
        services = {}
        main_services = ["whatsapp", "user", "openai", "error_handler"]
        
        for service_name in main_services:
            try:
                service = container.get_service(service_name)
                services[service_name] = service is not None
                logger.info(f"Servicio {service_name} obtenido: {service is not None}")
            except Exception as e:
                services[service_name] = False
                logger.error(f"Error obteniendo servicio {service_name}: {e}")
        
        # Verificar servicios opcionales
        optional_services = ["vision", "blob_storage", "redis"]
        for service_name in optional_services:
            try:
                service = container.get_service_safe(service_name)
                services[service_name] = service is not None
                logger.info(f"Servicio opcional {service_name} obtenido: {service is not None}")
            except Exception as e:
                services[service_name] = False
                logger.warning(f"Error obteniendo servicio opcional {service_name}: {e}")
        
        # Health check del contenedor
        try:
            health = container.health_check()
            services["container_health"] = health.get("container_healthy", False)
            logger.info(f"Health check del contenedor: {services['container_health']}")
        except Exception as e:
            services["container_health"] = False
            logger.error(f"Error en health check del contenedor: {e}")
        
        return services
        
    except Exception as e:
        logger.error(f"Error validando contenedor de dependencias: {e}")
        return {"error": str(e)}

def generate_report(
    mypy_result: Dict[str, Any],
    pyright_result: Dict[str, Any],
    service_validation: Dict[str, Any],
    container_validation: Dict[str, Any]
) -> str:
    """
    Generar reporte de validación de tipos.
    
    Args:
        mypy_result: Resultado de mypy
        pyright_result: Resultado de pyright
        service_validation: Validación de servicios
        container_validation: Validación del contenedor
        
    Returns:
        str: Reporte formateado
    """
    report = []
    report.append("=" * 80)
    report.append("REPORTE DE VALIDACIÓN DE TIPOS - BOT WHATSAPP VEA CONNECT")
    report.append("=" * 80)
    report.append("")
    
    # Resumen ejecutivo
    report.append("📊 RESUMEN EJECUTIVO")
    report.append("-" * 40)
    
    mypy_success = mypy_result.get("success", False)
    pyright_success = pyright_result.get("success", False)
    
    report.append(f"✅ MyPy: {'PASÓ' if mypy_success else 'FALLÓ'}")
    report.append(f"✅ PyRight: {'PASÓ' if pyright_success else 'FALLÓ'}")
    
    # Validación de servicios
    service_success = all(service_validation.values())
    report.append(f"✅ Servicios: {'PASÓ' if service_success else 'FALLÓ'}")
    
    # Validación del contenedor
    container_success = container_validation.get("container_health", False)
    report.append(f"✅ Contenedor: {'PASÓ' if container_success else 'FALLÓ'}")
    
    report.append("")
    
    # Detalles de servicios
    report.append("🔧 VALIDACIÓN DE SERVICIOS")
    report.append("-" * 40)
    for service, status in service_validation.items():
        status_icon = "✅" if status else "❌"
        report.append(f"{status_icon} {service}: {'OK' if status else 'ERROR'}")
    
    report.append("")
    
    # Detalles del contenedor
    report.append("📦 VALIDACIÓN DEL CONTENEDOR")
    report.append("-" * 40)
    for service, status in container_validation.items():
        if service != "error":
            status_icon = "✅" if status else "❌"
            report.append(f"{status_icon} {service}: {'OK' if status else 'ERROR'}")
    
    report.append("")
    
    # Errores de MyPy
    if not mypy_success:
        report.append("🚨 ERRORES DE MYPY")
        report.append("-" * 40)
        report.append(mypy_result.get("stdout", "No hay salida"))
        report.append("")
    
    # Errores de PyRight
    if not pyright_success:
        report.append("🚨 ERRORES DE PYRIGHT")
        report.append("-" * 40)
        report.append(pyright_result.get("stdout", "No hay salida"))
        report.append("")
    
    # Recomendaciones
    report.append("💡 RECOMENDACIONES")
    report.append("-" * 40)
    
    if not mypy_success or not pyright_success:
        report.append("1. Revisar errores de tipo en los archivos mencionados")
        report.append("2. Corregir incompatibilidades de tipos")
        report.append("3. Agregar type hints donde falten")
    
    if not service_success:
        report.append("4. Verificar que todos los servicios implementen sus interfaces")
        report.append("5. Agregar métodos faltantes en las implementaciones")
    
    if not container_success:
        report.append("6. Revisar configuración del contenedor de dependencias")
        report.append("7. Verificar que las factories funcionen correctamente")
    
    report.append("")
    report.append("=" * 80)
    
    return "\n".join(report)

def main():
    """Función principal del script."""
    logger.info("Iniciando validación de tipos...")
    
    # Ejecutar verificaciones
    mypy_result = run_mypy_check()
    pyright_result = run_pyright_check()
    service_validation = validate_service_implementations()
    container_validation = validate_dependency_container()
    
    # Generar reporte
    report = generate_report(
        mypy_result, pyright_result, service_validation, container_validation
    )
    
    # Mostrar reporte
    print(report)
    
    # Guardar reporte en archivo
    with open("type_validation_report.txt", "w", encoding="utf-8") as f:
        f.write(report)
    
    logger.info("Reporte guardado en type_validation_report.txt")
    
    # Determinar éxito general
    overall_success = (
        mypy_result.get("success", False) and
        pyright_result.get("success", False) and
        all(service_validation.values()) and
        container_validation.get("container_health", False)
    )
    
    if overall_success:
        logger.info("✅ Validación de tipos completada exitosamente")
        sys.exit(0)
    else:
        logger.error("❌ Validación de tipos encontró errores")
        sys.exit(1)

if __name__ == "__main__":
    main() 