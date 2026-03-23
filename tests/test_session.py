import unittest

from sqlactive.exceptions import NoSessionError
from sqlactive.session import SessionMixin


class TestModel(SessionMixin):
    pass


class TestSessionMixin(unittest.IsolatedAsyncioTestCase):
    """Tests for ``sqlactive.session.SessionMixin``."""

    async def test_no_session_error(self):
        """Test for ``NoSessionError`` exception."""
        with self.assertRaises(NoSessionError):
            TestModel.AsyncSession
