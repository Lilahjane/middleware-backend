This project is a possible implementation of the middleware and back end layer of a meal planner
At the heart of this project is to be able to scrape recipes off the Internet normalize their ingredients Have the application be able to create grocery lists using those normalized ingredients.

# dir refrence
- docs: overall Information explaining what the project is
- macro-parsing:  not implemented In the future it will be what normalizes nutrient values
- normalizer: Powered by Ingredient Normalizer NLP it takes a list of ingredients and uses Natural Language processing to parse Information out of the strings (IE: Quantity unit ingredient core ingredient)
- OG-scraper: The heart of the application It is what allows for recipe collection and feeds all other modules in this project
- source: stores The data as it goes through its many Stages of parsing in json mostly for refernce of structure and data visability 
- splitters: What splits the scrapers output into its different sections so Separations of concerns is maintained
- utils: Holds the script to add an id To every recipe object


### main issue point
the normalizer is not implemented correctly. it has many issues In the file normalized/observed_issues_possible_solutions.Md There is an audit done on source/normalized-ingredients.json  Bringing to light Issues with recipe confidence and  issues with Math that could disrupt future grocery list functions. normalizer/ingredient-normalizer.py Requires immenidiet repair and testing to make sure the next phase can rollout 


devlopment phases
phase 1 Define, parse and normalize recipes: This phase is breaking out the Json output provided from the scraper and visualizing data structure making sure that the data reflects the features that implemented in the final application
phase 2 Feature function testing stress testing data structures: As this phase suggests We are simulating user interaction and fine tuning how are will be used in the final application making sure that all logic works all features are fully implemented and tested. Stress test ingredient quantity unit integration Making sure Ingredient scale for yields Making sure ingredients and all ingredients variations are matched to the same food item garlic cloved And cloves a spice are not the same thing and could mess up a grocery list if not caught
phase 3: Schema implementation and front end connection: Once data structure define tested and works with all features The data structure will then be implemented into a database and everything can be connected to build a full stack app By phase three the database API routes functions and all middleware components should be fully completed



