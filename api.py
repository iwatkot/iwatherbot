import swagger_client

from swagger_client.rest import ApiException

from decouple import config
from pprint import pprint

from logger import Logger

logger = Logger(__name__)


class Caller:
    def __init__(self, telegram_id):
        self.telegram_id = telegram_id

        configuration = swagger_client.Configuration()
        configuration.api_key["key"] = config("API_KEY")

        self.instance = swagger_client.APIsApi(swagger_client.ApiClient(configuration))
        logger.debug(f"Created instance for user with telegrad ID {self.telegram_id}")

    def search(self, query):
        search_results = None
        try:
            search_results = self.instance.search_autocomplete_weather(query)
            logger.debug(
                f"Find {len(search_results)} results for {query} for user with telegrad ID {self.telegram_id}"
            )
        except ApiException as error:
            logger.error(
                f"There was an error while using the search for user with telegrad ID "
                f"{self.telegram_id}. Query: {query}. Error: {error}"
            )


caller = Caller(999)
caller.search("Velikiy")
