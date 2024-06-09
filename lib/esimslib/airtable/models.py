"""AirTable Connector"""

import os

from typing import List

from pyairtable.utils import attachment
from pyairtable.orm import Model, fields


from esimslib.connectors import SSMConnector as ssm
from esimslib.util import logger
from esimslib.airtable.constants import (
    AirTableConst as air_c,
    EsimProviderConst as prov_c,
    EsimPackageConst as pack_c,
    EsimAssetConst as esim_c,
    EsimDonationConst as don_c,
)


# pylint: disable=too-few-public-methods


class EsimProvider(Model):
    """eSIM Providers Model"""

    provider_geo = fields.TextField(prov_c.PROVIDER_GEO, readonly=True)
    provider = fields.SelectField(prov_c.PROVIDER, readonly=True)
    geo = fields.SelectField(prov_c.GEO, readonly=True)
    stock_status = fields.SelectField(prov_c.STOCK_STATUS, readonly=True)
    in_stock = fields.CountField(prov_c.IN_STOCK, readonly=True)
    smdp_domain = fields.MultipleSelectField(prov_c.SMDP_DOMAIN, readonly=True)
    automatic_restock = fields.CheckboxField(
        prov_c.AUTOMATIC_RESTOCK, readonly=True
    )
    renewable = fields.CheckboxField(prov_c.RENEWABLE, readonly=True)

    @classmethod
    def fetch_all(cls) -> List["EsimProvider"]:
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


class EsimPackage(Model):
    """eSIM Packages model"""

    package = fields.TextField(pack_c.PACKAGE, readonly=True)
    _esim_provider = fields.LinkField(
        pack_c.ESIM_PROVIDER, EsimProvider, readonly=True
    )
    stock_err = fields.CheckboxField(pack_c.STOCK_ERR)

    @property
    def esim_provider(self) -> EsimProvider:
        """Get eSIM Provider

        Returns:
            EsimProvider: eSIM Provider
        """
        return self._esim_provider[0]

    @classmethod
    def fetch_all(cls) -> List["EsimPackage"]:
        """Fetch all ID, Names from table.

        Returns:
            list: list of providers records.
        """
        return cls.all(view=air_c.DEFAULT_VIEW)

    def set_stock_err(self) -> None:
        """Set stocking error flag."""
        if not self.stock_err:
            EsimPackage(id=self.id, stock_err=True).save()

    def reset_stock_err(self) -> None:
        """Reset stocking error flag."""
        if self.stock_err:
            EsimPackage(id=self.id, stock_err=False).save()

    class Meta:
        """Config subClass"""

        table_name = pack_c.TABLE_NAME
        base_id = os.getenv(air_c.AIRTABLE_BASE_ID)
        api_key = ssm().get_parameter(os.getenv(air_c.AIRTABLE_API_KEY))


class EsimDonation(Model):
    """eSIM Donations Model"""

    _esim_package = fields.LinkField(
        don_c.ESIM_PACKAGE, EsimPackage, readonly=True
    )
    qr_codes_att = fields.AttachmentsField(don_c.QR_CODES, readonly=True)
    is_ingested = fields.CheckboxField(don_c.INGESTED_FLAG)
    is_rejected = fields.CheckboxField(don_c.REJECTED_FLAG)
    is_of_invalid_type = fields.CheckboxField(don_c.IS_INVALID_TYPE)
    is_of_missing_qr = fields.CheckboxField(don_c.MISSING_QR)
    is_of_provider_mismatch = fields.CheckboxField(don_c.PROVIDER_MISMATCH)
    email = fields.TextField(don_c.CLEAN_EMAIL, readonly=True)
    is_duplicate = fields.CheckboxField(don_c.IS_DUPLICATE)
    _duplicate_original = fields.LinkField(
        don_c.ORIGINAL_DONATION, "EsimDonation"
    )
    is_inoriginal_donor = fields.CheckboxField(don_c.IS_INORIGINAL_DONOR)

    @property
    def esim_package(self) -> EsimPackage:
        """Get eSIM Package

        Returns:
            EsimPackage: eSIM Package
        """
        return self._esim_package[0]

    @property
    def duplicate_original(self) -> "EsimDonation":
        """Get Duplicate Original Donation

        Returns:
            EsimDonation | None: duplicate original donation
                if in record. None otherwise
        """
        if self._duplicate_original:
            return self._duplicate_original[0]
        return None

    @duplicate_original.setter
    def duplicate_original(self, original_donation: "EsimDonation") -> None:
        """Set Duplicate Original Donation

        Args:
            original_donation (EsimDonation): Original Donation Record.
        """
        self._duplicate_original = [original_donation]

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
        for attachment_ in self.qr_codes_att:
            urls[attachment_.get(don_c.SHA)] = attachment_.get(don_c.URL)
        return urls

    def set_as_ingested(self) -> None:
        """Set as ingested"""
        self.is_ingested = True

    def set_as_rejected(self) -> None:
        """Set Donor Error to True"""
        self.is_rejected = True

    class Meta:
        """Config subClass"""

        table_name = don_c.TABLE_NAME
        base_id = os.getenv(air_c.AIRTABLE_BASE_ID)
        api_key = ssm().get_parameter(os.getenv(air_c.AIRTABLE_API_KEY))


class EsimAsset(Model):
    """eSIM Inventory Model"""

    order_id = fields.AutoNumberField(esim_c.ORDER_ID, readonly=True)
    _esim_package = fields.LinkField(esim_c.ESIM_PACKAGE, EsimPackage)
    qr_code_image = fields.AttachmentsField(esim_c.QR_CODE)
    qr_sha = fields.TextField(esim_c.QR_SHA)
    _donation = fields.LinkField(esim_c.DONATION, EsimDonation)
    phone_number = fields.PhoneNumberField(esim_c.PHONE_NUMBER)

    @property
    def esim_package(self) -> EsimPackage:
        """Get eSIM Package

        Returns:
            EsimPackage | None: eSIM Package if in record.
                None otherwise.
        """
        if self._esim_package:
            return self._esim_package[0]
        return None

    @esim_package.setter
    def esim_package(self, value: EsimPackage) -> None:
        """Set eSIM Package

        Args:
            value (EsimPackage): eSIM Package.
        """
        self._esim_package = [value]

    @property
    def donation(self) -> EsimDonation:
        """Get Donation

        Returns:
            EsimDonation | None: Donation if in record.
                None otherwise.
        """
        if self._donation:
            return self._donation[0]
        return None

    @donation.setter
    def donation(self, value: EsimDonation) -> None:
        """Set Donation

        Args:
            value (EsimDonation): Donation
        """
        self._donation = [value]

    @classmethod
    def fetch_all(cls) -> List["EsimAsset"]:
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
    def format_esim_package_field(esim_package_id: str) -> EsimPackage:
        """Format esim package field

        Args:
            esim_package_id (str): eSIM Package id.

        Returns:
            list: eSIM Packages fields.
        """
        return EsimPackage(id=esim_package_id)

    class Meta:
        """Config subClass"""

        table_name = esim_c.TABLE_NAME
        base_id = os.getenv(air_c.AIRTABLE_BASE_ID)
        api_key = ssm().get_parameter(os.getenv(air_c.AIRTABLE_API_KEY))
