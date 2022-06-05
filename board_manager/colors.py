import random

COLORS = ['#5688C7',  # 'blue',
          '#F45D5D',  # 'red',
          '#965DF4',  # 'purple',
          '#F4C95D',  # 'yellow',
]


def random_color() -> str:
    return random.choice(COLORS)
