from collections import Counter
import json
import re
import sys
from constants import *
from utility import *
sys.stdin.reconfigure(encoding='utf-8')
sys.stdout.reconfigure(encoding='utf-8')


# These files are edited
tomes_json = load_json(LOCATION_OF_TOMES_JSON)
skills_json = load_json(LOCATION_OF_SKILLS_JSON)


def filter_non_aspect_items(aspect_dict):
    return [(attribute, value) for attribute, value in aspect_dict if re.match(REMOVE_BOOST_ABILITIES_PATTERN, attribute) == None]

def get_sprite_items(aspect_dict):
    return [(attribute, value) for attribute, value in aspect_dict if re.match(ASPECTS_PATTERN, attribute)]    


def format_memory_description(memory_id):
    READING_STRING_TEMPLATE = "<i>[Upon reading gives <b>{memory}]</b> ({memory_aspects})</i>"
    matching_memories = ASPECTS_LOOKUP.lookup_id(memory_id, 1)

    memory = matching_memories[0]
    description = memory["Label"]
    memory_aspects =memory["aspects"].items()

    aspects = filter_non_aspect_items(memory_aspects)
    rendered_items = get_sprite_items(memory_aspects)
    
    if Counter(aspects) != Counter(rendered_items):
        raise Exception(f"Some elements won't be rendered in the game for memory {memory_id}! Rendered items: {rendered_items}, All items {aspects}")
    
    aspects_strings = [ASPECT_TEMPLATE.format(aspect=aspect, aspect_power=value) for (aspect,value) in aspects]

    return READING_STRING_TEMPLATE.format(memory=description, memory_aspects=", ".join(aspects_strings))


def format_lesson_description(lesson_id, xtrigger_aspect):
    # For example, the following line will only appear if the xtrigger for mastery.edge is present
    # @#mastery.edge|TEXT_TO_APPEAR_ONLY_AFTER_MASTERING@
    # and if you need it to appear if without it
    # @#mastery.edge|#|TEXT_TO_APPEAR_IF_NOT_MASTERED@

    MASTERY_STRING_TEMPLATE = "@#mastery.{xtrigger_aspect}|#|<i>[First mastery gives <b>{lesson}]</b>@"
    matching_lessons = LESSONS_LOOKUP.lookup_id(lesson_id, 1)

    description = matching_lessons[0]["Label"]
    return MASTERY_STRING_TEMPLATE.format(lesson=description, xtrigger_aspect=xtrigger_aspect)


def interpret_xtriggers_in_tomejson(xtriggers):
    description_string = []
    for xtrigger_aspect, read_results in xtriggers.items():
        mastering_pattern = re.match(MASTERING_XTRIGGER_PATTERN, xtrigger_aspect)
        if re.match(READING_XTRIGGER_PATTERN, xtrigger_aspect):
            for item in read_results:
                description_string.insert(
                    0, format_memory_description(item["id"]))
        elif mastering_pattern:
            for item in read_results:
                description_string.append(
                    format_lesson_description(item["id"], mastering_pattern.group(1)))

    # Creates the description
    if description_string:
        connector = ", " + FILLER
        return FILLER*2 + connector.join(description_string)
    else:
        raise Exception(
            f"Couldn't find a matching reading pattern {xtriggers}")


def format_tech_tree_entry(skill_id):
    tech_tree_commit_paths = TECH_TREE_LOOKUP.lookup_id_regex_pattern(
        skill_id, WISDOM_PATTERN, 2)

    rewards = []

    REWARDS_TEMPLATE = "<b>{soul_fragment} from {tech_tree_path}</b>"
    TECH_TREETEMPLATE = "@#wisdom.committed|#|<i>[Yields {rewards}]@"
    for path in tech_tree_commit_paths:
        soul_fragment_name = ""
        tech_tree_path = ""
        for skill in path["mutations"]:
            skill_name = skill["mutate"]
            path_match = re.match(TECH_TREE_PATH_NAME_PATTERN,
                                  skill_name)
            soul_fragment_match = re.match(TECH_TREE_SOUL_FRAGMENT_PATTERN,
                                           skill_name)
            if path_match != None:
                tech_tree_path = path_match.group(1).capitalize()
            elif soul_fragment_match != None:
                soul_fragment_name = SOULFRAGMENT_LOOKUP.lookup_id(
                    soul_fragment_match.group(1), 1)[0]["label"]

        rewards.append(REWARDS_TEMPLATE.format(
            soul_fragment=soul_fragment_name, tech_tree_path=tech_tree_path))

    return TECH_TREETEMPLATE.format(rewards=" or ".join(rewards))


def format_recipes(skill_id):
    recipes = RECIPES_LOOKUP.filter(lambda x: (skill_id in x["reqs"]))
    RECIPES_STRING_TEMPLATE = "<b><i>[Possible recipes]:</b><i>" + FILLER
    RECIPE_LINE_TEMPLATE = "<i> + [<b>{recipe}]: </b> ({aspects}{additional_item_string})</i>"
    ADDITIONAL_ITEM_TEMPLATE = " | {additional_items}"
    description_lines = []
    for recipe in recipes:
        reqs = recipe["reqs"]
        recipe_name = recipe["Label"]

        recipe_items = reqs.items()
        aspects = filter_non_aspect_items(recipe_items)
        recipe_items = get_sprite_items(recipe_items)

        aspect_string = ", ".join([ASPECT_TEMPLATE.format(aspect=attribute, aspect_power=value) for attribute, value in recipe_items
                         if re.match(REMOVE_BOOST_ABILITIES_PATTERN, attribute) == None])

        additional_items = set(aspects) - set(get_sprite_items(recipe_items))
        additional_item_string = ""
        if additional_items:
            additional_items_for_recipe_names = []
            for (k, _) in additional_items:
                # Try and lookup aspect label
                try:
                    additional_items_for_recipe_names.append(ASPECTS_LOOKUP.lookup_id(k, 1)[0]["Label"])
                except:
                    additional_items_for_recipe_names.append(k)
            additional_item_string = ADDITIONAL_ITEM_TEMPLATE.format(additional_items = ", ".join(additional_items_for_recipe_names))

        description_lines.append(RECIPE_LINE_TEMPLATE.format(
            recipe=recipe_name, aspects=aspect_string, additional_item_string = additional_item_string ))
    if description_lines:
        return RECIPES_STRING_TEMPLATE + FILLER.join(description_lines)
    else:
        return ""


def generate_patched_skills_file():
    for skill in skills_json["elements"]:
        reading_description = format_tech_tree_entry(
            skill["id"])
        
        recipe_description = format_recipes(skill["id"])

        if recipe_description:
            skill["Desc"] += FILLER*2 + recipe_description

        skill["Desc"] += FILLER*2 + reading_description

    f = open(SAVED_SKILLS_FILE, "w")
    f.write(json.dumps(skills_json))
    f.close()


def generate_patched_tomes_file():
    for book in tomes_json["elements"]:
        reading_description = interpret_xtriggers_in_tomejson(
            book["xtriggers"])
        book["Desc"] += reading_description

    f = open(SAVED_TOMES_FILE, "w")
    f.write(json.dumps(tomes_json))
    f.close()


if __name__ == "__main__": 
    generate_patched_skills_file()
    generate_patched_tomes_file()
