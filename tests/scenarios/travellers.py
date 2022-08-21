from dataclasses import dataclass
from typing import Dict, List, Optional, Union

from . import Scenario


@dataclass
class City:
    cityName: str
    countryName: str


@dataclass
class Traveller:
    travellerId: Union[str, int]
    birthCity: City
    marriageCity: Optional[City]
    # list of cities visited, either a real City object or a str city name
    citiesVisited: List[Union[City, str]]
    # mapping of country name -> list of years it was visited
    countriesVisited: Dict[str, List[int]]
    # mapping of YEAR to List of Cities planned to visit in that year
    holidays: Dict[str, List[Union[City, str]]]


TRAVELLER0 = Scenario(
    [Traveller, City],
    {
        "__dataclass__": "Traveller",
        "travellerId": "fred@example.com",
        "birthCity": {"__dataclass__": "City", "cityName": "Sydney", "countryName": "Australia"},
        "marriageCity": {
            "__dataclass__": "City",
            "cityName": "Brisbane",
            "countryName": "Australia",
        },
        "citiesVisited": [
            {"__dataclass__": "City", "cityName": "Cairns", "countryName": "AUS"},
            "Los Angeles",
            {"__dataclass__": "City", "cityName": "Perth", "countryName": "Australia"},
        ],
        "countriesVisited": {
            "USA": [2003, 2008, 2011],
            "France": [],
        },
        "holidays": {
            "2013": [
                "Los Angeles",
                "Las Vegas",
            ],
            # no holiday in 2014
            "2014": [],
            "2015": [
                {"__dataclass__": "City", "cityName": "Paris", "countryName": "France"},
                "New York",
                {"__dataclass__": "City", "cityName": "Rome", "countryName": "Italy"},
            ],
        },
    },
    verify_php='''
        assert($VAR->travellerId === "fred@example.com");
        assert($VAR->birthCity instanceof City);
        assert($VAR->birthCity->cityName === "Sydney");
        assert($VAR->birthCity->countryName === "Australia");
        assert($VAR->marriageCity instanceof City);
        assert(is_array($VAR->citiesVisited));
        assert(count($VAR->citiesVisited) === 3);
        assert($VAR->citiesVisited[0] instanceof City);
        assert($VAR->citiesVisited[0]->cityName === "Cairns");
        assert($VAR->citiesVisited[0]->countryName === "AUS");
        assert($VAR->citiesVisited[1] === "Los Angeles");
        assert($VAR->citiesVisited[2] instanceof City);
        assert($VAR->citiesVisited[2]->cityName === "Perth");
        assert($VAR->citiesVisited[2]->countryName === "Australia");
        assert(is_array($VAR->countriesVisited));
        assert(count($VAR->countriesVisited) === 2);
        assert(is_array($VAR->countriesVisited["USA"]));
        assert(count($VAR->countriesVisited["USA"]) === 3);
        assert($VAR->countriesVisited["USA"][0] === 2003);
        assert($VAR->countriesVisited["USA"][1] === 2008);
        assert($VAR->countriesVisited["USA"][2] === 2011);
        assert(is_array($VAR->countriesVisited["France"]));
        assert(count($VAR->countriesVisited["France"]) === 0);
        assert(is_array($VAR->holidays));
        assert(count($VAR->holidays) === 3);
        assert(is_array($VAR->holidays["2013"]) && count($VAR->holidays["2013"]) === 2);
        assert(is_array($VAR->holidays["2014"]) && count($VAR->holidays["2014"]) === 0);
        assert(is_array($VAR->holidays["2015"]) && count($VAR->holidays["2015"]) === 3);
        assert($VAR->holidays["2013"][0] === "Los Angeles");
        assert($VAR->holidays["2013"][1] === "Las Vegas");
        assert($VAR->holidays["2015"][0] instanceof City);
        assert($VAR->holidays["2015"][0]->cityName === "Paris");
        assert($VAR->holidays["2015"][1] === "New York");
        assert($VAR->holidays["2015"][2] instanceof City);
        assert($VAR->holidays["2015"][2]->cityName === "Rome");
    ''',
)


TRAVELLER1 = Scenario(
    [Traveller, City],
    {
        "__dataclass__": "Traveller",
        "travellerId": 54321,
        "birthCity": {"__dataclass__": "City", "cityName": "Barcelona", "countryName": "Spain"},
        "marriageCity": None,
        "citiesVisited": [],
        "countriesVisited": {},
        "holidays": {},
    },
    verify_php='''
        assert($VAR->travellerId === 54321);
        assert($VAR->birthCity instanceof City);
        assert($VAR->birthCity->cityName === "Barcelona");
        assert($VAR->birthCity->countryName === "Spain");
        assert($VAR->marriageCity === null);
        assert(is_array($VAR->citiesVisited));
        assert(count($VAR->citiesVisited) === 0);
        assert(is_array($VAR->countriesVisited));
        assert(count($VAR->countriesVisited) === 0);
        assert(is_array($VAR->holidays));
        assert(count($VAR->holidays) === 0);
    ''',
)
