from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import partial
from restockesims.constants import RestockEsimsConst as r_c

from io import BytesIO
from esimslib.connectors import (
    SSMConnector,
    S3Connector,
    LayanConnector
)

from esimslib.airtable import (
    EsimAsset,
    EsimProvider,
    EsimPackage
)

from esimslib.util import logger, ImageWithCaption, QRCodeProcessor

from typing import (
    List,
    Dict,
    Any
)

def _create_captioned_esim(esim: Dict[str, str], provider_networks: List[str], provider_gb: int, provider_days_valid: int) -> List[Dict[str, Any]]:
    """Takes an esim object and creates a captioned QR code image

    Args:
        esim (Dict[str, str]): esim dict with the schema {"qr_code": URL_str, "phone_number": str}    
        provider_networks 

    Returns:
        Dict: 
        Returns an eSIM object with the following schmema 
        {"phone_number": $PHONE_NUMER, "qr_code": BYTES_IO_IMAGE_OBJECT}
        
    """
    qr_code_url = esim.get("qr_code")
    phone_number = esim.get("phone_number")


    networks_str = ", ".join(provider_networks)
    title = f"الشبكة: {networks_str}"

    text_line_1 = f'رقم الهاتف:  {phone_number}'
    text_line_2 = f'المساحة: {provider_gb} جيجا'
    text_line_3 = f'مدة الصلاحية: {provider_days_valid} يوم'
    text_line_4 = f'الشريحة قابلة للتجديد عند الانتهاء'

    # Create the captioned image
    image_creator = ImageWithCaption(qr_code_url, title, text_line_1, text_line_2, text_line_3, text_line_4)
    captioned_esim = image_creator.create_image()

    return {
        "phone_number": phone_number,
        "qr_code": captioned_esim
    }

def batch_issue_esims_with_captioned_qr_codes(layan_client: LayanConnector, provider_name: str, provider_networks: List[str], provider_gb: int,
                                              provider_days_valid: int, quantity: int) -> List[Dict[str, Any]]:
    """Issues Layan-T esims of the specified quantity. This makes a number of concurrent calls to the Layan-T API
    and does not guarantee exactly as many results as the specified quantity, but a close approximation.

    Args:
        layan_client (LayanConnector): The instance of the authenticated Layan-Client to issue eSIMs with
        package_name (str): The name of the restockable package to issue esims for. (currently supports WeCom_500GB_30Days_Israel and HotMobile_110GB_30Days_Israel)
        quantity (int): The amount of esims to issue

    Returns:
        List[Dict[str, Any]]: List of captioned eSIM JSON objects with the schema
        [
            {
            "phone_number": str,
            "qr_code": BytesIO Image Object
            }
        ]
    """
    esims_data = layan_client.batch_issue_esims(
        provider_name=provider_name,
        target_count=quantity
    )
    
    results = []
    with ThreadPoolExecutor() as executor:
        future_to_sim = {executor.submit(_create_captioned_esim, esim, provider_networks, provider_gb, provider_days_valid): esim for esim in esims_data}
        for future in as_completed(future_to_sim):
            try:
                result = future.result()
                results.append(result)
            except Exception as exc:
                logger.error(f"An error occurred: {exc}")
    
    return results

def validate_qr_asset(esim_package: EsimPackage, image_url: str) -> EsimAsset:
    """Validate QR Asset.

    Args:
        esim_package (EsimPackage): eSIM Package.
        image_url (str): QR Code image URL.

    Returns:
        EsimAsset | None: eSIM Asset if valid.
    """
    new_asset = EsimAsset()
    new_asset.esim_package = esim_package
    new_asset.qr_code_image = image_url
    processor = QRCodeProcessor(image_url)
    if not processor.detect_qr():
        return None
    if not processor.validate_qr_code_protocol():
        return None
    if esim_package.esim_provider.smdp_domain:
        if not processor.validate_smdp_domain(
            esim_package.esim_provider.smdp_domain
        ):
            return None
    new_asset.qr_sha = processor.qr_sha
    if esim_package.esim_provider.renewable:
        if not processor.detect_phone_number():
            return None
        new_asset.phone_number = processor.phone_number
    return new_asset

def deduplicate_assets(assets: List[EsimAsset]) -> List[EsimAsset]:
    """Remove duplicate QR Codes.

    Args:
        assets (List[EsimAsset]): eSIM Assets.

    Returns:
        List[EsimAsset]: eSIM Assets without duplicates.
    """
    qr_shas = set()
    unique_esims = []
    for esim_asset in assets:
        if esim_asset.qr_sha in qr_shas:
            continue
        qr_shas.add(esim_asset.qr_sha)
        unique_esims.append(esim_asset)
    return unique_esims

def main()-> None:
    """Main Service Driver."""
    logger.info("Starting e-sims transport service")
    # load connectors
    s3_connector = S3Connector()
    layan_connector = LayanConnector()

    # Automatic restocking logic
    esim_providers: List[EsimProvider] = EsimProvider.fetch_all()

    for provider in esim_providers:
        logger.info("Processing Esims provider: %s", provider.provider)

        # If this is an eSIM provider with automatic_restock checked, and with stock_status == "Low"
        if provider.automatic_restock and provider.stock_status == "Low":
            automatic_restock_esims = []
            
            issued_esims = batch_issue_esims_with_captioned_qr_codes(
                layan_client=layan_connector,
                provider_name=provider.name,                
                quantity=r_c.RESTOCK_AMOUNT
                )
            if issued_esims:
                automatic_restock_esims.append(issued_esims)

            logger.info("Batch Issued %s esims", len(issued_esims))

        # Load each of the generated and captioned images into the S3 bucket
        restocked_esim_urls = [
            s3_connector.load_data(data=esim.get("qr_code"), key=f"{provider.name}_esim_{esim.get("phone_number")}.png")
            for esim in automatic_restock_esims
        ]
  
        logger.info("S3 Loaded Sims: %s", len(restocked_esim_urls))


        # NOTE: For the two restockable providers at this time, there is only one package, so just pick the first one.
        package = provider.packages[0]

        # validate qr codes
        partial_validate_qr_code = partial(validate_qr_asset, package)

        validated_assets = list(map(partial_validate_qr_code, restocked_esim_urls))
        valid_esim_assets = deduplicate_assets(
            list(filter(None, validated_assets))
        )
        logger.info("Valid Sims: %s", len(valid_esim_assets))

        # upload to AirTable
        EsimAsset.load_records(valid_esim_assets)
        logger.info("Uploaded to AirTable: %s", package)

    
# pylint: disable=unused-argument
def handler(event: dict, context: dict) -> None:
    """Lambda Handler

    Args:
        event (dict): Lambda event
        context (dict): Lambda context

    Raises:
        Exception: Exception raised if refresh token fails
    """
    try:
        main()
    except Exception as exc:
        logger.error("Restocking esims failed: %s", exc)
        raise exc


if __name__ == "__main__":
    main()
