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
    "For a block such as motion_goto with a menu input, the menu should be represented using the same structure as an existing motion_goto_menu block in the provided project.\n"
    "For a block such as motion_pointtowards with a menu input, use the exact structure of an existing motion_pointtowards_menu block if available.\n"
    "For sensing_touchingobject, use the exact structure of an existing sensing_touchingobjectmenu block if available.\n"
    "For sound playback blocks, use the exact opcode and input structure found in the project instead of inventing variants.\n"
    "For control_if and other control blocks, copy the exact CONDITION and SUBSTACK structure from an existing equivalent block.\n\n"
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
    "The input name alone does not determine the correct JSON representation.\n\n"
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
    "They are structural hints only. Always prefer the exact serialization of the closest matching block in the provided project over these summaries.\n"
    "Scratch 3.0 input arrays use these container forms:\n"
    "- [1, [TYPE_CODE, \"value\"]] for a literal or shadow value; TYPE_CODE values include math_number=4, positive_number=5, whole_number=6, integer=7, angle=8, color=9, text=10, broadcast=11, variable=12, list=13.\n"
    "- [1, \"block_id\"] when an existing reporter or boolean block obscures the shadow slot.\n"
    "- [2, \"block_id\"] for stack inputs such as SUBSTACK.\n"
    "- [2, [TYPE_CODE, \"value\"]] for an empty boolean slot.\n\n"

    "EVENTS AND CONTROL:\n"
    "- event_whenflagclicked: no inputs, no fields; used as a top-level script entry block with topLevel=true and sensible x/y coordinates.\n"
    "- control_forever: inputs SUBSTACK=[2, \"block_id\"]; normally next=null because the loop repeats indefinitely.\n"
    "- control_if: inputs CONDITION holding either a boolean/reporter block reference or an empty boolean slot, and SUBSTACK=[2, \"block_id\"]; control_if_else additionally uses SUBSTACK2 for the else branch.\n"
    "- control_repeat: inputs TIMES=[1, [6, \"10\"]] and SUBSTACK=[2, \"block_id\"].\n\n"

    "MOTION:\n"
    "- motion_movesteps: inputs STEPS=[1, [4, \"50\"]].\n"
    "- motion_pointtowards: inputs TOWARDS=[1, \"<motion_pointtowards_menu_id>\"]; companion shadow/menu block motion_pointtowards_menu with fields TO holding \"_mouse_\" or a sprite name.\n"
    "- motion_goto: inputs TO=[1, \"<motion_goto_menu_id>\"]; companion shadow/menu block motion_goto_menu with fields TO holding \"_mouse_\" or \"_random_position_\".\n\n"

    "SENSING:\n"
    "- sensing_touchingobject: inputs TOUCHINGOBJECTMENU=[1, \"<sensing_touchingobjectmenu_id>\"]; companion sensing_touchingobjectmenu with fields TOUCHINGOBJECTMENU holding a sprite name, \"_mouse_\", or \"_edge_\".\n"
    "- sensing_keypressed: inputs KEY_OPTIONS=[1, \"<sensing_keyoptions_id>\"]; companion sensing_keyoptions with fields KEY_OPTION holding \"space\", letter or digit characters, or the arrow key names exactly as serialized in the provided project.\n\n"

    "LOOKS:\n"
    "- looks_nextcostume: no inputs, no fields.\n"
    "- looks_switchcostumeto: inputs COSTUME=[1, \"<looks_costume_id>\"]; companion looks_costume with fields COSTUME holding the costume name and costume id.\n"
    "- looks_changeeffectby: inputs EFFECT=[1, \"<looks_effectsmenu_id>\"] and CHANGE=[1, [4, \"25\"]]; companion looks_effectsmenu with fields EFFECT holding values such as \"COLOR\", \"FISHEYE\", \"WHIRL\", \"PIXELATE\", \"MOSAIC\", \"BRIGHTNESS\", \"GHOST\".\n"
    "- looks_seteffectto: inputs EFFECT=[1, \"<looks_effectsmenu_id>\"] and VALUE=[1, [4, \"0\"]]; uses the same looks_effectsmenu companion block.\n\n"

    "SOUND:\n"
    "- sound_play: inputs SOUND_MENU=[1, \"<sound_sounds_menu_id>\"]; companion sound_sounds_menu with fields SOUND_MENU holding the sound name together with the sound id.\n"
    "- sound_playuntildone shares the identical input shape with sound_play; never invent unofficial variants such as sound_startsound.\n\n"

    "DATA:\n"
    "- data_setvariableto: carries the target variable using the project's existing variable-reference input format (exact name and id pair) and inputs VALUE=[1, [10, \"0\"]].\n"
    "- data_changevariableby: same variable-reference format with inputs VALUE=[1, [4, \"1\"]].\n\n"

    "OPERATORS:\n"
    "- operator_add, operator_subtract, operator_multiply, operator_divide: inputs NUM1 and NUM2 holding numeric literals or reporter references.\n"
    "- operator_gt, operator_lt, operator_equals: inputs OPERAND1 and OPERAND2.\n"
    "- operator_and, operator_or: boolean inputs OPERAND1 and OPERAND2; operator_not takes a single OPERAND boolean input.\n"
    "- operator_join, operator_contains: text inputs STRING1 and STRING2; operator_length takes STRING; operator_letter_of takes LETTER and STRING.\n"
    "- operator_mod: inputs NUM1 and NUM2; operator_round: input NUM; operator_mathop: fields OPERATOR plus input NUM.\n\n"

    "PROCEDURES:\n"
    "- procedures_definition: inputs custom_block=[1, \"<procedures_prototype_id>\"]; next points at the first block of the definition body.\n"
    "- procedures_prototype: carries a mutation object with proccode, argumentnames, argumentids, and warp; it is owned by its procedures_definition rather than being an independent script. Copy the exact mutation shape and flags from the project.\n"
    "- procedures_call: carries a mutation object with proccode and argumentids; its inputs are keyed by those argument ids and each input copies the corresponding prototype argument structure from the project.\n\n"
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
