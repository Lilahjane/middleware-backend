Getting Started
The Ingredient Parser package is a Python package for parsing structured information from recipe ingredient sentences.
The following parts of an ingredient sentence can be extracted:
Field
Description
name
The name of the ingredient, or names if multiple names are given.
size
A size modifier for the ingredient, such as small or large.
This size modifier only applies to the ingredient name, not the unit.
amount
The amounts parsed from the sentence. Each amount has a quantity and a unit, plus additional flags that provide extra information about the amount.
Where possible units are given as pint.Unit objects, which allows for convenient programmatic manipulation such as conversion to other units.
preparation
The preparation notes for the ingredient.
comment
The comment from the ingredient sentence, such as examples or asides.
purpose
The purpose of the ingredient, such as for garnish.
foundation foods
The entry or entries from the Food Data Central database matching the ingredient name. See Foundation Foods for more details.
Note that this is not extracted by default, but can be enabled using the foundation_foods keyword argument.

Installation
You can install Ingredient Parser from PyPi with pip:
$ python -m pip install ingredient_parser_nlp


Ingredient Parser depends on the following
python-crfsuite
NLTK
Pint
Numpy
Usage
The primary functionality of this package is provided by the parse_ingredient function.
This function takes a single ingredient sentence and returns a ParsedIngredient object containing the extracted information.
from ingredient_parser import parse_ingredient
parse_ingredient("3 pounds pork shoulder, cut into 2-inch chunks")
ParsedIngredient(
    name=[IngredientText(text='pork shoulder',
                         confidence=0.996256,
                         starting_index=2)],
    size=None,
    amount=[IngredientAmount(quantity=Fraction(3, 1),
                             quantity_max=Fraction(3, 1),
                             unit=<Unit('pound')>,
                             text='3 pounds',
                             confidence=0.999829,
                             starting_index=0,
                             unit_system=<UnitSystem.US_CUSTOMARY: 'us_customary'>,
                             APPROXIMATE=False,
                             SINGULAR=False,
                             RANGE=False,
                             MULTIPLIER=False,
                             PREPARED_INGREDIENT=False)],
    preparation=IngredientText(text='cut into 2 inch chunks',
                               confidence=0.999803,
                               starting_index=5),
    comment=None,
    purpose=None,
    foundation_foods=[],
    sentence='3 pounds pork shoulder, cut into 2-inch chunks'
)


Each of the fields (except sentence) has a confidence value associated with it. This is a value between 0 and 1, where 0 represents no confidence and 1 represent full confidence. This is the confidence that the natural language model has that the given label is correct, averaged across all tokens that contribute to that particular field.
Tip
The companion webtools has a parser tool that can be used to test the library’s functionality.
Options
The parse_ingredient function has the following optional boolean parameters:
separate_names
Default: True
If the ingredient sentence includes multiple alternative ingredient names, return each name separately.
Example
parse_ingredient("2 tbsp olive oil or butter").name
[
    IngredientText(text='olive oil', confidence=0.990395, starting_index=2),
    IngredientText(text='butter', confidence=0.998547, starting_index=5)
]


If disabled, the name field will be a list containing a single IngredientText object.
Example
parse_ingredient("2 tbsp olive oil or butter", separate_names=False).name
[
    IngredientText(text='olive oil or butter', confidence=0.994275, starting_index=2)
]


discard_isolated_stop_words
Default: True
Discard stop words that appear in isolation within the name, preparation, size, purpose or comment fields.
Example
parse_ingredient("2 tbsp of olive oil").comment
None


If disabled, then all words from the input sentence are retained in the parsed output.
Example
parse_ingredient("2 tbsp of olive oil", discard_isolated_stop_words=False).comment
IngredientText(text='of', confidence=0.915292)


expect_name_in_output
Default: True
Sometimes a name isn’t identified in the ingredient sentence, often due to the sentence structure being unusual or the sentence contains an ingredient name that is ambiguous. For these cases, attempt to find the most likely name even if the words making that name are considered more likely to belong to a different field of the ParsedIngredient object.
A minimum confidence threshold applies, meaning this does not guarantee a name is identified.
If disabled, when encountering such sentences the name field will be empty.
string_units
Default: False
Units in the IngredientAmount objects are returned pint.Unit objects, which allows for convenient manipulation programmatically.
Example
parse_ingredient("250 g plain flour").amount[0].unit
<Unit('gram')>


If set to True, the IngredientAmount unit will be the string identified from the sentence.
Example
parse_ingredient("250 g plain flour", string_units=True).amount[0].unit
'g'


imperial_units
Deprecated since version v2.5.0: This keyword argument will be removed in a future version.
Use the volumetric_units_system="imperial" for the same functionality.
Default: False
Some units have have multiple definitions versions with the same name but representing different quantities, such as fluid ounces, cups, pints, quarts or gallons.
pint.Unit objects are assumed to be the US customary version of the unit unless this is set to True.
Example
parse_ingredient("2 pints chicken stock").amount[0].unit
<Unit('pint')>

parse_ingredient("2 pints chicken stock", imperial_units=True).amount[0].unit
<Unit('imperial_pint')>


This option has no effect if string_units=True.
volumetric_units_system
Default: us_customary
Some units have have multiple definitions with the same name but representing different quantities, such as fluid ounces, cups, pints, quarts or gallons.
The following options are available to select between the different systems.
Options
Description
us_customary
Uses the US customary definitions for the following units:
gallon, quart, fluid ounce pint, cup, tablespoon, teaspoon.
imperial
Uses the Imperial definitions for the following units:
gallon, quart, fluid ounce pint, cup, tablespoon, teaspoon.
metric
Uses metric definitions for the following units:
cup (250 ml), tablespoon (15 ml), teaspoon (5 ml).
australian
Uses the Australian definitions for the following units:
pint (570 ml), tablespoon (20 ml).
Uses metric defintions for cup and teaspoon.
japanese
Uses the Japanese definitions for the following units:
cup (200 ml).

This option has no effect if string_units=True.
foundation_foods
Default: False
Food Data Central is a database of foods and their nutritional properties. If enabled, the ingredient names are matched to entries in the FDC database and returned as a list of FoundationFood objects in the foundation_foods field of the ParsedIngredient object. See the Foundation Foods page for more details.
This is disabled by default and the foundation_foods field is an empty list
Examples
This page lists a number of example that showcase the capability of the library, and also highlights some limitations.
Basic example
A basic example to show the full output from parse_ingredient().
parse_ingredient("1 large red onion, finely diced")
ParsedIngredient(name=[IngredientText(text='red onion',
                                      confidence=0.994235,
                                      starting_index=2)],
                 size=IngredientText(text='large',
                                     confidence=0.997111,
                                     starting_index=1),
                 amount=[IngredientAmount(quantity=Fraction(1, 1),
                                          quantity_max=Fraction(1, 1),
                                          unit='',
                                          text='1',
                                          confidence=0.999933,
                                          starting_index=0,
                                          unit_system=<UnitSystem.NONE: 'none'>,
                                          APPROXIMATE=False,
                                          SINGULAR=False,
                                          RANGE=False,
                                          MULTIPLIER=False,
                                          PREPARED_INGREDIENT=False)],
                 preparation=IngredientText(text='finely diced',
                                            confidence=0.998908,
                                            starting_index=5),
                 comment=None,
                 purpose=None,
                 foundation_foods=[],
                 sentence='1 large red onion, finely diced')


Multiple amounts
A common pattern used in ingredient sentences is to specify amounts in terms of a fixed size item, e.g. 2 28 ounce cans. In these cases, the outer amount (2 cans) and inner amount (28 ounce) are separated. The inner amount has the SINGULAR flag set to True to indicate that it applies to a singular item of the outer amount.
parse_ingredient("2 28 ounce cans whole tomatoes")
ParsedIngredient(name=[IngredientText(text='whole tomatoes',
                                      confidence=0.999044,
                                      starting_index=4)],
                 size=None,
                 amount=[IngredientAmount(quantity=Fraction(2, 1),
                                          quantity_max=Fraction(2, 1),
                                          unit='cans',
                                          text='2 cans',
                                          confidence=0.999825,
                                          starting_index=0,
                                          unit_system=<UnitSystem.OTHER: 'other'>,
                                          APPROXIMATE=False,
                                          SINGULAR=False,
                                          RANGE=False,
                                          MULTIPLIER=False,
                                          PREPARED_INGREDIENT=False),
                         IngredientAmount(quantity=Fraction(28, 1),
                                          quantity_max=Fraction(28, 1),
                                          unit=<Unit('ounce')>,
                                          text='28 ounces',
                                          confidence=0.999437,
                                          starting_index=1,
                                          unit_system=<UnitSystem.US_CUSTOMARY: 'us_customary'>,
                                          APPROXIMATE=False,
                                          SINGULAR=True,
                                          RANGE=False,
                                          MULTIPLIER=False,
                                          PREPARED_INGREDIENT=False)],
                 preparation=None,
                 comment=None,
                 purpose=None,
                 foundation_foods=[],
                 sentence='2 28 ounce cans whole tomatoes')


Approximate amounts
Approximate amounts, indicate by the use of words like approximately, about, roughly etc., have the APPROXIMATE flag set.
parse_ingredient("4 pork chops, about 400 g each")
ParsedIngredient(name=[IngredientText(text='pork chops',
                                      confidence=0.9961,
                                      starting_index=1)],
                 size=None,
                 amount=[IngredientAmount(quantity=Fraction(4, 1),
                                          quantity_max=Fraction(4, 1),
                                          unit='',
                                          text='4',
                                          confidence=0.999876,
                                          starting_index=0,
                                          unit_system=<UnitSystem.NONE: 'none'>,
                                          APPROXIMATE=False,
                                          SINGULAR=False,
                                          RANGE=False,
                                          MULTIPLIER=False,
                                          PREPARED_INGREDIENT=False),
                         IngredientAmount(quantity=Fraction(400, 1),
                                          quantity_max=Fraction(400, 1),
                                          unit=<Unit('gram')>,
                                          text='400 g',
                                          confidence=0.995449,
                                          starting_index=5,
                                          unit_system=<UnitSystem.METRIC: 'metric'>,
                                          APPROXIMATE=True,
                                          SINGULAR=True,
                                          RANGE=False,
                                          MULTIPLIER=False,
                                          PREPARED_INGREDIENT=False)],
                 preparation=None,
                 comment=None,
                 purpose=None,
                 foundation_foods=[],
                 sentence='4 pork chops, about 400 g each')


Prepared ingredients
The order in which the amount, name and preparation instructions are given can change the amount of the ingredient specified by the sentence.
For example, 1 cup flour, sifted instructs the chef to measure 1 cup of flour and then sift it. Conversely, 1 cup sifted flour instructs the chef to sift flour to obtain 1 cup, which would have a different mass to the first case. For this second case, the PREPARED_INGREDIENT flag will be set to True.
parse_ingredient("1 cup flour, sifted")
ParsedIngredient(name=[IngredientText(text='flour',
                                      confidence=0.998215,
                                      starting_index=2)],
                 size=None,
                 amount=[IngredientAmount(quantity=Fraction(1, 1),
                                          quantity_max=Fraction(1, 1),
                                          unit=<Unit('cup')>,
                                          text='1 cup',
                                          confidence=0.999959,
                                          starting_index=0,
                                          unit_system=<UnitSystem.US_CUSTOMARY: 'us_customary'>,
                                          APPROXIMATE=False,
                                          SINGULAR=False,
                                          RANGE=False,
                                          MULTIPLIER=False,
                                          PREPARED_INGREDIENT=False)],
                 preparation=IngredientText(text='sifted',
                                            confidence=0.999754,
                                            starting_index=4),
                 comment=None,
                 purpose=None,
                 foundation_foods=[],
                 sentence='1 cup flour, sifted')

parse_ingredient("1 cup sifted flour")
ParsedIngredient(name=[IngredientText(text='flour',
                                      confidence=0.986433,
                                      starting_index=3)],
                 size=None,
                 amount=[IngredientAmount(quantity=Fraction(1, 1),
                                          quantity_max=Fraction(1, 1),
                                          unit=<Unit('cup')>,
                                          text='1 cup',
                                          confidence=0.99918,
                                          starting_index=0,
                                          unit_system=<UnitSystem.US_CUSTOMARY: 'us_customary'>,
                                          APPROXIMATE=False,
                                          SINGULAR=False,
                                          RANGE=False,
                                          MULTIPLIER=False,
                                          PREPARED_INGREDIENT=True)],
                 preparation=IngredientText(text='sifted',
                                            confidence=0.990133,
                                            starting_index=2),
                 comment=None,
                 purpose=None,
                 foundation_foods=[],
                 sentence='1 cup sifted flour')


Alternative ingredients
Sometimes an ingredient sentence will include a number of alternative ingredients that can be used in the same quantities.
The library attempts to ensure that each of the identified ingredient names makes sense on it’s own. For example in the sentence 2 tbsp olive or sunflower oil, it would be incorrect to identify the two ingredient names as olive and sunflower oil. The actual names are olive oil and sunflower oil.
parse_ingredient("2 tbsp olive or sunflower oil")
ParsedIngredient(name=[IngredientText(text='olive oil',
                                      confidence=0.989134,
                                      starting_index=2),
                       IngredientText(text='sunflower oil',
                                      confidence=0.982565,
                                      starting_index=4)],
                 size=None,
                 amount=[IngredientAmount(quantity=Fraction(2, 1),
                                          quantity_max=Fraction(2, 1),
                                          unit=<Unit('tablespoon')>,
                                          text='2 tbsps',
                                          confidence=0.999819,
                                          starting_index=0,
                                          unit_system=<UnitSystem.US_CUSTOMARY: 'us_customary'>,
                                          APPROXIMATE=False,
                                          SINGULAR=False,
                                          RANGE=False,
                                          MULTIPLIER=False,
                                          PREPARED_INGREDIENT=False)],
                 preparation=None,
                 comment=None,
                 purpose=None,
                 foundation_foods=[],
                 sentence='2 tbsp olive or sunflower oil')


Alternative ingredients with different amounts
Sometimes a single ingredient sentence will contain multiple phrases, each specifying a different ingredient with a different amount.
Limitation
This library assumes an ingredient sentence does not contain different ingredients with different amounts.
For cases where the sentence contains multiple phrases, specifying different ingredients in different amounts, everything after the first phrase will be returned in the comment field.
parse_ingredient("1 cup peeled and cooked fresh chestnuts (about 20), or 1 cup canned, unsweetened chestnuts")
ParsedIngredient(name=[IngredientText(text='fresh chestnuts',
                                  confidence=0.977679,
                                  starting_index=5)],
             size=None,
             amount=[IngredientAmount(quantity=Fraction(1, 1),
                                      quantity_max=Fraction(1, 1),
                                      unit=<Unit('cup')>,
                                      text='1 cup',
                                      confidence=0.999549,
                                      starting_index=0,
                                      unit_system=<UnitSystem.US_CUSTOMARY: 'us_customary'>,
                                      APPROXIMATE=False,
                                      SINGULAR=False,
                                      RANGE=False,
                                      MULTIPLIER=False,
                                      PREPARED_INGREDIENT=True),
                     IngredientAmount(quantity=Fraction(20, 1),
                                      quantity_max=Fraction(20, 1),
                                      unit='',
                                      text='20',
                                      confidence=0.887524,
                                      starting_index=9,
                                      unit_system=<UnitSystem.NONE: 'none'>,
                                      APPROXIMATE=True,
                                      SINGULAR=False,
                                      RANGE=False,
                                      MULTIPLIER=False,
                                      PREPARED_INGREDIENT=False)],
             preparation=IngredientText(text='peeled and cooked',
                                        confidence=0.999523,
                                        starting_index=2),
             comment=IngredientText(text='or 1 cup canned, unsweetened '
                                         'chestnuts',
                                    confidence=0.925894,
                                    starting_index=12),
             purpose=None,
             foundation_foods=[],
             sentence='1 cup peeled and cooked fresh chestnuts (about 20), '
                      'or 1 cup canned, unsweetened chestnuts')


Alternative unit systems
Volumetric units can vary in different parts of the world, for example the volume of a “cup” is different in the USA, UK and other countries.
When handling volumetric units, US customary units are assumed by default but this can be changed to a different volumetric unit system.
parse_ingredient("2 cups boiled water")
ParsedIngredient(name=[IngredientText(text='water',
                                      confidence=0.823288,
                                      starting_index=3)],
                 size=None,
                 amount=[IngredientAmount(quantity=Fraction(2, 1),
                                          quantity_max=Fraction(2, 1),
                                          unit=<Unit('cup')>,
                                          text='2 cups',
                                          confidence=0.999709,
                                          starting_index=0,
                                          unit_system=<UnitSystem.US_CUSTOMARY: 'us_customary'>,
                                          APPROXIMATE=False,
                                          SINGULAR=False,
                                          RANGE=False,
                                          MULTIPLIER=False,
                                          PREPARED_INGREDIENT=True)],
                 preparation=IngredientText(text='boiled',
                                            confidence=0.833938,
                                            starting_index=2),
                 comment=None,
                 purpose=None,
                 foundation_foods=[],
                 sentence='2 cups boiled water')

parse_ingredient("2 cups boiled water", volumetric_units_system="imperial")
ParsedIngredient(name=[IngredientText(text='water',
                                      confidence=0.823288,
                                      starting_index=3)],
                 size=None,
                 amount=[IngredientAmount(quantity=Fraction(2, 1),
                                          quantity_max=Fraction(2, 1),
                                          unit=<Unit('imperial_cup')>,
                                          text='2 cups',
                                          confidence=0.999709,
                                          starting_index=0,
                                          unit_system=<UnitSystem.IMPERIAL: 'imperial'>,
                                          APPROXIMATE=False,
                                          SINGULAR=False,
                                          RANGE=False,
                                          MULTIPLIER=False,
                                          PREPARED_INGREDIENT=True)],
                 preparation=IngredientText(text='boiled',
                                            confidence=0.833938,
                                            starting_index=2),
                 comment=None,
                 purpose=None,
                 foundation_foods=[],
                 sentence='2 cups boiled water')


Limitation
This library only handles individual ingredient sentences, which means there will not ever be a way to automatically detect the correct volumetric unit system.
Foundation foods
A basic example to show the full output from parse_ingredient when foundation_foods=True.
parse_ingredient("1 large red onion, finely diced", foundation_foods=True)
ParsedIngredient(name=[IngredientText(text='red onion',
                                      confidence=0.994235,
                                      starting_index=2)],
                 size=IngredientText(text='large',
                                     confidence=0.997111,
                                     starting_index=1),
                 amount=[IngredientAmount(quantity=Fraction(1, 1),
                                          quantity_max=Fraction(1, 1),
                                          unit='',
                                          text='1',
                                          confidence=0.999933,
                                          starting_index=0,
                                          unit_system=<UnitSystem.NONE: 'none'>,
                                          APPROXIMATE=False,
                                          SINGULAR=False,
                                          RANGE=False,
                                          MULTIPLIER=False,
                                          PREPARED_INGREDIENT=False)],
                 preparation=IngredientText(text='finely diced',
                                            confidence=0.998908,
                                            starting_index=5),
                 comment=None,
                 purpose=None,
                 foundation_foods=[
                    FoundationFood(text='Onions, red, raw',
                                   confidence=1.0,
                                   fdc_id=790577,
                                   category='Vegetables and Vegetable Products',
                                   data_type='foundation_food',
                                   url='https://fdc.nal.usda.gov/food-details/790577/nutrients',
                                   name_index=0)
                 ],
                 sentence='1 large red onion, finely diced')
Convert between units
Where possible, IngredientAmount units are returned as a pint.Unit. This allows easy programmatic conversion between different units.
Prerequisites
Programmatic conversion of units is only possible if none of the quantity, quantity_max and unit fields are str.
The convert_to function of IngredientAmount accepts the units to convert to and, optionally, a density if the conversion is between mass and volume.
amount = parse_ingredient("1.2 kg lamb shank").amount[0]
amount.convert_to("lbs")
IngredientAmount(quantity=Fraction(66138678655463271, 25000000000000000),
    quantity_max=Fraction(66138678655463271, 25000000000000000),
    unit=<Unit('pound')>,
    text='2.65 pound',
    confidence=0.99986,
    starting_index=0,
    unit_system=<UnitSystem.US_CUSTOMARY: 'us_customary'>,
    APPROXIMATE=False,
    SINGULAR=False,
    RANGE=False,
    MULTIPLIER=False,
    PREPARED_INGREDIENT=False
)


The unit parameter of convert_to must a unit recognised by Pint.
CompositeIngredientAmount also supports unit conversion. In this case, the convert_to function return a pint.Quantity object which is the combined quantity converted to the given units.
amount = parse_ingredient("1lb 2 oz lamb shank").amount[0]
amount.convert_to("kg")
<Quantity(255145708125000060785923700000001/500000000000000000000000000000000, 'kilogram')>


The convert_to function of CompositeIngredientAmount is the same as doing
CompositeIngredientAmount.combined().to(unit)


however it also supports conversion between mass and volume as described below.
Converting between mass and volume
It is quite common for recipes that use US customary units to give amounts in units of volume for ingredients, such as flour and sugar, where other recipes more commonly use units of mass. Conversion between these units is possible, but requires a density value to enable the conversion.
The density value can be provided as an optional argument to convert_to and must be given as a pint.Quantity. The default value is the density of water: 1000 kg/m3.
amount = parse_ingredient("1 cup water").amount[0]
# Using default density value
amount.convert_to("g")
IngredientAmount(quantity=236.58823649999997,
    quantity_max=236.58823649999997,
    unit=<Unit('gram')>,
    text='236.588 gram',
    confidence=0.999943,
    starting_index=0,
    unit_system=<UnitSystem.METRIC: 'metric'>,
    APPROXIMATE=False,
    SINGULAR=False,
    RANGE=False,
    MULTIPLIER=False,
    PREPARED_INGREDIENT=False
)


amount = parse_ingredient("2 cups all purpose flour").amount[0]
# Using custom density value: 1 cup flour = 120 g
amount.convert_to("g", density=120 * UREG("g/cup"))
IngredientAmount(quantity=240.0,
    quantity_max=240.0,
    unit=<Unit('gram')>,
    text='240 gram',
    confidence=0.999949,
    starting_index=0,
    unit_system=<UnitSystem.METRIC: 'metric'>,
    APPROXIMATE=False,
    SINGULAR=False,
    RANGE=False,
    MULTIPLIER=False,
    PREPARED_INGREDIENT=False
)


Attention
When converting between mass and volume, the quantity values are convert to float.
This is a result of how Pint handles the conversion.
Resources such as King Arthur Baking’s Ingredient Weight Chart are helpful in providing the densities for various ingredients commonly used in baking.
Logging
Python’s standard logging module is used to implement debug log output for ingredient-parser. This allows ingredient-parser’s logging to integrate in a standard way with other application and libraries.
All logging for ingredient-parser is within ingredient-parser namespace.
The ingredient-parser namespace contains general logging for parsing of ingredient sentences.
The ingredient-parser.foundation-foods namespace contains logging related to the Foundation Foods functionality.
For example, to output debug logs to stdout:
import logging, sys
from ingredient_parser import parse_ingredient

logging.basicConfig(stream=sys.stdout)
logging.getLogger("ingredient-parser").setLevel(logging.DEBUG)

parsed = parse_ingredient("24 fresh basil leaves or dried basil")
DEBUG:ingredient-parser:Parsing sentence "24 fresh basil leaves or dried basil" using "en" parser.
DEBUG:ingredient-parser:Normalised sentence: "24 fresh basil leaves or dried basil".
DEBUG:ingredient-parser:Tokenized sentence: ['24', 'fresh', 'basil', 'leaf', 'or', 'dried', 'basil'].
DEBUG:ingredient-parser:Singularised tokens at indices: [3].
DEBUG:ingredient-parser:Generating features for tokens.
DEBUG:ingredient-parser:Sentence token labels: ['QTY', 'B_NAME_TOK', 'I_NAME_TOK', 'I_NAME_TOK', 'NAME_SEP', 'B_NAME_TOK', 'I_NAME_TOK'].


Only enabling logging for foundation foods:
import logging, sys
from ingredient_parser import parse_ingredient

logging.basicConfig(stream=sys.stdout)
logging.getLogger("ingredient-parser.foundation-foods").setLevel(logging.DEBUG)

parsed = parse_ingredient("24 fresh basil leaves or dried basil", foundation_foods=True)
DEBUG:ingredient-parser.foundation-foods:Matching FDC ingredient for ingredient name tokens: ['fresh', 'basil', 'leaves']
DEBUG:ingredient-parser.foundation-foods:Prepared tokens: ['fresh', 'basil', 'leav'].
DEBUG:ingredient-parser.foundation-foods:Loaded 13318 FDC ingredients.
DEBUG:ingredient-parser.foundation-foods:Selecting best match from 1 candidates based on preferred FDC datatype.
DEBUG:ingredient-parser.foundation-foods:Matching FDC ingredient for ingredient name tokens: ['dried', 'basil']
DEBUG:ingredient-parser.foundation-foods:Prepared tokens: ['dri', 'basil'].
DEBUG:ingredient-parser.foundation-foods:Selecting best match from 1 candidates based on preferred FDC datatype.


Parsers
ingredient_parser.parsers.inspect_parser(sentence: str, lang: str = 'en', separate_names: bool = True, discard_isolated_stop_words: bool = True, expect_name_in_output: bool = True, string_units: bool = False, imperial_units: bool = False, volumetric_units_system: str = 'us_customary', foundation_foods: bool = False) → ParserDebugInfo
[source]
Return intermediate objects generated during parsing for inspection.
Parameters:
sentencestr
Ingredient sentence to parse.
langstr
Language of sentence. Currently supported options are: en.
separate_namesbool, optional
If True and the sentence contains multiple alternative ingredients, return an IngredientText object for each ingredient name, otherwise return a single IngredientText object. Default is True.
discard_isolated_stop_wordsbool, optional
If True, any isolated stop words in the name, preparation, or comment fields are discarded. Default is True.
expect_name_in_outputbool, optional
If True, if the model doesn’t label any words in the sentence as the name, fallback to selecting the most likely name from all tokens even though the model gives it a different label. Note that this does guarantee the output contains a name. Default is True.
string_unitsbool
If True, return all IngredientAmount units as strings. If False, convert IngredientAmount units to pint.Unit objects where possible. Default is False.
imperial_unitsbool
If True, use imperial units instead of US customary units for pint.Unit objects for the the following units: fluid ounce, cup, pint, quart, gallon. Default is False, which results in US customary units being used. This has no effect if string_units=True.
Deprecated since version v2.5.0: Use volumetric_units_system="imperial" for the same functionality.
volumetric_units_systemstr, optional
Sets the units system for volumetric measurements, like “cup” or “tablespoon”. Available options are “us_customary” (default), “imperial”, “metric”, “australian”, “japanese”. This has no effect if string_units=True.
Added in version v2.5.0.
foundation_foodsbool, optional
If True, extract foundation foods from ingredient name. Foundation foods are the fundamental foods without any descriptive terms, e.g. ‘cucumber’ instead of ‘organic cucumber’. Default is False.
Returns:
ParserDebugInfo
ParserDebugInfo object containing the PreProcessor object, PostProcessor object and Tagger.
ingredient_parser.parsers.parse_ingredient(sentence: str, lang: str = 'en', separate_names: bool = True, discard_isolated_stop_words: bool = True, expect_name_in_output: bool = True, string_units: bool = False, imperial_units: bool = False, volumetric_units_system: str = 'us_customary', foundation_foods: bool = False) → ParsedIngredient
[source]
Parse an ingredient sentence to return structured data.
Parameters:
sentencestr
Ingredient sentence to parse.
langstr
Language of sentence. Currently supported options are: en.
separate_namesbool, optional
If True and the sentence contains multiple alternative ingredients, return an IngredientText object for each ingredient name, otherwise return a single IngredientText object. Default is True.
discard_isolated_stop_wordsbool, optional
If True, any isolated stop words in the name, preparation, or comment fields are discarded. Default is True.
expect_name_in_outputbool, optional
If True, if the model doesn’t label any words in the sentence as the name, fallback to selecting the most likely name from all tokens even though the model gives it a different label. Note that this does guarantee the output contains a name. Default is True.
string_unitsbool, optional
If True, return all IngredientAmount units as strings. If False, convert IngredientAmount units to pint.Unit objects where possible. Default is False.
imperial_unitsbool, optional
If True, use imperial units instead of US customary units for pint.Unit objects for the the following units: fluid ounce, cup, pint, quart, gallon. Default is False, which results in US customary units being used. This has no effect if string_units=True.
Deprecated since version v2.5.0: Use volumetric_units_system="imperial" for the same functionality.
volumetric_units_systemstr, optional
Sets the units system for volumetric measurements, like “cup” or “tablespoon”. Available options are “us_customary” (default), “imperial”, “metric”, “australian”, “japanese”. This has no effect if string_units=True.
Added in version v2.5.0.
foundation_foodsbool, optional
If True, extract foundation foods from ingredient name. Foundation foods are the fundamental foods without any descriptive terms, e.g. ‘cucumber’ instead of ‘organic cucumber’. Default is False.
Returns:
ParsedIngredient
ParsedIngredient object of structured data parsed from input string.
ingredient_parser.parsers.parse_multiple_ingredients(sentences: Iterable[str], lang: str = 'en', separate_names: bool = True, discard_isolated_stop_words: bool = True, expect_name_in_output: bool = True, string_units: bool = False, imperial_units: bool = False, volumetric_units_system: str = 'us', foundation_foods: bool = False) → list[ParsedIngredient]
[source]
Parse multiple ingredient sentences in one go.
This function accepts a list of sentences, with element of the list representing one ingredient sentence. A list of dictionaries is returned, with optional confidence values. This function is a simple for-loop that iterates through each element of the input list.
Parameters:
sentencesIterable[str]
Iterable of sentences to parse.
langstr
Language of sentence. Currently supported options are: en.
separate_namesbool, optional
If True and the sentence contains multiple alternative ingredients, return an IngredientText object for each ingredient name, otherwise return a single IngredientText object. Default is True.
discard_isolated_stop_wordsbool, optional
If True, any isolated stop words in the name, preparation, or comment fields are discarded. Default is True.
expect_name_in_outputbool, optional
If True, if the model doesn’t label any words in the sentence as the name, fallback to selecting the most likely name from all tokens even though the model gives it a different label. Note that this does guarantee the output contains a name. Default is True.
string_unitsbool
If True, return all IngredientAmount units as strings. If False, convert IngredientAmount units to pint.Unit objects where possible. Default is False.
imperial_unitsbool
If True, use imperial units instead of US customary units for pint.Unit objects for the the following units: fluid ounce, cup, pint, quart, gallon. Default is False, which results in US customary units being used. This has no effect if string_units=True.
Deprecated since version v2.5.0: Use volumetric_units_system="imperial" for the same functionality.
volumetric_units_systemstr, optional
Sets the units system for volumetric measurements, like “cup” or “tablespoon”. Available options are “us_customary” (default), “imperial”, “metric”, “australian”, “japanese”. This has no effect if string_units=True.
Added in version v2.5.0.
foundation_foodsbool, optional
If True, extract foundation foods from ingredient name. Foundation foods are the fundamental foods without any descriptive terms, e.g. ‘cucumber’ instead of ‘organic cucumber’. Default is False.
Returns:
list[ParsedIngredient]
List of ParsedIngredient objects of structured data parsed from input sentences.
Preprocess
class ingredient_parser.en.preprocess.PreProcessor(input_sentence: str)
[source]
Recipe ingredient sentence PreProcessor class.
Performs the necessary preprocessing on a sentence to generate the features required for the ingredient parser model.
Each input sentence goes through a cleaning process to tidy up the input into a standardised form.
Parameters:
input_sentencestr
Input ingredient sentence.
Attributes:
inputstr
Input ingredient sentence.
sentencestr
Input ingredient sentence, cleaned to standardised form.
singularised_indiceslist[int]
Indices of tokens in tokenized sentence that have been converted from plural to singular
tokenized_sentencelist[Token]
Tokenised ingredient sentence.
Methods
sentence_features()
Return dict of features for each token in sentence.

Notes
The cleaning steps are as follows
Replace all en-dashes and em-dashes with hyphens.
Replace numbers given as words with the numeric equivalent.
e.g. one >> 1
Replace fractions given in html markup with the unicode representation.
e.g. &frac12; >> ½
Replace unicode fractions with the equivalent decimal form. Decimals are
rounded to a maximum of 3 decimal places.
e.g. ½ >> 0.5
Identify fractions represented by 1/2, 2/3 etc. by replaceing the slash with $
and the prepending # in front of the fraction e.g. #1$2
e.g. 1/2 >> 0.5
A space is enforced between quantities and units
Remove trailing periods from units
e.g. tsp. >> tsp
Numeric ranges indicated in words using “to” or “or” are replaced with a
standard numeric form
e.g. 1 or 2 >> 1-2; 10 to 12 >> 10-12
Units are made singular. This step uses a predefined list of plural units and
their singular form.
Following the cleaning of the input sentence, it is tokenized into a list of tokens.
Each token is one of the following
A word, including most punctuation marks
Opening or closing parentheses, braces, brackets; comma; speech marks
The features for each token are computed on demand using the sentence_features method, which returns a list of dictionaries. Each dictionary is the feature set for each token.
The sentence features can then be passed to the CRF model which will generate the parsed output.
sentence_features() → list[dict[str, str | bool]]
[source]
Return dict of features for each token in sentence.
Returns:
list[FeatureDict]
List of feature dicts for each token in sentence.
Postprocess
class ingredient_parser.en.postprocess.PostProcessor(sentence: str, tokens: list[str], pos_tags: list[str], labels: list[str], scores: list[float], separate_names: bool = True, discard_isolated_stop_words: bool = True, string_units: bool = False, volumetric_units_system: str = 'us_customary', foundation_foods: bool = False)
[source]
Recipe ingredient sentence PostProcessor class.
Performs the necessary postprocessing on the sentence tokens and labels and scores for the tokens after tagging with the CRF model in order to return a coherent structure of parsed information.
Attributes:
sentencestr
Original ingredient sentence.
tokenslist[str]
List of tokens for original ingredient sentence.
pos_tagslist[str]
List of part of speech tags for tokens.
labelslist[str]
List of labels for tokens.
scoreslist[float]
Confidence associated with the label for each token.
separate_namesbool, optional
If True and the sentence contains multiple alternative ingredients, return an IngredientText object for each ingredient name, otherwise return a single IngredientText object. Default is True.
discard_isolated_stop_wordsbool, optional
If True, isolated stop words are discarded from the name, preparation or comment fields. Default value is True.
string_unitsbool, optional
If True, return all IngredientAmount units as strings. If False, convert IngredientAmount units to pint.Unit objects where possible. Default is False.
imperial_unitsbool, optional
If True, use imperial units instead of US customary units for pint.Unit objects for the the following units: fluid ounce, cup, pint, quart, gallon. Default is False, which results in US customary units being used. This has no effect if string_units=True.
foundation_foodsbool, optional
If True, populate the foundation_foods field of ParsedIngredient. Default is False, in which case the foundation_foods field is an empty list.
consumedlist[int]
List of indices of tokens consumed as part of postprocesing the tokens and labels.
property parsed: ParsedIngredient
[source]
Return parsed ingredient data.
Returns:
ParsedIngredient
Object containing structured data from sentence.
Common
ingredient_parser._common.consume(iterator: Iterator, n: int | None) → None
[source]
Advance the iterator n-steps ahead. If n is none, consume entirely.
See consume from https://docs.python.org/3/library/itertools.html#itertools-recipes
Parameters:
iteratorIterator
Iterator to advance.
nint | None
Number of iterations to advance by. If None, consume entire iterator.
Examples
it = iter(range(10))
consume(it, 3)
next(it)
3


it = iter(range(10))
consume(it, None)
next(it)
StopIteration


ingredient_parser._common.download_nltk_resources() → None
[source]
Check if required nltk resources can be found and if not, download them.
ingredient_parser._common.group_consecutive_idx(idx: list[int]) → Generator[Iterator[int], None, None]
[source]
Yield groups of consecutive indices.
Given a list of integers, yield groups of integers where the value of each in a group is adjacent to the previous element’s value.
Parameters:
idxlist[int]
List of indices.
Yields:
list[list[int]]
List of lists, where each sub-list contains consecutive indices.
Examples
groups = group_consecutive_idx([0, 1, 2, 4, 5, 6, 8, 9])
[list(g) for g in groups]
[[0, 1, 2], [4, 5, 6], [8, 9]]


ingredient_parser._common.is_float(value: str) → bool
[source]
Check if value can be converted to a float.
Parameters:
valuestr
Value to check.
Returns:
bool
True if the value can be converted to float, else False.
Examples
is_float("3")
True


is_float("2.5")
True


is_float("1-2")
False


ingredient_parser._common.is_range(value: str) → bool
[source]
Check if value is a range e.g. 100-200.
Parameters:
valuestr
Value to check.
Returns:
bool
True if the value is a range, else False.
Examples
is_range("1-2")
True


is_float("100-500")
True


is_float("1")
False


ingredient_parser._common.show_model_card(lang: str = 'en') → None
[source]
Open model card for specified language in default application.
Parameters:
langstr, optional
Selected language to open model card for.
Raises:
FileNotFoundError
Raised if model card not found at expected path.
ValueError
Raised if unsupported language provided in lang argument.
Dataclasses
class ingredient_parser.dataclasses.UnitSystem(*values)
[source]
Enum defining unit systems
METRIC = 'metric'
US_CUSTOMARY = 'us_customary'
IMPERIAL = 'imperial'
AUSTRALIAN = 'australian'
JAPANESE = 'japanese'
OTHER = 'other'
NONE = 'none'
class ingredient_parser.dataclasses.CompositeIngredientAmount(amounts: list[IngredientAmount], join: str, subtractive: bool)
[source]
Dataclass for a composite ingredient amount.
This is an amount comprising more than one IngredientAmount object e.g. “1 lb 2 oz” or “1 cup plus 1 tablespoon”.
Attributes:
amountslist[IngredientAmount]
List of IngredientAmount objects that make up the composite amount. The order in this list is the order they appear in the sentence.
joinstr
String of text that joins the amounts, e.g. “plus”.
subtractivebool
If True, the amounts combine subtractively. If False, the amounts combine additively.
textstr
Composite amount as a string, automatically generated the amounts and join attributes.
confidencefloat
Confidence of parsed ingredient amount, between 0 and 1. This is the average confidence of all tokens that contribute to this object.
starting_indexint
Index of token in sentence that starts this amount.
unit_systemUnitSystem
Unit system (e.g. metric) that the unit of the amount belongs to.
Methods
combined()
Return the combined amount in a single unit for the composite amount.
convert_to(unit, density)
Convert units of the combined CompositeIngredientAmount object to given unit.

combined() → Quantity
[source]
Return the combined amount in a single unit for the composite amount.
The amounts that comprise the composite amount are combined according to whether the composite amount is subtractive or not. The combined amount is returned as a pint.Quantity object.
Returns:
pint.Quantity
Combined amount.
Raises:
TypeError
Raised if any of the amounts in the object do not comprise a float quantity and a pint.Unit unit. In these cases, they amounts cannot be combined.
convert_to(unit: str, density: Quantity = <Quantity(1000.0, 'kilogram / meter ** 3')>) → Quantity
[source]
Convert units of the combined CompositeIngredientAmount object to given unit.
Conversion is only possible if none of the quantity, quantity_max and unit are strings.
Conversion between mass and volume is supported using the density parameter, but otherwise a DimensionalityError is raised if attempting to convert units of different dimensionality.
Warning
When a conversion between mass <-> volume is performed, the quantities will be converted to floats.
Parameters:
unitstr
Unit to convert to.
densitypint.Quantity, optional
Density used for conversion between volume and mass. Default is the density of water.
Returns:
pint.Quantity
Combined amount converted to given units.
class ingredient_parser.dataclasses.FoundationFood(text: str, confidence: float, fdc_id: int, category: str, data_type: str, name_index: int)
[source]
Dataclass for the attributes of an entry in the Food Data Central database.
Attributes:
textstr
Description FDC database entry.
confidencefloat
Confidence of the match, between 0 and 1.
fdc_idint
ID of the FDC database entry.
categorystr
Category of FDC database entry.
data_typestr
Food Data Central data set the entry belongs to.
urlstr
URL for FDC database entry.
name_indexint
Index of associated name in ParsedIngredient.name list.
class ingredient_parser.dataclasses.IngredientAmount(quantity: Fraction | str, quantity_max: Fraction | str, unit: str | Unit, text: str, confidence: float, starting_index: int, APPROXIMATE: bool = False, SINGULAR: bool = False, RANGE: bool = False, MULTIPLIER: bool = False, PREPARED_INGREDIENT: bool = False)
[source]
Dataclass for holding a parsed ingredient amount.
On instantiation, the unit is made plural if necessary.
Attributes:
quantityFraction | str
Parsed ingredient quantity, as a Fraction where possible, otherwise a string. If the amount if a range, this is the lower limit of the range.
quantity_maxFraction | str
If the amount is a range, this is the upper limit of the range. Otherwise, this is the same as the quantity field. This is set automatically depending on the type of quantity.
unitstr | pint.Unit
Unit of parsed ingredient quantity. If the quantity is recognised in the pint unit registry, a pint.Unit object is used.
textstr
String describing the amount e.g. “1 cup”, “8 oz”
confidencefloat
Confidence of parsed ingredient amount, between 0 and 1. This is the average confidence of all tokens that contribute to this object.
starting_indexint
Index of token in sentence that starts this amount
unit_systemUnitSystem
Unit system (e.g. metric) that the unit of the amount belongs to.
APPROXIMATEbool, optional
When True, indicates that the amount is approximate. Default is False.
SINGULARbool, optional
When True, indicates if the amount refers to a singular item of the ingredient. Default is False.
RANGEbool, optional
When True, indicates the amount is a range e.g. 1-2. Default is False.
MULTIPLIERbool, optional
When True, indicates the amount is a multiplier e.g. 1x, 2x. Default is False.
PREPARED_INGREDIENTbool, optional
When True, indicates the amount applies to the prepared ingredient. When False, indicates the amount applies to the ingredient before preparation. Default is False.
Methods
convert_to(unit, density)
Convert units of IngredientAmount object to given unit.

convert_to(unit: str, density: Quantity = <Quantity(1000.0, 'kilogram / meter ** 3')>)
[source]
Convert units of IngredientAmount object to given unit.
Conversion is only possible if none of the quantity, quantity_max and unit are strings.
Conversion between mass and volume is supported using the density parameter, but otherwise a DimensionalityError is raised if attempting to convert units of different dimensionality.
Warning
When a conversion between mass <-> volume is performed, the quantities will be converted to floats.
Parameters:
unitstr
Unit to convert to.
densitypint.Quantity, optional
Density used for conversion between volume and mass. Default is the density of water.
Returns:
Self
Copy of IngredientAmount object with units converted to given unit.
Raises:
TypeError
Raised if unit, quantity or quantity_max are str
class ingredient_parser.dataclasses.IngredientText(text: str, confidence: float, starting_index: int)
[source]
Dataclass for holding a parsed ingredient string.
Attributes:
textstr
Parsed text from ingredient. This is comprised of all tokens with the same label.
confidencefloat
Confidence of parsed ingredient text, between 0 and 1. This is the average confidence of all tokens that contribute to this object.
starting_indexint
Index of token in sentence that starts this text
class ingredient_parser.dataclasses.ParsedIngredient(name: list[IngredientText], size: IngredientText | None, amount: list[IngredientAmount | CompositeIngredientAmount], preparation: IngredientText | None, comment: IngredientText | None, purpose: IngredientText | None, foundation_foods: list[FoundationFood], sentence: str)
[source]
Dataclass for holding the parsed values for an input sentence.
Attributes:
namelist[IngredientText]
List of IngredientText objects, each representing an ingreident name parsed from input sentence. If no ingredient names are found, this is an empty list.
sizeIngredientText | None
Size modifier of ingredients, such as small or large. If no size modifier, this is None.
amountList[IngredientAmount | CompositeIngredientAmount]
List of IngredientAmount objects, each representing a matching quantity and unit pair parsed from the sentence. If no ingredient amounts are found, this is an empty list.
preparationIngredientText | None
Ingredient preparation instructions parsed from sentence. If no ingredient preparation instruction was found, this is None.
commentIngredientText | None
Ingredient comment parsed from input sentence. If no ingredient comment was found, this is None.
purposeIngredientText | None
The purpose of the ingredient parsed from the sentence. If no purpose was found, this is None.
foundation_foodslist[FoundationFood]
List of foundation foods from the parsed sentence.
sentencestr
Normalised input sentence
class ingredient_parser.dataclasses.ParserDebugInfo(sentence: str, PreProcessor: Any, PostProcessor: Any, tagger: Tagger)
[source]
Dataclass for holding intermediate objects generated during parsing.
Attributes:
sentencestr
Input ingredient sentence.
PreProcessorPreProcessor
PreProcessor object created using input sentence.
PostProcessorPostProcessor
PostProcessor object created using tokens, labels and scores from input sentence.
Taggerpycrfsuite.Tagger
CRF model tagger object.
class ingredient_parser.dataclasses.Token(index: int, text: str, feat_text: str, pos_tag: str, features: TokenFeatures)
[source]
Dataclass representing a token from a ingredient sentence.
Attributes:
indexint
Index of the token in the sentence.
textstr
Token text.
feat_textstr
Token text used for feature generation.
pos_tagstr
Part of speech tag for token.
featuresTokenFeatures
Common features for token.
class ingredient_parser.dataclasses.TokenFeatures(stem: str, shape: str, is_capitalised: bool, is_unit: bool, is_punc: bool, is_ambiguous_unit: bool)
[source]
Dataclass for common token features.
Attributes:
stemstr
Stem of the token.
shapestr
Shape of the token, represented by X, x, d characters.
is_capitalisedbool
True if the token starts with a capital letter, else False.
is_unitstr
True if the token is in the list of units, else False.
is_puncstr
True if the token is a punctuation character, else False.
is_ambiguous_unitstr
True if the token is in the list of ambiguous units, else False.
Foundation Foods
ingredient_parser.en.foundationfoods.match_foundation_foods(tokens: list[str], pos_tags: list[str], name_idx: int) → FoundationFood | None
[source]
Match ingredient name to foundation foods from FDC ingredient.
This is done in three stages. The first stage prepares and normalises the tokens.
The second stage uses an Unsupervised Smooth Inverse Frequency calculation to down select the possible candidate matching FDC ingredients.
The third stage selects the best of these candidates using a fuzzy embedding document metric.
The need for two stages is that the ingredient embeddings do not seem to be as accurate as off the shelf pre-trained general embeddings are for general tasks. Improving the quality of the embeddings might remove the need for the second stage.
Parameters:
tokenslist[str]
Ingredient name tokens.
pos_tagslist[str]
POS tags for tokens.
name_idxint
Index of corresponding name in ParsedIngredient.names list.
Returns:
FoundationFood|None

