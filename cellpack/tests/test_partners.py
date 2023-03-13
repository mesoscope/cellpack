#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""

Docs: https://docs.pytest.org/en/latest/
      https://docs.pytest.org/en/latest/goodpractices.html#conventions-for-python-test-discovery
"""
import pytest
from cellpack.autopack.ingredient.agent import Agent
from cellpack.autopack.interface_objects import Partners


@pytest.mark.parametrize(
    "input_data, expected_result",
    [
        (
            [{"name": "partner_name"}],
            [
                {
                    "name": "partner_name",
                    "binding_probability": 1.0,
                    "weight": 0.8,
                    "position": [0, 0, 0],
                }
            ],
        ),
        (
            [
                {
                    "name": "partner_name",
                    "binding_probability": 2.0,
                    "weight": 0.5,
                    "position": [1, 0, 10],
                }
            ],
            [
                {
                    "name": "partner_name",
                    "binding_probability": 2.0,
                    "weight": 0.5,
                    "position": [1, 0, 10],
                }
            ],
        ),
        (
            [
                {
                    "name": "partner_name_1",
                    "binding_probability": 2.0,
                    "weight": 0.5,
                    "position": [1, 0, 10],
                },
                {
                    "name": "partner_name_2",
                    "binding_probability": 2.0,
                    "weight": 0.5,
                    "position": [1, 0, 10],
                },
            ],
            [
                {
                    "name": "partner_name_1",
                    "binding_probability": 2.0,
                    "weight": 0.5,
                    "position": [13, 0, 10],
                },
                {
                    "name": "partner_name_2",
                    "binding_probability": 2.0,
                    "weight": 0.5,
                    "position": [13, 0, 1],
                },
            ],
        ),
    ],
)
def test_partners(input_data, expected_result):
    for index, partner in enumerate(Partners(input_data).all_partners):
        expected_partner = expected_result[index]
        assert expected_partner["name"] == partner.name
        assert expected_partner["binding_probability"] == partner.binding_probability
        assert expected_partner["weight"] == partner.weight


def test_is_partner():
    partners = Partners(
        [
            {
                "name": "partner_name_1",
                "binding_probability": 2.0,
                "weight": 0.5,
                "position": [1, 0, 10],
            },
            {
                "name": "partner_name_2",
                "binding_probability": 2.0,
                "weight": 0.5,
                "position": [1, 0, 10],
            },
        ],
    )
    assert partners.is_partner("partner_name_1_ext")
    assert not partners.is_partner("not_partner_ext")


def test_partner_ingredient():
    partners = Partners(
        [
            {
                "name": "partner_name_1",
                "binding_probability": 2.0,
                "weight": 0.5,
                "position": [1, 0, 10],
            },
            {
                "name": "partner_name_2",
                "binding_probability": 2.0,
                "weight": 0.5,
                "position": [1, 0, 10],
            },
        ],
    )
    ingr_name = "partner_name_1_ingr"
    ingr = Agent(name=ingr_name, concentration=10)
    partners.all_partners[0].set_ingredient(ingr)
    partner_ingr = partners.get_partner_by_ingr_name(ingr_name)
    assert partner_ingr.name == "partner_name_1"
