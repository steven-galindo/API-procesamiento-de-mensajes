import os
import sys
import subprocess
from pathlib import Path

def run_all_tests():
    """
    Script para ejecutar todos los tests del proyecto manejando 
    automáticamente los directorios según el tipo de test.
    """
    project_root = Path(__file__).parent
    src_dir = project_root / "src"

    print("Ejecutando todos los Tests")
    print("=" * 50)
    
    # Test unitarios
    print("\nEjecutando Tests Unitarios...")
    print("-" * 30)
    
    unit_tests = [
        "tests/test_auth/",
        "tests/test_services/"
    ]
    
    for test_path in unit_tests:
        if (project_root / test_path).exists():
            print(f"Ejecutando: {test_path}")
            result = subprocess.run([
                sys.executable, "-m", "pytest", test_path, "-v"
            ], cwd=project_root)
            
            if result.returncode != 0:
                print(f" Error en {test_path}")
                return result.returncode
        else:
            print(f" No se encontró: {test_path}")
    
    # Tests de integración (desde la carpeta src)
    print("\nEjecutando Tests de Integración...")
    print("-" * 30)
    print(" Cambiando al directorio src...")
    
    integration_test = "../tests/test_integration/test_messages_endpoint.py"
    
    result = subprocess.run([
        sys.executable, "-m", "pytest", integration_test, "-v"
    ], cwd=src_dir)
    
    if result.returncode != 0:
        print(" Error en tests de integración")
        return result.returncode
    
    print("\nTodos los tests completados exitosamente!")
    return 0

def run_coverage():
    """Ejecutar tests con cobertura completa"""
    project_root = Path(__file__).parent
    src_dir = project_root / "src"
    
    print(" Ejecutando Tests con Cobertura...")
    print("=" * 50)
    
    # Limpiar cobertura anterior
    subprocess.run(["coverage", "erase"], cwd=project_root)
    
    # Tests unitarios con cobertura
    unit_tests = ["tests/test_auth/", "tests/test_services/"]
    for test_path in unit_tests:
        if (project_root / test_path).exists():
            subprocess.run([
                "coverage", "run", "--append", "-m", "pytest", test_path
            ], cwd=project_root)
    
    # Tests de integración con cobertura (desde src)
    subprocess.run([
        "coverage", "run", "--append", "-m", "pytest", 
        "../tests/test_integration/test_messages_endpoint.py"
    ], cwd=src_dir)
    
    # Generar reporte
    print("\n Reporte de Cobertura:")
    subprocess.run(["coverage", "report", "--include=src/*"], cwd=project_root)
    
    # Generar HTML
    subprocess.run(["coverage", "html", "--include=src/*"], cwd=project_root)
    print("Reporte HTML generado en: htmlcov/index.html")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Ejecutar tests del proyecto")
    parser.add_argument("--coverage", "-c", action="store_true", 
                       help="Ejecutar con cobertura")
    parser.add_argument("--integration-only", "-i", action="store_true",
                       help="Solo tests de integración")
    parser.add_argument("--unit-only", "-u", action="store_true",
                       help="Solo tests unitarios")
    
    args = parser.parse_args()
    
    if args.coverage:
        run_coverage()
    elif args.integration_only:
        # Solo integración
        project_root = Path(__file__).parent
        src_dir = project_root / "src"
        subprocess.run([
            sys.executable, "-m", "pytest", 
            "../tests/test_integration/test_messages_endpoint.py", "-v"
        ], cwd=src_dir)
    elif args.unit_only:
        # Solo unitarios
        project_root = Path(__file__).parent
        subprocess.run([
            sys.executable, "-m", "pytest", "tests/test_auth/", "tests/test_services/", "-v"
        ], cwd=project_root)
    else:
        # Todos los tests
        sys.exit(run_all_tests())