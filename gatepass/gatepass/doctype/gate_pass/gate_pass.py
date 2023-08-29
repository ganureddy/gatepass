# Copyright (c) 2023, Ganu Reddy and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from erpnext.accounts.party import  get_party_details

class GatePass(Document):
	pass


@frappe.whitelist()
def party_address_details(party,party_type,company):
        
    party_details = get_party_details(
        party=party,
		party_type=party_type,
		company=company,
		doctype=None,
		party_address=None,
		company_address=None,
		shipping_address=None,
	)        
    return party_details
