from esimslib.connectors import (
    SSMConnector,
    LayanConnector
)

from esimslib.airtable import (
    Providers,
    Attachments,
    Inventory
)


from esimslib.util import logger, ImageWithCaption

from io import BytesIO

from typing import (
    List,
    Dict,
    Any
)

def create_captioned_esim(esim: Dict[str, str], provider_networks: List[str], provider_gb: int, provider_days_valid: int) -> BytesIO:
    """Takes an esim object and creates a captioned QR code image

    Args:
        esim (Dict[str, str]): esim dict with the schema {"qr_code": URL_str, "phone_number": str}    
        provider_networks 

    Returns:
        BytesIO: Image Bytes object of the captioned image
    """
    qr_code_url = esim.get("qr_code")
    phone_number = esim.get("phone_number")


    networks_str = ", ".join(provider_networks)
    title = f"الشبكة: {networks_str}"

    text_line_1 = f'رقم الهاتف:  {phone_number}'
    text_line_2 = f'المساحة: {provider_gb} جيجا'
    text_line_3 = f'مدة الصلاحية: {provider_days_valid} يوم'

    # Create the captioned image
    image_creator = ImageWithCaption(qr_code_url, title, text_line_1, text_line_2, text_line_3)
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
        package_name=provider_name,
        target_count=quantity
    )
    
    results = []
    with ThreadPoolExecutor() as executor:
        future_to_sim = {executor.submit(create_captioned_esim, esim, provider_networks, provider_gb, provider_days_valid): esim for esim in esims_data}
        for future in as_completed(future_to_sim):
            try:
                result = future.result()
                results.append(result)
            except Exception as exc:
                print(f"An error occurred: {exc}")
    
    return results



def main():


    # Automatic restocking logic

    # TODO: Cycle through the restockable eSIMs 

    # If this is a restockable esims provider (Hot and wecom atm), and the inventory is low, then
    # batch request 50 esims, and generate the captioned QR code for each one
    automatic_restock_esims = []
    # TODO: Make this more concise
    restocking_conditions = provider.name == "HotMobile_110GB_30Days_Israel" and Inventory.hotmobile_inventory().low_flag and Inventory.hotmobile_inventory().automatic_restock_flag or \
    provider.name == "WeCom_500GB_30Days_Israel" and Inventory.wecom_inventory().low_flag and Inventory.wecom_inventory().automatic_restock_flag 

    if restocking_conditions:
        # TODO: Check if current inventory + len(objects) is less than the low inventory threshold 
        # (question: may this cause a cycle if invalid QR codes remain in the Dropbox and get reloaded in future runs?)
        if len(objects) < 20:
            issued_esims = batch_issue_esims_with_captioned_qr_codes(
                layan_client=layan_connector,
                package_name=provider.name,
                # TODO: Change this to 50+ when it is confirmed working
                quantity=1
                
                )
            if issued_esims:
                automatic_restock_esims.append(issued_esims)

    # Load each of the generated and captioned images into the S3 bucket
    restocked_esim_urls = [
        s3_connector.load_data(data=esim.get("qr_code"), key=f"{provider.name}esim_{esim.get("phone_number")}.png")
        for esim in automatic_restock_esims
    ]