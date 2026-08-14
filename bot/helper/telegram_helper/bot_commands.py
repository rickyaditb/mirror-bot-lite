from ...core.config_manager import Config

i = Config.CMD_SUFFIX


class BotCommands:
    StartCommand = f"start{i}"
    MirrorCommand = [f"mirror{i}", f"m{i}"]
    LeechCommand = [f"leech{i}", f"l{i}"]
    YtdlCommand = [f"ytdl{i}", f"y{i}"]
    YtdlLeechCommand = [f"ytdlleech{i}", f"yl{i}"]
    CancelTaskCommand = [f"cancel{i}", f"c{i}"]
    CancelAllCommand = f"cancelall{i}"
    ForceStartCommand = [f"forcestart{i}", f"fs{i}"]
    StatusCommand = f"status{i}"
    UsersCommand = f"users{i}"
    AuthorizeCommand = f"auth{i}"
    UnAuthorizeCommand = f"unauth{i}"
    AddSudoCommand = f"addsudo{i}"
    RmSudoCommand = f"rmsudo{i}"
    PingCommand = f"ping{i}"
    RestartCommand = f"restart{i}"
    StatsCommand = f"stats{i}"
    HelpCommand = f"help{i}"
    LogCommand = f"log{i}"
    BotSetCommand = [f"bsetting{i}", f"bs{i}"]
    UserSetCommand = [f"usetting{i}", f"us{i}"]
    SelectCommand = f"sel{i}"
    TestCommand = [f"test{i}", f"smoketest{i}"]
