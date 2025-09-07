from loguru import logger

def setup_logger():
    logger.remove()
    logger.add(
        "bot.log",
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <white>{message}</white>",
        level="INFO",
        rotation="1 day",
        compression="zip"
    )
    
    logger.add(
        lambda msg: print(msg, end=""),
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <white>{message}</white>",
        level="INFO",
        colorize=True
    )
