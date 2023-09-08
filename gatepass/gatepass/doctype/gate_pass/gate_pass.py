# Copyright (c) 2023, Ganu Reddy and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from erpnext.accounts.party import  get_party_details
from erpnext.stock.stock_ledger import NegativeStockError, get_previous_sle, get_valuation_rate
import json
import pandas as pd

class GatePass(Document):
    pass
    


# GL Entry Creation base on gate pass types
def create_gl_entry_through_gate_pass(data,total,fiscal_year):
    '''
    This Method Is Used To Create GL Entry Againt Account.
    It's Used Both Returnable (In And Out Material)
    And Non Returnable (Out Material)
    
    '''
    # Company Account Detail
    company_account = frappe.get_doc("Company",data.company)
    
    gl_entry_raw_data = {
        'doctype':"GL Entry",
        "posting_date":None,
        "account":None,
        "cost_center":None,
        "debit":0.0,
        "credit":0.0,
        "account_currency":"INR",
        "against":None,
        "debit_in_account_currency":0.0,
        "credit_in_account_currency":0.0,
        "voucher_type":None,
        "voucher_no":None,
        "remarks":None,
        "is_opening":"No",
        "is_advance":"No",
        "fiscal_year":None,
        'company':None
    }
    
    # First entry for inventory account (Stock In Hand) for gate pass Out (Issue) or In (Receipt)
    gl_entry_raw_data.update({
        "posting_date":data.date,
        "account":company_account.default_inventory_account,
        "cost_center":company_account.cost_center,
        "credit":round(total,2) if data.status not in ["To Be Return","Partially Return"] else 0.0,
        
        "credit_in_account_currency":round(total,2)
        if data.status not in ["To Be Return","Partially Return"] else 0.0,
        
        "debit":0.0 if data.status not in ["To Be Return","Partially Return"] else round(total,2),
        
        "debit_in_account_currency":0.0 
        if data.status not in ["To Be Return","Partially Return"] else round(total,2),
        
        "against":company_account.default_expense_account 
        if data.status not in ["To Be Return","Partially Return"] else company_account.stock_adjustment_account,
        
        "voucher_type":data.doctype,
        'voucher_no':data.name,
        'remarks':"Accounting Entry for Stock",
        "fiscal_year":fiscal_year,
        "company":data.company
    })
    
    first_entry = frappe.get_doc(gl_entry_raw_data)
    first_entry.docstatus =1
    first_entry.insert()
        
    # Second entry for expense account Out (Cost of Goods Sold) or In (Stock Adjustment)
    gl_entry_raw_data.update({
        "account":company_account.default_expense_account if data.status not in ["To Be Return","Partially Return"] else company_account.stock_adjustment_account,
        
        "cost_center":company_account.cost_center,
        "credit":0.0 
        if data.status not in ["To Be Return","Partially Return"] else round(total,2),
        
        "credit_in_account_currency":0.0 
        if data.status not in ["To Be Return","Partially Return"] else round(total,2),
        
        "debit":round(total,2) 
        if data.status not in ["To Be Return","Partially Return"] else 0.0,
        
        "debit_in_account_currency":round(total,2) 
        if data.status not in ["To Be Return","Partially Return"] else 0.0,
        
        "against":company_account.default_inventory_account,
        "voucher_type":data.doctype,
        'voucher_no':data.name,
        'remarks':"Accounting Entry for Stock",
        "fiscal_year":fiscal_year,
        "company":data.company
    })
    
    second_entry = frappe.get_doc(gl_entry_raw_data)
    second_entry.docstatus = 1
    second_entry.insert()

  

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
    This Method Work On Gate Pass Type Is Non-Returnable And Returnable.
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
    
    total_amount = 0.0
    fiscal_year = None
    
    
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
                "valuation_rate":(self.item[i].rate),
                "stock_value_difference":-(self.item[i].qty*self.item[i].rate)
            })
            
            # its Give last or previous stock ledger entry of this item code 
            previous_sle = get_previous_sle({
                        "item_code": self.item[i].item_code,
                        "warehouse": self.source_warehouse or self.source_warehouse,
                        "posting_date": self.date,
                        "posting_time": self.time,
            })
            
            total_amount += (self.item[i].qty*self.item[i].rate)
            fiscal_year = previous_sle['fiscal_year']
            
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
            
        create_gl_entry_through_gate_pass(self,total_amount,fiscal_year)
        
        if self.gate_pass_type == 'Returnable' and self.docstatus == 1:
            frappe.db.set_value(self.doctype, {"name":self.name}, "status", "To Be Return")
            frappe.db.commit()
            
        if self.gate_pass_type == 'Non-Returnable' and self.docstatus == 1:
            frappe.db.set_value(self.doctype, {"name":self.name}, "status", "Completed")
            frappe.db.commit()
            
    if method == 'on_cancel':
        self.ignore_linked_doctypes = ("Stock Ledger Entry","GL Entry")
        frappe.db.set_value("Stock Ledger Entry", {"voucher_no":self.name}, "is_cancelled", 1)
        frappe.db.commit()
        
        frappe.db.set_value("GL Entry", {"voucher_no":self.name}, "is_cancelled", 1)
        frappe.db.commit()
        
        frappe.db.set_value(self.doctype, {"name":self.name}, "status", "Cancelled")
        frappe.db.commit()
        
    self.reload()
    frappe.db.commit()    
    
       
@frappe.whitelist()        
def material_returns_through_gatepass(doctype,name,return_item):
    print(doctype, name, return_item)
    
    
    data_details = frappe.get_doc(doctype,name)
    
    actual_items_in_gp = data_details.as_dict()['item']
    
    return_items = json.loads(return_item)['alternative_items']
    
    data = []
    
    for i in return_items:
        for j in actual_items_in_gp:
            if i['docname'] == j["name"]:
                data.append(i)
                continue
        
    if data_details.docstatus == 1:
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
        total_amount = 0.0
        fiscal_year = None
        
        for i in range(len(data)):
            gate_pass_item.update({
                'item_code':data[i]["item_code"],
                'warehouse':data_details.source_warehouse,
                "posting_date":data_details.date,
                'posting_time':data_details.time,
                'actual_qty':data[i]["qty"],
                'stock_uom':data[i]["uom"],
                'company':data_details.company,
                'voucher_no':data_details.name,
                "valuation_rate":(data[i]["rate"]),
                "stock_value_difference":(data[i]["qty"]*data[i]["rate"])
            })
            total_amount += (data[i]["qty"]*data[i]["rate"])
            
            # its Give last or previous stock ledger entry of this item code 
            previous_sle = get_previous_sle({
                        "item_code": data[i]["item_code"],
                        "warehouse": data_details.source_warehouse or data_details.source_warehouse,
                        "posting_date": data_details.date,
                        "posting_time": data_details.time,
            })
            
            fiscal_year = previous_sle['fiscal_year']
            
            gate_pass_item.update({
                "qty_after_transaction":(previous_sle['qty_after_transaction']+data[i]["qty"]),
                "stock_value":(previous_sle["stock_value"] + gate_pass_item['valuation_rate']),
            })
            
            after_transaction = gate_pass_item['qty_after_transaction']
            queue = gate_pass_item['valuation_rate']
            stock_queue= f"[[{after_transaction}, {queue}]]"
            
            gate_pass_item.update({
                "stock_queue":stock_queue,
                'fiscal_year':previous_sle['fiscal_year'],
                'voucher_detail_no':data[i]["docname"],
                'incoming_rate':data[i]["rate"]
            })
            
            # enrty create
            doc = frappe.get_doc(gate_pass_item)
            doc.docstatus = 1
            doc.insert()
            
        create_gl_entry_through_gate_pass(data_details,total_amount,fiscal_year)
        
        
        return {'success':True}
    
    
# update actual qty in item child table,
def update_actual_value(doc, method=None):
    for each in doc.item:
        frappe.db.set_value("Gate pass item details",{'name':each.name},"actual_qty", each.qty)
        frappe.db.commit()
        doc.reload()
        