import swagger_client

from swagger_client.rest import ApiException

from decouple import config

from logger import Logger

logger = Logger(__name__)


class Instance:
    def __init__(self, telegram_id):
        self.telegram_id = telegram_id

        configuration = swagger_client.Configuration()
        configuration.api_key["key"] = config("API_KEY")

        self.instance = swagger_client.APIsApi(swagger_client.ApiClient(configuration))
        logger.debug(
            f"Created API instance for user with telegram ID [{self.telegram_id}]."
        )

    def search(self, query):
        try:
            search_results = self.instance.search_autocomplete_weather(query)
            logger.debug(
                f"Find [{len(search_results)}] results for search query: [{query}] "
                f"for user with telegrad ID [{self.telegram_id}]."
            )
            return search_results
        except ApiException as error:
            logger.error(
                f"There was an error while using the search for user with telegram ID "
                f"{self.telegram_id}. Query: {query}. Error: {error}."
            )

        return search_results

    def get_current_weather(self, location):
        try:
            current_weather = self.instance.realtime_weather(location)
            logger.debug(
                f"Got current weather for for location: [{location}] for user with telegram ID {self.telegram_id}."
            )
            return current_weather
        except ApiException as error:
            logger.error(
                f"There was an error while using the current weather API for user with "
                f"telegram ID {self.telegram_id}. Location: {location}. Error: {error}."
            )
