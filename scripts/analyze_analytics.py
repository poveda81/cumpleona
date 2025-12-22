#!/usr/bin/env python3
"""
Script para analizar los datos de analytics exportados del juego.

Uso:
    python scripts/analyze_analytics.py portal27_analytics_XXXXX.json
"""

import json
import sys
from pathlib import Path
from collections import Counter, defaultdict
from datetime import datetime


def load_events(filepath):
    """Carga eventos desde un archivo JSON."""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def analyze_events(events):
    """Analiza los eventos y genera estadísticas."""

    # Métricas básicas
    total_events = len(events)
    unique_sessions = len(set(e['sessionId'] for e in events))
    event_types = Counter(e['eventType'] for e in events)

    print("=" * 60)
    print("📊 ANÁLISIS DE ANALYTICS - OPERACIÓN PORTAL 27")
    print("=" * 60)
    print()

    print(f"📈 Métricas generales:")
    print(f"   Total de eventos: {total_events}")
    print(f"   Sesiones únicas: {unique_sessions}")
    print(f"   Eventos por sesión: {total_events / unique_sessions:.1f}")
    print()

    print(f"📋 Tipos de eventos:")
    for event_type, count in event_types.most_common():
        print(f"   {event_type}: {count} ({count/total_events*100:.1f}%)")
    print()

    # Analizar sesiones
    sessions_started = len([e for e in events if e['eventType'] == 'session_start'])
    missions_started = len([e for e in events if e['eventType'] == 'mission_start'])
    endings_reached = len(set(e['sessionId'] for e in events if e['eventType'] == 'ending_reached'))

    conversion_rate = (endings_reached / sessions_started * 100) if sessions_started > 0 else 0

    print(f"🎯 Conversión:")
    print(f"   Sesiones iniciadas: {sessions_started}")
    print(f"   Misiones iniciadas: {missions_started}")
    print(f"   Sesiones con final: {endings_reached}")
    print(f"   Tasa de completación: {conversion_rate:.1f}%")
    print()

    # Analizar agentes
    agent_events = [e for e in events if e['eventType'] == 'session_start']
    agents = Counter(e['data'].get('agent', 'unknown') for e in agent_events)

    if agents:
        print(f"👥 Agentes más elegidos:")
        for agent, count in agents.most_common(10):
            print(f"   {agent}: {count} ({count/len(agent_events)*100:.1f}%)")
        print()

    # Analizar escenas
    scene_events = [e for e in events if e['eventType'] == 'scene_view']
    scenes = Counter(e['data']['sceneId'] for e in scene_events)

    if scenes:
        print(f"🎬 Escenas más visitadas:")
        for scene, count in scenes.most_common(10):
            print(f"   {scene}: {count} visitas")
        print()

    # Analizar decisiones
    choice_events = [e for e in events if e['eventType'] == 'choice_made']
    choices = Counter(
        f"{e['data']['fromScene']} → {e['data']['toScene']}"
        for e in choice_events
    )

    if choices:
        print(f"🔀 Decisiones más tomadas:")
        for choice, count in choices.most_common(10):
            print(f"   {choice}: {count} veces")
        print()

    # Analizar finales
    ending_events = [e for e in events if e['eventType'] == 'ending_reached']
    endings = Counter(e['data']['sceneId'] for e in ending_events)

    if endings:
        print(f"🏁 Finales alcanzados:")
        for ending, count in endings.most_common():
            print(f"   {ending}: {count} veces ({count/len(ending_events)*100:.1f}%)")
        print()

    # Analizar tiempos
    if ending_events:
        times = [e['data']['totalSessionTime'] / 1000 / 60 for e in ending_events]  # minutos
        avg_time = sum(times) / len(times)
        min_time = min(times)
        max_time = max(times)

        print(f"⏱️  Tiempos de juego (sesiones completadas):")
        print(f"   Tiempo promedio: {avg_time:.1f} minutos")
        print(f"   Tiempo mínimo: {min_time:.1f} minutos")
        print(f"   Tiempo máximo: {max_time:.1f} minutos")
        print()

    # Analizar tiempo por escena
    scene_times = defaultdict(list)
    for event in [e for e in events if e['eventType'] == 'scene_time']:
        scene_id = event['data']['sceneId']
        duration = event['data']['duration'] / 1000  # segundos
        scene_times[scene_id].append(duration)

    if scene_times:
        print(f"📍 Tiempo promedio por escena (top 10):")
        avg_scene_times = {
            scene: sum(times) / len(times)
            for scene, times in scene_times.items()
        }
        for scene, avg_time in sorted(avg_scene_times.items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"   {scene}: {avg_time:.1f}s")
        print()

    # Analizar puzzles
    puzzle_events = [e for e in events if e['eventType'] == 'puzzle_complete']
    if puzzle_events:
        puzzles_success = len([e for e in puzzle_events if e['data'].get('success')])
        puzzles_fail = len(puzzle_events) - puzzles_success
        success_rate = (puzzles_success / len(puzzle_events) * 100) if puzzle_events else 0

        print(f"🧩 Puzzles:")
        print(f"   Total de intentos: {len(puzzle_events)}")
        print(f"   Completados: {puzzles_success}")
        print(f"   Fallados: {puzzles_fail}")
        print(f"   Tasa de éxito: {success_rate:.1f}%")
        print()

    # Analizar uso de funciones
    back_button_uses = len([e for e in events if e['eventType'] == 'back_button'])
    resets = len([e for e in events if e['eventType'] == 'mission_reset'])
    agent_switches = len([e for e in events if e['eventType'] == 'agent_switch'])

    print(f"🎮 Uso de funcionalidades:")
    print(f"   Botón 'Atrás': {back_button_uses} veces")
    print(f"   Reinicio de misión: {resets} veces")
    print(f"   Cambio de agente: {agent_switches} veces")
    print()

    # Analizar abandono
    sessions_by_id = defaultdict(list)
    for event in events:
        sessions_by_id[event['sessionId']].append(event)

    incomplete_sessions = [
        session_events for session_id, session_events in sessions_by_id.items()
        if not any(e['eventType'] == 'ending_reached' for e in session_events)
    ]

    if incomplete_sessions:
        last_scenes = []
        for session_events in incomplete_sessions:
            scene_views = [e for e in session_events if e['eventType'] == 'scene_view']
            if scene_views:
                # Ordenar por timestamp y tomar la última
                last_scene = max(scene_views, key=lambda x: x['timestamp'])
                last_scenes.append(last_scene['data']['sceneId'])

        abandonment_points = Counter(last_scenes)

        print(f"🚪 Puntos de abandono (escenas donde más usuarios dejan el juego):")
        for scene, count in abandonment_points.most_common(10):
            print(f"   {scene}: {count} abandonos")
        print()

    # Análisis de caminos completos
    print(f"🗺️  Análisis de caminos:")
    paths = []
    for session_events in sessions_by_id.values():
        scene_views = sorted(
            [e for e in session_events if e['eventType'] == 'scene_view'],
            key=lambda x: x['timestamp']
        )
        if scene_views:
            path = ' → '.join(e['data']['sceneId'] for e in scene_views)
            paths.append(path)

    path_counts = Counter(paths)
    if path_counts:
        print(f"   Caminos únicos: {len(path_counts)}")
        print(f"   Top 5 caminos más comunes:")
        for i, (path, count) in enumerate(path_counts.most_common(5), 1):
            print(f"   {i}. ({count} veces)")
            print(f"      {path[:100]}...")  # Truncar si es muy largo
        print()

    print("=" * 60)
    print(f"✅ Análisis completado")
    print("=" * 60)


def main():
    if len(sys.argv) < 2:
        print("Uso: python scripts/analyze_analytics.py <archivo.json>")
        print("Ejemplo: python scripts/analyze_analytics.py portal27_analytics_1234567890.json")
        sys.exit(1)

    filepath = Path(sys.argv[1])

    if not filepath.exists():
        print(f"❌ Error: El archivo {filepath} no existe")
        sys.exit(1)

    try:
        events = load_events(filepath)

        if not events:
            print("⚠️  El archivo no contiene eventos")
            sys.exit(1)

        analyze_events(events)

    except json.JSONDecodeError:
        print(f"❌ Error: El archivo {filepath} no es un JSON válido")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
