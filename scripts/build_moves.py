"""Builds data/moves.json, the list behind moves.html.

Every move that at least one Pokemon learns is taken from data/pokemon.json,
then TM numbers and TM / Move Tutor locations are merged in from
data/tm-and-move-tutors.json. Rerun after changing either file:

    python scripts/build_moves.py
"""

import json
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
POKEMON_PATH = DATA_DIR / "pokemon.json"
TM_TUTOR_PATH = DATA_DIR / "tm-and-move-tutors.json"
OUTPUT_PATH = DATA_DIR / "moves.json"


def load_json(path):
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def collect_moves(pokemon_list):
    moves = {}
    for pokemon in pokemon_list:
        for learnset in (pokemon.get("moves") or {}).values():
            for move in learnset:
                move_id = str(move.get("id") or "").upper()
                if not move_id or move_id in moves:
                    continue
                moves[move_id] = {
                    "name": move.get("name") or move_id,
                    "internalName": move_id,
                    "type": move.get("type"),
                    "category": move.get("category"),
                    "power": move.get("power"),
                    # pokemon.json stores "never misses" as 0.
                    "accuracy": move.get("accuracy") or None,
                    "pp": move.get("pp"),
                    "description": move.get("description"),
                    "tmNumber": None,
                    "tmLocation": None,
                    "tutorLocation": None,
                }
    return moves


def merge_tm_tutor(moves, tm_tutor_moves):
    missing = []
    for entry in tm_tutor_moves:
        move_id = str(entry.get("internalName") or "").upper()
        move = moves.get(move_id)
        if move is None:
            missing.append(move_id or entry.get("name"))
            continue
        if entry.get("sourceType") == "TM":
            move["tmNumber"] = entry.get("tmNumber")
            move["tmLocation"] = entry.get("location")
        else:
            move["tutorLocation"] = entry.get("location")
    return missing


def main():
    moves = collect_moves(load_json(POKEMON_PATH))
    tm_tutor = load_json(TM_TUTOR_PATH)
    missing = merge_tm_tutor(moves, tm_tutor.get("moves", []))

    ordered = sorted(moves.values(), key=lambda move: move["name"].lower())
    with open(OUTPUT_PATH, "w", encoding="utf-8", newline="\n") as handle:
        json.dump({"count": len(ordered), "moves": ordered}, handle, indent=2, ensure_ascii=False)
        handle.write("\n")

    tms = sum(1 for move in ordered if move["tmNumber"] is not None)
    tutors = sum(1 for move in ordered if move["tutorLocation"])
    print(f"Wrote {len(ordered)} moves ({tms} TMs, {tutors} tutor moves) to {OUTPUT_PATH}")
    if missing:
        print("No Pokemon learns these TM/tutor moves, so they were skipped:", ", ".join(missing))


if __name__ == "__main__":
    main()
