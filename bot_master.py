from copy import deepcopy
from irc.bot import SingleServerIRCBot
import config


# @TODO worker management


class EventParser:

    @staticmethod
    def is_command(event):
        return True if event.arguments[0].startswith('!') else False

    @staticmethod
    def is_report(event):
        return True if event.arguments[0].startswith('Task') else False

    @staticmethod
    def is_status(event):
        return True if event.arguments[0].startswith('!status') else False

    @staticmethod
    def get_worker_name(event):
        return event.source.split('!')[0]

    @staticmethod
    def get_task_uid(event):
        return event.arguments[0].split()[1]

    @staticmethod
    def get_command(task):
        # @TODO refactor this method
        return ' '.join(task.split()[:-4])

    @staticmethod
    def get_number_of_executions(task):
        if '-n' not in task:
            return 1
        number = task.split().index('-n') + 1
        return int(task.split()[number])

    @staticmethod
    def get_number_of_requested_workers(task):
        if '-w' not in task:
            return 0
        number = task.split().index('-w') + 1
        return int(task.split()[number])


class BotMaster(SingleServerIRCBot):
    ADMIN_USERNAME = config.ADMIN_USERNAME
    BOTMASTER_USERNAME = config.BOTMASTER_USERNAME

    def __init__(self, channel_name, server, port=6667, nickname=BOTMASTER_USERNAME,
                 password=config.BOTMASTER_PASSWORD):
        SingleServerIRCBot.__init__(self, [(server, port)], nickname, nickname)

        self.channel_name = channel_name
        self.server = server
        self.port = port
        self.nickname = nickname
        self.password = password
        self.tasks = []

    def connect(self, *args, **kwargs):
        super(BotMaster, self).connect(self.server, self.port, self.nickname,
                                       password=self.password)

    def on_welcome(self, connection, event):
        connection.join(self.channel_name)

    def skip_workers(self):
        return [self.ADMIN_USERNAME, self.nickname, 'ChanServ']

    def get_all_workers(self):
        users = deepcopy(list(self.channels[self.channel_name].users()))
        for user in self.skip_workers():
            users.remove(user)
        return users

    @property
    def available_workers_count(self):
        return len(self.get_available_workers())

    def get_available_workers(self):
        # TODO refactor to get available workers
        return self.get_all_workers()

    def on_privmsg(self, connection, event):
        if EventParser.is_command(event):
            if EventParser.is_status(event):
                status = self.get_task_by_uid(self.get_task_by_uid(event.arguments[0].split()[1])).workers_status()
                self.send_message(connection, status, event.source.split('!')[0])
            else:
                command = event.arguments[0]
                self.dispatch_command(connection, command)
        elif EventParser.is_report(event):
            task_uid = EventParser.get_task_uid(event)
            worker_name = EventParser.get_worker_name(event)
            task = self.get_task_by_uid(task_uid)
            task.finish_worker(worker_name)

    def get_task_by_uid(self, uid):
        for task in self.tasks:
            if task.uid == uid:
                return task

    def on_pubmsg(self, connection, event):
        if EventParser.is_command(event):
            command = event.arguments[0]
            self.dispatch_command(connection, command)
        elif EventParser.is_report(event):
            task_uid = EventParser.get_task_uid(event)
            worker_name = EventParser.get_worker_name(event)
            task = self.get_task_by_uid(task_uid)
            task.finish_worker(worker_name)

    def send_message(self, connection, message, user):
        connection.privmsg(user, message)

    def get_workers(self, number_of_requested_workers):
        available_workers = self.get_available_workers()
        if number_of_requested_workers > len(available_workers):
            number_of_workers = len(available_workers)
        else:
            number_of_workers = number_of_requested_workers
        return available_workers[:number_of_workers]

    def make_message_for_task(self, task):
        message = "!" + "task {}: {} -n {}".format(task.uid, task.command, task.number_of_executions_per_worker)
        return message

    def create_task(self, command, workers):
        number_of_execution_per_worker = EventParser.get_number_of_executions(command)
        cmd = EventParser.get_command(command)
        task = Task(cmd, workers, number_of_execution_per_worker)
        return task

    def dispatch_command(self, connection, command):
        number_of_requested_workers = EventParser.get_number_of_requested_workers(
            command) or self.available_workers_count

        workers = self.get_workers(number_of_requested_workers)

        task = self.create_task(command, workers)
        self.tasks.append(task)

        message = self.make_message_for_task(task)
        for worker in workers:
            self.send_message(connection, message, worker)


class Task:
    STATUS_UNFINISHED = 'unfinished'
    STATUS_FINISHED = 'finished'

    def __init__(self, command, workers_list, number_of_executions_per_worker):
        self.command = command
        self.workers_status = {k: {'status': self.STATUS_UNFINISHED} for k in workers_list}
        self.uid = str(id(self))
        self.number_of_executions_per_worker = number_of_executions_per_worker

    @property
    def number_of_workers(self):
        return len(self.workers_status)

    def finish_worker(self, worker):
        """
        Indicate that the worker with the given nick has finished this task
        """
        self.workers_status[worker]['status'] = self.STATUS_FINISHED

    def is_finished(self):
        statuses = self.workers_status.values()
        return all(status['status'] == self.STATUS_FINISHED for status in statuses)


if __name__ == "__main__":
    bot = BotMaster(config.CHANNEL_NAME, config.SERVER, config.PORT)
    bot.start()
