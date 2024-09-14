import json
import re

# These files are found in BOOK OF HOURS\bh_Data\StreamingAssets\bhcontent\core\elements
# Some of them won't validate correctly in a json validator and others may have random unicode characters in places
# So use a validator and read the validated json instead of accessing the jsons in that directory directly if you have issues
LOCATION_OF_TOMES_JSON = r"tomes.json"
LOCATION_OF_LESSIONS_JSON = r"xlessons.json", r"xlessons_unique.json"
LOCATION_OF_READING_ASPECTS_JSON = r"aspecteditems.json"

# In the xtrigger section of the json, it always starts with stuff like reading.edge or mastering.edge etc
# Can use regex to recognise these patterns
READING_XTRIGGER_PATTERN = r"^reading\..*$"
MASTERING_XTRIGGER_PATTERN = r"^mastering\..*$"

# All the memory attributes are included including boost and sound, so we do not want these
BOOST_PATTERN = r"^(boost\..*|sound)$"

# This is the name of the json file that we create
SAVED_JSONFILE = r"tomes_json_patched.json"

# These are various string templates to match what we want
READING_STRING_TEMPLATE = "<i>[Upon reading gives <b>{memory}]</b> ({memory_aspects})</i>"
MASTERY_STRING_TEMPLATE = "<i>[First mastery gives <b>{lesson}]</b>"
MEMORY_ASPECT_TEMPLATE = "<sprite name={aspect}> {aspect_power}"
FILLER = "\r\n"


def load_json(file):
    with open(file, "r", encoding="utf-8") as f:
        return json.loads(f.read())


tomes_json = load_json(LOCATION_OF_TOMES_JSON)
aspects_json = load_json(LOCATION_OF_READING_ASPECTS_JSON)

# There are two different lesson jsons so have all of them in one file
lessons_json = load_json(LOCATION_OF_LESSIONS_JSON[0])
lessons_json["elements"].extend(
    load_json(LOCATION_OF_LESSIONS_JSON[1])["elements"])


def lookup_elements_by_id(element_id, json_file):
    result = list(filter(
        lambda json_file_element: (
            json_file_element.get("ID", None) == element_id or
            json_file_element.get("id", None) == element_id),
        json_file["elements"]))

    # We only expect one entry when looking up a memory or lesson etc
    if len(result) != 1:
        raise Exception(
            f"The number of elements that match {element_id} is {len(result)}")
    return result[0]


def format_memory_description(memory_id):
    memory = lookup_elements_by_id(memory_id, aspects_json)
    description = memory["Label"]
    aspect = [MEMORY_ASPECT_TEMPLATE.format(aspect=attribute, aspect_power=value) for attribute, value in memory["aspects"].items()
              if re.match(BOOST_PATTERN, attribute) == None]
    return READING_STRING_TEMPLATE.format(memory=description, memory_aspects=", ".join(aspect))


def format_lesson_description(lesson_id):
    lesson = lookup_elements_by_id(lesson_id, lessons_json)
    description = lesson["Label"]
    return MASTERY_STRING_TEMPLATE.format(lesson=description)


def interpret_xtriggers_in_tomejson(xtriggers):
    description_string = []
    for k, read_results in xtriggers.items():
        if re.match(READING_XTRIGGER_PATTERN, k):
            for item in read_results:
                description_string.insert(
                    0, format_memory_description(item["id"]))
        elif re.match(MASTERING_XTRIGGER_PATTERN, k):
            for item in read_results:
                description_string.append(
                    format_lesson_description(item["id"]))

    # Creates the description
    if description_string:
        connector = ", " + FILLER
        return FILLER*2 + connector.join(description_string)
    else:
        raise Exception(
            f"Couldn't find a matching reading pattern {xtriggers}")


for book in tomes_json["elements"]:
    reading_description = interpret_xtriggers_in_tomejson(book["xtriggers"])
    book["Desc"] = book["Desc"] + reading_description

f = open(SAVED_JSONFILE, "w")
f.write(json.dumps(tomes_json))
f.close()
