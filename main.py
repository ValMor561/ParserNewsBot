import asyncio
import logging
from handlers import bot, dp, router, run_bot

async def main():
    dp.include_router(router)
    await run_bot()
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
