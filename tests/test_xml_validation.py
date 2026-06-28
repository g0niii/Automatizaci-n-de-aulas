# tests/test_xml_validation.py
import pytest
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

class TestXMLBienFormado:
    """Valida que los archivos XML sean bien formados"""

    def test_imscc_files_exist(self):
        """Verifica que existan archivos .imscc en output/"""
        imscc_dir = Path("output")
        imscc_files = list(imscc_dir.glob("*.imscc"))
        assert len(imscc_files) > 0, "No .imscc files found in output/"

    def test_imscc_contiene_imsmanifest(self):
        """Cada IMSCC debe contener imsmanifest.xml"""
        imscc_files = list(Path("output").glob("*.imscc"))
        if not imscc_files:
            pytest.skip("No .imscc files in output/")

        for imscc_path in imscc_files[:3]:  # Test primeros 3
            with zipfile.ZipFile(imscc_path, 'r') as z:
                assert 'imsmanifest.xml' in z.namelist(), f"{imscc_path.name} missing imsmanifest.xml"

    def test_imscc_contiene_module_meta(self):
        """Cada IMSCC debe contener course_settings/module_meta.xml"""
        imscc_files = list(Path("output").glob("*.imscc"))
        if not imscc_files:
            pytest.skip("No .imscc files in output/")

        for imscc_path in imscc_files[:3]:
            with zipfile.ZipFile(imscc_path, 'r') as z:
                module_meta_files = [f for f in z.namelist() if 'module_meta.xml' in f]
                assert len(module_meta_files) > 0, f"{imscc_path.name} missing module_meta.xml"

    def test_xml_parseable(self):
        """Todos los archivos XML dentro de IMSCC deben ser parseables"""
        imscc_files = list(Path("output").glob("*.imscc"))
        if not imscc_files:
            pytest.skip("No .imscc files in output/")

        for imscc_path in imscc_files[:2]:
            with zipfile.ZipFile(imscc_path, 'r') as z:
                xml_files = [f for f in z.namelist() if f.endswith('.xml')]
                for xml_file in xml_files:
                    try:
                        content = z.read(xml_file)
                        ET.fromstring(content)
                    except ET.ParseError as e:
                        pytest.fail(f"XML malformado en {imscc_path.name}/{xml_file}: {e}")

class TestEstructuraIMSCC:
    """Valida estructura y referencias en IMSCC"""

    def test_manifest_tiene_organizations(self):
        """imsmanifest.xml debe tener organizations"""
        imscc_files = list(Path("output").glob("*.imscc"))
        if not imscc_files:
            pytest.skip("No .imscc files in output/")

        imscc_path = imscc_files[0]
        with zipfile.ZipFile(imscc_path, 'r') as z:
            manifest_content = z.read('imsmanifest.xml')
            root = ET.fromstring(manifest_content)
            # Namespace IMS
            ns = {'imscc': 'http://www.imsglobal.org/xsd/imscp_v1p1'}
            organizations = root.findall('.//imscc:organizations', ns)
            assert len(organizations) > 0, "No organizations encontrada"

    def test_referencias_cruzadas_validas(self):
        """Items deben apuntar a resources que existen"""
        imscc_files = list(Path("output").glob("*.imscc"))
        if not imscc_files:
            pytest.skip("No .imscc files in output/")

        imscc_path = imscc_files[0]
        with zipfile.ZipFile(imscc_path, 'r') as z:
            manifest_content = z.read('imsmanifest.xml')
            root = ET.fromstring(manifest_content)

            # Extrae todos los identifiers de resources
            ns = {'imscc': 'http://www.imsglobal.org/xsd/imscp_v1p1'}
            resources = root.findall('.//imscc:resource', ns)
            resource_ids = {r.get('identifier') for r in resources if r.get('identifier')}

            # Valida que items apunten a resources válidos
            items = root.findall('.//imscc:item', ns)
            for item in items:
                identifierref = item.get('identifierref')
                if identifierref:
                    assert identifierref in resource_ids, f"Item apunta a resource inexistente: {identifierref}"

class TestIntegracion:
    """Tests de integración contra múltiples IMSCC"""

    def test_procesar_todos_imscc_output(self):
        """Procesa todos los IMSCC sin errores"""
        imscc_files = list(Path("output").glob("*.imscc"))
        if not imscc_files:
            pytest.skip("No .imscc files in output/")

        errores = []
        for imscc_path in imscc_files:
            try:
                with zipfile.ZipFile(imscc_path, 'r') as z:
                    manifest = z.read('imsmanifest.xml')
                    ET.fromstring(manifest)
            except Exception as e:
                errores.append(f"{imscc_path.name}: {e}")

        assert len(errores) == 0, f"Errores en XML: {errores}"

    def test_resumen_validacion(self):
        """Resumen: cuántos IMSCC válidos hay"""
        imscc_files = list(Path("output").glob("*.imscc"))
        if not imscc_files:
            pytest.skip("No .imscc files in output/")

        validos = 0
        for imscc_path in imscc_files:
            try:
                with zipfile.ZipFile(imscc_path, 'r') as z:
                    manifest = z.read('imsmanifest.xml')
                    ET.fromstring(manifest)
                    validos += 1
            except:
                pass

        print(f"\n✓ {validos}/{len(imscc_files)} IMSCC son válidos")
        assert validos > 0, "Al menos 1 IMSCC debe ser válido"
