import logging
import signal
import sys
import time

from config import load_config
from ha_client import HAClient
from persistence import Persistence
from release_checker import ReleaseChecker
from stremio_client import StremioClient

logger = logging.getLogger("streamio_notifications")

shutdown_requested = False


def handle_signal(signum, frame):
    global shutdown_requested
    logger.info("Received signal %s, shutting down gracefully...", signum)
    shutdown_requested = True


def setup_logging(log_level: int) -> None:
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[logging.StreamHandler(sys.stdout)],
    )


def run_check_cycle(
    stremio: StremioClient,
    checker: ReleaseChecker,
    ha: HAClient,
    persistence: Persistence,
    content_types: list,
) -> None:
    logger.info("Starting check cycle")

    # Fetch library
    try:
        items = stremio.get_library(content_types)
    except Exception as e:
        logger.error("Failed to fetch Stremio library: %s", e)
        # Try re-login once
        try:
            logger.info("Attempting re-login to Stremio")
            stremio.login()
            items = stremio.get_library(content_types)
        except Exception as e2:
            logger.error("Re-login failed, skipping this cycle: %s", e2)
            return

    if not items:
        logger.info("No library items found, nothing to check")
        return

    # Check releases
    releases = checker.check_releases(items)

    # Create calendar events for new releases
    created_count = 0
    for release in releases:
        if persistence.is_created(release.event_key):
            logger.debug("Already created event for %s, skipping", release.event_key)
            continue

        try:
            ha.create_calendar_event(release)
            persistence.mark_created(release.event_key)
            created_count += 1
        except Exception as e:
            logger.error("Failed to create calendar event for %s: %s", release.event_key, e)
            # Do NOT mark as created so it retries next cycle

    # Cleanup and save
    persistence.cleanup_old_entries()
    persistence.save()

    logger.info("Check cycle complete: %d new events created", created_count)


def main() -> None:
    signal.signal(signal.SIGTERM, handle_signal)
    signal.signal(signal.SIGINT, handle_signal)

    # Load config
    try:
        config = load_config()
    except Exception as e:
        print(f"FATAL: Failed to load configuration: {e}", file=sys.stderr)
        sys.exit(1)

    setup_logging(config.log_level_int)
    logger.info("Stremio Notifications addon starting")

    # Initialize clients
    ha = HAClient(config.ha_base_url, config.supervisor_token, config.calendar_entity)
    stremio = StremioClient(config.stremio_email, config.stremio_password)
    checker = ReleaseChecker(config.days_ahead)
    persistence = Persistence()

    # Startup checks
    try:
        ha.check_connection()
    except Exception as e:
        logger.fatal("Cannot connect to Home Assistant API: %s", e)
        sys.exit(1)

    try:
        stremio.login()
    except Exception as e:
        logger.fatal("Stremio login failed: %s", e)
        sys.exit(1)

    logger.debug("force_refresh option value: %s", config.force_refresh)

    if config.force_refresh:
        logger.info("Force refresh enabled, clearing persistence")
        persistence.clear()
        persistence.save()
        logger.info("Persistence cleared")
    else:
        persistence.load()

    logger.info(
        "Configuration: check every %dh, %d days ahead, types=%s, calendar=%s",
        config.check_interval_hours,
        config.days_ahead,
        config.content_types,
        config.calendar_entity,
    )

    # Main loop
    interval_seconds = config.check_interval_hours * 3600

    while not shutdown_requested:
        run_check_cycle(stremio, checker, ha, persistence, config.content_types)

        # Sleep in small increments to allow graceful shutdown
        elapsed = 0
        while elapsed < interval_seconds and not shutdown_requested:
            time.sleep(min(30, interval_seconds - elapsed))
            elapsed += 30

    # Cleanup
    logger.info("Shutting down...")
    stremio.close()
    checker.close()
    ha.close()
    logger.info("Goodbye!")


if __name__ == "__main__":
    main()
