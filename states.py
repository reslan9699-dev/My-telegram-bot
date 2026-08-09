"""FSM states for the admin upload workflow."""

from aiogram.fsm.state import State, StatesGroup


class AdminUploadStates(StatesGroup):
    """Lifecycle of an admin upload session.

    Idle            - admin is not uploading anything.
    ReceivingFiles  - admin is sending files for the post.
    WaitingPost     - files are collected, waiting for the post (text or photo).
    Publishing      - the post is being persisted and published to the channel.
    """

    Idle = State()
    ReceivingFiles = State()
    WaitingPost = State()
    Publishing = State()
