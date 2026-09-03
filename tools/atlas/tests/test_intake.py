from __future__ import annotations

import pytest

from atlas.core.intake import (
    ContactSnapshot,
    IntakeError,
    ProjectAddress,
    ProjectIntake,
    ProjectUseCase,
    USE_CASES,
)


def test_project_address_provides_full_and_short_forms():
    address = ProjectAddress(
        street="1842 Oak Street",
        unit="Apt 4B",
        city="Oakland",
        state="ca",
        postal_code="94612-1234",
    )

    assert address.formatted == "1842 Oak Street, Apt 4B, Oakland, CA 94612-1234"
    assert address.short == "1842 Oak Street"
    assert address.state == "CA"


def test_project_address_accepts_hyphenated_nyc_street_number():
    address = ProjectAddress("80-23 64th Lane", "Queens", "NY", "11379")

    assert address.short == "80-23 64th Lane"


@pytest.mark.parametrize(
    ("changes", "message"),
    [
        ({"street": "Oak Street"}, "street number"),
        ({"city": ""}, "city"),
        ({"state": "California"}, "state"),
        ({"state": "XX"}, "state"),
        ({"postal_code": "9461"}, "ZIP"),
    ],
)
def test_project_address_rejects_incomplete_or_invalid_us_address(changes, message):
    values = {
        "street": "1842 Oak Street",
        "city": "Oakland",
        "state": "CA",
        "postal_code": "94612",
    }
    values.update(changes)

    with pytest.raises(IntakeError, match=message):
        ProjectAddress(**values)


def test_project_use_case_accepts_canonical_values_and_requires_other_label():
    assert ProjectUseCase("Renovation + Addition").display == "Renovation + Addition"
    assert ProjectUseCase("Other", "Adaptive reuse").display == "Adaptive reuse"
    assert "Code Compliance" in USE_CASES

    with pytest.raises(IntakeError, match="custom"):
        ProjectUseCase("Other")
    with pytest.raises(IntakeError, match="Project Use Case"):
        ProjectUseCase("New Build")


def test_project_intake_requires_name_and_contact_references():
    intake = ProjectIntake(
        project_name=" Oak House ",
        project_address=ProjectAddress("1842 Oak Street", "Oakland", "CA", "94612"),
        project_use_case=ProjectUseCase("Renovation"),
        billing_contact_id=" billing-1 ",
        client_contact_id=" client-1 ",
        description=" Kitchen ",
    )

    assert intake.project_name == "Oak House"
    assert intake.description == "Kitchen"
    assert intake.billing_contact_id == "billing-1"
    assert intake.client_contact_id == "client-1"

    with pytest.raises(IntakeError, match="Project Name"):
        ProjectIntake(
            project_name=" ",
            project_address=intake.project_address,
            project_use_case=intake.project_use_case,
            billing_contact_id="billing-1",
            client_contact_id="client-1",
        )

    with pytest.raises(IntakeError, match="Billing Contact"):
        ProjectIntake(
            project_name="Oak House",
            project_address=intake.project_address,
            project_use_case=intake.project_use_case,
            billing_contact_id="",
            client_contact_id="client-1",
        )


@pytest.mark.parametrize("field", ["project_name", "description"])
def test_project_intake_rejects_control_characters(field):
    values = {
        "project_name": "Oak House",
        "project_address": ProjectAddress("1842 Oak Street", "Oakland", "CA", "94612"),
        "project_use_case": ProjectUseCase("Renovation"),
        "billing_contact_id": "billing-1",
        "client_contact_id": "client-1",
        "description": "Kitchen",
    }
    values[field] = "bad\nvalue"

    with pytest.raises(IntakeError, match="control"):
        ProjectIntake(**values)


def test_contact_snapshot_normalizes_project_copy():
    contact = ContactSnapshot(
        id="contact-1",
        first_name="Ada",
        last_name="Lovelace",
        email="ADA@example.com",
        company="Analytical Engines",
    )

    assert contact.email == "ada@example.com"
    assert contact.full_name == "Ada Lovelace"
