from decouple import config
from sqlalchemy import create_engine, Column, Text, BigInteger, Boolean
from sqlalchemy.orm import sessionmaker, declarative_base

from logger import Logger

logger = Logger(__name__)
Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    telegram_id = Column(BigInteger, primary_key=True, nullable=False)
    username = Column(Text)
    location = Column(Text)
    notify_today = Column(Boolean, default=False)
    notify_tomorrow = Column(Boolean, default=False)


class Database:
    """A class to create connection sessions to the database for user with specific telegram_id.

    Args:
        telegram_id (int): telegram_id to connect to the database.
    """

    def __init__(self, telegram_id: int):
        self.telegram_id = telegram_id

        connection_config = {
            "user": config("DBUSER"),
            "password": config("PASSWORD"),
            "host": config("HOST"),
            "port": config("PORT"),
            "database": config("DATABASE"),
            "sslmode": "require",
        }

        self.engine = create_engine("postgresql://", connect_args=connection_config)

        self.connect()

    def connect(self):
        """Creates a connection session to the database."""
        try:
            Connection = sessionmaker(bind=self.engine)
            self.session = Connection()
            logger.info(
                f"Connected to database [{config('DATABASE')}] with telegram ID [{self.telegram_id}]."
            )
        except Exception as error:
            logger.error(
                f"Error connecting to database: {error} with telegram ID [{self.telegram_id}]."
            )

    def disconnect(self):
        """Closes the connection session to the database."""
        self.session.close()
        logger.debug(
            f"Disconnected from database with telegram ID [{self.telegram_id}]."
        )

    def exists_in_database(self) -> bool:
        """Checks if user with telegram_id exists in the database.

        Returns:
            bool: True if user exists in the database, False otherwise.
        """
        exists = (
            self.session.query(User)
            .filter(User.telegram_id == self.telegram_id)
            .count()
            > 0
        )

        logger.debug(
            f"User with telegram ID [{self.telegram_id}] exists: [{exists}] in the database."
        )

        return exists

    def update_user(self, username: str, location: str):
        """Adds user to the database if it doesn't exist, otherwise updates the username and location
        for existing user in the database.

        Args:
            username (str): telegram username
            location (str): string-like location of the user in WeatherAPI format
        """
        if not self.exists_in_database():
            # Creating new user if it doesn't exist in the database.
            user = User(
                telegram_id=self.telegram_id, username=username, location=location
            )

            # Adding user to the database.
            self.session.add(user)
            self.session.commit()

            logger.info(
                f"User with telegram ID [{self.telegram_id}] added to the database."
            )
        else:
            # Getting user from the database.
            user = (
                self.session.query(User)
                .filter(User.telegram_id == self.telegram_id)
                .first()
            )

            logger.debug(
                f"Updating username from [{user.username}] to [{username}] for "
                f"user with telegram ID [{self.telegram_id}]."
            )
            logger.debug(
                f"Updating location from [{user.location}] to [{location}] for "
                f"user with telegram ID [{self.telegram_id}]."
            )

            # Updating user data.
            user.username = username
            user.location = location
            self.session.commit()

            logger.debug(
                f"Location and username updated for user with telegram ID [{self.telegram_id}]."
            )

    def get_user_location(self) -> str | None:
        """Returns the location of the user with telegram_id if it exists in the database.

        Returns:
            str | None: location of the user in WeatherAPI format if it exists in the database, None otherwise.
        """
        if self.exists_in_database():
            location = (
                self.session.query(User)
                .filter(User.telegram_id == self.telegram_id)
                .first()
                .location
            )
            return location

    def get_all_usernames(self) -> list[str]:
        """Retrieves all usernames from the database, adds @ to the beginning of
        each username and returns them as a list.

        Returns:
            list[str]: list of usernames with @ in front of each username.
        """
        query = self.session.query(User.username).all()
        usernames = [f"@{username[0]}" for username in query]

        logger.debug(f"Get [{len(usernames)}] usernames from database.")

        return usernames

    def change_notification_status(self, notification: str):
        """Changes the notification status for user with telegram_id to opposite of the current status.
        Requires notification to be either "today" or "tomorrow".

        Args:
            notification (str): notification to change status for ("today" or "tomorrow")
        """
        user = (
            self.session.query(User)
            .filter(User.telegram_id == self.telegram_id)
            .first()
        )
        if notification == "today":
            user.notify_today = not user.notify_today

            logger.debug(
                f"User with telegram ID [{self.telegram_id}] changed {notification} "
                f"notification status to [{user.notify_today}]."
            )

        elif notification == "tomorrow":
            user.notify_tomorrow = not user.notify_tomorrow

            logger.debug(
                f"User with telegram ID [{self.telegram_id}] changed {notification} "
                f"notification status to [{user.notify_tomorrow}]."
            )

        self.session.commit()

    def notification_status(self, notification: str) -> bool:
        """Retrieves the status for specified notification for user in the database.
        Returns True if notification is enabled, False otherwise.

        Args:
            notification (str): notification to retrieve status for ("today" or "tomorrow")

        Returns:
            bool: boolean value representing the status of the notification.
        """
        user = (
            self.session.query(User)
            .filter(User.telegram_id == self.telegram_id)
            .first()
        )

        logger.debug(
            f"Checking [{notification}] notification status for user with telegram ID [{self.telegram_id}]."
        )

        if notification == "today":
            return user.notify_today
        elif notification == "tomorrow":
            return user.notify_tomorrow

    def get_notified_users(self, notification: str) -> list[User]:
        """Retrieves all users with specified notification enabled.

        Args:
            notification (str): notification to retrieve users for ("today" or "tomorrow")

        Returns:
            list[User]: list of User objects with specified notification enabled.
        """
        if notification == "today":
            users = self.session.query(User).filter(User.notify_today == True).all()
        elif notification == "tomorrow":
            users = self.session.query(User).filter(User.notify_tomorrow == True).all()

        logger.debug(
            f"Retrieved [{len(users)}] users with [{notification}] enabled notification status."
        )

        return users
