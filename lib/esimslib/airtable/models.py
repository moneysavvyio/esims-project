"""AirTable Connector"""

import os

from pyairtable.utils import attachment
from pyairtable.orm import Model, fields

from esimslib.connectors.aws_connector import SSMConnector as ssm
from esimslib.airtable.constants import (
    AirTableConst as air_c,
    ProvidersModelConst as prov_c,
    DonationsModelConst as don_c,
    AttachmentModelConst as att_c,
)
from esimslib.util.logger import logger

# pylint: disable=too-few-public-methods


class Providers(Model):
    """eSIM Providers Model"""

    name = fields.TextField(prov_c.NAME)
    qr_text = fields.SelectField(prov_c.QR_TEXT)

    @classmethod
    def fetch_all(cls) -> list:
        """Fetch all ID, Names from table.

        Returns:
            list: list of providers records.
        """
        return cls.all(view=air_c.DEFAULT_VIEW)

    class Meta:
        """Config subClass"""

        table_name = prov_c.TABLE_NAME
        base_id = os.getenv(air_c.AIRTABLE_BASE_ID)
        api_key = ssm().get_parameter(os.getenv(air_c.AIRTABLE_API_KEY))


class Donations(Model):
    """eSIM Donations Model"""

    esim_provider = fields.LinkField(don_c.ESIM_PROVIDER, Providers)
    qr_codes = fields.AttachmentsField(don_c.QR_CODE)
    in_use_flag = fields.SelectField(don_c.IN_USE_FLAG)
    donor_error = fields.CheckboxField(don_c.DONOR_ERROR)
    invalid_type = fields.CheckboxField(don_c.INVALID_TYPE)
    missing_qr = fields.CheckboxField(don_c.MISSING_QR)
    provider_mismatch = fields.CheckboxField(don_c.PROVIDER_MISMATCH)
    email = fields.TextField(don_c.EMAIL)
    duplicate = fields.CheckboxField(don_c.DUPLICATE)
    original = fields.LinkField(don_c.ORIGINAL, "Donations")

    @classmethod
    def fetch_all(cls) -> list:
        """Fetch all new donations.

        Returns:
            list: list of donation records.
        """
        return cls.all(view=air_c.DEFAULT_VIEW)

    def extract_urls(self) -> dict:
        """Extract SHA: URL from attachment.

        Returns:
            dict: {SHA: URL}.
        """
        urls = {}
        for attachment_ in self.qr_codes:
            urls[attachment_.get(don_c.SHA)] = attachment_.get(don_c.URL)
        return urls

    def set_in_use(self) -> None:
        """Set in use Flag to Yes"""
        self.in_use_flag = don_c.YES

    def set_donor_error(self) -> None:
        """Set Donor Error to True"""
        self.donor_error = True

    def set_duplicate_error(self) -> None:
        """Set Duplicate Error to True"""
        self.duplicate = True

    class Meta:
        """Config subClass"""

        table_name = don_c.TABLE_NAME
        base_id = os.getenv(air_c.AIRTABLE_BASE_ID)
        api_key = ssm().get_parameter(os.getenv(air_c.AIRTABLE_API_KEY))


class Attachments(Model):
    """E-SIMs Linked Model"""

    esim_provider = fields.LinkField(att_c.ESIM_PROVIDER, Providers)
    attachment = fields.AttachmentsField(att_c.ATTACHMENT)
    donor = fields.LinkField(att_c.DONOR, Donations)
    qr_sha = fields.TextField(att_c.QR_SHA)
    order_id = fields.TextField(att_c.ORDER_ID)

    @classmethod
    def fetch_all(cls) -> list:
        """Fetch all duplicated eSIMs.

        Returns:
            list: list of linked eSIMs records.
        """
        return cls.all(view=air_c.DEFAULT_VIEW)

    @classmethod
    def load_records(cls, records: list) -> None:
        """Load records to AirTable

        Args:
            records (list): list of records to be loaded.

        Raises:
            Exception: if failed to connect to AirTable
        """
        try:
            cls.batch_save(records)
        except Exception as exc:
            logger.error("Airtable upload error: %s", exc)
            raise exc

    @staticmethod
    def format_attachment_field(url: str) -> list:
        """Format attachment field

        Args:
            url (str): URL of object.

        Returns:
            list: attachment field.
        """
        return [attachment(url=url)]

    @staticmethod
    def format_esim_provider_field(provider_id: str) -> list:
        """Format esim provider field

        Args:
            provider_id (str): Sim Provider Id.

        Returns:
            list: esim provider field.
        """
        return [Providers(id=provider_id)]

    class Meta:
        """Config subClass"""

        table_name = att_c.TABLE_NAME
        base_id = os.getenv(air_c.AIRTABLE_BASE_ID)
        api_key = ssm().get_parameter(os.getenv(air_c.AIRTABLE_API_KEY))
