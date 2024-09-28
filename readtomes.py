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
aspecteditems_json = load_json(LOCATION_OF_READING_ASPECTS_JSON)

load_json("elements\DLC_HOL_instituteaspects_foe.json")


def filter_non_aspect_items(aspect_dict) -> list:
    return [(attribute, value) for attribute, value in aspect_dict if re.match(REMOVE_NON_ASPECTS_PATTERN, attribute) == None]


def get_sprite_items(aspect_dict):
    return [(attribute, value) for attribute, value in aspect_dict if re.match(ASPECTS_PATTERN, attribute)]


def format_item_description(descriptionlabel, aspects_label, item=None):
    if type(item) == str:
        matching_item = ASPECTS_LOOKUP.lookup_id(item, 1)[0]
    else:
        matching_item = item
    description = matching_item[descriptionlabel]
    item_aspects = matching_item[aspects_label].items()

    aspects = filter_non_aspect_items(item_aspects)
    rendered_items = get_sprite_items(item_aspects)

    # eg stuff like lens might fall into these items
    required_items_that_arent_aspects = set(
        aspects) - set(get_sprite_items(rendered_items))

    additional_recipe_items_required = []
    if required_items_that_arent_aspects:
        for (k, _) in required_items_that_arent_aspects:
            # Try and lookup item label, eg Mazarine Fife
            try:
                additional_recipe_items_required.append(
                    ASPECTS_LOOKUP.lookup_id(k, 1)[0]["Label"])
            # Sometimes generic requirements apply, like lens
            except:
                additional_recipe_items_required.append(k)
    list_of_templated_aspects = [ASPECT_TEMPLATE.format(
        aspect=aspect, aspect_power=value) for (aspect, value) in rendered_items]
    return (description, list_of_templated_aspects, additional_recipe_items_required)


def format_memory_description(memory_id):
    READING_STRING_TEMPLATE = "<i>[Upon reading gives <b>{memory}]</b> ({memory_aspects})</i>"
    description, aspects_strings, additional_aspects_found = format_item_description(
        "Label", "aspects", memory_id)

    # This is just to check that our blacklist covers all expected scenarios since for memories we don't expect
    # anything additional
    if additional_aspects_found:
        raise Exception(
            f"Some elements won't be rendered in the game for memory item {memory_id}! Unrendered items: {additional_aspects_found}")

    return READING_STRING_TEMPLATE.format(memory=description, memory_aspects=", ".join(aspects_strings))


def format_lesson_description(lesson_id, xtrigger_aspect):
    # For example, the following line will only appear if the xtrigger for mastery.edge is present
    # @#mastery.edge|TEXT_TO_APPEAR_ONLY_AFTER_MASTERING@
    # and if you need it to appear if without it
    # @#mastery.edge|#|TEXT_TO_APPEAR_IF_NOT_MASTERED@

    # Please see https://docs.google.com/document/d/1BZiUrSiT8kKvWIEvx5DObThL4HMGVI1CluJR20CWBU0 for more details

    MASTERY_STRING_TEMPLATE = "@#mastery.{xtrigger_aspect}|#|<i>[First mastery gives <b>{lesson} ({aspects})]</b>@"
    matching_lessons = LESSONS_LOOKUP.lookup_id(lesson_id, 1)

    description, aspects_list, _ = format_item_description(
        "Label", "aspects", matching_lessons[0])
    return MASTERY_STRING_TEMPLATE.format(lesson=description, xtrigger_aspect=xtrigger_aspect, aspects=", ".join(aspects_list))


def interpret_xtriggers_in_tomejson(xtriggers):
    description_string = []
    for xtrigger_aspect, read_results in xtriggers.items():
        mastering_pattern = re.match(
            MASTERING_XTRIGGER_PATTERN, xtrigger_aspect)
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
        connector = FILLER
        return FILLER * 2 + connector.join(description_string)
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
        soul_fragment = ""
        no_longer_commitable_path = ""
        for skill in path["mutations"]:
            skill_name = skill["mutate"]
            path_match = re.match(TECH_TREE_PATH_NAME_PATTERN,
                                  skill_name)
            soul_fragment_match = re.match(TECH_TREE_SOUL_FRAGMENT_PATTERN,
                                           skill_name)
            if path_match != None:
                no_longer_commitable_path = path_match.group(1).capitalize()
            elif soul_fragment_match != None:
                soul_fragment = SOULFRAGMENT_LOOKUP.lookup_id(
                    soul_fragment_match.group(1), 1)[0]["label"]
        rewards.append([soul_fragment, no_longer_commitable_path])

    # the commit action makes the unused path unusable
    rewards[0][0], rewards[1][0] = rewards[1][0], rewards[0][0]

    return TECH_TREETEMPLATE.format(rewards=" or ".join([REWARDS_TEMPLATE.format(
        soul_fragment=soul_fragment, tech_tree_path=tech_tree_path) for soul_fragment, tech_tree_path in rewards]))


def format_crafting_recipes(skill_id):
    recipes = CRAFTING_RECIPES_LOOKUP.filter(lambda x: (skill_id in x["reqs"]))
    complete_recipe = Recipe()
    for recipe in recipes:
        recipe_name, aspect_list, additional_items_for_recipe_names = format_item_description(
            "Label", "reqs", recipe)

        recipe_product = [k for k, v in recipe["effects"].items() if v == 1]
        if len(recipe_product) != 1:
            raise Exception(
                f"Unexpected number of products that wasn't 1!: {recipe_product}")

        _, final_recipe_product_aspects, _ = format_item_description(
            "Label", "aspects", recipe_product[0])

        complete_recipe.add_recipe_line(
            recipe_name, final_recipe_product_aspects, aspect_list, additional_items_for_recipe_names)

    return str(complete_recipe)


def format_cooking_recipes(cooked_item, item_modification):
    # what ingredients need the recipe card added to them
    recipe_ingredients_to_modify = []

    # this is what's displayed in the recipe eg egg it doesn't matter what egg
    recipe_ingredients_generic = []
    for ingredient_name in cooked_item["reqs"]:
        if re.match(COOKING_INGREDIENTS_PATTERN, ingredient_name) != None:
            try:
                # in the event that it's an aspected item
                item = ASPECTS_LOOKUP.lookup_id(ingredient_name, 1)[0]
                item_modification.setdefault(ingredient_name, Recipe())
                recipe_ingredients_to_modify.append(ingredient_name)
                recipe_ingredients_generic.append(item["Label"])

            except:
                item_ids_with_aspects = [x["ID"] for x in ASPECTS_LOOKUP.filter(
                    lambda x: ingredient_name in x["aspects"])]
                recipe_ingredients_to_modify.extend(item_ids_with_aspects)
                [item_modification.setdefault(
                    ingredient, Recipe()) for ingredient in item_ids_with_aspects]
                recipe_ingredients_generic.append(ingredient_name)

    for cooked_product_id in cooked_item["effects"].keys():
        recipe_name, aspects_list, _ = format_item_description(
            "Label", "aspects", cooked_product_id)
        for item in recipe_ingredients_to_modify:
            item_modification[item].add_recipe_line(
                recipe_name, aspects_list, recipe_ingredients_generic, [])
    return item_modification


def save_file(filename, json_value):
    f = open(filename, "w")
    f.write(json.dumps(json_value))
    f.close()


def generate_patched_skills_file():
    for skill in skills_json["elements"]:
        reading_description = format_tech_tree_entry(
            skill["id"])

        recipe_description = format_crafting_recipes(skill["id"])

        if recipe_description:
            skill["Desc"] += FILLER * 2 + recipe_description

        skill["Desc"] += FILLER * 2 + reading_description

    save_file(SAVED_SKILLS_FILE, skills_json)


def generate_patched_tomes_file():
    for book in tomes_json["elements"]:
        reading_description = interpret_xtriggers_in_tomejson(
            book["xtriggers"])
        book["Desc"] += reading_description
    save_file(SAVED_TOMES_FILE, tomes_json)


def generate_patched_aspecteditems_file():
    cooking = COOKING_RECIPES_LOOKUP.filter(
        lambda x: x["id"].startswith('cook.'))

    item_modification = {}
    for cooked_item in cooking:
        format_cooking_recipes(cooked_item, item_modification)

    number_items_updated = 0
    for item in aspecteditems_json["elements"]:
        if item["ID"] in item_modification:
            recipe = str(item_modification[item["ID"]])
            item["Desc"] += FILLER * 2 + recipe
            number_items_updated += 1

    # should update the same number of items as there are to be updated - are they all in the aspect items file?
    assert number_items_updated == len(item_modification)
    save_file(SAVED_ASPECT_ITEMS_FILE, aspecteditems_json)


if __name__ == "__main__":
    generate_patched_skills_file()
    generate_patched_tomes_file()
    generate_patched_aspecteditems_file()
