# Copyright (c) 2023, Ganu Reddy and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from erpnext.accounts.party import  get_party_details
from erpnext.stock.stock_ledger import NegativeStockError, get_previous_sle, get_valuation_rate

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

def create_stock_ledger_entry_through_gatepass(self,method=None):
    '''
    This Method Create Stock Ledger Entry Through Gate Pass After Submit.
    Also Cancel of Stock Ledger Entry Of Same Voucher No.
    
    '''
    gate_pass_item = {
        "doctype":"Stock Ledger Entry",
        'item_code':None,
        'warehouse':None,
        'posting_date':None,
        'posting_time':None,
        'actual_qty':0,
        'voucher_type':"Gate Pass",
        'valuation_rate':0.0,
        'voucher_no':None,
        "company":None,
        'fiscal_year':None,
        'qty_after_transaction':0,
        'stock_uom':None,
        'stock_value':0.0,
        'stock_value_difference':0.0,
        'stock_queue':None,
        "incoming_rate":0.0,
        'outgoing_rate':0.0
    }
    
    if method == 'on_submit':
        
        for i in range(len(self.item)):
            gate_pass_item.update({
                'item_code':self.item[i].item_code,
                'warehouse':self.source_warehouse,
                "posting_date":self.date,
                'posting_time':self.time,
                'actual_qty':-self.item[i].qty,
                'stock_uom':self.item[i].uom,
                'company':self.company,
                'voucher_no':self.item[i].parent,
                "valuation_rate":(self.item[i].qty*self.item[i].rate),
                "stock_value_difference":-(self.item[i].qty*self.item[i].rate)
            })
            
            # its Give last or previous stock ledger entry of this item code 
            previous_sle = get_previous_sle({
                        "item_code": self.item[i].item_code,
                        "warehouse": self.source_warehouse or self.source_warehouse,
                        "posting_date": self.date,
                        "posting_time": self.time,
            })
            
            gate_pass_item.update({
                "qty_after_transaction":(previous_sle['qty_after_transaction']-self.item[i].qty),
                "stock_value":(previous_sle["stock_value"] -gate_pass_item['valuation_rate']),
            })
            
            after_transaction = gate_pass_item['qty_after_transaction']
            queue = gate_pass_item['valuation_rate']
            stock_queue= f"[[{after_transaction}, {queue}]]"
            
            gate_pass_item.update({
                "stock_queue":stock_queue,
                'fiscal_year':previous_sle['fiscal_year'],
                'voucher_detail_no':self.item[i].name
            })
            
            # enrty create
            data = frappe.get_doc(gate_pass_item)
            data.docstatus = 1
            data.insert()
            
    if method == 'on_cancel':
        self.ignore_linked_doctypes = ("Stock Ledger Entry")
        frappe.db.set_value("Stock Ledger Entry", {"voucher_no":self.name}, "is_cancelled", 1)
        frappe.db.commit()
        
        
@frappe.whitelist()        
def material_returns():
    print("-----------------------------------------")    