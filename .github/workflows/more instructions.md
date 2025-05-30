

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
* Added LLM selection ability
* Build version check when opening app
* Fixed Bug  where accessibility information was not available after giving permissions
* 
