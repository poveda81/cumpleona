#!/usr/bin/env python3
"""
Script de testing completo para Operación Portal 27.

Verifica:
- Integridad de datos JSON
- Referencias entre escenas
- Existencia de imágenes
- Configuración de puzzles
- Navegabilidad completa
- Finales alcanzables
"""

import json
import sys
from pathlib import Path
from collections import defaultdict, deque

# Colores para output
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_section(title):
    """Imprime un título de sección."""
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}{title}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.RESET}\n")

def print_success(msg):
    """Imprime mensaje de éxito."""
    print(f"{Colors.GREEN}✓{Colors.RESET} {msg}")

def print_warning(msg):
    """Imprime mensaje de advertencia."""
    print(f"{Colors.YELLOW}⚠{Colors.RESET} {msg}")

def print_error(msg):
    """Imprime mensaje de error."""
    print(f"{Colors.RED}✗{Colors.RESET} {msg}")

def print_info(msg):
    """Imprime mensaje informativo."""
    print(f"{Colors.BLUE}ℹ{Colors.RESET} {msg}")

class GameTester:
    def __init__(self, base_path):
        self.base_path = Path(base_path)
        self.errors = []
        self.warnings = []
        self.agents = {}
        self.scenes = {}
        self.puzzles = {}
        self.start_scene = None

    def load_json_file(self, path):
        """Carga y valida un archivo JSON."""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            self.errors.append(f"JSON inválido en {path}: {e}")
            return None
        except FileNotFoundError:
            self.errors.append(f"Archivo no encontrado: {path}")
            return None

    def test_json_integrity(self):
        """Verifica que todos los archivos JSON sean válidos."""
        print_section("1. INTEGRIDAD DE ARCHIVOS JSON")

        # Cargar agents.json
        agents_path = self.base_path / 'web/data/agents.json'
        agents_data = self.load_json_file(agents_path)
        if agents_data:
            self.agents = agents_data
            print_success(f"agents.json: {len(self.agents)} agentes encontrados")

        # Cargar story.json
        story_path = self.base_path / 'web/data/story.json'
        story_data = self.load_json_file(story_path)
        if story_data:
            self.scenes = story_data.get('scenes', {})
            self.start_scene = story_data.get('meta', {}).get('start', 'intro')
            print_success(f"story.json: {len(self.scenes)} escenas encontradas")
            print_info(f"Escena inicial: {self.start_scene}")

        # Cargar puzzles.json
        puzzles_path = self.base_path / 'web/data/puzzles.json'
        puzzles_data = self.load_json_file(puzzles_path)
        if puzzles_data:
            self.puzzles = puzzles_data.get('puzzles', {})
            print_success(f"puzzles.json: {len(self.puzzles)} puzzles encontrados")

    def test_agent_data(self):
        """Verifica la completitud de datos de agentes."""
        print_section("2. DATOS DE AGENTES")

        required_fields = ['name', 'tag', 'avatar', 'qualities', 'specialItem', 'fullbody']
        optional_fields = ['luckyNumber', 'generated']

        for agent_id, agent in self.agents.items():
            missing = [f for f in required_fields if f not in agent]
            if missing:
                self.errors.append(f"Agente '{agent_id}' falta campos: {', '.join(missing)}")

            # Verificar luckyNumber
            if 'luckyNumber' not in agent:
                self.warnings.append(f"Agente '{agent_id}' no tiene luckyNumber")

            # Verificar que qualities sea un array
            if 'qualities' in agent and not isinstance(agent['qualities'], list):
                self.errors.append(f"Agente '{agent_id}': 'qualities' debe ser un array")

        if not self.errors:
            print_success(f"Todos los {len(self.agents)} agentes tienen datos completos")

        # Mostrar lucky numbers
        lucky_numbers = {aid: a.get('luckyNumber', 'N/A') for aid, a in self.agents.items()}
        if all(v != 'N/A' for v in lucky_numbers.values()):
            print_success(f"Todos los agentes tienen luckyNumber asignado")

    def test_images(self):
        """Verifica que todas las imágenes existan."""
        print_section("3. EXISTENCIA DE IMÁGENES")

        missing_images = []
        missing_avatars = []

        # Verificar imágenes de agentes
        print_info("Verificando imágenes de agentes...")
        for agent_id, agent in self.agents.items():
            # Avatar (solo advertencia, no son críticos)
            if 'avatar' in agent:
                avatar_path = self.base_path / 'web' / agent['avatar']
                if not avatar_path.exists():
                    missing_avatars.append(f"Avatar de {agent_id}: {agent['avatar']}")

            # Fullbody (sí son críticos)
            if 'fullbody' in agent:
                fullbody_path = self.base_path / 'web' / agent['fullbody']
                if not fullbody_path.exists():
                    missing_images.append(f"Fullbody de {agent_id}: {agent['fullbody']}")

        # Verificar imágenes de escenas
        print_info("Verificando imágenes de escenas...")
        for scene_id, scene in self.scenes.items():
            if 'image' in scene:
                img_path = self.base_path / 'web' / scene['image']
                if not img_path.exists():
                    missing_images.append(f"Escena {scene_id}: {scene['image']}")

        # Los avatares faltantes son advertencias, no errores
        if missing_avatars:
            for img in missing_avatars:
                self.warnings.append(f"Avatar no encontrado (opcional): {img}")
            print_warning(f"{len(missing_avatars)} avatares faltantes (no crítico)")

        if missing_images:
            for img in missing_images:
                self.errors.append(f"Imagen no encontrada: {img}")
        else:
            print_success("Todas las imágenes críticas (fullbody y escenas) existen")

    def test_scene_references(self):
        """Verifica que todas las referencias entre escenas sean válidas."""
        print_section("4. REFERENCIAS ENTRE ESCENAS")

        broken_refs = []

        for scene_id, scene in self.scenes.items():
            # Verificar choices
            if 'choices' in scene:
                for choice in scene['choices']:
                    target = choice.get('next')
                    if target and target not in self.scenes:
                        broken_refs.append(f"Escena '{scene_id}' → '{target}' (no existe)")

            # Verificar puzzle success/fail
            if 'puzzle' in scene:
                puzzle = scene['puzzle']
                # El puzzle puede ser un objeto con {type, id, data}
                if isinstance(puzzle, dict):
                    puzzle_id = puzzle.get('id')
                else:
                    puzzle_id = puzzle

                # Verificar success
                if 'success' in scene and scene['success'] not in self.scenes:
                    broken_refs.append(f"Escena '{scene_id}' → success '{scene['success']}' (no existe)")

                # Verificar fail
                if 'fail' in scene and scene['fail'] not in self.scenes:
                    broken_refs.append(f"Escena '{scene_id}' → fail '{scene['fail']}' (no existe)")

        if broken_refs:
            for ref in broken_refs:
                self.errors.append(f"Referencia rota: {ref}")
        else:
            print_success("Todas las referencias entre escenas son válidas")

    def test_puzzle_configuration(self):
        """Verifica la configuración de puzzles."""
        print_section("5. CONFIGURACIÓN DE PUZZLES")

        # Encontrar escenas con puzzles
        scenes_with_puzzles = []
        for scene_id, scene in self.scenes.items():
            if 'puzzle' in scene:
                puzzle = scene['puzzle']
                # El puzzle puede ser un objeto con {type, id, data} o un string
                if isinstance(puzzle, dict):
                    puzzle_id = puzzle.get('id', 'unknown')
                else:
                    puzzle_id = puzzle
                scenes_with_puzzles.append((scene_id, puzzle_id, puzzle))

        print_info(f"Encontradas {len(scenes_with_puzzles)} escenas con puzzles")

        for scene_id, puzzle_id, puzzle_data in scenes_with_puzzles:
            scene = self.scenes[scene_id]

            # Si el puzzle es inline (objeto dict), ya está configurado
            if isinstance(puzzle_data, dict):
                print_success(f"Escena '{scene_id}': puzzle inline '{puzzle_id}' configurado")
            else:
                # Verificar si existe en puzzles.json
                if puzzle_id in self.puzzles:
                    print_success(f"Escena '{scene_id}': puzzle '{puzzle_id}' en puzzles.json")
                else:
                    self.errors.append(f"Escena '{scene_id}': puzzle '{puzzle_id}' no encontrado")

            # Verificar que tenga success/fail
            if 'success' not in scene:
                self.warnings.append(f"Escena '{scene_id}': puzzle sin ruta 'success'")
            if 'fail' not in scene:
                self.warnings.append(f"Escena '{scene_id}': puzzle sin ruta 'fail'")

    def test_game_navigation(self):
        """Verifica que todas las escenas sean alcanzables."""
        print_section("6. NAVEGABILIDAD DEL JUEGO")

        # BFS para encontrar todas las escenas alcanzables
        visited = set()
        queue = deque([self.start_scene])
        visited.add(self.start_scene)

        while queue:
            scene_id = queue.popleft()
            scene = self.scenes.get(scene_id)

            if not scene:
                continue

            # Agregar escenas alcanzables desde choices
            if 'choices' in scene:
                for choice in scene['choices']:
                    target = choice.get('next')
                    if target and target not in visited and target in self.scenes:
                        visited.add(target)
                        queue.append(target)

            # Agregar escenas desde puzzles
            if 'puzzle' in scene:
                if 'success' in scene and scene['success'] not in visited:
                    visited.add(scene['success'])
                    queue.append(scene['success'])
                if 'fail' in scene and scene['fail'] not in visited:
                    visited.add(scene['fail'])
                    queue.append(scene['fail'])

        unreachable = set(self.scenes.keys()) - visited

        print_info(f"Escenas alcanzables: {len(visited)}/{len(self.scenes)}")

        if unreachable:
            print_warning(f"Escenas inalcanzables ({len(unreachable)}):")
            for scene_id in sorted(unreachable):
                print(f"  - {scene_id}")
                self.warnings.append(f"Escena inalcanzable: {scene_id}")
        else:
            print_success("Todas las escenas son alcanzables desde el inicio")

    def test_endings(self):
        """Verifica los finales del juego."""
        print_section("7. FINALES DEL JUEGO")

        endings = []
        for scene_id, scene in self.scenes.items():
            # Buscar isEnding o ending (ambos formatos)
            if scene.get('isEnding', False) or scene.get('ending', ''):
                # Solo contar si ending es un string no vacío o si isEnding es True
                ending_value = scene.get('ending', '')
                if scene.get('isEnding', False) or (ending_value and ending_value != False):
                    endings.append(scene_id)

        print_info(f"Finales encontrados: {len(endings)}")

        if endings:
            for ending in sorted(endings):
                ending_type = self.scenes[ending].get('ending', 'final')
                print_success(f"  {ending} (tipo: {ending_type})")
        else:
            self.warnings.append("No se encontraron finales marcados explícitamente")

    def test_dead_ends(self):
        """Detecta callejones sin salida (escenas sin opciones de continuar)."""
        print_section("8. DETECCIÓN DE CALLEJONES SIN SALIDA")

        dead_ends = []

        for scene_id, scene in self.scenes.items():
            # Una escena es dead end si no es un final y no tiene choices ni puzzle
            is_ending = scene.get('isEnding', False)
            has_choices = 'choices' in scene and len(scene['choices']) > 0
            has_puzzle = 'puzzle' in scene

            if not is_ending and not has_choices and not has_puzzle:
                dead_ends.append(scene_id)

        if dead_ends:
            print_warning(f"Callejones sin salida encontrados ({len(dead_ends)}):")
            for scene_id in dead_ends:
                print(f"  - {scene_id}")
                self.warnings.append(f"Callejón sin salida: {scene_id}")
        else:
            print_success("No se encontraron callejones sin salida")

    def generate_statistics(self):
        """Genera estadísticas del juego."""
        print_section("9. ESTADÍSTICAS DEL JUEGO")

        # Contar tipos de escenas
        regular_scenes = 0
        puzzle_scenes = 0
        ending_scenes = 0

        for scene in self.scenes.values():
            ending_value = scene.get('ending', '')
            if scene.get('isEnding', False) or (ending_value and ending_value != False):
                ending_scenes += 1
            elif 'puzzle' in scene:
                puzzle_scenes += 1
            else:
                regular_scenes += 1

        # Contar tipos de finales
        ending_types = defaultdict(int)
        for scene in self.scenes.values():
            ending_value = scene.get('ending', '')
            if scene.get('isEnding', False) or (ending_value and ending_value != False):
                ending_type = ending_value if ending_value else 'unknown'
                ending_types[ending_type] += 1

        print(f"{Colors.BOLD}Agentes:{Colors.RESET} {len(self.agents)}")
        print(f"{Colors.BOLD}Escenas totales:{Colors.RESET} {len(self.scenes)}")
        print(f"  - Escenas regulares: {regular_scenes}")
        print(f"  - Escenas con puzzle: {puzzle_scenes}")
        print(f"  - Finales: {ending_scenes}")

        if ending_types:
            print(f"\n{Colors.BOLD}Tipos de finales:{Colors.RESET}")
            for ending_type, count in ending_types.items():
                print(f"  - {ending_type}: {count}")

        print(f"\n{Colors.BOLD}Puzzles definidos:{Colors.RESET} {len(self.puzzles)}")

    def print_summary(self):
        """Imprime resumen final."""
        print_section("RESUMEN FINAL")

        total_issues = len(self.errors) + len(self.warnings)

        if self.errors:
            print(f"\n{Colors.RED}{Colors.BOLD}ERRORES CRÍTICOS ({len(self.errors)}):{Colors.RESET}")
            for error in self.errors:
                print(f"  {Colors.RED}✗{Colors.RESET} {error}")

        if self.warnings:
            print(f"\n{Colors.YELLOW}{Colors.BOLD}ADVERTENCIAS ({len(self.warnings)}):{Colors.RESET}")
            for warning in self.warnings:
                print(f"  {Colors.YELLOW}⚠{Colors.RESET} {warning}")

        print(f"\n{Colors.BOLD}{'='*70}{Colors.RESET}")
        if self.errors:
            print(f"{Colors.RED}{Colors.BOLD}❌ TEST FALLIDO{Colors.RESET}")
            print(f"Se encontraron {len(self.errors)} errores críticos")
            return False
        elif self.warnings:
            print(f"{Colors.YELLOW}{Colors.BOLD}⚠ TEST CON ADVERTENCIAS{Colors.RESET}")
            print(f"Se encontraron {len(self.warnings)} advertencias")
            return True
        else:
            print(f"{Colors.GREEN}{Colors.BOLD}✓ TODOS LOS TESTS PASARON{Colors.RESET}")
            print("El juego está completamente funcional")
            return True

    def run_all_tests(self):
        """Ejecuta todos los tests."""
        print(f"\n{Colors.BOLD}{Colors.CYAN}")
        print("╔═══════════════════════════════════════════════════════════════════╗")
        print("║         TESTING COMPLETO - OPERACIÓN PORTAL 27                   ║")
        print("╚═══════════════════════════════════════════════════════════════════╝")
        print(f"{Colors.RESET}\n")

        self.test_json_integrity()
        self.test_agent_data()
        self.test_images()
        self.test_scene_references()
        self.test_puzzle_configuration()
        self.test_game_navigation()
        self.test_endings()
        self.test_dead_ends()
        self.generate_statistics()

        return self.print_summary()

def main():
    # Encontrar la raíz del proyecto
    script_dir = Path(__file__).parent
    project_root = script_dir.parent

    tester = GameTester(project_root)
    success = tester.run_all_tests()

    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
