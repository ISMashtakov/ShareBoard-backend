import random

COLORS = ['#F45D01',  # 'orange',
          '#C7567F',  # 'dark pink',
          '#5688C7',  # 'blue',
          '#B756C7',  # 'violet',
          '#56C7A5',  # 'turquoise',
          '#C75656',  # 'red',
          '#81C756']  # 'green'


def random_color() -> str:
    return random.choice(COLORS)
