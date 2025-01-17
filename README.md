# bb_app chat gpt prompt:

Alright I'm working to create a "Patient's Reaction Form" using html. The form would involve displaying Antigram information stored in the app's database and allowing the user to input reactions for every cell in the antigram, saving the antigram's Lot Number, Cell number, Antigen, Reaction & patients reaction to some sort of Patient Reaction Profile object/entity which would store this information. This information would then be used to run some filter/formula to display ABID Results Display field / Summarizing the ABID. Does this make sense? 

I am creating a Flask app, and there are many components I am invisioning with this type of application. I was thinking it would have the Antigram Finder Search Bar at the top which allowed the user to filter by antrigram lot number. Each antigram lot number would be display in a row with an Select Antigram Button, when clicked this would open up an Patient Reaction Input Form. The user would then input reactions for some of the cells in the antigram. I would need to save  the Patient Reaction Input Form data, specifically the selected antigrams Lot Number, antigrams Cell Number & user input's Patient's Rxn. User could select multiple antigrams using the Select Antigram Button to save cells with patient reactions say to an Patient Reaction Profile. This would be a collection of cells the user has selected to 

From here a ruleout algorithm/filter would use the Patient Reaction Profile, implement some RULES that would Display Results/Summary at the bottom of the page. But FOR NOW, I just want to focus on creating the necessary elements in the paragraph above including the Antigram Finder Search Bar & Patient Reaction Input Form. Can you help me develop these pages with logic?

I added the following pages:
- models.py # page containing the models used to store antigram data which  is profile of cell reactions to antigen.  
- routes/antigrams.py # this file contains routes used for the databases CRUD operations.
-main.py # used to start app


Reivew the files I attached. I need help creating the routes, javascript files and html files used in the Antibody Identification page. I have an empty antibody_id.py,  antibody_id.js and antibody_id.html file I need to create to achieve the states goal above. Please help me