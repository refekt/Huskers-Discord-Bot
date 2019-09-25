dm_str = 'Direct Message'
correct_channel = False


async def check_command_channel(command: str, channel):
    global correct_channel

    croot_commands = ["crootbot", "referee", "cb_search", "recentballs", "cb_refresh"]
    flag_commands = ["crappyflag", "randomflag"]
    mkv_commands = ["markov", "channelmarkov"]
    all_commands = croot_commands + flag_commands + mkv_commands

    # print("Checking command [${}]".format(command))

    if str(command) not in all_commands:
        # print("Command [${}] doesn't need to be regulated".format(command))
        correct_channel = True
        return

    # print("Regulated command found. Checking channel [#{}]".format(channel))

    #   Production Server:...
    #   the-war-room = 525519594417291284
    #   💯🌽👊 scotts-tots = 507520543096832001
    #   bot-spam = 593984711706279937
    #   runza = 442047437561921548
    #   football = 443822461759520769
    #   vexillology = 597900461483360287
    # Test Server:
    #   discussion = 606655884340232192
    #   spam = 595705205069185047

    bot_spam_channels = [595705205069185047, 593984711706279937, 442047437561921548]
    croot_channels = [525519594417291284, 507520543096832001, 443822461759520769, 538419127535271946]
    flag_channels = [597900461483360287]
    all_channels = bot_spam_channels + croot_channels + flag_channels

    if dm_str in str(channel):
        flag = True
    elif channel.id in all_channels:
        flag = True
    else:
        flag = False

    # print("Regulation of [${}] == [{}]".format(command, flag))
    correct_channel = flag
