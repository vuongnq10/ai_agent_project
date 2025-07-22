# tool_server.py
from dataclasses import dataclass
from typing import Callable
import random


@dataclass
class Tool:
    name: str
    func: Callable
    description: str
    input_params: dict


class Calculator:

    @staticmethod
    def gen_random(start=0, end=100):
        return random.randint(int(start), int(end))

    @staticmethod
    def sum_numbers(a: int, b: int) -> int:
        """Sum two numbers."""
        return a + b
