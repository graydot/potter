

Add tests for important functionality. ie, if open api key is not present, settings page opens up. it opens up if accessibility perm is not given. cancel and apply buttons close the dialogs (settings and also create/edit prompt dialogs etc). Also check individual functionality to make the app functionality as verfied as possible since we are going to refactor next. 



refactor to be modular. i think potter.py does a lot of things. firstly refactor to be elegant by moving to aptly named functions etc. Then create new files and classes as needed to make it elegant. refactor to remove duplicate code (small blocks are ok, think like a staff engineer)Then run tests. 

login fuinctionality does nto work. add status check, and move to a separate function iof it isn't already
verify keyboard conflict and move to a separate function if it insnt already

token limits. 
click on icon to process
version check when existing instance is running. have a random build id - not working

default prompt and setting config valuse seem to be in code files
show error if settings window cannot be created and terminate. 



Release Notes
* Changed default to cmd + shift + a
* Changed Settings UI
* Added support for multiple llms
* Build version check when opening app. Kills older version app after confirming. 
* Fixed Bug  where accessibility information was not available after giving permissions - the app restarts on permission change
* left click starts llm processing (in case you want to use app without giving permissions)
* Other UI fixes and improvements


More Bugs/Features
* Move Quit below cancel and save buttons
* When i refresh permissions, the app asks me to restart despite there being no changes
* the pills are not calculating sizes correctly. for cmd, shift and a, all the last chars are cut off. 
* the settings panes are all scrolled to the bottom. so i have to scroll up to see stuff.
* reduee the size of the prompts table. 
* move the add/delete buttons to the bottom of teh table using osx patters. ie, have a + and - in the table iteself. doubleclicing should edit the item
* Add some more logging, such as app started, permissions checked, which are avaible etc. the logs right now are empty. 
* also i had asked you to find a way to allow recording by clicking on the menu bar icon. do you think we could right click to open settings and a left click initiates llm processing?

Add a verify llm setup button which sends a test message to the llm and verifies that it works. - done

add functionality which shows the error message in the drop down menu bar if there is an error. and shows an exclamation mark on the menu bar icon. - done



it looks like other clients are not implemmented actually. validation only checks format. - done

need to adjust green/red marker closeness to labes for perms
move the log file text box a bit up
log files isn't showing everything that is hsowing in terminal. which is wierd. maybe debug output is not betting saved

i also ahven't tested permissions
clicking on menu bar icon should start recording
move code to a single place so that we can use this with ios app too
menu bar drop downs clicked should open settings
the first access one doesn't need to mention too many detaisl. 
doesn't log when combo is hit, so i don't know if it is detecting. it worked once.

delte old code such as potter original
settings file is too big.
Add functionality which counts tokens before sending so we don't get token errors. shows error text in the menu bar.. details in next line. 
logo update plus also the settings page icon
also update with latest model names












