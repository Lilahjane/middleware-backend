


discovery to be done. 
how to logically lay out the execution of modules 
the scraper recived a recipe (the scraper is an api)
how do I error check it for empty recipes or recipes with errors
how do i tell my program that when the user (as described above) saves a recipe to add an id to the recope json then split the json into 4  saving one original copy to 'raw' table (the saving of the scraped json as a whole can be saved temparaily )
and then seperating the ingredients and nutrients from the original json so the can be sanitized
how does all this stuff work



order of how i want everything done
1. somehow add error handling to scraper it needs to check if the response has a value other than null in the error key and then go check if the ingredients array is empty Because sometimes there will be no error but if there are no ingredients for the recipe then the recipe is useless and needs to be marked But if there is an error present that error needs to be displayed and if there is no error present and the ingredients Array is empty then it needs to an empty error and all of that stuff needs to be logged But no assertion of a recipe ID There needs to be an error id So the response for an empty or errored Should be a timestamp The URL if applicable And the error which could be the error that's actually present within the response object or it could be a response predefined because the recipe is empty
2. Then once error handling is checked and the recipe passed I need some way to add confirmation possibly another end point that when the recipe is scraped assign a recipe ID My thought process is is that making assigning an ID a separate end point when I call the scrape end point I could then call the assign ID endpoint so in the future when there's a user interface the ID assertion would happen there (Please note if the recipe errors there is no recipe ID that ID becomes an error ID And no further steps should be taken)  
3. Somehow simulate the process of the response from the scraper getting split into multiple components As you can tell in my files present in my directory and the code Macros get split and then they get sanitized where it removes letters or anything like that and then is technically ready for a database once I build it because I'm not ready yet
4. With ingredients I still need to understand how that logic works Some ingredients are getting named wrong and getting assigned the wrong FDC ID and needs to be double checked I don't quite understand what A git controlled ingredient registry does and how that even works
5. And I want to be able to see all of my separate modules for just handling a recipe and getting it prepared for a database would look like how they would all talk to one another how to get the order of steps down so that way they execute properly

Once all of that is done


make fake application to simulate data flow(html css and js nothing big something to just show me the process visually)

1. url input from scraper
2. implement a checker for error handling 
3. have application display error messages or json data 
4. allow for me to 'save' to simulate  assigning a primary key recipe id splitting the json normalizing ingredints and sanitizing macros
5. allow for yeild scaling (show visually the math behind the scenes as ingredients get higher amounts)
6. show combonation of like ingredients simulating grocery list 