# Secured-Homework-Help-Website
## Project Overview
A secure-by-design web platform enabling students to request help and helpers to provide solutions, with credit-based interactions forming the core workflow. The application focuses on strong authentication, strict role separation, and hardened request handling to prevent common web vulnerabilities. Developed as part of Secure Programming classes, the project highlights security-focused development practices within a minimal Flask environment to demonstrate how even simple applications require robust protection and threat mitigation.
## Authors
Nolann Nougues

Piotr Szkoda

Martyna Kochalska 

## Technologies 
Website Frontend : Bootstrap
Website Backend : Python Flask
Accounts Database : PostgreSQL
Containerization : Docker (Compose)

## Installation - Windows

1. Open Command Prompt
2. Navigate to the folder where you want to load the code

3. Keep the terminal to the side for now, open a browser.
4. Head to the following code repository : https://github.com/pyskaa0506/Secured-Homework-Help-Website
5. Click on the green "Code" Button
6. Copy the URL for the Repository, HTTPS should be sufficient.

7. Return to the terminal, type ```git clone``` then paste the URL you copied
8. A new "Secured-Homework-Help-Website" folder has been created, move inside the folder with ```cd Secured-Homework-Help-Website```.
9. Then move into the source folder with ```cd source```


10. Make sure Docker Desktop is active, on Windows, Docker Desktop can be activated by simply opening it, then it can be closed and it will stay running in the background until the computer is powered off.

10. Run ```docker compose build --no-cache```, this should begin downloading images and preparing the application.

11. Access the Website prototype on a browser at the address : "http://127.0.0.1:8080" (or http://localhost:8080", then you may start interacting with the website! By registering, logging in and depending on your chosen role. Ask or answer a question!

12. To take down the containers running the website, you can run ```docker compose down -v```.

### COMMON ISSUES :

If the database container fails to create properly and there are a bunch of lines about variables defaulting to blank strings, go inside source with a file browser, and verify that the '.env' file is called as such, the error is likely to show up if the file is called 'env' instead of '.env'

If the web container fails to create properly, it is possible that it's trying to run on an already used port, a LLM is able to assist you in verifying if the port 8080 is being used by another one of your services, if it is being used by a critical service, you may need to modify the port being used manually by going into docker-compose.yml and changing the left port on line 5, the specified port on line 12 then saving the file. Next, run.py will need to have it's line 28 modified with the new port as well, do not forget to save.
