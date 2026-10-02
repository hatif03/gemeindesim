"""Tests for NPC movement collision deduplication in run_round."""

from __future__ import annotations

from graph.nodes.run_round import _deduplicate_moves


class TestMoveDeduplication:
    def test_no_conflict_both_move(self):
        npcs = [{"id": "npc_01", "x": 0, "y": 0}, {"id": "npc_02", "x": 5, "y": 5}]
        result = _deduplicate_moves(npcs, {"npc_01": (1, 0), "npc_02": (5, 6)})
        assert result == {"npc_01": (1, 0), "npc_02": (5, 6)}

    def test_two_npcs_target_same_tile(self):
        npcs = [{"id": "npc_01", "x": 0, "y": 0}, {"id": "npc_02", "x": 2, "y": 0}]
        result = _deduplicate_moves(npcs, {"npc_01": (1, 0), "npc_02": (1, 0)})
        assert len(result) == 1
        assert len([nid for nid, pos in result.items() if pos == (1, 0)]) == 1

    def test_moving_into_stationary_npc(self):
        npcs = [{"id": "npc_01", "x": 0, "y": 0}, {"id": "npc_02", "x": 1, "y": 0}]
        result = _deduplicate_moves(npcs, {"npc_01": (1, 0)})
        assert "npc_01" not in result

    def test_no_moves(self):
        npcs = [{"id": "npc_01", "x": 3, "y": 3}, {"id": "npc_02", "x": 7, "y": 7}]
        assert _deduplicate_moves(npcs, {}) == {}

    def test_single_npc_moves_freely(self):
        npcs = [{"id": "npc_01", "x": 5, "y": 5}, {"id": "npc_02", "x": 10, "y": 10}]
        assert _deduplicate_moves(npcs, {"npc_01": (5, 6)}) == {"npc_01": (5, 6)}

    def test_three_npcs_same_target(self):
        npcs = [
            {"id": "npc_01", "x": 0, "y": 0},
            {"id": "npc_02", "x": 2, "y": 0},
            {"id": "npc_03", "x": 0, "y": 2},
        ]
        result = _deduplicate_moves(npcs, {"npc_01": (1, 1), "npc_02": (1, 1), "npc_03": (1, 1)})
        assert len([nid for nid, pos in result.items() if pos == (1, 1)]) == 1

    def test_swap_positions_both_succeed(self):
        # Both vacate their tiles, so both moves are valid
        npcs = [{"id": "npc_01", "x": 0, "y": 0}, {"id": "npc_02", "x": 1, "y": 0}]
        result = _deduplicate_moves(npcs, {"npc_01": (1, 0), "npc_02": (0, 0)})
        assert result == {"npc_01": (1, 0), "npc_02": (0, 0)}

    def test_chain_collision_only_first_wins(self):
        npcs = [
            {"id": "npc_01", "x": 2, "y": 3},
            {"id": "npc_02", "x": 3, "y": 2},
            {"id": "npc_03", "x": 4, "y": 3},
        ]
        result = _deduplicate_moves(npcs, {"npc_01": (3, 3), "npc_02": (3, 3), "npc_03": (4, 4)})
        assert len([nid for nid, pos in result.items() if pos == (3, 3)]) == 1
        assert result.get("npc_03") == (4, 4)

    def test_all_positions_unique_after_dedup(self):
        npcs = [{"id": f"npc_{i:02d}", "x": i, "y": 0} for i in range(10)]
        moves = {
            "npc_00": (5, 5), "npc_01": (5, 5), "npc_02": (5, 5),
            "npc_03": (6, 6), "npc_04": (6, 6),
        }
        result = _deduplicate_moves(npcs, moves)
        final = [result[n["id"]] if n["id"] in result else (n["x"], n["y"]) for n in npcs]
        assert len(final) == len(set(final))
