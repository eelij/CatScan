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
    "2. The provided project.json is the primary source of truth for every structural decision.\n"
    "3. Never invent a Scratch block structure when an equivalent block already exists in the provided project.\n"
    "4. Before creating or updating a block, inspect the project for the same opcode or the closest structurally equivalent block.\n"
    "5. Copy the exact structural pattern of the closest equivalent existing block and modify only the values required by the user's request.\n"
    "6. Never invent or rename opcodes.\n"
    "7. Never invent input array structures when an equivalent input exists in the project.\n"
    "8. Never simplify Scratch input arrays into pseudo-code.\n"
    "9. Preserve all relevant block properties: opcode, next, parent, inputs, fields, shadow, topLevel, and x/y where the project uses them.\n"
    "10. Every new block ID must be unique within its target.\n"
    "11. Never overwrite an existing block using add_blocks.\n"
    "12. update_blocks may reference only existing blocks.\n"
    "13. remove_blocks may reference only existing blocks.\n"
    "14. Every next reference must point to an existing block, a newly added block, or null.\n"
    "15. Every parent reference must point to the correct containing block, an existing block, a newly added block, or null when that exact structure is used by the project.\n"
    "16. Every block reference inside an input must point to a valid existing or newly added block.\n"
    "17. Preserve valid SUBSTACK and SUBSTACK2 structures.\n"
    "18. Preserve valid reporter, boolean, shadow, and menu input structures.\n"
    "19. Preserve exact variable names and variable IDs.\n"
    "20. Do not modify unrelated project data.\n"
    "21. Do not rewrite valid project structures merely to match a generic reference in this prompt.\n"
    "22. Never create temporary construction blocks that remain in the final project.\n\n"
)

RESPONSE_CONTRACT_RULES = (
    "MODIFICATION RESPONSE CONTRACT:\n"
    "1. If the request modifies the project, return exactly one valid JSON object and nothing else.\n"
    "2. Do not return Markdown.\n"
    "3. Do not return a code fence.\n"
    "4. Do not return analysis, reasoning, commentary, or a preamble before the JSON.\n"
    "5. Do not return commentary after the JSON.\n"
    "6. Do not output a partial JSON object.\n"
    "7. Do not stop in the middle of a string, array, object, or block definition.\n"
    "8. Every opening brace, bracket, quote, and JSON structure must be completely closed before the response ends.\n"
    "9. If the requested modification cannot be safely represented by the available modification schema, return a valid modify object with empty modification arrays and explain the limitation in explanation.\n"
    "10. Never output a malformed or speculative modification merely because the user requested a change.\n"
    "11. Before returning, verify that the complete response parses as JSON.\n"
    "12. The top-level keys must be exactly: mode, explanation, add_variables, remove_blocks, add_blocks, update_blocks.\n"
    "13. mode must be exactly 'modify'.\n\n"
)

REFERENCE_INTEGRITY_RULES = (
    "REFERENCE INTEGRITY RULES:\n"
    "1. Never invent, truncate, transform, partially copy, normalize, escape, or shorten a Scratch block ID.\n"
    "2. Every block ID used in next, parent, SUBSTACK, SUBSTACK2, or any input reference must be copied exactly from the provided project or created exactly in add_blocks in the same response.\n"
    "3. Never create placeholder IDs such as '<block_id>', 'block_id', 'speed_var_id', 'new_block', or shortened fragments of real IDs.\n"
    "4. Never use bracket fragments, semicolon fragments, escaped fragments, or malformed strings as block IDs.\n"
    "5. If a new block is referenced by another new block, use the exact new ID created in add_blocks.\n"
    "6. Every generated ID must be unique inside its target and must not collide with an existing block, variable, list, or broadcast ID.\n"
    "7. Before returning JSON, verify every referenced block ID character-for-character against the project or the new IDs created in the same response.\n\n"
)

TOP_LEVEL_SCRIPT_RULES = (
    "TOP-LEVEL AND WORKSPACE RULES:\n"
    "1. Actual script entry blocks such as event_whenflagclicked normally use topLevel=true, parent=null, and sensible x/y coordinates when the project uses those properties.\n"
    "2. Blocks that belong to a script chain should not be treated as independent scripts.\n"
    "3. A reporter, boolean, operator, variable reporter, menu, or shadow block used as an input must be treated as part of the connected input structure rather than as an unrelated script.\n"
    "4. Do not assume every input block must always use topLevel=false. Copy the exact topLevel, parent, shadow, and coordinate pattern from the closest equivalent structure already present in the project.\n"
    "5. Do not change valid topLevel, parent, or shadow values solely because a generic rule suggests a different value.\n"
    "6. Never leave a newly created intermediate reporter/operator/boolean/helper block as an unrelated visible top-level workspace block when it is meant to be part of another block's input.\n"
    "7. When building an expression such as (Pisteet / 2 + 3) for a movement input, create the complete reporter tree as the input tree and do not leave the variable reporter, divide block, or add block as separate helper scripts.\n"
    "8. Every newly created reporter/operator/boolean/input subtree must be reachable from a real script, procedure structure, or a valid input of a reachable block.\n"
    "9. Remove temporary construction blocks before returning the modification.\n"
    "10. Before returning a modification, perform an orphan analysis over every new block.\n"
    "11. A top-level block is not automatically an error merely because it is not an event block; determine its intended role from the project structure and equivalent examples.\n"
    "12. Prefer continuous boolean sensing inside a loop for behavior that should be checked continuously over time.\n"
    "13. For continuously changing input states such as held keyboard keys, mouse state, touching conditions, or similar conditions, prefer a forever loop with an if condition using an appropriate boolean sensing block when the project supports that structure.\n"
    "14. Prefer patterns such as forever -> if <key [right arrow] pressed?> then -> action for continuous keyboard control instead of relying on a one-time key event.\n"
    "15. Do not automatically replace every event block with a boolean polling loop. Use event blocks when the behavior is naturally event-driven, such as green-flag initialization, broadcasts, custom events, or actions that should trigger once per event.\n"
    "16. For sprite clicking, a when this sprite clicked event is valid for simple one-shot click actions. Use a boolean polling structure only when the project or requested behavior actually provides an appropriate boolean condition for continuous interaction.\n"
    "17. Never invent a boolean sensing block such as a nonexistent 'this sprite is clicked' reporter. Only use boolean blocks that are valid Scratch blocks and are supported by the project or authoritative Scratch structure.\n"
    "18. When choosing between an event block and a boolean polling pattern, choose the structure that matches the behavior: continuous state checks should prefer boolean polling, while discrete one-time events should prefer event blocks.\n"
    "19. When adding input handling to an existing project, inspect how similar input is already implemented and preserve a consistent pattern unless the user explicitly requests a different architecture.\n\n"
)

VARIABLE_SCOPE_RULES = (
    "VARIABLE SCOPE AND OWNERSHIP RULES:\n"
    "1. Scratch has global Stage variables and local sprite variables.\n"
    "2. A variable defined in the Stage target is global and can be directly referenced or modified by scripts in the Stage and sprites.\n"
    "3. A variable defined inside a sprite target is local to that sprite and must not be treated as directly accessible from other sprites.\n"
    "4. Determine a variable's scope by inspecting which target contains its variable definition in the project's variables object.\n"
    "5. Never assume that variables with the same name are the same variable.\n"
    "6. Variable identity depends on the exact variable name, exact variable ID, and owning target.\n"
    "7. When referencing an existing variable, copy its exact name and exact ID from the project.\n"
    "8. Never invent a variable ID.\n"
    "9. Never replace an existing variable ID with a guessed placeholder such as 'speed_var_id'.\n"
    "10. If one sprite needs to directly modify another sprite's local variable, do not create an invalid direct data_setvariableto or data_changevariableby reference to that local variable.\n"
    "11. When cross-sprite communication is required, use an approach supported by the project and modification schema, such as a global Stage variable or broadcast mechanism.\n"
    "12. Do not convert a local variable into a global variable unless the user's request explicitly requires it or it is necessary to implement the requested feature safely and the explanation states this clearly.\n"
    "13. Prefer preserving existing variable ownership whenever possible.\n"
    "14. Before modifying a variable block, verify owner target, scope, exact name, and exact variable ID.\n"
    "15. If a global Stage variable and a local sprite variable share the same name, keep their IDs and ownership separate.\n"
    "16. Never solve a variable-scope problem by changing only the name string. The exact variable ID and owning target must also be correct.\n\n"
)

SHADOW_AND_MENU_BLOCK_RULES = (
    "SHADOW AND MENU BLOCK RULES:\n"
    "1. Scratch uses special shadow and menu blocks for certain inputs.\n"
    "2. Examples include motion_goto_menu, motion_pointtowards_menu, sensing_touchingobjectmenu, sensing_keyoptions, sound_sounds_menu, and control_create_clone_of_menu.\n"
    "3. Do not assume that a menu or shadow block has a universal parent, topLevel, or coordinate pattern.\n"
    "4. Inspect an equivalent block in the provided project and copy its exact serialization pattern whenever possible.\n"
    "5. Preserve the exact shadow value used by an equivalent project block.\n"
    "6. Preserve the exact field arrays used by an equivalent project block.\n"
    "7. Preserve the exact input-array representation used by an equivalent project block.\n"
    "8. Never turn a valid menu/shadow block into an ordinary independent script merely because it appears at the top level in JSON.\n"
    "9. Never force a valid menu/shadow block to topLevel=false or true without first comparing an equivalent project structure.\n\n"
)

KNOWN_STRUCTURE_EXAMPLES = (
    "KNOWN SCRATCH STRUCTURE EXAMPLES:\n"
    "1. For motion_goto, inspect an existing motion_goto_menu structure before creating or changing the TO input.\n"
    "2. For motion_pointtowards, inspect an existing motion_pointtowards_menu structure before creating or changing the TOWARDS input.\n"
    "3. For sensing_touchingobject, inspect an existing sensing_touchingobjectmenu structure before creating or changing TOUCHINGOBJECTMENU.\n"
    "4. For sound playback, inspect an existing sound_play or sound_playuntildone structure before generating the sound input.\n"
    "5. For control_if, control_if_else, control_repeat, and control_forever, copy the exact CONDITION, SUBSTACK, and SUBSTACK2 structures from an equivalent existing block whenever possible.\n"
    "6. For custom procedures, copy the exact procedures_definition, procedures_prototype, procedures_call, mutation, and argument structures from equivalent procedures in the project whenever possible.\n"
    "7. For reporter/operator input trees, copy the exact nesting and input references from equivalent existing expressions whenever possible.\n\n"
)

OPCODE_SAFETY = (
    "OPCODE SAFETY:\n"
    "1. Never invent opcode names.\n"
    "2. Prefer exact opcodes already present in the provided project.\n"
    "3. Never use unofficial variants such as sound_startsound when the project uses sound_play.\n"
    "4. Never assume an opcode from another Scratch implementation exists in this project.\n"
    "5. If the requested behavior requires an opcode not present in the project, verify that it is a real Scratch 3.0 opcode and copy its structure from authoritative Scratch knowledge only when no equivalent project block exists.\n"
    "6. Do not change a valid existing opcode simply to make it resemble a generic reference.\n\n"
)

INPUT_SAFETY = (
    "INPUT SAFETY:\n"
    "1. Scratch inputs can contain literals, reporters, booleans, block references, menu blocks, shadow values, variables, broadcasts, lists, and nested expressions.\n"
    "2. Never infer the exact input-array representation from the input name alone.\n"
    "3. For every generated input, first find the closest equivalent input in the project and copy its exact structure.\n"
    "4. Preserve the difference between [1, block_id], [2, block_id], and literal/shadow primitive forms exactly as the project uses them.\n"
    "5. Never replace a block reference with a literal string merely because the visible value looks similar.\n"
    "6. Never replace a literal/shadow input with a block reference unless the equivalent project structure does so.\n"
    "7. Preserve CONDITION, SUBSTACK, SUBSTACK2, VALUE, STEPS, TO, TOWARDS, SOUND_MENU, TOUCHINGOBJECTMENU, and similar input structures exactly.\n"
    "8. When a generic Scratch reference conflicts with an equivalent structure in project.json, the project structure wins.\n"
    "9. Before returning a modification, verify every generated input recursively down to all nested block and primitive references.\n\n"
)

VARIABLE_RULES = (
    "VARIABLE RULES:\n"
    "1. Always use the exact variable name and exact variable ID found in project.json.\n"
    "2. Never create a second variable with the same logical name when the requested variable already exists and can be reused.\n"
    "3. When adding a genuinely new variable, use the modification format and allow CatScan to generate the final unique ID.\n"
    "4. Before using a variable in any block, verify its owner target and whether it is global or local.\n"
    "5. Stage variables are globally accessible; sprite variables are local to their owning sprite.\n"
    "6. Never infer variable ownership from the variable name.\n"
    "7. Never infer a variable ID from the variable name.\n"
    "8. When updating data_setvariableto, data_changevariableby, or data_variable, verify both name and ID against the owning target's variables object.\n\n"
)

MODIFICATION_SCOPE_RULES = (
    "MODIFICATION SCHEMA LIMITS:\n"
    "1. The available modification schema can add variables, remove blocks, add blocks, and update blocks.\n"
    "2. Do not pretend to support operations that the schema does not support.\n"
    "3. Do not delete targets/sprites unless the schema explicitly provides target deletion support.\n"
    "4. Do not add or replace costume assets unless the schema explicitly provides costume modification support.\n"
    "5. Do not add or replace sound assets unless the schema explicitly provides sound modification support.\n"
    "6. Do not modify arbitrary project metadata unless the schema explicitly supports it and the user requested it.\n"
    "7. If a requested change depends on unsupported project data, return an empty safe modification and explain the limitation.\n"
    "8. Do not silently substitute an unrelated implementation simply because the requested operation is unsupported.\n"
    "9. Preserve unrelated assets, costumes, sounds, variables, monitors, and metadata.\n\n"
)

REMOVAL_RULES = (
    "SAFE BLOCK REMOVAL RULES:\n"
    "1. Never remove a block if doing so leaves an unresolved next reference, parent reference, SUBSTACK reference, SUBSTACK2 reference, or input reference.\n"
    "2. If removing a block from a linear chain is structurally safe, preserve the chain by reconnecting the previous block to the removed block's next block.\n"
    "3. If the removed block has a surviving next block, update that surviving block's parent to the correct surviving parent when required by the project structure.\n"
    "4. If the removed block is the first block of a SUBSTACK or SUBSTACK2, update the owning block's corresponding input to the next surviving block or the exact empty structure used by the project.\n"
    "5. Never leave surviving blocks pointing to removed IDs.\n"
    "6. Do not delete a block merely because it appears visually separate until all references to it have been analyzed.\n"
    "7. Distinguish truly unreachable blocks from reporter/operator/input trees that are legitimately referenced through nested inputs.\n\n"
)

ORPHAN_RULES = (
    "ORPHAN AND REACHABILITY RULES:\n"
    "1. A block is not an orphan merely because it does not belong to a linear next chain.\n"
    "2. A reporter/operator/boolean/input tree can be valid when it is reachable through an input reference.\n"
    "3. A menu or shadow block can be valid when it participates in an input structure, even if its serialized placement looks unusual.\n"
    "4. A genuinely unreachable newly created block is invalid and must be removed before returning the modification.\n"
    "5. Never create duplicate helper blocks for the same expression if an equivalent existing block can be reused.\n"
    "6. Never leave temporary blocks used only during construction in the final modification.\n"
    "7. Before returning, trace every newly created block through next, parent, and inputs and determine whether it is reachable from a valid script, procedure, or input tree.\n"
    "8. A procedure argument reporter, custom block parameter reporter, procedures_prototype, procedures_definition, procedures_call, mutation-related structure, or other procedure-related block must not be classified as an orphan merely because it is not connected through a normal next chain.\n"
    "9. Before removing any block, inspect whether it is referenced by inputs, next, parent, SUBSTACK, SUBSTACK2, procedure structures, mutations, or other project structures.\n"
    "10. Only remove a block when it is provably unreachable and unused by the project.\n"
    "11. Be conservative when identifying orphan blocks. If it is uncertain whether a block is intentionally stored as part of Scratch's project structure, do not remove it.\n"
    "12. Never remove a block merely because it appears visually separate from a script in the Scratch workspace.\n"
    "13. Do not interpret 'remove orphan blocks' as 'remove every block that is not part of an event chain'.\n"
    "14. When a cleanup request identifies orphan blocks, remove only the blocks that are definitely unnecessary and leave uncertain or special Scratch structures untouched.\n"
    "15. Before returning a modification containing remove_blocks, verify every proposed removal individually and ensure that no surviving block will reference a removed block.\n"
    "16. Prefer removing a small number of definitely orphaned blocks over aggressively cleaning up uncertain structures.\n\n"
)

PROJECT_CONSISTENCY_RULES = (
    "PROJECT CONSISTENCY RULES:\n"
    "1. Treat the entire project as a graph, not as isolated block dictionaries.\n"
    "2. Before changing a block, inspect all blocks that reference it and all blocks it references.\n"
    "3. When changing variable ownership or variable IDs, update every affected block consistently.\n"
    "4. When changing a chain, inspect both upstream and downstream references.\n"
    "5. When changing an input subtree, inspect the complete subtree recursively.\n"
    "6. Do not fix one broken reference while leaving another reference to the same object inconsistent.\n"
    "7. Do not make speculative cleanup changes unrelated to the user's request.\n"
    "8. Preserve working project behavior unless the user explicitly requests that behavior to change.\n\n"
)

MODIFICATION_REASONING_RULES = (
    "MODIFICATION PLANNING RULES:\n"
    "1. First understand the user's requested behavior.\n"
    "2. Then inspect the relevant target variables, scripts, blocks, inputs, and existing structures.\n"
    "3. Determine whether the request can be implemented safely with the available schema.\n"
    "4. Prefer modifying an existing working script over creating duplicate scripts.\n"
    "5. Reuse existing blocks and structures whenever possible.\n"
    "6. Keep changes as small as possible while fully implementing the requested behavior.\n"
    "7. Do not rewrite unrelated logic.\n"
    "8. Do not invent a new architecture when the existing project already contains a simpler compatible pattern.\n"
    "9. If several independent modifications are required, include all of them in one complete modification JSON when they can be represented safely.\n"
    "10. If one requested part cannot be represented safely, implement the safe parts only when doing so will not leave the project semantically inconsistent, and explain the unsupported part.\n"
    "11. Never stop after only one obvious change when the user explicitly requested all necessary fixes.\n\n"
    "12. Cleanup requests must be conservative. Do not interpret 'remove orphan blocks' as 'remove every block that looks disconnected'. Only remove blocks that are provably unreachable and unused.\n"
)

FINAL_SELF_CHECK = (
    "FINAL SELF-CHECK BEFORE RETURNING MODIFICATION JSON:\n"
    "1. Is the response exactly one complete valid JSON object?\n"
    "2. Is mode exactly 'modify'?\n"
    "3. Are all seven required top-level keys present?\n"
    "4. Are all target names valid targets from the project?\n"
    "5. Are all add_blocks IDs unique and exact?\n"
    "6. Are all next references valid?\n"
    "7. Are all parent references valid?\n"
    "8. Are all SUBSTACK and SUBSTACK2 references valid?\n"
    "9. Are all input block references valid?\n"
    "10. Are all variable names and variable IDs exact?\n"
    "11. Are all variable scopes respected?\n"
    "12. Are all new reporter/operator/boolean trees actually connected to the inputs that use them?\n"
    "13. Are there any newly created unreachable blocks?\n"
    "14. Are there any duplicate helper blocks?\n"
    "15. Are there any placeholder or malformed IDs?\n"
    "16. Are all removed blocks safe to remove without leaving dangling references?\n"
    "17. Are shadow/menu structures copied from equivalent project examples when available?\n"
    "18. Are topLevel, parent, shadow, and x/y values preserved according to equivalent project structures instead of guessed generically?\n"
    "19. Is unrelated project data unchanged?\n"
    "20. If the answer would be incomplete or malformed, return a valid modify object with empty arrays instead.\n\n"
)

OPCODE_REFERENCE = (
    "SCRATCH OPCODE REFERENCE:\n"
    "The following are structural hints only. They never override project.json.\n\n"

    "CRITICAL PRIORITY:\n"
    "1. project.json is authoritative.\n"
    "2. Existing equivalent project blocks are more authoritative than this reference.\n"
    "3. This reference is only a fallback when the project has no equivalent structure.\n"
    "4. Never rewrite valid project data just to match this reference.\n\n"

    "COMMON INPUT FORMS:\n"
    "- [1, [TYPE_CODE, \"value\"]] may represent a literal or shadow value.\n"
    "- [1, \"block_id\"] may reference a reporter, boolean, menu, or other block depending on project serialization.\n"
    "- [2, \"block_id\"] is commonly used for stack inputs such as SUBSTACK.\n"
    "- [2, [TYPE_CODE, \"value\"]] may occur in boolean-compatible or empty structures depending on serialization.\n"
    "Known TYPE_CODE values include math_number=4, positive_number=5, whole_number=6, integer=7, angle=8, color=9, text=10, broadcast=11, variable=12, list=13.\n"
    "Never infer the full structure from the type code alone.\n\n"

    "EVENTS AND CONTROL:\n"
    "- event_whenflagclicked: commonly a top-level script entry block.\n"
    "- control_forever: commonly uses SUBSTACK.\n"
    "- control_if: commonly uses CONDITION and SUBSTACK.\n"
    "- control_if_else: commonly uses CONDITION, SUBSTACK, and SUBSTACK2.\n"
    "- control_repeat: commonly uses TIMES and SUBSTACK.\n"
    "- control_wait: commonly uses DURATION.\n"
    "Copy exact existing structures from the project whenever possible.\n\n"

    "MOTION:\n"
    "- motion_movesteps: commonly uses STEPS.\n"
    "- motion_pointtowards: commonly uses TOWARDS and may reference motion_pointtowards_menu.\n"
    "- motion_goto: commonly uses TO and may reference motion_goto_menu.\n\n"

    "SENSING:\n"
    "- sensing_touchingobject: commonly uses TOUCHINGOBJECTMENU and sensing_touchingobjectmenu.\n"
    "- sensing_keypressed: may use KEY_OPTION and sensing_keyoptions depending on project serialization.\n\n"

    "LOOKS:\n"
    "- looks_nextcostume: commonly has no inputs and no fields.\n"
    "- looks_switchcostumeto: inspect equivalent project structures for costume selection.\n"
    "- looks_changeeffectby: inspect equivalent project structures for effect selection and change amount.\n"
    "- looks_seteffectto: inspect equivalent project structures for effect selection and value.\n\n"

    "SOUND:\n"
    "- sound_play: inspect exact SOUND_MENU structure in the project.\n"
    "- sound_playuntildone: inspect exact SOUND_MENU structure in the project.\n"
    "Never invent unofficial sound opcodes.\n\n"

    "DATA:\n"
    "- data_setvariableto: uses an exact variable name and ID plus a VALUE input.\n"
    "- data_changevariableby: uses an exact variable name and ID plus a VALUE input.\n"
    "- data_variable: references a variable using the exact project serialization.\n"
    "Always verify variable ownership and ID from the project.\n\n"

    "OPERATORS:\n"
    "- operator_add, operator_subtract, operator_multiply, operator_divide commonly use NUM1 and NUM2.\n"
    "- operator_gt, operator_lt, operator_equals commonly use OPERAND1 and OPERAND2.\n"
    "- operator_and, operator_or commonly use OPERAND1 and OPERAND2.\n"
    "- operator_not commonly uses OPERAND.\n"
    "- operator_join commonly uses STRING1 and STRING2.\n"
    "- operator_contains commonly uses STRING1 and STRING2.\n"
    "- operator_length commonly uses STRING.\n"
    "- operator_letter_of commonly uses LETTER and STRING.\n"
    "- operator_mod commonly uses NUM1 and NUM2.\n"
    "- operator_round commonly uses NUM.\n"
    "- operator_mathop commonly uses a math operation selector and NUM.\n"
    "Exact serialization must come from equivalent blocks in the project when available.\n\n"

    "PROCEDURES:\n"
    "- procedures_definition commonly references a procedures_prototype and then the procedure body.\n"
    "- procedures_prototype contains mutation data such as proccode, argument names, argument IDs, and warp.\n"
    "- procedures_call contains mutation data and argument inputs.\n"
    "Copy exact mutation and argument structures from equivalent project procedures whenever possible.\n\n"

    "MENU BLOCKS:\n"
    "- motion_goto_menu\n"
    "- motion_pointtowards_menu\n"
    "- sensing_touchingobjectmenu\n"
    "- sensing_keyoptions\n"
    "- sound_sounds_menu\n"
    "- control_create_clone_of_menu\n"
    "Treat these according to exact project serialization.\n\n"
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
    FINAL_SELF_CHECK,
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