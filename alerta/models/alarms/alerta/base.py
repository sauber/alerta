from enum import Enum

from flask import current_app

from alerta.models import severity_code
from alerta.models.alarms.base import AlarmModel
from alerta.app import severity


class Status(Enum):
    OPEN = 'open'
    ASSIGN = 'assign'
    ACK = 'ack'
    CLOSED = 'closed'
    EXPIRED = 'expired'
    BLACKOUT = 'blackout'
    SHELVED = 'shelved'
    UNKNOWN = 'unknown'


class Action(Enum):
    ACTION_ACK = 'ack'
    ACTION_UNACK = 'unack'
    ACTION_SHELVE = 'shelve'
    ACTION_UNSHELVE = 'unshelve'
    ACTION_CLOSE = 'close'


class Lifecycle(AlarmModel):

    def transition(self, previous_severity, current_severity, previous_status=None, current_status=None, **kwargs):

        previous_status = previous_status or Status.OPEN
        current_status = current_status or Status.UNKNOWN
        action = kwargs.get('action', None)

        # operator transitions
        if action == Action.ACTION_UNACK:
            return current_severity, Status.OPEN

        if action == Action.ACTION_SHELVE:
            return current_severity, Status.SHELVED

        if action == Action.ACTION_UNSHELVE:
            return current_severity, Status.OPEN

        if action == Action.ACTION_ACK:
            return current_severity, Status.ACK

        if action == Action.ACTION_CLOSE:
            return current_app.config['DEFAULT_NORMAL_SEVERITY'], Status.CLOSED

        # alert transitions
        if current_severity in [severity_code.NORMAL, severity_code.CLEARED, severity_code.OK]:
            return current_app.config['DEFAULT_NORMAL_SEVERITY'], Status.CLOSED

        if current_status in [Status.BLACKOUT, Status.SHELVED]:
            return current_severity, current_status

        if previous_status in [Status.BLACKOUT, Status.CLOSED, Status.EXPIRED]:
            return current_severity, Status.OPEN

        if severity.trend(previous_severity, current_severity) == severity_code.MORE_SEVERE:
            return current_severity, Status.OPEN

        return current_severity, previous_status
