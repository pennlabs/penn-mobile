from requests import get


class APIError(ValueError):
    pass


def headers():
    """
    Returns headers necessary for Penn Dining API access
    TODO: add the username + password to environment
    """

    return {
        "Authorization-Bearer": "sadfsfdsa",
        "Authorization-Token": "asdfsdfas",
    }


def dining_request(url):
    """
    Makes GET request to Penn Dining API and returns the response
    """

    response = get(url, params=None, headers=headers(), timeout=30)

    if response.status_code != 200:
        raise APIError("Request to {} returned {}".format(response.url, response.status_code))

    response = response.json()

    error_text = response["service_meta"]["error_text"]
    if error_text:
        raise APIError(error_text)

    return response


def normalize_weekly(data):
    """
    Normalization for dining menu data
    """

    if "tblMenu" not in data["result_data"]["Document"]:
        data["result_data"]["Document"]["tblMenu"] = []
    if isinstance(data["result_data"]["Document"]["tblMenu"], dict):
        data["result_data"]["Document"]["tblMenu"] = [data["result_data"]["Document"]["tblMenu"]]
    for day in data["result_data"]["Document"]["tblMenu"]:
        if "tblDayPart" not in day:
            continue
        if isinstance(day["tblDayPart"], dict):
            day["tblDayPart"] = [day["tblDayPart"]]
        for meal in day["tblDayPart"]:
            if isinstance(meal["tblStation"], dict):
                meal["tblStation"] = [meal["tblStation"]]
            for station in meal["tblStation"]:
                if isinstance(station["tblItem"], dict):
                    station["tblItem"] = [station["tblItem"]]
    return data


def get_meals(v2_response, building_id):
    """
    Extract meals into old format from a DiningV2 JSON response
    """

    result_data = v2_response["result_data"]
    meals = []
    day_parts = result_data["days"][0]["cafes"][building_id]["dayparts"][0]
    for meal in day_parts:
        stations = []
        for station in meal["stations"]:
            items = []
            for item_id in station["items"]:
                item = result_data["items"][item_id]
                new_item = {}
                new_item["txtTitle"] = item["label"]
                new_item["txtPrice"] = ""
                new_item["txtNutritionInfo"] = ""
                new_item["txtDescription"] = item["description"]
                new_item["tblSide"] = ""
                new_item["tblFarmToFork"] = ""
                attrs = [{"description": item["cor_icon"][attr]} for attr in item["cor_icon"]]
                if len(attrs) == 1:
                    new_item["tblAttributes"] = {"txtAttribute": attrs[0]}
                elif len(attrs) > 1:
                    new_item["tblAttributes"] = {"txtAttribute": attrs}
                else:
                    new_item["tblAttributes"] = ""
                if isinstance(item["options"], list):
                    item["options"] = {}
                if "values" in item["options"]:
                    for side in item["options"]["values"]:
                        new_item["tblSide"] = {"txtSideName": side["label"]}
                items.append(new_item)
            stations.append({"tblItem": items, "txtStationDescription": station["label"]})
        meals.append({"tblStation": stations, "txtDayPartDescription": meal["label"]})
    return meals
