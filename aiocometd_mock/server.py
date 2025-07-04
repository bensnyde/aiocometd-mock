import asyncio
import logging
from argparse import Namespace

from aiohttp import web

from . import adapters
from . import validators
from .routes import process_request

logger: logging.Logger = logging.getLogger(__name__)


def create_app(args: Namespace) -> web.Application:
    """Creates and configures the aiohttp application."""
    logger.info("Creating application")
    app = web.Application()
    app["client_ids"] = {}

    # Pass command-line arguments to the application state
    app["no_validation"] = args.no_validation
    app["connect_interval"] = args.connect_interval
    app["connect_timeout"] = args.connect_timeout
    app["reconnection_interval"] = args.reconnection_interval
    app["reconnection_interval_seconds"] = args.reconnection_interval_seconds
    app["expire_client_ids_after"] = args.expire_client_ids_after
    app["expire_client_ids_after_seconds"] = args.expire_client_ids_after_seconds

    # The app uses the handler imported from the library
    app.router.add_post("/cometd", process_request)

    # Load adapters
    adapters.load_adapters(args.adapters)

    # Load validators
    validators.load_validators(args.validators)
    return app


async def start_server(app: web.Application, host: str, port: int) -> None:
    """Sets up and starts the web server."""
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host, port)
    await site.start()

    logger.info("======== Running on http://%s:%s ========", host, port)
    # Wait forever
    await asyncio.Event().wait()


def run(args: Namespace) -> None:
    """Configures logging and starts the server."""
    logging.basicConfig(
        level=logging.DEBUG if args.debug else logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    logging.debug("Parsed arguments: %s", args)
    app = create_app(args)

    try:
        asyncio.run(start_server(app, args.host, args.port))
    except KeyboardInterrupt:
        logger.info("Server shutting down.")
