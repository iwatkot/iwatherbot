from decouple import config
from sqlalchemy import create_engine, Column, Text, BigInteger
from sqlalchemy.orm import sessionmaker, declarative_base

from logger import Logger

logger = Logger(__name__)
Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    telegram_id = Column(BigInteger, primary_key=True, nullable=False)
    username = Column(Text)
    location = Column(Text)


class Database:
    def __init__(self, telegram_id):
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
        self.session.close()
        logger.debug(
            f"Disconnected from database with telegram ID [{self.telegram_id}]."
        )

    def exists_in_database(self):
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

    def update_location(self, username, location):
        if not self.exists_in_database():
            user = User(
                telegram_id=self.telegram_id, username=username, location=location
            )

            self.session.add(user)
            self.session.commit()
            logger.info(
                f"User with telegram ID [{self.telegram_id}] added to the database."
            )
        else:
            user = (
                self.session.query(User)
                .filter(User.telegram_id == self.telegram_id)
                .first()
            )
            logger.debug(
                f"Updating location from [{user.location}] to [{location}] for "
                f"user with telegram ID [{self.telegram_id}]."
            )

            user.location = location
            self.session.commit()

            logger.debug(
                f"Location updated for user with telegram ID [{self.telegram_id}]."
            )
