from dataclasses import dataclass
from typing import Dict, List, Optional, Union

from paradox.expressions import PanVar
from paradox.interfaces import AcceptsStatements

from . import (Scenario, assert_eq, assert_isdict, assert_isinstance,
               assert_islist)


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


class TRAVELLER0(Scenario):
    dataclasses = [Traveller, City]
    obj = {
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
    }

    def add_assertions(self, context: AcceptsStatements, v: PanVar) -> None:
        assert_eq(context, v.getprop('travellerId'), "fred@example.com")
        bc = v.getprop('birthCity')
        assert_isinstance(context, bc, 'City')
        assert_eq(context, bc.getprop('cityName'), "Sydney")
        assert_eq(context, bc.getprop('countryName'), "Australia")
        assert_isinstance(context, v.getprop('marriageCity'), 'City')

        cv = v.getprop('citiesVisited')
        assert_islist(context, cv, size=3)
        assert_isinstance(context, v.getprop('citiesVisited').getindex(0), 'City')
        assert_eq(context, cv.getindex(0).getprop('cityName'), "Cairns")
        assert_eq(context, cv.getindex(0).getprop('countryName'), "AUS")
        assert_eq(context, cv.getindex(1), "Los Angeles")
        assert_isinstance(context, v.getprop('citiesVisited').getindex(2), 'City')
        assert_eq(context, cv.getindex(2).getprop('cityName'), "Perth")
        assert_eq(context, cv.getindex(2).getprop('countryName'), "Australia")

        cv = v.getprop('countriesVisited')
        assert_isdict(context, cv, size=2)
        assert_islist(context, cv.getitem('USA'), size=3)
        assert_eq(context, cv.getitem("USA").getindex(0), 2003)
        assert_eq(context, cv.getitem("USA").getindex(1), 2008)
        assert_eq(context, cv.getitem("USA").getindex(2), 2011)
        assert_islist(context, cv.getitem('France'), size=0)

        hol = v.getprop('holidays')
        assert_isdict(context, hol, size=3)
        assert_islist(context, hol.getitem("2013"), size=2)
        assert_islist(context, hol.getitem("2014"), size=0)
        assert_islist(context, hol.getitem("2015"), size=3)
        assert_eq(context, hol.getitem("2013").getindex(0), "Los Angeles")
        assert_eq(context, hol.getitem("2013").getindex(1), "Las Vegas")
        assert_isinstance(context, hol.getitem("2015").getindex(0), 'City')
        assert_eq(context, hol.getitem("2015").getindex(0).getprop('cityName'), "Paris")
        assert_eq(context, hol.getitem("2015").getindex(1), "New York")
        assert_isinstance(context, hol.getitem("2015").getindex(2), 'City')
        assert_eq(context, hol.getitem("2015").getindex(2).getprop('cityName'), "Rome")


class TRAVELLER1(Scenario):
    dataclasses = [Traveller, City]
    obj = {
        "__dataclass__": "Traveller",
        "travellerId": 54321,
        "birthCity": {"__dataclass__": "City", "cityName": "Barcelona", "countryName": "Spain"},
        "marriageCity": None,
        "citiesVisited": [],
        "countriesVisited": {},
        "holidays": {},
    }

    def add_assertions(self, context: AcceptsStatements, v: PanVar) -> None:
        assert_eq(context, v.getprop('travellerId'), 54321)
        assert_isinstance(context, v.getprop('birthCity'), 'City')
        assert_eq(context, v.getprop('birthCity').getprop('cityName'), "Barcelona")
        assert_eq(context, v.getprop('birthCity').getprop('countryName'), "Spain")
        assert_eq(context, v.getprop('marriageCity'), None)
        assert_islist(context, v.getprop('citiesVisited'), size=0)
        assert_isdict(context, v.getprop('countriesVisited'), size=0)
        assert_isdict(context, v.getprop('holidays'), size=0)
