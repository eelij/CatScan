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
    "1. The provided project data is the source of truth. Before creating or changing a block, find the closest equivalent block in it and copy its exact structure (opcode, inputs, fields, shadow, topLevel, parent, x/y), changing only what the request needs.\n"
    "2. Never invent opcodes, input shapes, or block structures that the project or real Scratch 3.0 does not use.\n"
    "3. Every new block ID must be unique within its target and must not collide with any block, variable, list, or broadcast ID.\n"
    "4. add_blocks never overwrites; update_blocks and remove_blocks reference only existing blocks.\n"
    "5. Every next, parent, SUBSTACK, SUBSTACK2, and input block reference must be an exact ID copied from the project or created in this response. Never use placeholders, shortened, or altered IDs.\n"
    "6. Do not modify unrelated data. Do not rewrite valid structures to match a generic reference.\n"
    "7. Leave no temporary construction blocks behind.\n\n"
)

RESPONSE_CONTRACT_RULES = (
    "MODIFICATION RESPONSE CONTRACT:\n"
    "1. Return the complete JSON object. Never truncate, and close every string, array, and object.\n"
    "2. If the request cannot be represented by the schema, return mode 'modify' with empty arrays and explain the limitation in explanation.\n"
    "3. Never return a malformed or speculative modification just because a change was requested.\n\n"
)

REFERENCE_INTEGRITY_RULES = (
    "REFERENCE INTEGRITY RULES:\n"
    "1. Treat the project as a graph: before changing a block, check what references it and what it references, upstream and downstream.\n"
    "2. Fix every reference to a changed object consistently; do not leave one stale.\n"
    "3. Verify each referenced ID character-for-character before returning.\n\n"
)

TOP_LEVEL_SCRIPT_RULES = (
    "TOP-LEVEL AND WORKSPACE RULES:\n"
    "1. Script entry blocks such as event_whenflagclicked use topLevel=true, parent=null, and sensible x/y when the project uses them. Other blocks in a chain are not independent scripts.\n"
    "2. Reporters, booleans, operators, variable reporters, menus, and shadows used as inputs are part of the input structure. Copy topLevel, parent, shadow, and coordinates from the closest equivalent project structure rather than assuming a fixed value.\n"
    "3. Build an expression such as (Score / 2 + 3) as one complete input tree. Never leave its variable, divide, or add blocks as separate visible scripts.\n"
    "4. Every new block must be reachable from a real script, a procedure, or an input of a reachable block.\n"
    "5. Use an event block for discrete events (green flag, broadcast, one-shot sprite click). For continuously held state (keys, mouse, touching), prefer forever -> if <boolean sensing> over a one-time event, unless the project already handles similar input another way; then stay consistent with it.\n"
    "6. Never invent boolean blocks that do not exist, such as a 'this sprite is clicked' reporter.\n\n"
)

VARIABLE_SCOPE_RULES = (
    "VARIABLE SCOPE AND OWNERSHIP RULES:\n"
    "1. A variable defined in the Stage is global; one defined in a sprite is local to that sprite. Determine scope by which target's variables object contains it.\n"
    "2. Variables with the same name are not the same variable. Identity is exact name + exact ID + owning target.\n"
    "3. Never let one sprite directly reference another sprite's local variable. For cross-sprite communication use a Stage variable or a broadcast.\n"
    "4. Do not change a local variable to global unless the request requires it, and then say so in explanation.\n"
    "5. Never fix a scope problem by changing only the name string.\n\n"
)

SHADOW_AND_MENU_BLOCK_RULES = (
    "SHADOW AND MENU BLOCK RULES:\n"
    "1. Menu and shadow blocks (motion_goto_menu, motion_pointtowards_menu, sensing_touchingobjectmenu, sensing_keyoptions, sound_sounds_menu, control_create_clone_of_menu) have no universal parent, topLevel, or coordinate pattern.\n"
    "2. Copy the shadow value, field arrays, and input-array form exactly from an equivalent block in the project.\n"
    "3. Never turn a valid menu/shadow block into an independent script, and never force its topLevel without comparing an equivalent structure.\n\n"
)

KNOWN_STRUCTURE_EXAMPLES = (
    "KNOWN SCRATCH STRUCTURE EXAMPLES:\n"
    "Before generating these, copy the exact structure from an equivalent existing block:\n"
    "- motion_goto TO / motion_pointtowards TOWARDS / sensing_touchingobject TOUCHINGOBJECTMENU: their menu block.\n"
    "- sound_play / sound_playuntildone: the SOUND_MENU input.\n"
    "- control_if, control_if_else, control_repeat, control_forever: CONDITION, SUBSTACK, SUBSTACK2.\n"
    "- Custom procedures: procedures_definition, procedures_prototype, procedures_call, mutation, and argument structures.\n"
    "- Reporter/operator trees: nesting and input references.\n\n"
)

OPCODE_SAFETY = (
    "OPCODE SAFETY:\n"
    "1. Never invent opcode names or use variants from other Scratch implementations (e.g. sound_startsound when the project uses sound_play).\n"
    "2. Prefer opcodes already present in the project. If none exists for the request, use a real Scratch 3.0 opcode and its standard structure.\n"
    "3. Do not change a valid existing opcode just to resemble a generic reference.\n\n"
)

INPUT_SAFETY = (
    "INPUT SAFETY:\n"
    "1. Never infer an input-array shape from the input name alone; copy the closest equivalent input from the project.\n"
    "2. Preserve the difference between [1, block_id], [2, block_id], [3, block_id, shadow], and literal/shadow primitive forms exactly as the project uses them.\n"
    "3. Never replace a block reference with a literal, or a literal with a block reference, unless the equivalent project structure does.\n"
    "4. If this prompt's reference conflicts with project.json, project.json wins.\n"
    "5. Check every generated input recursively down to nested blocks and primitives.\n\n"
)

VARIABLE_RULES = (
    "VARIABLE RULES:\n"
    "1. Use the exact variable name and ID found in project.json, taken from the owning target's variables object. Never infer a name from an ID, an ID from a name, or ownership from a name.\n"
    "2. Reuse an existing variable instead of creating a duplicate. For a genuinely new variable use add_variables; CatScan generates its final ID.\n"
    "3. When using data_setvariableto, data_changevariableby, or data_variable, check name, ID, owner, and global/local scope.\n\n"
)

MODIFICATION_SCOPE_RULES = (
    "MODIFICATION SCHEMA LIMITS:\n"
    "1. The schema can only add variables, remove blocks, add blocks, and update blocks. It cannot delete targets or change costumes, sounds, monitors, or metadata.\n"
    "2. If the request depends on unsupported operations, return empty arrays and explain; do not substitute an unrelated implementation.\n\n"
)

REMOVAL_RULES = (
    "SAFE BLOCK REMOVAL RULES:\n"
    "1. Never remove a block if that leaves a dangling next, parent, SUBSTACK, SUBSTACK2, or input reference.\n"
    "2. Removing from a linear chain: reconnect the previous block to the removed block's next, and fix the surviving block's parent. If it was the first block of a SUBSTACK, update the owner's input to the next surviving block or the project's empty-substack form.\n"
    "3. A block that looks visually separate may still be referenced through inputs, procedures, or mutations. Analyze all references before removing.\n\n"
)

ORPHAN_RULES = (
    "ORPHAN AND REACHABILITY RULES:\n"
    "1. A block is not an orphan just because it is outside a next chain: reporter/boolean/operator trees, menus, and shadows are valid when reachable through inputs.\n"
    "2. Procedure blocks (definition, prototype, call, argument reporters, mutations) are never orphans just because they are not in a normal next chain.\n"
    "3. Remove only blocks that are provably unreachable and unused; when unsure, leave them. Do not read 'remove orphan blocks' as 'remove everything not under an event'.\n"
    "4. Never create duplicate helper blocks when an existing block can be reused.\n"
    "5. Verify each proposed removal individually so no surviving block references it.\n\n"
)

PROJECT_CONSISTENCY_RULES = (
    "PROJECT CONSISTENCY RULES:\n"
    "1. When changing variable ownership or IDs, update every affected block.\n"
    "2. Preserve working behavior unless the user asks to change it. Make no speculative cleanup unrelated to the request.\n\n"
)

MODIFICATION_REASONING_RULES = (
    "MODIFICATION PLANNING RULES:\n"
    "1. Understand the requested behavior, then inspect the relevant targets, variables, scripts, and structures.\n"
    "2. Prefer modifying an existing working script over creating a duplicate; reuse existing blocks; keep changes as small as possible while fully implementing the request.\n"
    "3. Do not rewrite unrelated logic or invent a new architecture when the project has a simpler compatible pattern.\n"
    "4. Put all needed changes in one complete modification. If part of the request cannot be done safely, implement the safe parts only if the project stays consistent, and explain the rest.\n\n"
)

OPCODE_REFERENCE = (
    "SCRATCH OPCODE REFERENCE (structural hints only; project.json and equivalent project blocks always override it):\n"
    "Input forms: [1,[TYPE,\"v\"]] literal/shadow; [1,\"id\"] reporter/menu block; [2,\"id\"] stack input such as SUBSTACK; [2,[TYPE,\"v\"]] may appear for boolean-compatible or empty inputs.\n"
    "TYPE codes: math_number=4, positive_number=5, whole_number=6, integer=7, angle=8, color=9, text=10, broadcast=11, variable=12, list=13. Never infer a full structure from the code alone.\n"
    "EVENTS/CONTROL: event_whenflagclicked (top-level entry); control_forever SUBSTACK; control_if CONDITION,SUBSTACK; control_if_else CONDITION,SUBSTACK,SUBSTACK2; control_repeat TIMES,SUBSTACK; control_wait DURATION.\n"
    "MOTION: motion_movesteps STEPS; motion_pointtowards TOWARDS (+motion_pointtowards_menu); motion_goto TO (+motion_goto_menu).\n"
    "SENSING: sensing_touchingobject TOUCHINGOBJECTMENU (+sensing_touchingobjectmenu); sensing_keypressed KEY_OPTION (+sensing_keyoptions, depending on serialization).\n"
    "LOOKS: looks_nextcostume (no inputs/fields); looks_switchcostumeto, looks_changeeffectby, looks_seteffectto: copy the costume/effect selection and amount from equivalent project blocks.\n"
    "SOUND: sound_play, sound_playuntildone: copy the SOUND_MENU structure (+sound_sounds_menu). Never invent sound opcodes.\n"
    "DATA: data_setvariableto and data_changevariableby take an exact variable name+ID plus a VALUE input; data_variable references a variable in the project's exact serialization.\n"
    "OPERATORS: operator_add/subtract/multiply/divide/mod NUM1,NUM2; operator_gt/lt/equals/and/or OPERAND1,OPERAND2; operator_not OPERAND; operator_join/contains STRING1,STRING2; operator_length STRING; operator_letter_of LETTER,STRING; operator_round NUM; operator_mathop NUM plus an operation field. Copy exact serialization from equivalent blocks when available.\n"
    "PROCEDURES: procedures_definition references a procedures_prototype and the body; procedures_prototype holds mutation data (proccode, argument names/IDs, warp); procedures_call holds mutation data and argument inputs. Copy mutation and argument structures from equivalent project procedures.\n"
    "MENU BLOCKS (follow exact project serialization): motion_goto_menu, motion_pointtowards_menu, sensing_touchingobjectmenu, sensing_keyoptions, sound_sounds_menu, control_create_clone_of_menu.\n\n"
)


_KNOWLEDGE_SECTIONS = (
    GENERAL_JSON_RULES,
    RESPONSE_CONTRACT_RULES,
    REFERENCE_INTEGRITY_RULES,
    TOP_LEVEL_SCRIPT_RULES,
    VARIABLE_SCOPE_RULES,
    SHADOW_AND_MENU_BLOCK_RULES,
    KNOWN_STRUCTURE_EXAMPLES,
    OPCODE_SAFETY,
    INPUT_SAFETY,
    VARIABLE_RULES,
    MODIFICATION_SCOPE_RULES,
    REMOVAL_RULES,
    ORPHAN_RULES,
    PROJECT_CONSISTENCY_RULES,
    MODIFICATION_REASONING_RULES,
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


def get_variable_scope_rules() -> str:
    return VARIABLE_SCOPE_RULES


def get_modification_scope_rules() -> str:
    return MODIFICATION_SCOPE_RULES


def get_removal_rules() -> str:
    return REMOVAL_RULES


def get_orphan_rules() -> str:
    return ORPHAN_RULES


def get_project_consistency_rules() -> str:
    return PROJECT_CONSISTENCY_RULES


def get_modification_reasoning_rules() -> str:
    return MODIFICATION_REASONING_RULES


def get_response_contract_rules() -> str:
    return RESPONSE_CONTRACT_RULES


def get_reference_integrity_rules() -> str:
    return REFERENCE_INTEGRITY_RULES


def get_menu_block_opcodes() -> tuple[str, ...]:
    return MENU_BLOCK_OPCODES


def get_input_type_codes() -> dict[int, str]:
    return dict(INPUT_TYPE_CODES)


def build_scratch_knowledge_prompt() -> str:
    return "".join(_KNOWLEDGE_SECTIONS)