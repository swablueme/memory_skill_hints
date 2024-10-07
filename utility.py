from constants import *
import json
import re
import functools


def load_json(file):
    path = BOH_PATH + file
    # JSON files in Book of Hours are in a variety of encodes - also make sure to run the json through a validator if it fails to load
    for encode in ["utf-8", "utf-16", "utf-16le"]:
        try:
            with open(path, "r", encoding=encode) as f:
                json_loaded = json.loads(f.read())
                print(f"{path} loading succeded for encoding: {encode}")
                return json_loaded, encode
        except:
            print(f"{path} loading failed for encoding: {encode}")


class LoadedJson:
    def __init__(self, file):
        self.encode = ""
        self.mutated_elements = []

        self.root_json_key_folder_name, self.file_name_patched = file.split(
            "\\")
        self.file_name_patched = self.file_name_patched.replace(
            ".", "_") + "_patched.json"

        self.json_file_dense, self.encode = load_json(file)
        # we want a sparse json with only the changes

        self.json_file_sparse = load_json(file)[0]
        self.json_file_sparse[self.root_json_key_folder_name] = self.mutated_elements

    def get_json(self):
        return self.json_file_dense

    def get_json_elements(self):
        return self.json_file_dense[self.root_json_key_folder_name]

    def save_edited_element(self, element):
        self.mutated_elements.append(element)

    def save_file_sparse(self):
        f = open(self.file_name_patched, "w", encoding=self.encode)
        f.write(json.dumps(self.json_file_sparse, ensure_ascii=False))
        f.close()

    def save_file_dense(self):
        f = open(self.file_name_patched, "w", encoding=self.encode)
        f.write(json.dumps(self.json_file_dense, ensure_ascii=False))
        f.close()


class JsonLookup:
    def __init__(self, *elements):
        for element in elements:
            root_json_key_folder_name, json_name = element.split("\\")
            variable_name = json_name.replace(".", "_")
            setattr(self, variable_name,
                    (root_json_key_folder_name, LoadedJson(element).get_json()))

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

    @functools.cache
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

    def add_recipe_line(self, recipe_name, aspects_needed_to_craft, recipe_item_aspects="", additional_item=[]):
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
            item_aspect_string = " (" + line["recipe_item_aspects"] + \
                ") " if line["recipe_item_aspects"] else ""

            string_representation.append(Recipe.RECIPE_LINE_TEMPLATE.format(
                recipe_name=line["recipe_name"],
                recipe_item_aspects=item_aspect_string,
                aspects_needed_to_craft=line["aspects_needed_to_craft"],
                punctuation=punctuation,
                additional_item_string=", ".join(
                    line["additional_item"])))

        if string_representation:
            return Recipe.RECIPES_STRING_TEMPLATE.format(recipe_type=self.type) + FILLER.join(string_representation)
        else:
            return ""

    def __repr__(self):
        return self.__str__()


class Aspects:
    def __init__(self, aspects):
        self.aspects = aspects
        self.additional_aspects = []

    def html(self):
        return ", ".join([ASPECT_TEMPLATE.format(
            aspect=aspect, aspect_power=value) for (aspect, value) in self.aspects]) + self._str_additional_aspects()

    def _str_additional_aspects(self):
        if self.additional_aspects:
            return ", " + ", ".join(self.additional_aspects)
        else:
            return ""

    def __str__(self):
        return ", ".join([aspect + ": " + str(value) for (aspect, value)
                          in self.aspects]) + self._str_additional_aspects()

    def extend_additional_aspects(self, values):
        self.additional_aspects.extend(values)


ASPECTS_LOOKUP = JsonLookup(LOCATION_OF_READING_ASPECTS_JSON)
BASE_LOOKUP = JsonLookup(*LOCATION_OF_PROTOTYPES_BASEASPECTS)
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
