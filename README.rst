==================
Barrenero Telegram
==================

Telegram bot for Barrenero that serves information and provides interactive methods through Barrenero API.

:Version: 1.0.0
:Status: Production/Stable
:Author: José Antonio Perdiguero López

This bot provides a real time interaction with Barrenero through its API, allowing a simple way to register an user in the API and link it to a Telegram chat. 
Once the registration is done, it's possible to query for Barrenero status, restart services and performs any action allowed in the API.

Full `documentation <http://barrenero.readthedocs.io>`_ for Barrenero project.

Help us Donating
----------------

This project is free and open sourced, you can use it, spread the word, contribute to the codebase and help us donating:

:Ether: 0x566d41b925ed1d9f643748d652f4e66593cba9c9
:Bitcoin: 1Jtj2m65DN2UsUzxXhr355x38T6pPGhqiA

Requirements
------------

* Python 3.5 or newer. Download `here <https://www.python.org/>`_.
* Docker. `Official docs <https://docs.docker.com/engine/installation/>`_.


Quick start
-----------
1. Register a new telegram bot following `these instructions <https://core.telegram.org/bots#creating-a-new-bot>`_ and save the token to use it when installing.

2. Install services:
    
    .. code:: console

        sudo ./make install --path=/usr/local/lib/barrenero <token_from_previous_step>

3. Move to installation folder:

    .. code:: console

        cd /usr/local/lib/barrenero/barrenero-telegram/

4. (Optional) Configure parameters in *setup.cfg* file.

5. Build the service:

    .. code:: console

        ./make build

6. Reboot or restart Systemd unit:

    .. code:: console

        sudo service barrenero_telegram restart

7. Add the bot to your Telegram chat and configure it using `/start` command.

Systemd
-------

The project provides a service file for Systemd that will be installed. These service files gives a reliable way to run
each miner, as well as overclocking scripts.

To check a miner service status:

.. code:: console

    service barrenero_telegram status

Run manually
------------

As well as using systemd services you can run miners manually using:

.. code:: console

    ./make run
