# These files are found in BOOK OF HOURS\bh_Data\StreamingAssets\bhcontent\core\elements
# Some of them won't validate correctly in a json validator and others may have random unicode characters in places
# So use a validator and read the validated json instead of accessing the jsons in that directory directly if you have issues
LOCATION_OF_TOMES_JSON = r"elements\tomes.json"
LOCATION_OF_LESSONS_JSON = r"elements\xlessons.json", r"elements\xlessons_unique.json"
LOCATION_OF_ABILITY_JSON = r"elements\abilities.json"
LOCATION_OF_READING_ASPECTS_JSON = r"elements\aspecteditems.json"
LOCATION_OF_WISDOM_COMMITMENTS_JSON = r"recipes\wisdom_commitments.json"
LOCATION_OF_SKILLS_JSON = r"elements\skills.json"
LOCATION_OF_CRAFTING_RECIPES = r"recipes\crafting_2_keeper.json", r"recipes\crafting_3_scholar.json", r"recipes\crafting_4b_prentice.json"
LOCATION_OF_COOKING_RECIPES = r"recipes\DLC_HOL_cooking.json"
LOCATION_OF_WRITING_CASE_RECIPES = r"recipes\DLC_HOL_manuscripting_write.json"

# In the xtrigger section of the json, it always starts with stuff like reading.edge or mastering.edge etc
# Can use regex to recognise these patterns
READING_XTRIGGER_PATTERN = r"^reading\..*$"
MASTERING_XTRIGGER_PATTERN = r"^mastering\.(.*)$"

TECH_TREE_PATH_NAME_PATTERN = r"^w\.(.*)$"
TECH_TREE_SOUL_FRAGMENT_PATTERN = r"^a\.(.*)$"

ID_PATTERN_GROUP = "id_pattern"
# eg commit.hus.s.thegreatsignsandthegreatscars
WISDOM_PATTERN = fr"^commit\.[A-Za-z]+\.(?P<{ID_PATTERN_GROUP}>.*)$"

# All the memory attributes are included including boost and sound, so we do not want these
REMOVE_BOOST_ABILITIES_PATTERN = r"^(boost\..*|sound|ability|s\..*|e\..*|omen)$"
ASPECTS_PATTERN = r"(edge|forge|grail|heart|knock|lantern|moon|moth|nectar|rose|scale|sky|winter)"
COOKING_INGREDIENTS = r"^(?!ingredient$).*$"

# This is the name of the json file that we create
SAVED_TOMES_FILE = r"tomes_json_patched.json"
SAVED_SKILLS_FILE = r"skills_json_patched.json"
SAVED_CORRESPONDENCE_FILE = r"correspondence_elements_json_patched.json"
SAVED_ASPECT_ITEMS_FILE = r"aspecteditems_json_patched.json"
# These are various string templates to match what we want
FILLER = "\r\n"
ASPECT_TEMPLATE = "<sprite name={aspect}> {aspect_power}"
# Path to your game files
BOH_PATH = "D:\\games\\BOOK OF HOURS\\bh_Data\\StreamingAssets\\bhcontent\\core\\"
