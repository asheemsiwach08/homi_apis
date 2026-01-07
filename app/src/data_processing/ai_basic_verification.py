import logging
logger = logging.getLogger(__name__)


def safe_int_compare(value1, value2):
    """
    Safely compare two values as integers, handling None, "Not found", and empty values.
    
    Args:
        value1: First value to compare
        value2: Second value to compare
        
    Returns:
        bool: True if values are equal as integers, False otherwise
    """
    try:
        # Handle None, "Not found", or empty values
        if value1 in [None, "Not found", ""] or value2 in [None, "Not found", ""]:
            return False
        
        return int(value1) == int(value2)
    except (ValueError, TypeError):
        return False



def ai_basic_verification(ai_data, basic_data):
    """
    This method is used to verify the data from AI analysis 
    and data saved in Basic database
    """
    bankAppId_verified = []
    if not ai_data and not basic_data:
        logger.warning("No data found for verification.")
        return "No data found for verification."

    for ai_item in ai_data:
        items_verified = {}
        bankAppId = ai_item.get('bankAppId')
        basic_item = basic_data.get(bankAppId)

        if basic_item is None:
            basic_item = basic_data.get(ai_item.get('loanAccountNumber'))

        if basic_item in ["", "Not Found", "Not found"]:
            continue

        try:
            # Correct it when live with the API data
            # basic_item_data = basic_item.get("data")[0]
            basic_item_data = basic_item

            if not basic_item_data:
                logger.warning(f"No matching bankAppId found for {bankAppId}")
                continue

            ai_extracted_name = ai_item.get('firstName').lower() + " " + ai_item.get('lastName').lower()
            basic_extracted_name = basic_item_data.get('firstName').lower() + " " + basic_item_data.get('lastName').lower()
            
            # Match the data
            if ai_extracted_name.strip() == basic_extracted_name.strip():
                items_verified['firstName'] = ai_item.get('firstName')
                items_verified['lastName'] = ai_item.get('lastName')
            else:
                items_verified['firstName'] = ""
                items_verified['lastName'] = ""

            if ai_item.get('loanAccountNumber') == basic_item_data.get('loanAccountNumber'):
                items_verified['loanAccountNumber'] = basic_item_data.get('loanAccountNumber')
            else:
                items_verified['loanAccountNumber'] = ""

            # Safe date comparison for disbursedOn
            try:
                basic_disbursed_on = basic_item_data.get('disbursedOn')
                if basic_disbursed_on and 'T' in str(basic_disbursed_on):
                    disbursedOn = basic_disbursed_on.split('T')[0]
                else:
                    disbursedOn = basic_disbursed_on
            except (AttributeError, TypeError):
                disbursedOn = basic_item_data.get('disbursedOn')

            if ai_item.get('disbursedOn') == disbursedOn:
                items_verified['disbursedOn'] = ai_item.get('disbursedOn')
            else:
                items_verified['disbursedOn'] = ""
            
            # Safe date comparison for disbursedCreatedOn
            try:
                basic_disbursed_created = basic_item_data.get('disbursedCreatedOn')
                if basic_disbursed_created and 'T' in str(basic_disbursed_created):
                    disbursedCreatedOn = basic_disbursed_created.split('T')[0]
                else:
                    disbursedCreatedOn = basic_disbursed_created
            except (AttributeError, TypeError):
                disbursedCreatedOn = basic_item_data.get('disbursedCreatedOn')

            if ai_item.get('disbursedCreatedOn') == disbursedCreatedOn:   
                items_verified['disbursedCreatedOn'] = ai_item.get('disbursedCreatedOn')
            else:
                items_verified['disbursedCreatedOn'] = ""
            
            # Safe date comparison for sanctionDate
            try:
                basic_sanction = basic_item_data.get('sanctionDate')
                if basic_sanction and 'T' in str(basic_sanction):
                    sanctionDate = basic_sanction.split('T')[0]
                else:
                    sanctionDate = basic_sanction
            except (AttributeError, TypeError):
                sanctionDate = basic_item_data.get('sanctionDate')

            if ai_item.get('sanctionDate') == sanctionDate:
                items_verified['sanctionDate'] = ai_item.get('sanctionDate')
            else:
                items_verified['sanctionDate'] = ""

            # Safe comparison for disbursementAmount
            if safe_int_compare(ai_item.get('disbursementAmount'), basic_item_data.get('disbursementAmount')):
                items_verified['disbursementAmount'] = ai_item.get('disbursementAmount')
            else:
                items_verified['disbursementAmount'] = ""

            # Safe comparison for loanSanctionAmount
            if safe_int_compare(ai_item.get('loanSanctionAmount'), basic_item_data.get('loanSanctionAmount')):
                items_verified['loanSanctionAmount'] = ai_item.get('loanSanctionAmount')
            else:
                items_verified['loanSanctionAmount'] = ""

            if ai_item.get('bankAppId') == basic_item_data.get('bankAppId'):
                items_verified['bankAppId'] = ai_item.get('bankAppId')
            else:
                items_verified['bankAppId'] = ""
            
            if ai_item.get('basicAppId') == basic_item_data.get('basicAppId'):
                items_verified['basicAppId'] = ai_item.get('basicAppId')
            else:
                items_verified['basicAppId'] = ""
            
            if ai_item.get('disbursementId') == basic_item_data.get('disbursementId'):
                items_verified['disbursementId'] = ai_item.get('disbursementId')
            else:
                items_verified['disbursementId'] = ""
            
            if ai_item.get('appBankName') == basic_item_data.get('appBankName'):
                items_verified['appBankName'] = ai_item.get('appBankName')
            else:
                items_verified['appBankName'] = ""

            if ai_item.get('disbursementStage') == basic_item_data.get('disbursementStage'):
                items_verified['disbursementStage'] = ai_item.get('disbursementStage')
            else:
                items_verified['disbursementStage'] = basic_item_data.get('disbursementStage')
            
            if ai_item.get('disbursementStatus') == basic_item_data.get('disbursementStatus'):
                items_verified['disbursementStatus'] = ai_item.get('disbursementStatus')
            else:
                items_verified['disbursementStatus'] = basic_item_data.get('disbursementStatus')

            if ai_item.get('primaryborrowerMobile') == basic_item_data.get('primaryborrowerMobile'):
                items_verified['primaryborrowerMobile'] = ai_item.get('primaryborrowerMobile')
            else:
                items_verified['primaryborrowerMobile'] = ""
            
            if ai_item.get('pdd') == basic_item_data.get('pdd'):
                items_verified['pdd'] = ai_item.get('pdd')
            else:
                items_verified['pdd'] = ""

            if ai_item.get('otc') == basic_item_data.get('otc'):
                items_verified['otc'] = ai_item.get('otc')
            else:
                items_verified['otc'] = ""

            if ai_item.get('sourcingChannel') == basic_item_data.get('sourcingChannel'):
                items_verified['sourcingChannel'] = ai_item.get('sourcingChannel')
            else:
                items_verified['sourcingChannel'] = ""

            if ai_item.get('sourcingCode') == basic_item_data.get('sourcingCode'):
                items_verified['sourcingCode'] = ai_item.get('sourcingCode')
            else:
                items_verified['sourcingCode'] = ""
            
            if ai_item.get('applicationProductType') == basic_item_data.get('applicationProductType'):
                items_verified['applicationProductType'] = ai_item.get('applicationProductType')
            else:
                items_verified['applicationProductType'] = ""

            items_verified['VerificationStatus'] = "VerifiedByAI"

            bankAppId_verified.append(items_verified)
            
        except Exception as e:
            logger.warning(f"Error in ai_basic_verification: {e}")
            continue
    
    return bankAppId_verified

    
            



    
