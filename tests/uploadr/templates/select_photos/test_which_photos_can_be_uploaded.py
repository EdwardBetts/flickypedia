from typing import TypedDict

import bs4
from flask import Flask, render_template
import pytest

from flickypedia.photos import CategorisedPhotos
from utils import minify


EMPTY_DATA: CategorisedPhotos = {
    "duplicates": {},
    "disallowed_licenses": {},
    "restricted": set(),
    "available": [],
}


ParagraphData = TypedDict("ParagraphData", {"class": str, "text": str})


def get_paragraphs(html: str) -> list[ParagraphData]:
    soup = bs4.BeautifulSoup(html, "html.parser")

    result: list[ParagraphData] = []

    for paragraph in soup.find_all("p"):
        p_class = paragraph.attrs["class"][0]
        text = minify(paragraph.getText())

        result.append({"class": p_class, "text": text})

    return result


@pytest.mark.parametrize(
    ["count", "expected_text"],
    [
        (1, "This photo can be uploaded to Wikimedia Commons. Yay!"),
        (2, "Both photos can be uploaded to Wikimedia Commons. Yay!"),
        (3, "All 3 photos can be uploaded to Wikimedia Commons. Yay!"),
        (10, "All 10 photos can be uploaded to Wikimedia Commons. Yay!"),
    ],
)
def test_shows_correct_message_when_all_available(
    app: Flask, count: int, expected_text: str
) -> None:
    """
    Every photo can be uploaded to Wikimedia Commons.
    """
    html = render_template(
        "select_photos/which_photos_can_be_uploaded.html",
        photos={
            **EMPTY_DATA,
            "available": [f"photo-{i}" for i in range(count)],
        },
    )

    assert get_paragraphs(html) == [
        {
            "class": "message_available",
            "text": expected_text,
        }
    ]


@pytest.mark.parametrize(
    ["count", "expected_text"],
    [
        (1, "Your work is done! This photo is already on Wikimedia Commons. W00t!"),
        (2, "Your work is done! Both photos are already on Wikimedia Commons. W00t!"),
        (3, "Your work is done! All 3 photos are already on Wikimedia Commons. W00t!"),
        (
            10,
            "Your work is done! All 10 photos are already on Wikimedia Commons. W00t!",
        ),
    ],
)
def test_shows_correct_message_when_all_duplicates(
    app: Flask, count: int, expected_text: str
) -> None:
    """
    Every photo is a duplicate of one already on Commons.
    """
    html = render_template(
        "select_photos/which_photos_can_be_uploaded.html",
        photos={
            **EMPTY_DATA,
            "duplicates": {
                f"photo-{i}": {"id": "M1234", "title": "File:duplicate"}
                for i in range(count)
            },
        },
    )

    assert get_paragraphs(html) == [
        {"class": "message_duplicate", "text": expected_text},
    ]


@pytest.mark.parametrize(
    ["count", "expected_text"],
    [
        (
            1,
            "This photo can’t be used because it has a license that Wikimedia Commons doesn’t accept.",
        ),
        (
            2,
            "Neither of these photos can be used because they have licenses that Wikimedia Commons doesn’t accept.",
        ),
        (
            3,
            "None of these photos can be used because they have licenses that Wikimedia Commons doesn’t accept.",
        ),
        (
            10,
            "None of these photos can be used because they have licenses that Wikimedia Commons doesn’t accept.",
        ),
    ],
)
def test_shows_correct_message_when_all_disallowed(
    app: Flask, count: int, expected_text: str
) -> None:
    """
    Every photo has a CC-BY 2.0 license which isn't allowed on Commons.
    """
    html = render_template(
        "select_photos/which_photos_can_be_uploaded.html",
        photos={
            **EMPTY_DATA,
            "disallowed_licenses": {f"photo-{i}": "CC BY-NC 2.0" for i in range(count)},
        },
    )

    assert get_paragraphs(html) == [
        {"class": "message_disallowed", "text": expected_text}
    ]


@pytest.mark.parametrize(
    ["count", "expected_text"],
    [
        (1, "This photo can’t be used."),
        (2, "Neither of these photos can be used."),
        (3, "None of these photos can be used."),
        (10, "None of these photos can be used."),
    ],
)
def test_shows_correct_message_when_all_restricted(
    app: Flask, count: int, expected_text: str
) -> None:
    html = render_template(
        "select_photos/which_photos_can_be_uploaded.html",
        photos={
            **EMPTY_DATA,
            "restricted": {f"photo-{i}" for i in range(count)},
        },
    )

    assert get_paragraphs(html) == [
        {"class": "message_disallowed", "text": expected_text}
    ]


@pytest.mark.parametrize(
    ["available", "expected_available_text"],
    [
        (0, None),
        (1, "One of these photos can be uploaded to Wikimedia Commons. Yay!"),
        (2, "2 of these photos can be uploaded to Wikimedia Commons. Yay!"),
        (3, "3 of these photos can be uploaded to Wikimedia Commons. Yay!"),
        (10, "10 of these photos can be uploaded to Wikimedia Commons. Yay!"),
    ],
)
@pytest.mark.parametrize(
    ["duplicates", "expected_duplicate_text"],
    [
        (0, None),
        (
            1,
            "Some of your work is done! One photo is already on Wikimedia Commons. W00t!",
        ),
        (
            2,
            "Some of your work is done! 2 photos are already on Wikimedia Commons. W00t!",
        ),
        (
            3,
            "Some of your work is done! 3 photos are already on Wikimedia Commons. W00t!",
        ),
        (
            10,
            "Some of your work is done! 10 photos are already on Wikimedia Commons. W00t!",
        ),
    ],
)
@pytest.mark.parametrize(
    ["disallowed_licenses", "expected_disallowed_licenses_text"],
    [
        (0, None),
        (
            1,
            "One photo can’t be used because it has a license that Wikimedia Commons doesn’t accept.",
        ),
        (
            2,
            "2 photos can’t be used because they have licenses that Wikimedia Commons doesn’t accept.",
        ),
        (
            3,
            "3 photos can’t be used because they have licenses that Wikimedia Commons doesn’t accept.",
        ),
        (
            10,
            "10 photos can’t be used because they have licenses that Wikimedia Commons doesn’t accept.",
        ),
    ],
)
@pytest.mark.parametrize("restricted", [0, 1])
def test_shows_correct_message(
    app: Flask,
    available: int,
    duplicates: int,
    disallowed_licenses: int,
    restricted: int,
    expected_available_text: str,
    expected_duplicate_text: str,
    expected_disallowed_licenses_text: str,
) -> None:
    # This test is explicitly for cases where we have a mixed collection
    # of photos; any time the parameters give us a single type of photo,
    # we want to skip.
    if (
        (available == 0 and duplicates == 0)
        or (duplicates == 0 and disallowed_licenses == 0)
        or (disallowed_licenses == 0 and available == 0)
    ):
        pytest.skip("invalid parameter combination")

    html = render_template(
        "select_photos/which_photos_can_be_uploaded.html",
        photos={
            "available": [f"photo-{i}" for i in range(available)],
            "duplicates": {
                f"photo-{i}": {"id": f"M{i}", "title": "dupe"}
                for i in range(duplicates)
            },
            "disallowed_licenses": {
                f"photo-{i}": "CC BY-NC 2.0" for i in range(disallowed_licenses)
            },
            "restricted": {f"photo-{i}" for i in range(restricted)},
        },
    )

    expected = []

    if available > 0:
        expected.append(
            {
                "class": "message_available",
                "text": expected_available_text,
            }
        )

    if duplicates > 0:
        expected.extend(
            [
                {"class": "message_duplicate", "text": expected_duplicate_text},
            ]
        )

    if disallowed_licenses > 0:
        expected.extend(
            [
                {
                    "class": "message_disallowed",
                    "text": expected_disallowed_licenses_text,
                },
            ]
        )

    assert get_paragraphs(html) == expected
