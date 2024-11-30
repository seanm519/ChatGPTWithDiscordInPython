# ChatGPTWithDiscordInPython

This is the Class Assistant portion of the OwlTA Project.

The Class Assistant is responsible for all interactions with students reguarding lesson material.
This includes:
    Answering questions
    Answering questions based on lesson material
    identifying commonly asked questions and explaining them in depth
    summarizing lectures


Key Points:
    This project was created in Python
    Pytesseract for text-extraction of an image
    blobText for parsing a text doccument to find commonly asked questions


How can I impliment this discord bot into my own server?
You will need:
    Python's Tesseract: https://pypi.org/project/pytesseract/ take note of where you install this.
        once downloaded and installed this must be added to your system's PATH
            open Control Panel -> at the top right search for "PATH" -> click "edit the system environment variables" -> then click the "environment variables" button
                once the menu opens there should be a table that says "System variables" , double-click on the variable that says "path"
                    now open file explorer and find your Tesseract-OCR folder where you installed it, the default location might be in your Program Files
                        hold shift and right-click the folder and choose the option that says "copy as path"
                    you can close out of file explorer and go back to the edit environment variable table.
                choose the "new" option and paste the path you copied, make sure to delete the parenthasis that gets pasted into the field.
            your new path should look like C:\Program Files\Tesseract-OCR
        you can now close out of all windows and control panel and restart your computer to let these changes take effect.

Additionaly you will need to provide your own .env file for the discord bot token and chatGPT api key
the variables are as follows:
DISCORD_TOKEN=
OPENAI_API_KEY=

When starting the program the bot will send a message introducing itself and explaining how to interact with it.
    Some commands can only be accessed with a role called "Professor" these are commands that only the professor should have access to.