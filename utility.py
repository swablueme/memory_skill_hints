from constants import *
import json
import re


def load_json(file):
    path = BOH_PATH + file

    # JSON files in Book of Hours are in a variety of encodes - also make sure to run the json through a validator if it fails to load
    for encode in ["utf-8", "utf-16", "utf-16le"]:
        try:
            with open(path, "r", encoding=encode) as f:
                json_loaded = json.loads(f.read())
                print(f"{path} loading succeded for encoding: {encode}")
                return json_loaded
        except:
            print(f"{path} loading failed for encoding: {encode}")


def save_file(filename, json_value):
    f = open(filename, "w")
    f.write(json.dumps(json_value))
    f.close()


class JsonLookup:
    def __init__(self, *elements):
        for element in elements:
            folder_name, json_name = element.split("\\")
            variable_name = json_name.replace(".", "_")
            setattr(self, variable_name, (folder_name, load_json(element)))

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
        if count != None and len(result) != count:
            raise Exception(
                f"The number of elements that match {element_id} is {len(result)}, but it is expected that {count} result/s exist")

    def lookup_id_regex_pattern(self, element_id, dict_regex_pattern, count=None):
        result = self.lookup_field(element_id, "ID", dict_regex_pattern)
        JsonLookup.validate_returned_count(result, element_id, count)
        return result

    def lookup_id(self, element_id, count=None):
        result = self.lookup_field(element_id, "ID", None)
        JsonLookup.validate_returned_count(result, element_id, count)
        return result

    def _get_all_dicts(self):
        entrylist = []
        for key in self.__dict__.keys():
            if key.endswith("_json"):
                root_json_key, json_dict = getattr(self, key)
                entrylist.extend(json_dict[root_json_key])
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
    RECIPES_STRING_TEMPLATE = "<b><i>[Possible {recipe_type}]:</b><i>" + FILLER
    RECIPE_LINE_TEMPLATE = "<i> + [<b>{recipe_name}{recipe_item_aspects}] - </b> {aspects_needed_to_craft}{punctuation}{additional_item_string}</i>"
    ADDITIONAL_ITEM_TEMPLATE = "{additional_items}"

    def __init__(self, recipe_type="recipes"):
        self.type = recipe_type
        self.description_lines = []

    def add_recipe_line(self, recipe_name, aspects_needed_to_craft, recipe_item_aspects=[], additional_item=[]):
        dictionary_to_add = {"recipe_name": recipe_name,
                             "recipe_item_aspects": recipe_item_aspects,
                             "aspects_needed_to_craft": aspects_needed_to_craft,
                             "additional_item": additional_item}
        self.description_lines.append(dictionary_to_add)
        return self.description_lines

    def __str__(self):
        string_representation = []
        for line in self.description_lines:
            punctuation = ""
            if line["aspects_needed_to_craft"] and line["additional_item"]:
                punctuation = ", "
            item_aspect_string = " (" + ", ".join(
                line["recipe_item_aspects"]) + ") " if line["recipe_item_aspects"] else ""

            string_representation.append(Recipe.RECIPE_LINE_TEMPLATE.format(
                recipe_name=line["recipe_name"],
                recipe_item_aspects=item_aspect_string,
                aspects_needed_to_craft=", ".join(
                    line["aspects_needed_to_craft"]),
                punctuation=punctuation,
                additional_item_string=", ".join(
                    line["additional_item"])))

        if string_representation:
            return Recipe.RECIPES_STRING_TEMPLATE.format(recipe_type=self.type) + FILLER.join(string_representation)
        else:
            return ""

    def __repr__(self):
        return self.__str__()


ASPECTS_LOOKUP = JsonLookup(LOCATION_OF_READING_ASPECTS_JSON)
PROTOTYPES_LOOKUP = JsonLookup(LOCATION_OF_PROTOTYPES)
SKILLS_LOOKUP = JsonLookup(LOCATION_OF_SKILLS_JSON)
LESSONS_LOOKUP = JsonLookup(*LOCATION_OF_LESSONS_JSON)
TECH_TREE_LOOKUP = JsonLookup(LOCATION_OF_WISDOM_COMMITMENTS_JSON)
CRAFTING_RECIPES_LOOKUP = JsonLookup(*LOCATION_OF_CRAFTING_RECIPES)
COOKING_RECIPES_LOOKUP = JsonLookup(LOCATION_OF_COOKING_RECIPES)
SOULFRAGMENT_LOOKUP = JsonLookup(LOCATION_OF_ABILITY_JSON)
ORDER_DESCRIPTION_LOOKUP = JsonLookup(LOCATION_OF_ORDERING_DESCRIPTION_JSON)
ORDER_RECIPE_LOOKUP = JsonLookup(*LOCATION_OF_ORDERING_DETAILS_JSON)
VISITOR_SUMMON_LOOKUP = JsonLookup(
    LOCATION_OF_SUMMONINGVISITOR_REQUIREMENTS_JSON)
