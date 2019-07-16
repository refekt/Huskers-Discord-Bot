dm_str = 'Direct Message'
correct_channel = False


async def check_command_channel(command, channel):
    # Debugging
    print("***\nCommand: {}\nChannel: {}\nChannel ID: {}\n***\n".format(command, channel, channel.id))

    # Bot Spam channel ID
    bot_spam_id = 593984711706279937

    # Commands and Channel IDs for CrootBot based commands
    croot_commands = ['crootbot', 'referee', 'cb_search', 'recentballs']
    croot_channels = [593984711706279937, 507520543096832001, 443822461759520769]

    # Commands and Channel ID for Vexillology
    flag_commands = ['crappyflag']
    flag_channels = [597900461483360287, 442047437561921548]

    global correct_channel
    flag = False

    if dm_str in str(channel):
        flag = True
    else:
        if str(command) in croot_commands and channel.id in croot_channels:
            flag = True
        elif str(command) in flag_commands and channel.id in flag_channels:
            flag = True
        elif bot_spam_id == channel.id:
            flag = True

    correct_channel = flag

    # Debugging
    # print("Flag: {}\n".format(flag))