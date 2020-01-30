# Twitch Plays Arena
Welcome to *Twitch Plays Arena*, the exciting user-vote-based Magic Arena experience.

This software will run a twitch bot on your computer that will allow strangers on the internet help you lose games of Magic: The Gathering, Arena.

You will want to first set up a [twitch stream](twitch.tv) from which you will broadcast games of Magic: Arena. Users on your channel will click positions on the screen (using a provided twitch extension) to vote on the next game action.

## Getting Started

### Set up your environment
You must use a Windows machine capable of running Magic: Arena. Install python, and setup a virtual environment:

```
virtualenv -p python3 venv
source venv/Scripts/activate
pip install -r requirements.txt
```

### Set up the twitch bot

The *arena_bot* sends messages to your twitch stream chat. To set it up, you will need to configure it with an oauth token.

Generate an oauth token here:

https://twitchapps.com/tmi/
```
cp arena_bot/tpa-sample.ini arena_bot/tpa.ini
vim arena_bot/tpa.ini # Add your oath token
```

Twitch operates at:
```
irc://irc.chat.twitch.tv:6697
```

#### Bot Docs
guide:
https://dev.twitch.tv/docs/irc/guide/#join

reference:
https://dev.twitch.tv/docs/irc


## Running Twitch-Plays-Arena
The program consists of three binaries: (1) a twitch *extension* for gathering user click votes and sends them to (2) a twitch extension *backend* that aggregates user votes and sends them to (3) an MTG *arena_bot* that tallies votes and controls screen clicks.

### Running the Extension
TODO

### Running the Backend
TODO

### Running the Arena Bot
```
python arena_bot/mouse_web_controller.py --help
```
Or, see the configuration in `.vscode/launch.json` and modify as needed.

