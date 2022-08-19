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
    ''',
)
