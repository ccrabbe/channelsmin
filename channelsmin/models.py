from otree.api import (
    models, widgets, BaseConstants, BaseSubsession, BaseGroup, BasePlayer,
    Currency as c, currency_range
)


author = 'crabbe@caltech.edu'

doc = """
A minimal example app which does all the things necessary to use channels 1.0 with oTree
"""


class Constants(BaseConstants):
    name_in_url = 'channelsmin'
    players_per_group = None
    num_rounds = 1


class Subsession(BaseSubsession):
    pass


class Group(BaseGroup):
    firstpage_done = models.BooleanField(initial=False)


class Player(BasePlayer):
    pass
