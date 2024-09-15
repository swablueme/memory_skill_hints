from constants import *
import json
import re

def load_json(file):
    path = BOH_PATH + file
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        file_read = f.read()
        return json.loads(file_read)

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


ASPECTS_LOOKUP = JsonLookup(
    "elements", LOCATION_OF_READING_ASPECTS_JSON)
SKILLS_LOOKUP = JsonLookup("elements", LOCATION_OF_SKILLS_JSON)
LESSONS_LOOKUP = JsonLookup("elements", *LOCATION_OF_LESSONS_JSON)
TECH_TREE_LOOKUP = JsonLookup(
    "recipes",  LOCATION_OF_WISDOM_COMMITMENTS_JSON)
RECIPES_LOOKUP = JsonLookup("recipes", *LOCATION_OF_RECIPES)
SOULFRAGMENT_LOOKUP = JsonLookup("elements", LOCATION_OF_ABILITY_JSON)