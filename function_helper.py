dm_str = 'Direct Message'
correct_channel = False


async def check_command_channel(command: str, channel):
    global correct_channel
    flag = False

    gameDay = True
    if gameDay:
        correct_channel = True
        return

    # Commands to check for
    croot_commands = ['crootbot', 'referee', 'cb_search', 'recentballs', 'cb_refresh']
    flag_commands = ['crappyflag', 'randomflag']
    commandFound = False

    for c in croot_commands:
        if str(c) == str(command):
            commandFound = True

    for cc in flag_commands:
        if str(cc) == str(command):
            commandFound = True

    # Exit function if the command isn't listed
    if not commandFound:
        return

    #   Production Server:
    #   the-war-room = 525519594417291284
    #   💯🌽👊 scotts-tots = 507520543096832001
    #   bot-spam = 593984711706279937
    #   runza = 442047437561921548
    #   football = 443822461759520769
    #   vexillology = 597900461483360287
    # Test Server:
    #   discussion = 606655884340232192
    #   spam = 595705205069185047
    bot_spam_channels = [606655884340232192, 595705205069185047, 593984711706279937, 442047437561921548]
    croot_channels = [525519594417291284, 507520543096832001, 593984711706279937, 442047437561921548, 443822461759520769, 538419127535271946]
    flag_channels = [593984711706279937, 597900461483360287, 442047437561921548]


    # All commands authorized within Direct Messages
    if dm_str in str(channel):
        flag = True
    else:
        if channel.id in bot_spam_channels:
            flag = True
        # Command is within croot_commands and the channel ID is within croot_channels
        elif str(command) in croot_commands and channel.id in croot_channels:
            flag = True
        # Command is within flag_commands and the channel ID is within flag_channels
        elif str(command) in flag_commands and channel.id in flag_channels:
            flag = True
        # All commands authorized within bot_spam_channels
    correct_channel = flag
