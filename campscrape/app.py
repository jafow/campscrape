from enum import Enum
import logging
import os

import requests

from campscrape import config

# log level is one of 10, 20, 30, 40, 50
LOG_LEVEL = os.getenv('LOG_LEVEL', logging.INFO)
logging.basicConfig(level=LOG_LEVEL)
logger = logging.getLogger('campscrape')

# get facility data endpoint
ENDPOINT_ROOT = 'CaliforniaWebHome/Facilities/SearchViewUnitAvailabity.aspx'
ENDPOINT = 'https://www.reservecalifornia.com/{}/GetFacilityData'.format(ENDPOINT_ROOT)

# template for request parameters sent to get information on a site availability at a date
req_params_template = {
    "RegionId": 0,
    "PlaceId": 680,
    "FacilityId": 0,
    "StartDate": "12/29/2019",
    "Nights": "1",
    "CategoryId": "0",
    "UnitTypeIds": [],
    "UnitTypesCategory": [],
    "ShowOnlyAdaUnits": False,
    "ShowOnlyTentSiteUnits": False,
    "ShowOnlyRvSiteUnits": False,
    "MinimumVehicleLength": "0",
    "FacilityTypes_new": 0,
    "AccessTypes": [],
    "ShowIsPremiumUnits": False,
    "ParkFinder": [],
    "UnitTypeCategoryId": "0",
    "ShowSiteUnitsName": "0",
    "AmenitySearchParameters": []
}
HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:67.0) Gecko/20100101 Firefox/67.0",
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "deflate",
    "X-Requested-With": "XMLHttpRequest",
    "Connection": "keep-alive",
    "DNT": "1",
    "Pragma": "no-cache"
}


class MessageType(Enum):
    """ enum for slack message types """
    success = 0
    error = 1


def send_alert(msg_data, msg_type):
    """ sends a slack message with found data """
    msg_text = ""

    if msg_type == MessageType.error:
        msg_text = """
        :robot: Uh oh something went wrong!\r
        I dont know what to do with this: {}""".format(msg_data)
    else:
        msg_text = """:mega: Attention! Attention! :mega: \r
    Found {0} {1} units open at {2} on {3}""".format(
            msg_data["num_avail"], msg_data["unit_type"], msg_data["campsite_name"],
            msg_data["date_avail"])

    # send the message text to slack
    send = requests.post(config.CHANNEL_ENDPOINT, json={"text": msg_text})
    logger.info("Sent message: {}".format(msg_text))
    if not send.ok:
        # something broke
        logger.error("Error posting to slack {}".format(send.json()))


def has_count(unit):
    """ return true if unit has count """
    return unit.get('Count', 0) > 0


def main():
    # look up availability for all combinations of date and campsite
    lookup_set = {
        (_date, place_id) for place_id in config.PLACE_IDS
        for _date in config.DATES_TO_SEARCH
    }

    for d, place in lookup_set:
        req_params = {"UnitAvailabilitySearchParams": {
            **req_params_template, "StartDate": d, "PlaceId": place}}

        # make the request to with the given place and date
        res = requests.post(ENDPOINT, headers=HEADERS, json=req_params)
        if res.ok:
            # read the response data
            payload = res.json()

            # scan over the data about the units at the site
            units = payload.get('d', [])
            availabe_units = [x for x in units if has_count(x)]
            logging.debug("Scanning {} units for availability".format(len(units)))

            if len(availabe_units):
                for u in availabe_units:
                    # there is availability, alert!
                    msg_data = {
                        "num_avail": u.get("Count"),
                        "unit_type": u.get('UnitTypeName', "unknown unit type"),
                        "campsite_name": u.get("PlaceName", "missing campsite name"),
                        "date_avail": d
                    }

                    logger.info("Found {0} {1} units open at {2} on {3}".format(
                        msg_data["num_avail"],
                        msg_data["unit_type"],
                        msg_data["campsite_name"],
                        msg_data["date_avail"])
                    )

                    send_alert(msg_data, MessageType.success)
            else:
                logging.info("No available units {}".format(u"\U0001f63f"))
        else:
            logger.error("Error requesting campsite data: {}".format(res.json()))
            send_alert(msg_data, MessageType.error)


if __name__ == "__main__":
    main()
