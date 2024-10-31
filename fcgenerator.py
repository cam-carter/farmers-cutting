import json
import shutil
from pathlib import Path
from dataclasses import dataclass
from typing import List, Dict, Optional

# Farmer's Cutting Generator (fcgenerator)
# v0.1.1a

@dataclass
class ModConfig:
    """Configuration for a single mod."""
    namespace: str
    name: str
    id_suffix: str
    data_pack_version: str
    pack_format: int
    woods: List[str]
    recipe_types: List[str]
    platforms: List[str]
    dye_recipes: List[Dict]
    overrides: List[Dict]
    custom_recipes: List[Dict]

# Constants
CONFIG_DIR = Path(__file__).parent / 'fcgenerator'

RECIPE_TYPES = {
    "PLANKS_RECYCLE": ["door", "hanging_sign", "sign", "trapdoor"],
    "STRIPPING": ["log", "wood", "bark", "stem", "hyphae"]
}

TOOL_ACTIONS = {
    "axe": "axe_dig",
    "axe_strip": "axe_strip",
    "pickaxe": "pickaxe_dig"
}

PLATFORMS = {
    "fabric": {
        "type_key": "fabric:type"
    },
    "neoforge": {
        "type_key": "type"
    }
}

CLEANUP_DIRS = ['fabric', 'neoforge', 'forge', 'data']
KNIFE_TOOL_TAG = "c:tools/knife"
STRIPPING_SOUND = "minecraft:item.axe.strip"
DEFAULT_PLATFORM = "fabric"
RECIPE_DIR = "recipe"

OVERRIDE_TYPES = {
    "RECIPE_TYPES": "replace_recipe_types",
    "SINGLE_RECIPE": "replace_single_recipe"
}

def set_item_ability(platform: str, action: str) -> Dict:
    """Get the platform-specific item ability structure."""
    platform_config = PLATFORMS[platform]
    return {
        platform_config["type_key"]: "farmersdelight:item_ability",
        "action": action
    }

def create_base_recipe(ingredient_key: str, ingredient_value: str) -> Dict:
    """Create the base structure for all cutting recipes."""
    return {
        "type": "farmersdelight:cutting",
        "ingredients": [
            {ingredient_key: ingredient_value}
        ]
    }

def generate_cutting_recipe(config: ModConfig, wood_type: str, recipe_type: str, 
                          platform: str, wood_override: Optional[Dict] = None) -> Dict:
    """Generate a cutting recipe for a specific wood type and recipe type."""
    # Default ingredient
    default_ingredient = f"{config.namespace}:{wood_type}_{recipe_type}"
    ingredient = wood_override.get('ingredient', default_ingredient) if wood_override else default_ingredient
    
    recipe = create_base_recipe("item", ingredient)
    recipe["tool"] = set_item_ability(platform, TOOL_ACTIONS["axe"])

    if recipe_type in RECIPE_TYPES["PLANKS_RECYCLE"]:
        recipe["result"] = [{
            "item": {
                "count": 1,
                "id": f"{config.namespace}:{wood_type}_planks"
            }
        }]
    elif recipe_type in RECIPE_TYPES["STRIPPING"]:
        default_stripped = f"{config.namespace}:stripped_{wood_type}_{recipe_type}"
        stripped_item = wood_override.get('result', default_stripped) if wood_override else default_stripped
        
        recipe["result"] = [
            {
                "item": {
                    "count": 1,
                    "id": stripped_item
                }
            },
            {
                "item": {
                    "count": 1,
                    "id": wood_override.get('side_product', "farmersdelight:tree_bark") if wood_override else "farmersdelight:tree_bark"
                }
            }
        ]
        recipe["sound"] = {"sound_id": STRIPPING_SOUND}
        recipe["tool"] = set_item_ability(platform, TOOL_ACTIONS["axe_strip"])

    return recipe

def generate_dye_recipe(namespace: str, input_item: str, color: str, count: int) -> Dict:
    """Generate a dye cutting recipe."""
    is_tag = input_item.startswith('#')
    ingredient_key = "tag" if is_tag else "item"
    ingredient_value = input_item[1:] if is_tag else f"{namespace}:{input_item}"
    
    recipe = create_base_recipe(ingredient_key, ingredient_value)
    recipe["result"] = [{
        "item": {
            "count": count,
            "id": f"minecraft:{color}_dye"
        }
    }]
    recipe["tool"] = {"tag": KNIFE_TOOL_TAG}
    
    return recipe

def generate_custom_recipe(recipe_info: Dict, platform: str) -> Dict:
    """Generate a custom cutting recipe."""
    is_tag = recipe_info['ingredient'].startswith('#')
    ingredient_key = "tag" if is_tag else "item"
    ingredient_value = recipe_info['ingredient'][1:] if is_tag else recipe_info['ingredient']

    recipe = create_base_recipe(ingredient_key, ingredient_value)
    recipe["result"] = [{
        "item": {
            "count": recipe_info['count'],
            "id": recipe_info['result']
        }
    }]

    if recipe_info['tool'] == "knife":
        recipe["tool"] = {"tag": KNIFE_TOOL_TAG}
    else:
        recipe["tool"] = set_item_ability(platform, TOOL_ACTIONS[recipe_info['tool']])

    return recipe

def generate_beet_files(config: ModConfig, platform: str, minecraft_version: str) -> tuple[Dict, Dict]:
    """Generate Beet configuration files."""
    if len(config.platforms) > 1:
        version = f"{minecraft_version}-{config.data_pack_version}-{platform}"
    else:
        version = f"{minecraft_version}-{config.data_pack_version}"
    
    beet_build = {
        "id": f"farmers-cutting-{config.id_suffix}",
        "name": f"Farmer's Cutting: {config.name}",
        "version": version,
        "output": "build",
        "data_pack": {
            "pack_format": config.pack_format,
            "description": f"Adds Farmer's Delight cutting recipes for {config.name}",
            "load": ["."],
            "zipped": True
        }
    }

    beet = {
        "id": f"farmers-cutting-{config.id_suffix}",
        "name": f"Farmer's Cutting: {config.name}",
        "version": version,
        "data_pack": {
            "pack_format": config.pack_format,
            "description": f"Adds Farmer's Delight cutting recipes for {config.name}",
            "load": ["."]
        }
    }

    return beet_build, beet

def write_json_file(filepath: Path, data: Dict, indent: int = 2) -> bool:
    """Write JSON data to a file with error handling."""
    try:
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=indent)
        print(f"Generated: {filepath}")
        return True
    except IOError as e:
        print(f"Error writing file {filepath}: {e}")
        return False

def cleanup_old_files(mods: List[str]):
    """Clean up old generated files and directories."""
    print("Cleaning up old files...")

    for mod in mods:
        for directory in CLEANUP_DIRS:
            path = Path(mod) / Path(directory)
            if path.exists():
                try:
                    shutil.rmtree(path)
                    print(f"Removed {path}/")
                except Exception as e:
                    print(f"Error removing {path}/: {e}")

def get_override_fields(override: Dict, fields: List[str]) -> Optional[Dict]:
    """Extract specified fields from an override."""
    if not override:
        return None
    return {k: v for k, v in override.items() if k in fields}

def find_override(overrides: List[Dict], override_type: str, **conditions) -> Optional[Dict]:
    """Find an override matching the given conditions."""
    return next((o for o in overrides 
                if o['type'] == override_type 
                and all(o.get(k) == v for k, v in conditions.items())), None)

def get_output_paths(config: ModConfig, platform: str) -> tuple[Path, Path]:
    """
    Get the base and output directories for a platform.
    
    :param config: Mod configuration
    :param platform: Target platform
    :return: Tuple of (base_dir, output_dir)
    """
    base_dir = Path(config.namespace) / platform if len(config.platforms) > 1 else Path(config.namespace)
    output_dir = base_dir / 'data' / f"fc{config.id_suffix}" / RECIPE_DIR
    return base_dir, output_dir

def get_recipe_path(output_dir: Path, filename: str) -> Path:
    """
    Get the full path for a recipe file.
    
    :param output_dir: Base output directory
    :param filename: Name of the recipe file
    :return: Full path to the recipe file
    """
    return output_dir / filename

def process_wood_recipes(config: ModConfig, wood_type: str, platform: str, output_dir: Path):
    """Process wood recipes for a specific wood type."""
    # Check for recipe type override
    type_override = find_override(config.overrides, 
                                OVERRIDE_TYPES["RECIPE_TYPES"], 
                                wood=wood_type)
    
    current_recipe_types = type_override['recipe_types'] if type_override else config.recipe_types

    for recipe_type in current_recipe_types:
        # Check for single recipe override
        recipe_override = find_override(config.overrides, 
                                      OVERRIDE_TYPES["SINGLE_RECIPE"], 
                                      wood=wood_type, 
                                      recipe_type=recipe_type)
        
        # Create override dict with only the specified fields
        wood_override = get_override_fields(recipe_override, ['ingredient', 'result', 'side_product'])
        recipe = generate_cutting_recipe(config, wood_type, recipe_type, platform, wood_override)
        
        filepath = get_recipe_path(output_dir, f"{wood_type}_{recipe_type}.json")
        if not write_json_file(filepath, recipe):
            continue

def generate_recipes(config: ModConfig, platform: str, output_dir: Path):
    """Generate dye and custom recipes."""
    # Generate dye cutting recipes
    for dye_recipe in config.dye_recipes:
        input_item = dye_recipe['input']
        color = dye_recipe['color']
        count = dye_recipe['count']
        
        recipe = generate_dye_recipe(config.namespace, input_item, color, count)
        
        filename = f"{color}_dye_from_tag.json" if input_item.startswith('#') else f"{input_item}.json"
        filepath = get_recipe_path(output_dir, filename)
        if not write_json_file(filepath, recipe):
            continue

    # Generate custom recipes
    for custom_recipe in config.custom_recipes:
        recipe = generate_custom_recipe(custom_recipe, platform)
        filepath = get_recipe_path(output_dir, custom_recipe['filename'])
        if not write_json_file(filepath, recipe):
            continue

def process_platform(config: ModConfig, platform: str, minecraft_version: str):
    """Process recipes for a specific platform."""
    try:
        # Set up directories
        base_dir, output_dir = get_output_paths(config, platform)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Process each type of recipe
        for wood_type in config.woods:
            process_wood_recipes(config, wood_type, platform, output_dir)

        # Generate other recipes
        generate_recipes(config, platform, output_dir)

        # Generate beet files
        beet_build, beet = generate_beet_files(config, platform, minecraft_version)
        if not write_json_file(base_dir / 'beet-build.json', beet_build, indent=4):
            print(f"Error writing beet-build.json for platform {platform}")
            return
        if not write_json_file(base_dir / 'beet.json', beet, indent=4):
            print(f"Error writing beet.json for platform {platform}")
            return

    except Exception as e:
        print(f"Error processing platform {platform}: {e}")

def process_mod_config(mod_config_name: str, minecraft_version: str):
    """Process a single mod configuration."""
    mod_config_path = CONFIG_DIR / f'{mod_config_name}.json'
    try:
        with open(mod_config_path, 'r') as mod_config_file:
            mod_info = json.load(mod_config_file)
    except FileNotFoundError:
        print(f"Error: Mod configuration file not found at {mod_config_path}")
        return
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON in mod configuration file {mod_config_path}")
        return

    # Create ModConfig object
    config = ModConfig(
        namespace=mod_info['namespace'],
        name=mod_info['name'],
        id_suffix=mod_info['id_suffix'],
        data_pack_version=mod_info['data_pack_version'],
        pack_format=mod_info['pack_format'],
        woods=mod_info['wood_recipes']['woods'],
        recipe_types=mod_info['wood_recipes']['types'],
        platforms=mod_info.get('platforms', [DEFAULT_PLATFORM]),
        dye_recipes=mod_info.get('dye_recipes', []),
        overrides=mod_info.get('overrides', []),
        custom_recipes=mod_info.get('custom_recipes', [])
    )

    for platform in config.platforms:
        process_platform(config, platform, minecraft_version)

def main():
    """Main entry point for the script."""
    try:
        config_path = CONFIG_DIR / 'generator_config.json'
        try:
            with open(config_path, 'r') as config_file:
                generator_config = json.load(config_file)
        except FileNotFoundError:
            print(f"Error: Configuration file not found at {config_path}")
            return
        except json.JSONDecodeError:
            print(f"Error: Invalid JSON in configuration file {config_path}")
            return

        minecraft_version = generator_config['minecraft_version']

        cleanup_old_files(generator_config['mods'])

        for mod in generator_config['mods']:
            process_mod_config(mod, minecraft_version)

    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()
