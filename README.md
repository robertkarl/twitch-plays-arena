# Twitch Plays Arena

#### Use virtualenv
$ virtualenv -p python3.6 venv
$ . venv/bin/activate
(venv) $ pip install irc

#### Set up the twitch bot

Generate an oath token here:

https://twitchapps.com/tmi/
```
cp tpa-sample.ini tpa.ini
vim tpa-sample.ini # Add your oath token
```

#### 
Twitch operates at:
```
irc://irc.chat.twitch.tv:6697
```

#### Bot Docs
guide:
https://dev.twitch.tv/docs/irc/guide/#join

reference:
https://dev.twitch.tv/docs/irc

