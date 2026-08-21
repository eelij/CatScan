from __future__ import annotations

INPUT_TYPE_CODES = {
    4: "math_number",
    5: "positive_number",
    6: "whole_number",
    7: "integer",
    8: "angle",
    9: "color",
    10: "text",
    11: "broadcast",
    12: "variable",
    13: "list",
}

MENU_BLOCK_OPCODES = (
    "motion_goto_menu",
    "motion_pointtowards_menu",
    "sensing_touchingobjectmenu",
    "sensing_keyoptions",
    "sound_sounds_menu",
    "control_create_clone_of_menu",
)

GENERAL_JSON_RULES = (
    "GENERAL SCRATCH JSON RULES:\n"
    "1. Preserve the exact Scratch 3.0 project.json serialization style used by the provided project.\n"
    "2. Never invent Scratch block structures from memory when an equivalent block exists in the provided project.\n"
    "3. Before creating any block, search the provided project JSON for an existing block with the same opcode or the closest equivalent opcode.\n"
    "4. Copy the existing block's structural format exactly, then change only the values that actually need to change.\n"
    "5. Never invent an opcode. Only use valid Scratch 3.0 opcodes and prefer opcodes already present in the project.\n"
    "6. Never invent input array formats. Copy the exact structure of equivalent existing inputs.\n"
    "7. Never simplify Scratch input arrays into pseudo-code.\n"
    "8. Preserve all required block properties: opcode, next, parent, inputs, fields, shadow, topLevel, and x/y where applicable.\n"
    "9. Every new block ID must be unique inside its target.\n"
    "10. add_blocks must never overwrite an existing block.\n"
    "11. update_blocks may only reference an existing block.\n"
    "12. remove_blocks may only reference an existing block.\n"
    "13. All next references must point to an existing block, a newly created block, or null.\n"
    "14. All parent references must point to the correct containing block, an existing block, a newly created block, or null when Scratch normally uses null.\n"
    "15. All block references inside inputs must point to valid blocks.\n"
    "16. Preserve correct SUBSTACK structures.\n"
    "17. Preserve correct boolean/reporter input structures.\n"
    "18. Preserve correct shadow/menu input structures.\n"
    "19. Preserve correct variable references and variable IDs.\n"
    "20. Do not modify unrelated project data.\n\n"
)

TOP_LEVEL_SCRIPT_RULES = (
    "TOP-LEVEL SCRIPT RULES:\n"
    "1. Actual top-level scripts and event blocks should use topLevel=true.\n"
    "2. Actual top-level scripts must have sensible visible x/y coordinates.\n"
    "3. Blocks belonging to a script but not serving as the script's top-level entry block must use topLevel=false.\n"
    "4. Shadow/menu blocks used as inputs are NOT independent top-level scripts.\n"
    "5. Shadow/menu blocks used as inputs should normally use topLevel=false and must have the correct parent reference to the block that contains them.\n"
    "6. Never create unrelated shadow/menu blocks with topLevel=true and parent=null when they are being used as inputs.\n"
    "7. Use an existing equivalent shadow/menu block from the project as the exact template whenever possible.\n\n"
)

SHADOW_AND_MENU_BLOCK_RULES = (
    "SHADOW AND MENU BLOCK RULES:\n"
    "Scratch uses special shadow/menu blocks for dropdowns and special inputs.\n"
    "Examples include:\n"
    "- motion_goto_menu\n"
    "- motion_pointtowards_menu\n"
    "- sensing_touchingobjectmenu\n"
    "- sensing_keyoptions\n"
    "- sound_sounds_menu\n"
    "- control_create_clone_of_menu\n"
    "Do NOT treat these blocks as ordinary independent scripts.\n"
    "When a shadow/menu block is connected to an input:\n"
    "- preserve shadow=true when appropriate\n"
    "- use topLevel=false unless the existing project explicitly demonstrates otherwise for the same structure\n"
    "- set parent to the block that directly owns the input when that is how the existing project serializes it\n"
    "- preserve its fields exactly\n"
    "- connect it through the correct input array\n"
    "Always copy the exact metadata pattern from the closest matching existing block in the project.\n\n"
)

KNOWN_STRUCTURE_EXAMPLES = (
    "KNOWN SCRATCH STRUCTURE EXAMPLES:\n"
    "For a block such as motion_goto with a menu input, use the exact structure of an existing motion_goto_menu block in the provided project.\n"
    "For a block such as motion_pointtowards with a menu input, use the exact structure of an existing motion_pointtowards_menu block in the provided project.\n"
    "For sensing_touchingobject, use the exact structure of an existing sensing_touchingobjectmenu block in the provided project.\n"
    "For sound playback blocks, use the exact opcode and input structure found in the project instead of inventing variants.\n"
    "For control_if and other control blocks, copy the exact CONDITION and SUBSTACK structure from an existing equivalent block.\n"
    "For custom procedures, copy the exact procedures_definition, procedures_prototype, mutation, and procedures_call structures already present in the project whenever possible.\n\n"
)

OPCODE_SAFETY = (
    "OPCODE SAFETY:\n"
    "Never invent opcode names such as 'sound_startsound' or other unofficial variants.\n"
    "If the project contains 'sound_play', use 'sound_play' when that is the correct block for the requested behavior.\n"
    "Do not assume that an opcode from another Scratch implementation or extension exists in this project.\n"
    "Prefer exact opcodes already present in the supplied project.\n\n"
)

INPUT_SAFETY = (
    "INPUT SAFETY:\n"
    "Scratch inputs can contain literals, variable references, block references, shadow blocks, reporters, booleans, and menu blocks.\n"
    "Do not assume all inputs use the same array format.\n"
    "For every generated input, find an equivalent input in an existing block and reproduce its exact representation.\n"
    "Examples include CONDITION, SUBSTACK, VALUE, VARIABLE, STEPS, TO, TOWARDS, SOUND_MENU, TOUCHINGOBJECTMENU and similar fields.\n"
    "The input name alone does not determine the correct JSON representation.\n"
    "When a reference structure and the provided project disagree, the provided project always wins.\n\n"
)

VARIABLE_RULES = (
    "VARIABLE RULES:\n"
    "When referencing an existing variable, use the exact variable name and ID found in the project JSON.\n"
    "Do not create a second variable with the same logical name when the requested variable already exists.\n"
    "When adding a new variable, use the modification format and let CatScan generate the final unique ID.\n\n"
)

OPCODE_REFERENCE = (
    "SCRATCH OPCODE REFERENCE:\n"
    "The following summaries describe commonly used opcodes and their typical inputs, fields, and companion menu blocks.\n"
    "They are structural hints only. Always prefer the exact serialization of the closest matching block in the provided project over these summaries.\n\n"

    "CRITICAL PRIORITY RULE:\n"
    "1. The provided project.json is the authoritative source of truth.\n"
    "2. Existing blocks in the provided project have priority over every rule in this reference.\n"
    "3. If this reference conflicts with the project.json structure, ignore the reference and copy the project structure exactly.\n"
    "4. Do not generalize a block structure from this reference when an equivalent block exists in the project.\n"
    "5. If no equivalent block exists, use this reference only as a hint and preserve known Scratch conventions.\n"
    "6. Never change an existing project's valid serialization merely to make it match this reference.\n\n"

    "COMMON INPUT CONTAINER FORMS:\n"
    "Scratch input arrays use several forms. These examples are hints and must not override an equivalent structure already present in the project.\n"
    "- [1, [TYPE_CODE, \"value\"]] for a literal or shadow value.\n"
    "- [1, \"block_id\"] for a reporter, boolean, or menu block reference when serialized that way by the project.\n"
    "- [2, \"block_id\"] for stack inputs such as SUBSTACK.\n"
    "- [2, [TYPE_CODE, \"value\"]] for some empty or literal stack/boolean-compatible slots when the project uses that structure.\n"
    "Known TYPE_CODE values include math_number=4, positive_number=5, whole_number=6, integer=7, angle=8, color=9, text=10, broadcast=11, variable=12, list=13.\n"
    "The numeric type code alone does not determine the correct structure. Copy an equivalent input from the project whenever possible.\n\n"

    "EVENTS AND CONTROL:\n"
    "- event_whenflagclicked: normally has no inputs and no fields; used as a top-level script entry block with topLevel=true and sensible x/y coordinates.\n"
    "- control_forever: normally contains SUBSTACK=[2, \"block_id\"] and repeats the nested stack indefinitely.\n"
    "- control_if: normally contains CONDITION plus SUBSTACK=[2, \"block_id\"].\n"
    "- control_if_else: normally contains CONDITION, SUBSTACK, and SUBSTACK2.\n"
    "- control_repeat: normally contains TIMES plus SUBSTACK.\n"
    "- control_wait: normally contains DURATION.\n"
    "Use the exact input arrays and parent relationships from equivalent blocks already present in the project.\n\n"

    "MOTION:\n"
    "- motion_movesteps: normally uses a STEPS input.\n"
    "- motion_pointtowards: normally uses TOWARDS and may reference a motion_pointtowards_menu companion block.\n"
    "- motion_goto: normally uses TO and may reference a motion_goto_menu companion block.\n"
    "Menu field values such as mouse, random position, edge, or sprite names must be copied from the project rather than guessed.\n\n"

    "SENSING:\n"
    "- sensing_touchingobject: normally uses TOUCHINGOBJECTMENU and a companion sensing_touchingobjectmenu block.\n"
    "- sensing_keypressed: normally uses KEY_OPTION or the exact input structure used by the project and may use sensing_keyoptions.\n"
    "Menu field values must use the exact strings and field-array shapes serialized in the project.\n\n"

    "LOOKS:\n"
    "- looks_nextcostume: no inputs and no fields.\n"
    "- looks_switchcostumeto: typically uses a costume selector input or companion costume menu block depending on project serialization.\n"
    "- looks_changeeffectby: uses an effect selector and a numeric change value; exact serialization must be copied from an existing equivalent block.\n"
    "- looks_seteffectto: uses an effect selector and a value; exact serialization must be copied from an existing equivalent block.\n"
    "Do not assume whether effect selection is stored as a field or a menu block. Inspect the project first.\n\n"

    "SOUND:\n"
    "- sound_play: plays a selected sound using the exact SOUND_MENU structure found in the project.\n"
    "- sound_playuntildone: follows the same principle; copy the exact existing structure rather than inventing one.\n"
    "Never invent unofficial opcodes such as sound_startsound.\n\n"

    "DATA:\n"
    "- data_setvariableto: references a variable using the exact name and ID pair from the project and includes a VALUE input.\n"
    "- data_changevariableby: references a variable using the exact name and ID pair from the project and includes a VALUE input.\n"
    "- data_variable: references an existing variable using the exact project serialization.\n"
    "Do not invent variable IDs or replace project variable references with names alone.\n\n"

    "OPERATORS:\n"
    "- operator_add, operator_subtract, operator_multiply, operator_divide: typically use NUM1 and NUM2.\n"
    "- operator_gt, operator_lt, operator_equals: typically use OPERAND1 and OPERAND2.\n"
    "- operator_and, operator_or: typically use OPERAND1 and OPERAND2.\n"
    "- operator_not: typically uses a single OPERAND.\n"
    "- operator_join: typically uses STRING1 and STRING2.\n"
    "- operator_contains: typically uses STRING1 and STRING2.\n"
    "- operator_length: typically uses STRING.\n"
    "- operator_letter_of: typically uses LETTER and STRING.\n"
    "- operator_mod: typically uses NUM1 and NUM2.\n"
    "- operator_round: typically uses NUM.\n"
    "- operator_mathop: typically uses a math operation selector and NUM.\n"
    "For all operator blocks, copy exact existing input serialization when an equivalent block exists.\n\n"

    "PROCEDURES:\n"
    "- procedures_definition: normally references a procedures_prototype and points with next to the first block in the definition body.\n"
    "- procedures_prototype: carries a mutation object containing procedure metadata such as proccode, argument names, argument IDs, and warp. Copy the exact mutation object from an existing project procedure whenever possible.\n"
    "- procedures_call: carries a mutation object and procedure argument inputs. Copy the exact mutation and argument-input structures from an existing procedure call whenever possible.\n"
    "Never invent procedures_prototype mutation fields from memory when the project contains an equivalent custom block.\n\n"

    "MENU BLOCKS:\n"
    "Known menu opcodes include:\n"
    "- motion_goto_menu\n"
    "- motion_pointtowards_menu\n"
    "- sensing_touchingobjectmenu\n"
    "- sensing_keyoptions\n"
    "- sound_sounds_menu\n"
    "- control_create_clone_of_menu\n"
    "Menu blocks must be treated according to the exact structure already used by the project. Do not assume their topLevel, parent, shadow, fields, or input-array representation without checking an equivalent block first.\n\n"
)

_KNOWLEDGE_SECTIONS = (
    GENERAL_JSON_RULES,
    TOP_LEVEL_SCRIPT_RULES,
    SHADOW_AND_MENU_BLOCK_RULES,
    KNOWN_STRUCTURE_EXAMPLES,
    OPCODE_SAFETY,
    INPUT_SAFETY,
    VARIABLE_RULES,
    OPCODE_REFERENCE,
)


def get_general_json_rules() -> str:
    return GENERAL_JSON_RULES


def get_top_level_script_rules() -> str:
    return TOP_LEVEL_SCRIPT_RULES


def get_shadow_block_rules() -> str:
    return SHADOW_AND_MENU_BLOCK_RULES


def get_scratch_opcode_rules() -> str:
    return OPCODE_SAFETY + OPCODE_REFERENCE


def get_input_rules() -> str:
    return INPUT_SAFETY


def get_variable_rules() -> str:
    return VARIABLE_RULES


def get_menu_block_opcodes() -> tuple[str, ...]:
    return MENU_BLOCK_OPCODES


def get_input_type_codes() -> dict[int, str]:
    return dict(INPUT_TYPE_CODES)


def build_scratch_knowledge_prompt() -> str:
    return "".join(_KNOWLEDGE_SECTIONS)