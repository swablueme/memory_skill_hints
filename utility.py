from constants import *
import json
import re


def load_json(file):
    path = BOH_PATH + file
    for encode in ["utf-8", "utf-16le"]:
        try:
            with open(path, "r", encoding=encode) as f:
                return json.loads(f.read())
        except:
            print(path, "loading failed for encoding", encode)


class JsonLookup:
    def __init__(self, root_key, *elements):
        for element in elements:
            variable_name = element.split("\\")[-1].replace(".", "_")
            setattr(self, variable_name, load_json(element))
        self.root_key = root_key

    def _is_id_equal(self, id_in_dict, id_presented, dict_regex_pattern):
        if dict_regex_pattern == None:
            return id_in_dict == id_presented
        else:
            match = re.match(dict_regex_pattern, id_in_dict)
            if match == None or match.group(ID_PATTERN_GROUP) != id_presented:
                return False
            return True

    @staticmethod
    def validate_returned_count(result, element_id, count):
        # We only expect one entry when looking up a memory or lesson etc but two for if committing to the tech tree
        if len(result) != count:
            raise Exception(
                f"The number of elements that match {element_id} is {len(result)}, but it is expected that {count} result/s exist")

    def lookup_id_regex_pattern(self, element_id, dict_regex_pattern, count):
        result = self.lookup_field(element_id, "ID", dict_regex_pattern)
        JsonLookup.validate_returned_count(result, element_id, count)
        return result

    def lookup_id(self, element_id, count):
        result = self.lookup_field(element_id, "ID", None)
        JsonLookup.validate_returned_count(result, element_id, count)
        return result

    def _get_all_dicts(self):
        entrylist = []
        for key in self.__dict__.keys():
            if key.endswith("_json") and not key.startswith("_"):
                entrylist.extend(getattr(self, key)[self.root_key])
        return entrylist

    def lookup_field(self, element_id, field_name, dict_regex_pattern):
        result = []
        for list_of_dict_entries in self._get_all_dicts():
            for key, value in list_of_dict_entries.items():
                if key.lower() == field_name.lower() and self._is_id_equal(value, element_id, dict_regex_pattern):
                    result.append(list_of_dict_entries)
        return result

    def filter(self, filter_lambda):
        return list(filter(filter_lambda, self._get_all_dicts()))


class Recipe:
    RECIPES_STRING_TEMPLATE = "<b><i>[Possible recipes]:</b><i>" + FILLER
    RECIPE_LINE_TEMPLATE = "<i> + [<b>{recipe_name} ({recipe_item_aspects}) ] - </b> {aspects_needed_to_craft}{additional_item_string}</i>"
    ADDITIONAL_ITEM_TEMPLATE = ", {additional_items}"

    def __init__(self):
        self.description_lines = []

    def add_recipe_line(self, recipe_name, recipe_item_aspects, aspects_needed_to_craft, additional_item):
        self.description_lines.append({"recipe_name": recipe_name,
                                       "recipe_item_aspects": recipe_item_aspects,
                                       "aspects_needed_to_craft": aspects_needed_to_craft,
                                       "additional_item": additional_item})
        return self.description_lines

    def __str__(self):
        string_representation = []
        for line in self.description_lines:
            additional_item_string = Recipe.ADDITIONAL_ITEM_TEMPLATE.format(additional_items=", ".join(
                line["additional_item"])) if line["additional_item"] else ""

            string_representation.append(Recipe.RECIPE_LINE_TEMPLATE.format(
                recipe_name=line["recipe_name"],
                recipe_item_aspects=", ".join(line["recipe_item_aspects"]),
                aspects_needed_to_craft=", ".join(
                    line["aspects_needed_to_craft"]),
                additional_item_string=additional_item_string))

        if string_representation:
            return Recipe.RECIPES_STRING_TEMPLATE + FILLER.join(string_representation)
        else:
            return ""


ASPECTS_LOOKUP = JsonLookup(
    "elements", LOCATION_OF_READING_ASPECTS_JSON)
SKILLS_LOOKUP = JsonLookup("elements", LOCATION_OF_SKILLS_JSON)
LESSONS_LOOKUP = JsonLookup("elements", *LOCATION_OF_LESSONS_JSON)
TECH_TREE_LOOKUP = JsonLookup(
    "recipes", LOCATION_OF_WISDOM_COMMITMENTS_JSON)
CRAFTING_RECIPES_LOOKUP = JsonLookup("recipes", *LOCATION_OF_CRAFTING_RECIPES)
COOKING_RECIPES_LOOKUP = JsonLookup("recipes", LOCATION_OF_COOKING_RECIPES)
SOULFRAGMENT_LOOKUP = JsonLookup("elements", LOCATION_OF_ABILITY_JSON)
