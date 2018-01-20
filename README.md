# Barrenero Telegram

Telegram bot for Barrenero that serves information and provides interactive methods through Barrenero API.

* **Version**: 1.0.0
* **Status**: Production/Stable
* **Author**: José Antonio Perdiguero López

This bot provides a real time interaction with Barrenero through its API, allowing a simple way to register an user in the API and link it to a Telegram chat. 
Once the registration is done, it's possible to query for Barrenero status, restart services and performs any action allowed in the API.

Full [documentation](http://barrenero.readthedocs.io) for Barrenero project.

Help us Donating
----------------

This project is free and open sourced, you can use it, spread the word, contribute to the codebase and help us donating:

* **Ether**: `0x566d41b925ed1d9f643748d652f4e66593cba9c9`
* **Bitcoin**: `1Jtj2m65DN2UsUzxXhr355x38T6pPGhqiA`
* **PayPal**: `barrenerobot@gmail.com`

Requirements
------------

* Docker. [Official docs](https://docs.docker.com/engine/installation/).

Quick start
-----------
1. Register a new telegram bot following [these instructions](https://core.telegram.org/bots#creating-a-new-bot) and save the token to use it when installing.
2. Run the service: `docker run -v /etc/barrenero/barrenero-telegram/:/etc/barrenero/barrenero-telegram/ perdy/barrenero-telegram:latest start`
3. Add the bot to your Telegram chat and configure it using `/start` command.
