"""
Tests for RCS registration (registration, dossier, brands, agents)
"""

import json
import re

import pytest
from pytest_httpx import HTTPXMock

from sendly import AsyncSendly, Sendly
from sendly.errors import AuthenticationError, NotFoundError, SendlyError, ValidationError
from sendly.types import (
    RcsAgentBasics,
    RcsAgentDetail,
    RcsBrand,
    RcsBrandAddress,
    RcsBrandContact,
    RcsCampaign,
    RcsCustomerStage,
    RcsDossier,
    RcsRegistration,
    RcsReviewStatus,
    RcsTestDeviceInput,
    RcsTestDeviceListResponse,
)

BASE = "https://sendly.live/api/v1"
AUTO_KEY = re.compile(r"^sendly-python-retry-[0-9a-f-]{36}$")


def _body(httpx_mock: HTTPXMock):
    return json.loads(httpx_mock.get_request().read().decode())


@pytest.fixture
def mock_brand():
    return {
        "id": "rcs_brand_123",
        "reviewStatus": "draft",
        "customerStage": "draft",
        "displayName": "Acme Coffee",
        "legalName": "Acme Holdings LLC",
        "legalEntityType": "LIMITED_LIABILITY_COMPANY",
        "organizationType": "PRIVATE_PROFIT",
        "stockSymbol": None,
        "websiteUrl": "https://acme.example",
        "ein": "12-3456789",
        "address": {
            "line1": "1 Main St",
            "line2": None,
            "city": "Austin",
            "state": "TX",
            "postalCode": "78701",
            "countryCode": "US",
        },
        "contact": {
            "firstName": "Sam",
            "lastName": "Lee",
            "title": None,
            "email": "sam@acme.example",
            "phoneNumber": "+15551234567",
        },
        "reviewNote": None,
        "rejectionReason": None,
        "submittedForReviewAt": None,
        "sentToCarrierAt": None,
        "verifiedAt": None,
        "createdAt": "2026-09-01T10:00:00.000Z",
        "updatedAt": "2026-09-01T10:00:00.000Z",
    }


@pytest.fixture
def mock_device():
    return {
        "id": "rcs_dev_1",
        "phoneNumber": "+15551234567",
        "label": "Sam",
        "inviteStatus": None,
        "createdAt": "2026-09-02T10:00:00.000Z",
    }


@pytest.fixture
def mock_agent(mock_device):
    return {
        "id": "rcs_agent_123",
        "brandId": "rcs_brand_123",
        "status": "draft",
        "reviewStatus": "draft",
        "customerStage": "draft",
        "displayName": "Acme Coffee",
        "useCase": "MULTI_USE",
        "hostingRegion": None,
        "basics": {
            "displayName": "Acme Coffee",
            "useCase": "MULTI_USE",
            "hostingRegion": None,
            "description": "Order updates and support",
            "logoUrl": "https://acme.example/logo.png",
            "heroUrl": "https://acme.example/hero.png",
            "brandColor": "#5B3A29",
            "website": {"url": "https://acme.example", "label": "Acme"},
        },
        "campaign": None,
        "testing": None,
        "reviewNote": None,
        "rejectionReason": None,
        "testDevices": [mock_device],
        "submittedForReviewAt": None,
        "basicsSubmittedAt": None,
        "launchSubmittedAt": None,
        "liveAt": None,
        "createdAt": "2026-09-01T11:00:00.000Z",
        "updatedAt": "2026-09-01T11:00:00.000Z",
    }


@pytest.fixture
def mock_dossier():
    return {
        "brand": {
            "legalName": "Acme Holdings LLC",
            "displayName": "Acme",
            "ein": "12-3456789",
            "organizationType": "PRIVATE_PROFIT",
            "websiteUrl": "https://acme.example",
            "address": {
                "line1": "1 Main St",
                "city": "Austin",
                "state": "TX",
                "postalCode": "78701",
                "countryCode": "US",
            },
            "contact": {
                "firstName": "Sam",
                "lastName": "Lee",
                "email": "sam@acme.example",
                "phoneNumber": "+15551234567",
            },
        },
        "usEligible": True,
        "source": "tendlc",
    }


class TestRegistrationGet:
    def test_get(self, api_key, mock_brand, mock_agent, mock_device, httpx_mock: HTTPXMock):
        client = Sendly(api_key)

        httpx_mock.add_response(
            url=f"{BASE}/rcs/registration",
            method="GET",
            json={
                "brand": mock_brand,
                "agent": {**mock_agent, "customerStage": "testing", "status": "testing"},
                "devices": [mock_device],
                "stage": "testing",
                "usEligible": True,
            },
        )

        result = client.rcs.registration.get()

        assert isinstance(result, RcsRegistration)
        assert result.stage == "testing"
        assert result.stage == RcsCustomerStage.TESTING
        assert result.us_eligible is True
        assert isinstance(result.brand, RcsBrand)
        assert result.brand.legal_entity_type == "LIMITED_LIABILITY_COMPANY"
        assert result.brand.address.postal_code == "78701"
        assert result.brand.contact.phone_number == "+15551234567"
        assert isinstance(result.agent, RcsAgentDetail)
        assert result.agent.customer_stage == RcsCustomerStage.TESTING
        assert result.agent.basics.logo_url == "https://acme.example/logo.png"
        assert result.agent.basics.website.url == "https://acme.example"
        assert result.devices[0].phone_number == "+15551234567"
        assert result.devices[0].invite_status is None

        request = httpx_mock.get_request()
        assert "Idempotency-Key" not in request.headers

        client.close()

    def test_get_empty(self, api_key, httpx_mock: HTTPXMock):
        client = Sendly(api_key)

        httpx_mock.add_response(
            url=f"{BASE}/rcs/registration",
            method="GET",
            json={
                "brand": None,
                "agent": None,
                "devices": [],
                "stage": "draft",
                "usEligible": True,
            },
        )

        result = client.rcs.registration.get()

        assert result.brand is None
        assert result.agent is None
        assert result.devices == []
        assert result.stage == RcsCustomerStage.DRAFT

        client.close()

    def test_get_not_enabled_404(self, api_key, mock_error_response, httpx_mock: HTTPXMock):
        client = Sendly(api_key, max_retries=0)

        httpx_mock.add_response(
            url=f"{BASE}/rcs/registration",
            method="GET",
            status_code=404,
            json=mock_error_response(
                "rcs_not_enabled", "RCS registration isn't enabled for this account yet."
            ),
        )

        with pytest.raises(SendlyError) as exc_info:
            client.rcs.registration.get()

        assert exc_info.value.code == "rcs_not_enabled"
        assert exc_info.value.status_code == 404
        assert not isinstance(exc_info.value, NotFoundError)
        assert "isn't enabled" in exc_info.value.message

        client.close()

    def test_get_insufficient_permissions_403(
        self, api_key, mock_error_response, httpx_mock: HTTPXMock
    ):
        client = Sendly(api_key, max_retries=0)

        httpx_mock.add_response(
            url=f"{BASE}/rcs/registration",
            method="GET",
            status_code=403,
            json=mock_error_response("insufficient_permissions", "Missing scope rcs:read"),
        )

        with pytest.raises(AuthenticationError) as exc_info:
            client.rcs.registration.get()

        assert exc_info.value.code == "insufficient_permissions"

        client.close()


class TestDossierGet:
    def test_get(self, api_key, mock_dossier, httpx_mock: HTTPXMock):
        client = Sendly(api_key)

        httpx_mock.add_response(url=f"{BASE}/rcs/dossier", method="GET", json=mock_dossier)

        result = client.rcs.dossier.get()

        assert isinstance(result, RcsDossier)
        assert result.source == "tendlc"
        assert result.us_eligible is True
        assert result.brand.legal_name == "Acme Holdings LLC"
        assert result.brand.legal_entity_type is None
        assert result.brand.address.country_code == "US"
        assert result.brand.contact.first_name == "Sam"

        client.close()

    def test_get_prefills_brand_create(
        self, api_key, mock_dossier, mock_brand, httpx_mock: HTTPXMock
    ):
        client = Sendly(api_key)

        httpx_mock.add_response(url=f"{BASE}/rcs/dossier", method="GET", json=mock_dossier)
        httpx_mock.add_response(
            url=f"{BASE}/rcs/brands", method="POST", status_code=201, json={"brand": mock_brand}
        )

        dossier = client.rcs.dossier.get()
        client.rcs.brands.create(**dossier.brand.model_dump(exclude_none=True))

        body = json.loads(httpx_mock.get_requests()[1].read().decode())
        assert body["legalName"] == "Acme Holdings LLC"
        assert body["address"]["countryCode"] == "US"
        assert body["contact"]["phoneNumber"] == "+15551234567"
        assert "legalEntityType" not in body

        client.close()

    def test_get_empty(self, api_key, httpx_mock: HTTPXMock):
        client = Sendly(api_key)

        httpx_mock.add_response(
            url=f"{BASE}/rcs/dossier",
            method="GET",
            json={"brand": {}, "usEligible": False, "source": "none"},
        )

        result = client.rcs.dossier.get()

        assert result.source == "none"
        assert result.us_eligible is False
        assert result.brand.address is None

        client.close()

    def test_get_not_enabled_404(self, api_key, mock_error_response, httpx_mock: HTTPXMock):
        client = Sendly(api_key, max_retries=0)

        httpx_mock.add_response(
            url=f"{BASE}/rcs/dossier",
            method="GET",
            status_code=404,
            json=mock_error_response("rcs_not_enabled", "Not enabled"),
        )

        with pytest.raises(SendlyError) as exc_info:
            client.rcs.dossier.get()

        assert exc_info.value.code == "rcs_not_enabled"

        client.close()


class TestBrandsCreate:
    def test_create(self, api_key, mock_brand, httpx_mock: HTTPXMock):
        client = Sendly(api_key)

        httpx_mock.add_response(
            url=f"{BASE}/rcs/brands", method="POST", status_code=201, json={"brand": mock_brand}
        )

        result = client.rcs.brands.create(
            display_name="Acme Coffee",
            legal_name="Acme Holdings LLC",
            legal_entity_type="LIMITED_LIABILITY_COMPANY",
            organization_type="PRIVATE_PROFIT",
            website_url="https://acme.example",
            ein="12-3456789",
            address={
                "line1": "1 Main St",
                "city": "Austin",
                "state": "TX",
                "postal_code": "78701",
                "country_code": "US",
            },
            contact=RcsBrandContact(
                first_name="Sam",
                last_name="Lee",
                email="sam@acme.example",
                phone_number="+15551234567",
            ),
        )

        assert isinstance(result, RcsBrand)
        assert result.id == "rcs_brand_123"
        assert result.review_status == RcsReviewStatus.DRAFT
        assert result.customer_stage == "draft"
        assert result.stock_symbol is None
        assert result.address.line2 is None
        assert result.contact.email == "sam@acme.example"

        request = httpx_mock.get_request()
        assert request.method == "POST"
        assert AUTO_KEY.match(request.headers["Idempotency-Key"])
        body = json.loads(request.read().decode())
        assert body == {
            "displayName": "Acme Coffee",
            "legalName": "Acme Holdings LLC",
            "legalEntityType": "LIMITED_LIABILITY_COMPANY",
            "organizationType": "PRIVATE_PROFIT",
            "websiteUrl": "https://acme.example",
            "ein": "12-3456789",
            "address": {
                "line1": "1 Main St",
                "city": "Austin",
                "state": "TX",
                "postalCode": "78701",
                "countryCode": "US",
            },
            "contact": {
                "firstName": "Sam",
                "lastName": "Lee",
                "email": "sam@acme.example",
                "phoneNumber": "+15551234567",
            },
        }

        client.close()

    def test_create_accepts_camel_case_dicts(self, api_key, mock_brand, httpx_mock: HTTPXMock):
        client = Sendly(api_key)

        httpx_mock.add_response(
            url=f"{BASE}/rcs/brands", method="POST", status_code=201, json={"brand": mock_brand}
        )

        client.rcs.brands.create(
            address={"line1": "1 Main St", "postalCode": "78701", "countryCode": "US"},
        )

        body = _body(httpx_mock)
        assert body == {
            "address": {"line1": "1 Main St", "postalCode": "78701", "countryCode": "US"}
        }

        client.close()

    def test_create_with_explicit_idempotency_key(
        self, api_key, mock_brand, httpx_mock: HTTPXMock
    ):
        client = Sendly(api_key)

        httpx_mock.add_response(
            url=f"{BASE}/rcs/brands", method="POST", status_code=201, json={"brand": mock_brand}
        )

        client.rcs.brands.create(display_name="Acme Coffee", idempotency_key="brand-acme-1")

        assert httpx_mock.get_request().headers["Idempotency-Key"] == "brand-acme-1"

        client.close()

    def test_create_rejects_bad_nested_input_before_request(self, api_key):
        client = Sendly(api_key)

        with pytest.raises(ValidationError, match="address"):
            client.rcs.brands.create(address="1 Main St")

        client.close()

    def test_create_us_only_422(self, api_key, mock_error_response, httpx_mock: HTTPXMock):
        client = Sendly(api_key, max_retries=0)

        httpx_mock.add_response(
            url=f"{BASE}/rcs/brands",
            method="POST",
            status_code=422,
            json=mock_error_response(
                "rcs_us_only", "RCS registration is available to US businesses for now."
            ),
        )

        with pytest.raises(SendlyError) as exc_info:
            client.rcs.brands.create(address={"country_code": "GB"})

        assert exc_info.value.code == "rcs_us_only"
        assert exc_info.value.status_code == 422
        assert exc_info.value.field_errors == []

        client.close()

    def test_create_not_enabled_404(self, api_key, mock_error_response, httpx_mock: HTTPXMock):
        client = Sendly(api_key, max_retries=0)

        httpx_mock.add_response(
            url=f"{BASE}/rcs/brands",
            method="POST",
            status_code=404,
            json=mock_error_response("rcs_not_enabled", "Not enabled"),
        )

        with pytest.raises(SendlyError) as exc_info:
            client.rcs.brands.create(display_name="Acme Coffee")

        assert exc_info.value.code == "rcs_not_enabled"
        assert exc_info.value.status_code == 404

        client.close()


class TestBrandsUpdate:
    def test_update_sends_only_present_fields(
        self, api_key, mock_brand, httpx_mock: HTTPXMock
    ):
        client = Sendly(api_key)

        httpx_mock.add_response(
            url=f"{BASE}/rcs/brands/rcs_brand_123",
            method="PATCH",
            json={"brand": {**mock_brand, "stockSymbol": "NASDAQ:ACME"}},
        )

        result = client.rcs.brands.update(
            "rcs_brand_123",
            stock_symbol="NASDAQ:ACME",
            address=RcsBrandAddress(line2=None),
            idempotency_key="brand-acme-2",
        )

        assert result.stock_symbol == "NASDAQ:ACME"

        request = httpx_mock.get_request()
        assert request.method == "PATCH"
        assert request.headers["Idempotency-Key"] == "brand-acme-2"
        assert json.loads(request.read().decode()) == {
            "stockSymbol": "NASDAQ:ACME",
            "address": {"line2": None},
        }

        client.close()

    def test_update_no_auto_idempotency_key(self, api_key, mock_brand, httpx_mock: HTTPXMock):
        client = Sendly(api_key)

        httpx_mock.add_response(
            url=f"{BASE}/rcs/brands/rcs_brand_123", method="PATCH", json={"brand": mock_brand}
        )

        client.rcs.brands.update("rcs_brand_123", legal_name="Acme Holdings LLC")

        assert "Idempotency-Key" not in httpx_mock.get_request().headers

        client.close()

    def test_update_field_locked_409(self, api_key, mock_error_response, httpx_mock: HTTPXMock):
        client = Sendly(api_key, max_retries=0)

        httpx_mock.add_response(
            url=f"{BASE}/rcs/brands/rcs_brand_123",
            method="PATCH",
            status_code=409,
            json=mock_error_response(
                "rcs_field_locked",
                "This registration is being reviewed; we will email you if changes are needed.",
            ),
        )

        with pytest.raises(SendlyError) as exc_info:
            client.rcs.brands.update("rcs_brand_123", legal_name="Acme")

        assert exc_info.value.code == "rcs_field_locked"
        assert exc_info.value.status_code == 409

        client.close()

    def test_update_not_found_404(self, api_key, mock_error_response, httpx_mock: HTTPXMock):
        client = Sendly(api_key, max_retries=0)

        httpx_mock.add_response(
            url=f"{BASE}/rcs/brands/other",
            method="PATCH",
            status_code=404,
            json=mock_error_response("rcs_not_found", "Brand not found"),
        )

        with pytest.raises(SendlyError) as exc_info:
            client.rcs.brands.update("other", legal_name="Acme")

        assert exc_info.value.code == "rcs_not_found"

        client.close()


class TestAgentsCreate:
    def test_create(self, api_key, mock_agent, httpx_mock: HTTPXMock):
        client = Sendly(api_key)

        httpx_mock.add_response(
            url=f"{BASE}/rcs/agents", method="POST", status_code=201, json={"agent": mock_agent}
        )

        result = client.rcs.agents.create(
            "rcs_brand_123",
            display_name="Acme Coffee",
            use_case="MULTI_USE",
            basics={
                "description": "Order updates and support",
                "logo_url": "https://acme.example/logo.png",
                "hero_url": "https://acme.example/hero.png",
                "brand_color": "#5B3A29",
                "privacy_policy_url": "https://acme.example/privacy",
                "terms_and_conditions_url": "https://acme.example/terms",
                "website": {"url": "https://acme.example", "label": "Acme"},
                "phone_number": {"number": "+15551234567", "label": "Support"},
            },
            campaign=RcsCampaign(
                agent_overview="Order updates and support replies",
                interactions=[
                    {
                        "interaction_type": "TRANSACTIONAL_UPDATES",
                        "description": "Shipping updates",
                    }
                ],
                message_examples=["Your order #123 has shipped!"],
                consent_settings={
                    "opt_in_methods": [
                        {"method_type": "WEBSITE", "description": "Checkout checkbox"}
                    ],
                    "double_opt_in": False,
                    "opt_out_response": "You are unsubscribed.",
                },
            ),
            testing={"test_url": "https://acme.example/test", "message_id": "msg_1"},
        )

        assert isinstance(result, RcsAgentDetail)
        assert result.id == "rcs_agent_123"
        assert result.brand_id == "rcs_brand_123"
        assert result.status == "draft"
        assert result.review_status == "draft"
        assert result.customer_stage == RcsCustomerStage.DRAFT
        assert result.use_case == "MULTI_USE"
        assert isinstance(result.basics, RcsAgentBasics)
        assert result.basics.brand_color == "#5B3A29"
        assert result.basics.privacy_policy_url is None
        assert result.campaign is None
        assert result.testing is None
        assert result.test_devices[0].label == "Sam"

        request = httpx_mock.get_request()
        assert request.method == "POST"
        assert AUTO_KEY.match(request.headers["Idempotency-Key"])
        body = json.loads(request.read().decode())
        assert body == {
            "brandId": "rcs_brand_123",
            "displayName": "Acme Coffee",
            "useCase": "MULTI_USE",
            "basics": {
                "description": "Order updates and support",
                "logoUrl": "https://acme.example/logo.png",
                "heroUrl": "https://acme.example/hero.png",
                "brandColor": "#5B3A29",
                "privacyPolicyUrl": "https://acme.example/privacy",
                "termsAndConditionsUrl": "https://acme.example/terms",
                "website": {"url": "https://acme.example", "label": "Acme"},
                "phoneNumber": {"number": "+15551234567", "label": "Support"},
            },
            "campaign": {
                "agentOverview": "Order updates and support replies",
                "interactions": [
                    {
                        "interactionType": "TRANSACTIONAL_UPDATES",
                        "description": "Shipping updates",
                    }
                ],
                "messageExamples": ["Your order #123 has shipped!"],
                "consentSettings": {
                    "optInMethods": [
                        {"methodType": "WEBSITE", "description": "Checkout checkbox"}
                    ],
                    "doubleOptIn": False,
                    "optOutResponse": "You are unsubscribed.",
                },
            },
            "testing": {"testUrl": "https://acme.example/test", "messageId": "msg_1"},
        }

        client.close()

    def test_create_minimal(self, api_key, mock_agent, httpx_mock: HTTPXMock):
        client = Sendly(api_key)

        httpx_mock.add_response(
            url=f"{BASE}/rcs/agents", method="POST", status_code=201, json={"agent": mock_agent}
        )

        client.rcs.agents.create("rcs_brand_123")

        assert _body(httpx_mock) == {"brandId": "rcs_brand_123"}

        client.close()

    def test_create_invalid_content_422_exposes_field_errors(
        self, api_key, mock_error_response, httpx_mock: HTTPXMock
    ):
        client = Sendly(api_key, max_retries=0)

        httpx_mock.add_response(
            url=f"{BASE}/rcs/agents",
            method="POST",
            status_code=422,
            json=mock_error_response(
                "rcs_invalid_content",
                "Assets can't be uploaded over the API. Logo, hero, and call-to-action "
                "media must be public https:// URLs.",
                errors=[{"path": "basics.logoUrl", "message": "Must be a public https:// URL"}],
            ),
        )

        with pytest.raises(SendlyError) as exc_info:
            client.rcs.agents.create(
                "rcs_brand_123", basics={"logo_url": "http://acme.example/logo.png"}
            )

        assert exc_info.value.code == "rcs_invalid_content"
        assert exc_info.value.status_code == 422
        assert exc_info.value.field_errors == [
            {"path": "basics.logoUrl", "message": "Must be a public https:// URL"}
        ]

        client.close()

    def test_create_not_enabled_404(self, api_key, mock_error_response, httpx_mock: HTTPXMock):
        client = Sendly(api_key, max_retries=0)

        httpx_mock.add_response(
            url=f"{BASE}/rcs/agents",
            method="POST",
            status_code=404,
            json=mock_error_response("rcs_not_enabled", "Not enabled"),
        )

        with pytest.raises(SendlyError) as exc_info:
            client.rcs.agents.create("rcs_brand_123")

        assert exc_info.value.code == "rcs_not_enabled"

        client.close()


class TestAgentsGet:
    def test_get(self, api_key, mock_agent, mock_device, httpx_mock: HTTPXMock):
        client = Sendly(api_key)

        httpx_mock.add_response(
            url=f"{BASE}/rcs/agents/rcs_agent_123",
            method="GET",
            json={
                "agent": {
                    **mock_agent,
                    "status": "testing",
                    "reviewStatus": "approved_for_carrier",
                    "customerStage": "testing",
                    "reviewNote": "Add a privacy policy link",
                    "basicsSubmittedAt": "2026-09-03T10:00:00.000Z",
                    "testDevices": [{**mock_device, "inviteStatus": "PENDING"}],
                },
                "devices": [{**mock_device, "inviteStatus": "PENDING"}],
                "stage": "testing",
            },
        )

        result = client.rcs.agents.get("rcs_agent_123")

        assert isinstance(result, RcsAgentDetail)
        assert result.status == "testing"
        assert result.review_status == RcsReviewStatus.APPROVED_FOR_CARRIER
        assert result.customer_stage == RcsCustomerStage.TESTING
        assert result.review_note == "Add a privacy policy link"
        assert result.basics_submitted_at == "2026-09-03T10:00:00.000Z"
        assert result.test_devices[0].invite_status == "PENDING"

        request = httpx_mock.get_request()
        assert request.method == "GET"
        assert "Idempotency-Key" not in request.headers

        client.close()

    def test_get_not_found_404(self, api_key, mock_error_response, httpx_mock: HTTPXMock):
        client = Sendly(api_key, max_retries=0)

        httpx_mock.add_response(
            url=f"{BASE}/rcs/agents/other",
            method="GET",
            status_code=404,
            json=mock_error_response("rcs_not_found", "Agent not found"),
        )

        with pytest.raises(SendlyError) as exc_info:
            client.rcs.agents.get("other")

        assert exc_info.value.code == "rcs_not_found"
        assert exc_info.value.status_code == 404

        client.close()

    def test_get_not_enabled_404(self, api_key, mock_error_response, httpx_mock: HTTPXMock):
        client = Sendly(api_key, max_retries=0)

        httpx_mock.add_response(
            url=f"{BASE}/rcs/agents/rcs_agent_123",
            method="GET",
            status_code=404,
            json=mock_error_response("rcs_not_enabled", "Not enabled"),
        )

        with pytest.raises(SendlyError) as exc_info:
            client.rcs.agents.get("rcs_agent_123")

        assert exc_info.value.code == "rcs_not_enabled"

        client.close()

    def test_get_invalid_response(self, api_key, httpx_mock: HTTPXMock):
        client = Sendly(api_key)

        httpx_mock.add_response(
            url=f"{BASE}/rcs/agents/rcs_agent_123", method="GET", json={"ok": True}
        )

        with pytest.raises(SendlyError) as exc_info:
            client.rcs.agents.get("rcs_agent_123")

        assert exc_info.value.code == "invalid_response"

        client.close()


class TestAgentsUpdate:
    def test_update_campaign_section(self, api_key, mock_agent, httpx_mock: HTTPXMock):
        client = Sendly(api_key)

        campaign = {
            "agentOverview": "Order updates and support replies",
            "interactions": [
                {"interactionType": "CUSTOMER_SUPPORT", "description": "Support replies"}
            ],
            "messageExamples": ["A", "B", "C"],
            "consentSettings": {"optOutResponse": "You are unsubscribed."},
        }
        httpx_mock.add_response(
            url=f"{BASE}/rcs/agents/rcs_agent_123",
            method="PATCH",
            json={"agent": {**mock_agent, "campaign": campaign}},
        )

        result = client.rcs.agents.update(
            "rcs_agent_123",
            campaign={
                "agent_overview": "Order updates and support replies",
                "interactions": [
                    {"interaction_type": "CUSTOMER_SUPPORT", "description": "Support replies"}
                ],
                "message_examples": ["A", "B", "C"],
                "consent_settings": {"opt_out_response": "You are unsubscribed."},
            },
            idempotency_key="agent-campaign-1",
        )

        assert isinstance(result.campaign, RcsCampaign)
        assert result.campaign.interactions[0].interaction_type == "CUSTOMER_SUPPORT"
        assert result.campaign.message_examples == ["A", "B", "C"]
        assert result.campaign.consent_settings.opt_out_response == "You are unsubscribed."

        request = httpx_mock.get_request()
        assert request.method == "PATCH"
        assert request.headers["Idempotency-Key"] == "agent-campaign-1"
        assert json.loads(request.read().decode()) == {"campaign": campaign}

        client.close()

    def test_update_basics_group(self, api_key, mock_agent, httpx_mock: HTTPXMock):
        client = Sendly(api_key)

        httpx_mock.add_response(
            url=f"{BASE}/rcs/agents/rcs_agent_123", method="PATCH", json={"agent": mock_agent}
        )

        client.rcs.agents.update(
            "rcs_agent_123",
            display_name="Acme Coffee",
            basics=RcsAgentBasics(hero_url="https://acme.example/hero2.png"),
        )

        body = _body(httpx_mock)
        assert body == {
            "displayName": "Acme Coffee",
            "basics": {"heroUrl": "https://acme.example/hero2.png"},
        }
        assert "brandId" not in body

        client.close()

    def test_update_field_locked_409(self, api_key, mock_error_response, httpx_mock: HTTPXMock):
        client = Sendly(api_key, max_retries=0)

        httpx_mock.add_response(
            url=f"{BASE}/rcs/agents/rcs_agent_123",
            method="PATCH",
            status_code=409,
            json=mock_error_response("rcs_field_locked", "This registration is being reviewed"),
        )

        with pytest.raises(SendlyError) as exc_info:
            client.rcs.agents.update("rcs_agent_123", display_name="Acme")

        assert exc_info.value.code == "rcs_field_locked"

        client.close()


class TestAgentsSetTestDevices:
    def test_set_test_devices(self, api_key, mock_device, httpx_mock: HTTPXMock):
        client = Sendly(api_key)

        httpx_mock.add_response(
            url=f"{BASE}/rcs/agents/rcs_agent_123/test-devices",
            method="PUT",
            json={
                "devices": [
                    {**mock_device, "inviteStatus": "PENDING"},
                    {
                        "id": "rcs_dev_2",
                        "phoneNumber": "+15557654321",
                        "label": None,
                        "inviteStatus": None,
                        "createdAt": "2026-09-02T11:00:00.000Z",
                    },
                ]
            },
        )

        result = client.rcs.agents.set_test_devices(
            "rcs_agent_123",
            [
                "+15557654321",
                {"phone_number": "+15551234567", "label": "Sam"},
                RcsTestDeviceInput(phone_number="+15550000000", label="QA"),
            ],
            idempotency_key="devices-1",
        )

        assert isinstance(result, RcsTestDeviceListResponse)
        assert [d.phone_number for d in result.devices] == ["+15551234567", "+15557654321"]
        assert result.devices[0].invite_status == "PENDING"
        assert result.devices[1].label is None

        request = httpx_mock.get_request()
        assert request.method == "PUT"
        assert request.headers["Idempotency-Key"] == "devices-1"
        assert json.loads(request.read().decode()) == {
            "devices": [
                {"phoneNumber": "+15557654321"},
                {"phoneNumber": "+15551234567", "label": "Sam"},
                {"phoneNumber": "+15550000000", "label": "QA"},
            ]
        }

        client.close()

    def test_set_test_devices_empty_list_clears(self, api_key, httpx_mock: HTTPXMock):
        client = Sendly(api_key)

        httpx_mock.add_response(
            url=f"{BASE}/rcs/agents/rcs_agent_123/test-devices",
            method="PUT",
            json={"devices": []},
        )

        result = client.rcs.agents.set_test_devices("rcs_agent_123", [])

        assert result.devices == []
        assert _body(httpx_mock) == {"devices": []}

        client.close()

    def test_set_test_devices_rejects_non_list(self, api_key):
        client = Sendly(api_key)

        with pytest.raises(ValidationError, match="must be a list"):
            client.rcs.agents.set_test_devices("rcs_agent_123", "+15551234567")

        with pytest.raises(ValidationError, match="devices"):
            client.rcs.agents.set_test_devices("rcs_agent_123", [{"label": "no number"}])

        client.close()

    def test_set_test_devices_invalid_content_422(
        self, api_key, mock_error_response, httpx_mock: HTTPXMock
    ):
        client = Sendly(api_key, max_retries=0)

        httpx_mock.add_response(
            url=f"{BASE}/rcs/agents/rcs_agent_123/test-devices",
            method="PUT",
            status_code=422,
            json=mock_error_response(
                "rcs_invalid_content",
                "Check the devices",
                errors=[
                    {
                        "path": "devices.0.phoneNumber",
                        "message": "Enter the device's phone number in E.164 format, "
                        "like +13125550100",
                    }
                ],
            ),
        )

        with pytest.raises(SendlyError) as exc_info:
            client.rcs.agents.set_test_devices("rcs_agent_123", ["555"])

        assert exc_info.value.code == "rcs_invalid_content"
        assert exc_info.value.field_errors[0]["path"] == "devices.0.phoneNumber"

        client.close()


class TestAgentsSubmit:
    def test_submit(self, api_key, mock_agent, httpx_mock: HTTPXMock):
        client = Sendly(api_key)

        httpx_mock.add_response(
            url=f"{BASE}/rcs/agents/rcs_agent_123/submit",
            method="POST",
            json={
                "agent": {
                    **mock_agent,
                    "status": "submitted",
                    "reviewStatus": "awaiting_review",
                    "customerStage": "in_review",
                    "submittedForReviewAt": "2026-09-03T09:00:00.000Z",
                },
                "stage": "in_review",
            },
        )

        result = client.rcs.agents.submit("rcs_agent_123")

        assert isinstance(result, RcsAgentDetail)
        assert result.review_status == RcsReviewStatus.AWAITING_REVIEW
        assert result.customer_stage == RcsCustomerStage.IN_REVIEW
        assert result.submitted_for_review_at == "2026-09-03T09:00:00.000Z"

        request = httpx_mock.get_request()
        assert request.method == "POST"
        assert AUTO_KEY.match(request.headers["Idempotency-Key"])
        assert json.loads(request.read().decode()) == {}

        client.close()

    def test_submit_with_explicit_idempotency_key(
        self, api_key, mock_agent, httpx_mock: HTTPXMock
    ):
        client = Sendly(api_key)

        httpx_mock.add_response(
            url=f"{BASE}/rcs/agents/rcs_agent_123/submit",
            method="POST",
            json={"agent": mock_agent, "stage": "in_review"},
        )

        client.rcs.agents.submit("rcs_agent_123", idempotency_key="submit-rcs_agent_123")

        assert httpx_mock.get_request().headers["Idempotency-Key"] == "submit-rcs_agent_123"

        client.close()

    def test_submit_invalid_content_422(
        self, api_key, mock_error_response, httpx_mock: HTTPXMock
    ):
        client = Sendly(api_key, max_retries=0)

        httpx_mock.add_response(
            url=f"{BASE}/rcs/agents/rcs_agent_123/submit",
            method="POST",
            status_code=422,
            json=mock_error_response(
                "rcs_invalid_content",
                "Finish the brand and agent before submitting",
                errors=[
                    {"path": "brand.ein", "message": "Enter a 9-digit EIN"},
                    {"path": "agent.logoUrl", "message": "Must be a public https:// URL"},
                ],
            ),
        )

        with pytest.raises(SendlyError) as exc_info:
            client.rcs.agents.submit("rcs_agent_123")

        assert exc_info.value.code == "rcs_invalid_content"
        assert [e["path"] for e in exc_info.value.field_errors] == [
            "brand.ein",
            "agent.logoUrl",
        ]

        client.close()

    def test_submit_already_submitted_409(
        self, api_key, mock_error_response, httpx_mock: HTTPXMock
    ):
        client = Sendly(api_key, max_retries=0)

        httpx_mock.add_response(
            url=f"{BASE}/rcs/agents/rcs_agent_123/submit",
            method="POST",
            status_code=409,
            json=mock_error_response(
                "rcs_field_locked", "This agent has already been submitted for review."
            ),
        )

        with pytest.raises(SendlyError) as exc_info:
            client.rcs.agents.submit("rcs_agent_123")

        assert exc_info.value.code == "rcs_field_locked"

        client.close()

    def test_submit_not_enabled_404(self, api_key, mock_error_response, httpx_mock: HTTPXMock):
        client = Sendly(api_key, max_retries=0)

        httpx_mock.add_response(
            url=f"{BASE}/rcs/agents/rcs_agent_123/submit",
            method="POST",
            status_code=404,
            json=mock_error_response("rcs_not_enabled", "Not enabled"),
        )

        with pytest.raises(SendlyError) as exc_info:
            client.rcs.agents.submit("rcs_agent_123")

        assert exc_info.value.code == "rcs_not_enabled"

        client.close()


class TestAgentsRequestLaunch:
    def test_request_launch(self, api_key, mock_agent, httpx_mock: HTTPXMock):
        client = Sendly(api_key)

        httpx_mock.add_response(
            url=f"{BASE}/rcs/agents/rcs_agent_123/request-launch",
            method="POST",
            json={
                "agent": {
                    **mock_agent,
                    "status": "testing",
                    "reviewStatus": "launch_requested",
                    "customerStage": "launch_review",
                    "testing": {
                        "testUrl": "https://acme.example/test",
                        "messageId": None,
                        "additionalInformation": "Tested on Pixel",
                    },
                },
                "stage": "launch_review",
            },
        )

        result = client.rcs.agents.request_launch(
            "rcs_agent_123",
            test_url="https://acme.example/test",
            testing_additional_information="Tested on Pixel",
        )

        assert result.review_status == RcsReviewStatus.LAUNCH_REQUESTED
        assert result.customer_stage == RcsCustomerStage.LAUNCH_REVIEW
        assert result.testing.test_url == "https://acme.example/test"
        assert result.testing.additional_information == "Tested on Pixel"

        request = httpx_mock.get_request()
        assert request.method == "POST"
        assert AUTO_KEY.match(request.headers["Idempotency-Key"])
        assert json.loads(request.read().decode()) == {
            "testUrl": "https://acme.example/test",
            "testingAdditionalInformation": "Tested on Pixel",
        }

        client.close()

    def test_request_launch_without_body(self, api_key, mock_agent, httpx_mock: HTTPXMock):
        client = Sendly(api_key)

        httpx_mock.add_response(
            url=f"{BASE}/rcs/agents/rcs_agent_123/request-launch",
            method="POST",
            json={"agent": mock_agent, "stage": "launch_review"},
        )

        client.rcs.agents.request_launch("rcs_agent_123", idempotency_key="launch-1")

        request = httpx_mock.get_request()
        assert request.headers["Idempotency-Key"] == "launch-1"
        assert json.loads(request.read().decode()) == {}

        client.close()

    def test_request_launch_not_ready_409(
        self, api_key, mock_error_response, httpx_mock: HTTPXMock
    ):
        client = Sendly(api_key, max_retries=0)

        httpx_mock.add_response(
            url=f"{BASE}/rcs/agents/rcs_agent_123/request-launch",
            method="POST",
            status_code=409,
            json=mock_error_response(
                "rcs_launch_not_ready",
                "This agent isn't ready to launch yet. Finish testing on an invited "
                "device first.",
            ),
        )

        with pytest.raises(SendlyError) as exc_info:
            client.rcs.agents.request_launch("rcs_agent_123")

        assert exc_info.value.code == "rcs_launch_not_ready"
        assert exc_info.value.status_code == 409

        client.close()

    def test_request_launch_invalid_content_422(
        self, api_key, mock_error_response, httpx_mock: HTTPXMock
    ):
        client = Sendly(api_key, max_retries=0)

        httpx_mock.add_response(
            url=f"{BASE}/rcs/agents/rcs_agent_123/request-launch",
            method="POST",
            status_code=422,
            json=mock_error_response(
                "rcs_invalid_content",
                "Finish the campaign before requesting launch",
                errors=[
                    {"path": "campaign.messageExamples", "message": "Add at least 3 examples"},
                    {"path": "testing.testUrl", "message": "Add a link to your test"},
                ],
            ),
        )

        with pytest.raises(SendlyError) as exc_info:
            client.rcs.agents.request_launch("rcs_agent_123")

        assert exc_info.value.code == "rcs_invalid_content"
        assert len(exc_info.value.field_errors) == 2

        client.close()

    def test_request_launch_not_enabled_404(
        self, api_key, mock_error_response, httpx_mock: HTTPXMock
    ):
        client = Sendly(api_key, max_retries=0)

        httpx_mock.add_response(
            url=f"{BASE}/rcs/agents/rcs_agent_123/request-launch",
            method="POST",
            status_code=404,
            json=mock_error_response("rcs_not_enabled", "Not enabled"),
        )

        with pytest.raises(SendlyError) as exc_info:
            client.rcs.agents.request_launch("rcs_agent_123")

        assert exc_info.value.code == "rcs_not_enabled"

        client.close()


class TestExistingRcsSurfaceUnchanged:
    def test_agents_list_still_plain(self, api_key, httpx_mock: HTTPXMock):
        client = Sendly(api_key)

        httpx_mock.add_response(
            url=f"{BASE}/rcs/agents",
            method="GET",
            json={
                "agents": [
                    {
                        "id": "rcs_agent_123",
                        "name": "Acme Coffee",
                        "status": "approved",
                        "useCase": "MULTI_USE",
                        "sendable": True,
                        "stage": "live",
                        "createdAt": "2026-07-30T09:12:00Z",
                    }
                ]
            },
        )

        result = client.rcs.agents.list()

        assert result.agents[0].sendable is True

        client.close()


class TestAsyncRcsRegistration:
    async def test_async_registration_get(self, api_key, httpx_mock: HTTPXMock):
        client = AsyncSendly(api_key)

        httpx_mock.add_response(
            url=f"{BASE}/rcs/registration",
            method="GET",
            json={
                "brand": None,
                "agent": None,
                "devices": [],
                "stage": "draft",
                "usEligible": True,
            },
        )

        result = await client.rcs.registration.get()

        assert result.stage == RcsCustomerStage.DRAFT

        await client.close()

    async def test_async_dossier_get(self, api_key, mock_dossier, httpx_mock: HTTPXMock):
        client = AsyncSendly(api_key)

        httpx_mock.add_response(url=f"{BASE}/rcs/dossier", method="GET", json=mock_dossier)

        result = await client.rcs.dossier.get()

        assert result.source == "tendlc"

        await client.close()

    async def test_async_brands_create_and_update(
        self, api_key, mock_brand, httpx_mock: HTTPXMock
    ):
        client = AsyncSendly(api_key)

        httpx_mock.add_response(
            url=f"{BASE}/rcs/brands", method="POST", status_code=201, json={"brand": mock_brand}
        )
        httpx_mock.add_response(
            url=f"{BASE}/rcs/brands/rcs_brand_123", method="PATCH", json={"brand": mock_brand}
        )

        created = await client.rcs.brands.create(
            legal_name="Acme Holdings LLC", address={"country_code": "US"}
        )
        updated = await client.rcs.brands.update(
            created.id, ein="12-3456789", idempotency_key="brand-async-1"
        )

        assert updated.id == "rcs_brand_123"
        requests = httpx_mock.get_requests()
        assert json.loads(requests[0].read().decode()) == {
            "legalName": "Acme Holdings LLC",
            "address": {"countryCode": "US"},
        }
        assert requests[1].method == "PATCH"
        assert requests[1].headers["Idempotency-Key"] == "brand-async-1"
        assert json.loads(requests[1].read().decode()) == {"ein": "12-3456789"}

        await client.close()

    async def test_async_agent_lifecycle(
        self, api_key, mock_agent, mock_device, httpx_mock: HTTPXMock
    ):
        client = AsyncSendly(api_key)

        httpx_mock.add_response(
            url=f"{BASE}/rcs/agents", method="POST", status_code=201, json={"agent": mock_agent}
        )
        httpx_mock.add_response(
            url=f"{BASE}/rcs/agents/rcs_agent_123",
            method="GET",
            json={"agent": mock_agent, "devices": [mock_device], "stage": "draft"},
        )
        httpx_mock.add_response(
            url=f"{BASE}/rcs/agents/rcs_agent_123", method="PATCH", json={"agent": mock_agent}
        )
        httpx_mock.add_response(
            url=f"{BASE}/rcs/agents/rcs_agent_123/test-devices",
            method="PUT",
            json={"devices": [mock_device]},
        )
        httpx_mock.add_response(
            url=f"{BASE}/rcs/agents/rcs_agent_123/submit",
            method="POST",
            json={"agent": {**mock_agent, "reviewStatus": "awaiting_review"}, "stage": "in_review"},
        )
        httpx_mock.add_response(
            url=f"{BASE}/rcs/agents/rcs_agent_123/request-launch",
            method="POST",
            json={
                "agent": {**mock_agent, "reviewStatus": "launch_requested"},
                "stage": "launch_review",
            },
        )

        agent = await client.rcs.agents.create("rcs_brand_123", display_name="Acme Coffee")
        fetched = await client.rcs.agents.get(agent.id)
        updated = await client.rcs.agents.update(agent.id, testing={"test_url": "https://t"})
        devices = await client.rcs.agents.set_test_devices(agent.id, ["+15551234567"])
        submitted = await client.rcs.agents.submit(agent.id)
        launched = await client.rcs.agents.request_launch(agent.id, test_url="https://t")

        assert fetched.id == agent.id == updated.id
        assert devices.devices[0].id == "rcs_dev_1"
        assert submitted.review_status == "awaiting_review"
        assert launched.review_status == "launch_requested"

        methods = [(r.method, r.url.path) for r in httpx_mock.get_requests()]
        assert methods == [
            ("POST", "/api/v1/rcs/agents"),
            ("GET", "/api/v1/rcs/agents/rcs_agent_123"),
            ("PATCH", "/api/v1/rcs/agents/rcs_agent_123"),
            ("PUT", "/api/v1/rcs/agents/rcs_agent_123/test-devices"),
            ("POST", "/api/v1/rcs/agents/rcs_agent_123/submit"),
            ("POST", "/api/v1/rcs/agents/rcs_agent_123/request-launch"),
        ]
        assert json.loads(httpx_mock.get_requests()[2].read().decode()) == {
            "testing": {"testUrl": "https://t"}
        }

        await client.close()

    async def test_async_not_enabled_404(
        self, api_key, mock_error_response, httpx_mock: HTTPXMock
    ):
        client = AsyncSendly(api_key, max_retries=0)

        httpx_mock.add_response(
            url=f"{BASE}/rcs/registration",
            method="GET",
            status_code=404,
            json=mock_error_response("rcs_not_enabled", "Not enabled"),
        )

        with pytest.raises(SendlyError) as exc_info:
            await client.rcs.registration.get()

        assert exc_info.value.code == "rcs_not_enabled"
        assert exc_info.value.status_code == 404

        await client.close()
