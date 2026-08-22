from __future__ import annotations


SCRATCH_PATTERNS = {
    "smooth_size": {
        "name": "Smooth Size Change",
        "aliases": [
            "smooth size",
            "smooth size changing",
            "smoothly change size",
            "smoothly grow",
            "smoothly shrink",
            "size interpolation",
            "ease the size",
            "ease size",
        ],
        "description": (
            "Gradually moves a sprite's size toward a target size instead of changing "
            "the size instantly."
        ),
        "pattern": (
            "forever -> "
            "change size by ((target size - size) / smoothing)"
        ),
        "example": (
            "forever -> "
            "change size by ((120 - size) / 3)"
        ),
        "category": "visual",
        "scratch_specific": False,
        "rules": [
            "Use the target size as the desired final size.",
            "Use the sprite's current size as the current value.",
            "A larger smoothing divisor makes the approach slower.",
            "The pattern normally runs repeatedly.",
            "Preserve existing variables and project structure when adapting it.",
        ],
    },

    "smooth_x": {
        "name": "Smooth X Movement",
        "aliases": [
            "smooth x movement",
            "smooth horizontal movement",
            "smoothly move horizontally",
            "smooth x",
            "interpolate x",
        ],
        "description": (
            "Gradually moves a sprite toward a target X coordinate."
        ),
        "pattern": (
            "forever -> "
            "change x by ((target x - x position) / smoothing)"
        ),
        "category": "motion",
        "scratch_specific": False,
    },

    "smooth_y": {
        "name": "Smooth Y Movement",
        "aliases": [
            "smooth y movement",
            "smooth vertical movement",
            "smoothly move vertically",
            "smooth y",
            "interpolate y",
        ],
        "description": (
            "Gradually moves a sprite toward a target Y coordinate."
        ),
        "pattern": (
            "forever -> "
            "change y by ((target y - y position) / smoothing)"
        ),
        "category": "motion",
        "scratch_specific": False,
    },

    "smooth_move_to": {
        "name": "Smooth Move To",
        "aliases": [
            "smooth movement",
            "smooth move",
            "smoothly move to",
            "smoothly move toward",
            "smooth follow position",
            "interpolate position",
        ],
        "description": (
            "Gradually moves a sprite toward a target position using separate X and Y smoothing."
        ),
        "pattern": (
            "forever -> "
            "change x by ((target x - x position) / smoothing) -> "
            "change y by ((target y - y position) / smoothing)"
        ),
        "category": "motion",
        "scratch_specific": False,
    },

    "smooth_rotation": {
        "name": "Smooth Rotation",
        "aliases": [
            "smooth rotation",
            "smoothly rotate",
            "smooth turning",
            "smooth direction",
            "interpolate rotation",
        ],
        "description": (
            "Gradually rotates a sprite toward a target direction."
        ),
        "pattern": (
            "forever -> "
            "turn toward the target direction using a fraction of the angular difference"
        ),
        "category": "motion",
        "scratch_specific": False,
        "rules": [
            "Respect the project's existing rotation system.",
            "Handle wraparound between 180 and -180 degrees when necessary.",
            "Do not replace existing rotation logic without checking how the project handles directions.",
        ],
    },

    "boolean_input_loop": {
        "name": "Boolean Input Loop",
        "aliases": [
            "use boolean blocks for input",
            "use boolean input",
            "boolean key input",
            "key pressed boolean",
            "check the key continuously",
            "use if key pressed",
            "use forever and if for input",
            "continuous keyboard input",
        ],
        "description": (
            "Uses boolean sensing blocks inside a forever loop and conditional blocks "
            "for continuously checked input instead of relying entirely on key-pressed events."
        ),
        "pattern": (
            "forever -> "
            "if <key [right arrow] pressed?> then -> "
            "perform action"
        ),
        "example": (
            "when green flag clicked -> "
            "forever -> "
            "if <key [right arrow] pressed?> then -> "
            "change x by (5)"
        ),
        "category": "input",
        "scratch_specific": True,
        "rules": [
            "Prefer boolean sensing blocks for continuously held keyboard input.",
            "Use a forever loop with if conditions when an action should continue while a key is held.",
            "Do not replace a useful one-time event with a polling loop when the action should only happen once.",
            "Preserve existing event-based logic when it has different intended semantics.",
            "Inspect how the project currently handles keyboard input before replacing it.",
        ],
    },

    "continuous_boolean_input": {
        "name": "Continuous Boolean Input",
        "aliases": [
            "held key input",
            "key held input",
            "continuous key detection",
            "continuous input",
            "smooth keyboard controls",
            "responsive keyboard controls",
        ],
        "description": (
            "Continuously checks boolean input states so movement and controls can respond "
            "every loop rather than triggering only once when an event fires."
        ),
        "pattern": (
            "forever -> "
            "if <key [left arrow] pressed?> then -> "
            "change x by (-5) -> "
            "if <key [right arrow] pressed?> then -> "
            "change x by (5)"
        ),
        "category": "input",
        "scratch_specific": True,
    },

    "infinity_grayscale": {
        "name": "Infinity Grayscale Trick",
        "aliases": [
            "infinity color trick",
            "infinity color effect",
            "black and white effect",
            "black and white trick",
            "grayscale trick",
            "make sprite black and white",
            "make this sprite grayscale",
            "infinity grayscale",
        ],
        "description": (
            "A Scratch-specific visual trick that uses the string Infinity as the color "
            "effect value and makes the sprite appear black and white."
        ),
        "pattern": (
            "set color effect to (join [Infinity] [])"
        ),
        "category": "visual",
        "scratch_specific": True,
        "rules": [
            "Treat this as a Scratch-specific quirk rather than a general programming technique.",
            "Preserve the exact string Infinity.",
            "Do not replace it with a numeric color effect value when the user explicitly asks for the Infinity trick.",
        ],
    },

    "acceleration": {
        "name": "Acceleration",
        "aliases": [
            "acceleration",
            "accelerate",
            "accelerating movement",
            "speed acceleration",
            "accelerate the player",
        ],
        "description": (
            "Uses a velocity or speed variable that changes over time instead of moving at a fixed speed."
        ),
        "pattern": (
            "change speed by acceleration -> "
            "move speed steps"
        ),
        "category": "physics",
        "scratch_specific": False,
        "rules": [
            "Use a variable for velocity or speed when appropriate.",
            "Preserve the project's existing coordinate and movement system.",
            "Do not create duplicate speed variables when an appropriate one already exists.",
        ],
    },

    "friction": {
        "name": "Friction",
        "aliases": [
            "friction",
            "deceleration",
            "slow down gradually",
            "smooth stopping",
            "inertia",
        ],
        "description": (
            "Gradually reduces velocity over time to create smooth deceleration."
        ),
        "pattern": (
            "set speed to (speed * friction)"
        ),
        "category": "physics",
        "scratch_specific": False,
        "rules": [
            "A multiplier slightly below 1 creates gradual slowdown.",
            "Combine with acceleration when implementing momentum-based movement.",
            "Respect the sign and meaning of the project's velocity variable.",
        ],
    },

    "gravity": {
        "name": "Gravity",
        "aliases": [
            "gravity",
            "falling physics",
            "fall",
            "gravity system",
            "vertical velocity",
        ],
        "description": (
            "Uses vertical velocity and gravity to create falling motion."
        ),
        "pattern": (
            "change y by velocity -> "
            "change velocity by (-gravity)"
        ),
        "category": "physics",
        "scratch_specific": False,
    },

    "jump_physics": {
        "name": "Jump Physics",
        "aliases": [
            "jump system",
            "jump physics",
            "platformer jump",
            "jumping",
            "make player jump",
        ],
        "description": (
            "Uses vertical velocity to launch a sprite upward and gravity to bring it back down."
        ),
        "pattern": (
            "set velocity to jump force -> "
            "forever -> "
            "change y by velocity -> "
            "change velocity by (-gravity)"
        ),
        "category": "physics",
        "scratch_specific": False,
    },

    "bounce": {
        "name": "Bounce",
        "aliases": [
            "bounce",
            "bouncing",
            "bounce off ground",
            "bounce physics",
        ],
        "description": (
            "Reverses or resets velocity when an object reaches a surface."
        ),
        "pattern": (
            "if <touching ground> then -> "
            "set velocity to bounce force"
        ),
        "category": "physics",
        "scratch_specific": False,
    },

    "terminal_velocity": {
        "name": "Terminal Velocity",
        "aliases": [
            "terminal velocity",
            "maximum falling speed",
            "cap falling speed",
            "limit velocity",
        ],
        "description": (
            "Limits how fast a velocity variable can grow in one direction."
        ),
        "pattern": (
            "change velocity by (-gravity) -> "
            "if <velocity < -max speed> then -> "
            "set velocity to (-max speed)"
        ),
        "category": "physics",
        "scratch_specific": False,
    },

    "cooldown": {
        "name": "Cooldown",
        "aliases": [
            "cooldown",
            "ability cooldown",
            "attack cooldown",
            "wait before using again",
            "cooldown timer",
        ],
        "description": (
            "Prevents an action from being repeated until a timer reaches zero."
        ),
        "pattern": (
            "if <cooldown = 0> then -> "
            "perform action -> "
            "set cooldown to duration"
        ),
        "category": "gameplay",
        "scratch_specific": False,
        "rules": [
            "A separate loop or timer should decrease the cooldown.",
            "Use the project's existing timer variables when appropriate.",
        ],
    },

    "countdown_timer": {
        "name": "Countdown Timer",
        "aliases": [
            "countdown",
            "countdown timer",
            "timer",
            "count down",
            "timer system",
        ],
        "description": (
            "Uses a variable that decreases over time until it reaches zero."
        ),
        "pattern": (
            "set timer to starting value -> "
            "repeat or forever -> "
            "wait (1) seconds -> "
            "change timer by (-1)"
        ),
        "category": "gameplay",
        "scratch_specific": False,
    },

    "health_system": {
        "name": "Health System",
        "aliases": [
            "health system",
            "hp system",
            "hit points",
            "health",
            "life system",
        ],
        "description": (
            "Uses a health variable that decreases when damage is taken and can trigger death at zero."
        ),
        "pattern": (
            "change health by (-damage) -> "
            "if <health <= 0> then -> "
            "death logic"
        ),
        "category": "gameplay",
        "scratch_specific": False,
    },

    "health_clamp": {
        "name": "Health Clamp",
        "aliases": [
            "clamp health",
            "limit health",
            "keep health between zero and max",
        ],
        "description": (
            "Keeps a numeric health value inside a valid range."
        ),
        "pattern": (
            "if <health > max> then set health to max -> "
            "if <health < 0> then set health to 0"
        ),
        "category": "gameplay",
        "scratch_specific": False,
    },

    "stamina_system": {
        "name": "Stamina System",
        "aliases": [
            "stamina system",
            "energy system",
            "stamina",
            "energy mechanic",
            "fatigue system",
        ],
        "description": (
            "Uses a resource variable that decreases during actions and regenerates over time."
        ),
        "pattern": (
            "change stamina by (-cost) during activity -> "
            "change stamina by regeneration while resting"
        ),
        "category": "gameplay",
        "scratch_specific": False,
    },

    "smooth_health_bar": {
        "name": "Smooth Health Bar",
        "aliases": [
            "smooth health bar",
            "smooth hp bar",
            "animated health bar",
            "smooth stamina bar",
            "smooth resource bar",
        ],
        "description": (
            "Uses a displayed value that smoothly approaches the real health or stamina value."
        ),
        "pattern": (
            "forever -> "
            "change displayed value by ((actual value - displayed value) / smoothing)"
        ),
        "category": "ui",
        "scratch_specific": False,
    },

    "invincibility_frames": {
        "name": "Invincibility Frames",
        "aliases": [
            "invincibility frames",
            "iframes",
            "temporary invincibility",
            "damage immunity",
            "invulnerability",
        ],
        "description": (
            "Temporarily prevents repeated damage after the player is hit."
        ),
        "pattern": (
            "set invincible to 1 -> "
            "visual feedback -> "
            "wait duration -> "
            "set invincible to 0"
        ),
        "category": "gameplay",
        "scratch_specific": False,
    },

    "toggle": {
        "name": "Toggle",
        "aliases": [
            "toggle",
            "toggle switch",
            "on off toggle",
            "toggle state",
        ],
        "description": (
            "Switches a state between two values such as 0 and 1."
        ),
        "pattern": (
            "if <state = 0> then -> "
            "set state to 1 -> "
            "else -> "
            "set state to 0"
        ),
        "category": "logic",
        "scratch_specific": False,
    },

    "edge_trigger": {
        "name": "Edge Trigger",
        "aliases": [
            "edge trigger",
            "press once",
            "detect key press once",
            "one press event",
            "button press detection",
        ],
        "description": (
            "Detects the transition from an input being released to being pressed, "
            "instead of firing continuously while the input is held."
        ),
        "pattern": (
            "if <key pressed and previous key state was false> then -> "
            "perform action -> "
            "update previous key state"
        ),
        "category": "input",
        "scratch_specific": False,
    },

    "debounce": {
        "name": "Debounce",
        "aliases": [
            "debounce",
            "prevent repeated input",
            "input debounce",
            "key debounce",
        ],
        "description": (
            "Prevents a single key press from triggering repeated actions too quickly."
        ),
        "pattern": (
            "wait until key released -> "
            "wait until key pressed"
        ),
        "category": "input",
        "scratch_specific": False,
    },

    "distance_check": {
        "name": "Distance Check",
        "aliases": [
            "distance check",
            "nearby check",
            "check if close",
            "within range",
            "distance trigger",
        ],
        "description": (
            "Triggers behavior when two objects are within a chosen distance."
        ),
        "pattern": (
            "if <distance to target < range> then -> "
            "action"
        ),
        "category": "logic",
        "scratch_specific": False,
    },

    "follow_target": {
        "name": "Follow Target",
        "aliases": [
            "follow target",
            "follow player",
            "enemy follow",
            "sprite follows player",
            "make it follow",
        ],
        "description": (
            "Continuously moves an object toward another object."
        ),
        "pattern": (
            "forever -> "
            "point towards target -> "
            "move speed steps"
        ),
        "category": "motion",
        "scratch_specific": False,
    },

    "smooth_follow_target": {
        "name": "Smooth Follow Target",
        "aliases": [
            "smooth follow",
            "smoothly follow",
            "smooth follower",
            "smooth camera follow",
        ],
        "description": (
            "Smoothly follows a target without instantly snapping to it."
        ),
        "pattern": (
            "forever -> "
            "change x toward target -> "
            "change y toward target"
        ),
        "category": "motion",
        "scratch_specific": False,
    },

    "screen_wrap": {
        "name": "Screen Wrap",
        "aliases": [
            "screen wrap",
            "wrap around screen",
            "wrap at edges",
            "teleport across edge",
        ],
        "description": (
            "Moves an object to the opposite side when it leaves the screen."
        ),
        "pattern": (
            "if x position beyond edge -> set x to opposite side"
        ),
        "category": "motion",
        "scratch_specific": True,
    },

    "random_spawn": {
        "name": "Random Spawn",
        "aliases": [
            "random spawn",
            "random position",
            "spawn randomly",
            "randomly place",
            "random location",
        ],
        "description": (
            "Places an object at a random position."
        ),
        "pattern": (
            "go to random position"
        ),
        "category": "gameplay",
        "scratch_specific": True,
    },

    "velocity": {
        "name": "Velocity",
        "aliases": [
            "velocity system",
            "speed variable",
            "use velocity",
            "movement velocity",
            "momentum",
        ],
        "description": (
            "Stores movement speed in a variable and uses that value to control motion."
        ),
        "pattern": (
            "speed or velocity variable -> "
            "change velocity -> "
            "move using velocity"
        ),
        "category": "physics",
        "scratch_specific": False,
    },

    "inertia": {
        "name": "Inertia",
        "aliases": [
            "inertia",
            "momentum movement",
            "momentum",
            "sliding movement",
        ],
        "description": (
            "Keeps an object's movement continuing after input stops and gradually reduces the velocity."
        ),
        "pattern": (
            "input changes velocity -> "
            "position changes using velocity -> "
            "friction reduces velocity"
        ),
        "category": "physics",
        "scratch_specific": False,
    },

    "broadcast_communication": {
        "name": "Broadcast Communication",
        "aliases": [
            "broadcast communication",
            "use broadcasts",
            "broadcast between sprites",
            "communicate between sprites",
            "sprite communication",
        ],
        "description": (
            "Uses broadcasts to let one sprite trigger logic in another sprite."
        ),
        "pattern": (
            "broadcast message -> "
            "when I receive message -> "
            "perform action"
        ),
        "category": "architecture",
        "scratch_specific": True,
        "rules": [
            "Use broadcasts when one sprite needs to trigger another sprite's local logic.",
            "Do not use broadcasts merely to replace direct logic that can remain local.",
            "Broadcasts are especially useful when another sprite must react to a local variable change without directly accessing that local variable.",
        ],
    },

    "local_global_variable_bridge": {
        "name": "Local Variable Bridge",
        "aliases": [
            "local variable bridge",
            "access another sprite variable",
            "share local variable",
            "cross sprite variable",
        ],
        "description": (
            "Uses broadcasts or a global variable to communicate values when a sprite cannot directly access another sprite's local variable."
        ),
        "pattern": (
            "sprite A changes local state -> "
            "broadcast message -> "
            "sprite B receives message -> "
            "sprite B changes its own local state"
        ),
        "category": "architecture",
        "scratch_specific": True,
        "rules": [
            "Never directly modify another sprite's local variable.",
            "Prefer a global Stage variable when the value genuinely needs to be shared.",
            "Use broadcasts when the other sprite only needs to react to an event.",
            "Preserve existing variable scopes whenever possible.",
        ],
    },

    "targeted_color_effect": {
        "name": "Color Effect",
        "aliases": [
            "change color",
            "color effect",
            "change sprite color",
            "color shift",
            "color change",
        ],
        "description": (
            "Uses Scratch's color effect to visually change a sprite."
        ),
        "pattern": (
            "change color effect by amount"
        ),
        "category": "visual",
        "scratch_specific": True,
    },

    "ghost_fade": {
        "name": "Ghost Fade",
        "aliases": [
            "fade",
            "fade in",
            "fade out",
            "ghost fade",
            "fade effect",
            "smooth transparency",
        ],
        "description": (
            "Uses the ghost effect to smoothly fade a sprite in or out."
        ),
        "pattern": (
            "repeat or forever -> "
            "change ghost effect by amount"
        ),
        "category": "visual",
        "scratch_specific": True,
    },

    "costume_animation": {
        "name": "Costume Animation",
        "aliases": [
            "animate costume",
            "costume animation",
            "animate sprite",
            "change costume while moving",
            "walking animation",
            "animation frames",
        ],
        "description": (
            "Cycles through costumes repeatedly to create sprite animation."
        ),
        "pattern": (
            "forever -> "
            "next costume -> "
            "wait animation interval"
        ),
        "category": "visual",
        "scratch_specific": True,
    },

    "smooth_value": {
        "name": "Smooth Value",
        "aliases": [
            "smooth value",
            "smooth variable",
            "smooth interpolation",
            "interpolate value",
            "ease a variable",
        ],
        "description": (
            "Gradually moves one numeric value toward another instead of changing it instantly."
        ),
        "pattern": (
            "change displayed value by ((target value - current value) / smoothing)"
        ),
        "category": "logic",
        "scratch_specific": False,
    },
}


PATTERN_CATEGORIES = {
    "visual": "Visual and appearance techniques",
    "motion": "Movement and positioning techniques",
    "input": "Keyboard and input handling techniques",
    "physics": "Physics and movement simulation techniques",
    "gameplay": "Gameplay systems and mechanics",
    "logic": "General logic and state techniques",
    "ui": "Interface and display techniques",
    "architecture": "Multi-sprite and project architecture techniques",
}


def get_pattern(pattern_name: str) -> dict | None:
    return SCRATCH_PATTERNS.get(pattern_name)


def get_patterns() -> dict[str, dict]:
    return dict(SCRATCH_PATTERNS)


def get_pattern_names() -> list[str]:
    return list(SCRATCH_PATTERNS.keys())


def get_pattern_aliases(pattern_name: str) -> list[str]:
    pattern = SCRATCH_PATTERNS.get(pattern_name)
    if not pattern:
        return []
    return list(pattern.get("aliases", []))


def get_patterns_by_category(category: str) -> dict[str, dict]:
    return {
        name: pattern
        for name, pattern in SCRATCH_PATTERNS.items()
        if pattern.get("category") == category
    }


def build_scratch_patterns_prompt() -> str:
    sections = [
        "SCRATCH PROGRAMMING PATTERNS:\n",
        "The following are reusable Scratch programming patterns and community-style techniques.\n",
        "Patterns are suggestions, not mandatory implementations.\n",
        "When a user refers to one of these patterns, identify the intended technique and adapt it to the provided project.\n",
        "Do not blindly copy a pattern. Preserve the project's existing variables, targets, scripts, block structures, and behavior whenever possible.\n",
        "For Scratch-specific tricks, preserve the exact Scratch behavior described by the pattern.\n\n",
    ]

    for pattern_id, pattern in SCRATCH_PATTERNS.items():
        sections.append(f"PATTERN: {pattern['name']}\n")
        sections.append(f"ID: {pattern_id}\n")
        sections.append(f"CATEGORY: {pattern['category']}\n")
        sections.append(f"DESCRIPTION: {pattern['description']}\n")
        sections.append("ALIASES: " + ", ".join(pattern.get("aliases", [])) + "\n")
        sections.append(f"PATTERN: {pattern['pattern']}\n")

        if pattern.get("example"):
            sections.append(f"EXAMPLE: {pattern['example']}\n")

        if pattern.get("rules"):
            sections.append("RULES:\n")
            for rule in pattern["rules"]:
                sections.append(f"- {rule}\n")

        if pattern.get("scratch_specific"):
            sections.append("SCRATCH_SPECIFIC: true\n")
        else:
            sections.append("SCRATCH_SPECIFIC: false\n")

        sections.append("\n")

    return "".join(sections)