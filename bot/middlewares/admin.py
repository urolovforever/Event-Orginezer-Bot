from typing import Callable, Dict, Any, Awaitable, Union
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery

from bot.config import Config


class AdminMiddleware(BaseMiddleware):
    """
    Middleware to check admin privileges for certain commands.
    Adds is_admin flag to handler data.
    """

    async def __call__(
            self,
            handler: Callable[[Union[Message, CallbackQuery], Dict[str, Any]], Awaitable[Any]],
            event: Union[Message, CallbackQuery],
            data: Dict[str, Any]
    ) -> Any:
        """
        Check if user is admin and add flag to data.
        """
        user_id = event.from_user.id
        data["is_admin"] = user_id in Config.ADMIN_IDS
        data["is_photographer"] = user_id == Config.PHOTOGRAPHER_ID

        return await handler(event, data)