from __future__ import annotations


PROCEDURE_OPCODES = frozenset((
    "procedures_definition",
    "procedures_prototype",
    "procedures_call",
))

PROCEDURE_RELATED_OPCODES = frozenset((
    "procedures_definition",
    "procedures_prototype",
    "procedures_call",
    "argument_reporter_string_number",
))


def _extract_reference_ids(value) -> set[str]:
    ids = set()

    if isinstance(value, str):
        ids.add(value)
        return ids

    if isinstance(value, list):
        for item in value:
            if isinstance(item, str):
                ids.add(item)
            elif isinstance(item, list):
                ids.update(_extract_reference_ids(item))

    return ids


def _extract_input_block_ids(block: dict) -> set[str]:
    ids = set()
    inputs = block.get("inputs")

    if not isinstance(inputs, dict):
        return ids

    for input_value in inputs.values():
        if not isinstance(input_value, list):
            continue

        if len(input_value) >= 2:
            first = input_value[0]
            second = input_value[1]

            if first in (1, 2, 3):
                if isinstance(second, str):
                    ids.add(second)
                elif isinstance(second, list):
                    ids.update(_extract_reference_ids(second))

        if len(input_value) >= 3:
            shadow = input_value[2]

            if isinstance(shadow, str):
                ids.add(shadow)
            elif isinstance(shadow, list):
                ids.update(_extract_reference_ids(shadow))

    return ids


def _extract_direct_block_references(block: dict) -> set[str]:
    refs = set()

    next_id = block.get("next")
    if isinstance(next_id, str):
        refs.add(next_id)

    refs.update(_extract_input_block_ids(block))

    return refs


def _find_procedure_related_blocks(blocks: dict) -> set[str]:
    related = set()

    procedure_blocks = {
        bid: block
        for bid, block in blocks.items()
        if isinstance(block, dict) and block.get("opcode") in PROCEDURE_OPCODES
    }

    for bid, block in procedure_blocks.items():
        related.add(bid)

        refs = _extract_direct_block_references(block)

        for ref_id in refs:
            if ref_id in blocks:
                related.add(ref_id)

    changed = True

    while changed:
        changed = False

        for bid in list(related):
            block = blocks.get(bid)

            if not isinstance(block, dict):
                continue

            for ref_id in _extract_direct_block_references(block):
                if ref_id in blocks and ref_id not in related:
                    related.add(ref_id)
                    changed = True

    for bid, block in blocks.items():
        if not isinstance(block, dict):
            continue

        opcode = block.get("opcode")

        if opcode == "argument_reporter_string_number":
            parent_id = block.get("parent")

            if isinstance(parent_id, str) and parent_id in related:
                related.add(bid)

    return related


def _find_reachable_blocks(blocks: dict) -> set[str]:
    reachable = set()

    for bid, block in blocks.items():
        if not isinstance(block, dict):
            continue

        if block.get("topLevel") is True:
            reachable.add(bid)

    procedure_related = _find_procedure_related_blocks(blocks)
    reachable.update(procedure_related)

    changed = True

    while changed:
        changed = False

        for bid in list(reachable):
            block = blocks.get(bid)

            if not isinstance(block, dict):
                continue

            for ref_id in _extract_direct_block_references(block):
                if ref_id in blocks and ref_id not in reachable:
                    reachable.add(ref_id)
                    changed = True

    return reachable


def cleanup_orphan_blocks(project_data: dict) -> dict:
    targets = project_data.get("targets", [])

    if not isinstance(targets, list):
        return {
            "blocks_removed": 0,
            "targets_affected": [],
        }

    total_removed = 0
    targets_affected = []

    for target in targets:
        if not isinstance(target, dict):
            continue

        blocks = target.get("blocks")

        if not isinstance(blocks, dict) or not blocks:
            continue

        reachable = _find_reachable_blocks(blocks)

        orphans = []

        for bid, block in list(blocks.items()):
            if not isinstance(block, dict):
                continue

            if bid in reachable:
                continue

            opcode = block.get("opcode", "")

            if opcode in PROCEDURE_RELATED_OPCODES:
                continue

            orphans.append(bid)

        for bid in orphans:
            blocks.pop(bid, None)

        if orphans:
            total_removed += len(orphans)

            target_name = target.get("name", "Unnamed")

            if target_name not in targets_affected:
                targets_affected.append(target_name)

    return {
        "blocks_removed": total_removed,
        "targets_affected": targets_affected,
    }