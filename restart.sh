#!/bin/bash

echo "[*] Restarting the bot..."

#echo "... killing all python3.7 ..."
#killall python3.7

echo "[*] ~~> Starting the bot"
cd /home/botfrost/bot || exit

nohup python3.7 ./main.py prod &> /home/botfrost/bot.log &

echo "Bot started."
