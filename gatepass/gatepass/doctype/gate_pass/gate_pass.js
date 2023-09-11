// Copyright (c) 2023, Ganu Reddy and contributors
// For license information, please see license.txt

frappe.ui.form.on('Gate Pass', {
	party: function(frm) {
		if(frm.doc.party != '' && frm.doc.party_type != ''){
			frappe.call({
				method:"gatepass.gatepass.doctype.gate_pass.gate_pass.party_address_details",
				args:{
					party:frm.doc.party,
					party_type:frm.doc.party_type,
					company:frm.doc.company
				},
				callback: function(r){
					if (r.message){
						frm.set_value("company_address_name",r.message.company_address)
						frm.set_value("shipping_address_name",r.message.shipping_address_name)
						let company_address_display = r.message.company_address_display.replace("<br>\n","\n")
						let company_details = company_address_display.split("<br>")
						let comp_value = ''
						for (let i = 0; i < company_details.length; i++) {
							comp_value += company_details[i] + '\n'
						};
						frm.set_value("company_address",comp_value);
						let shipping_address = r.message.shipping_address.replace("<br>\n","\n");
						let new_value = shipping_address.split("<br>");
						let custom_value = '';
						for (let j = 0; j < new_value.length; j++) {
							custom_value += new_value[j] + '\n'
						};
						frm.set_value("shipping_address",custom_value);
					}
				}
	
			})
		}
		
	}
});

// frappe.ui.form.on('Gate Pass', {
// 	item: function(frm) {
// 		if (frm.doc.item){
// 			let total = 0.0
// 			let item = frm.doc.item
// 			item.forEach(f=>{
// 				console.log(f,";;;;;;;;;;;;;;;;;;;")
// 				total += (f.qty * f.rate)
// 			})
// 			frm.set_value("total",total)

// 		}
// 	}
// })


frappe.ui.form.on('Gate Pass', {
    refresh: function(frm) {
		if(frm.doc.docstatus === 1 && frm.doc.status !== 'Cancelled' && frm.doc.status !== "Completed"){
			frm.add_custom_button(__('Material Returns'), function() {
				let data = [];
				let child_docname = "item"
				let child_doctype = "Gate pass item details"
				
				let dialogs = new frappe.ui.Dialog({
					title: __('Item Details'),
					fields: [
						{fieldtype:'Section Break', label: __('Items')},
						{
							fieldname: "alternative_items", fieldtype: "Table", cannot_add_rows: true,
							in_place_edit: true, data: data,
							get_data: () => {
								return data;
							},
							fields: [{
								fieldtype:'Data',
								fieldname:"docname",
								hidden: 1
							},
							{
								fieldtype:'Link',
								fieldname:"item_code",
								options: 'Item',
								in_list_view: 1,
								read_only: 1,
								label: __('Item Code')
							},{
								fieldtype:'Data',
								fieldname:"item_name",
								default: "",
								fetch_from: "item_code.item_name",
								in_list_view: 1,
								label: __('Item Name'),
							},{
								fieldtype:'Float',
								fieldname:"actual_qty",
								read_only: 1,
								in_list_view: 1,
								label: __('Actual Qty')
							},
							{
								fieldtype:'Float',
								fieldname:"qty",
								// read_only: 1,
								in_list_view: 1,
								label: __('Qty')
							},
							{
								fieldtype:'Float',
								fieldname:"amount",
								read_only: 1,
								in_list_view: 1,
								label: __('Amount')
							},
							{
								fieldtype:'Link',
								fieldname:"uom",
								options: 'UOM',
								read_only: 1,
								in_list_view: 1,
								label: __('UOM')
							},{
								fieldtype:'Float',
								fieldname:"remaining_qty",
								hidden: 1,
								// read_only: 1,
								// in_list_view: 1,
								label: __('Remaining Qty')
							},{

								fieldtype:'Float',
								fieldname:"rate",
								hidden: 1,
								// read_only: 1,
								// in_list_view: 1,
								label: __('Rate')
							},
							]
						},
						
					],
					primary_action(values) {
						let final_remaining_qty = 0
						frappe.call({method: "gatepass.gatepass.doctype.gate_pass.gate_pass.material_returns_through_gatepass",
						args: {
							name:frm.doc.name,
							doctype:frm.doc.doctype,
							return_item :values
						},"callback": function(response){
							if(response){
								
								values['alternative_items'].forEach(gate_child=>{
						
									let row = frappe.get_doc(child_doctype, gate_child.docname);
									let transfer_in = gate_child.qty
									let qty = 0
									let remaining_qty = 0
									let amount = 0.0
									row['item_code'] = gate_child.item_code
									if (row.remaining_qty === 0){
										qty = transfer_in+0
										remaining_qty = (row.actual_qty - (transfer_in+0))
										final_remaining_qty += (row.actual_qty - (transfer_in+0))
									}
									else{
										qty = transfer_in+row.qty
										remaining_qty = (row.actual_qty - (transfer_in+row.qty))
										final_remaining_qty += (row.actual_qty - (transfer_in+row.qty))
									}

									frappe.model.set_value(row.doctype, row.name, 'qty', qty);
									
									if (final_remaining_qty === 0){
										let status = 'Completed'
										frm.set_value("status",status)
									}
									else{
										frm.set_value("status","Partially Return")
									}
									amount = row.rate * qty
									frappe.model.set_value(row.doctype,row.name,"remaining_qty",remaining_qty)
									frappe.model.set_value(row.doctype,row.name,"amount",amount)
									frm.trigger(gate_child.item_code, row.doctype, row.name)
								});
							}
						}
					});
					refresh_field(child_docname);
					dialogs.hide();
				},
					size: 'medium', 
					primary_action_label: __('Return'),
					
				});
				
				// To get child date and set into table
				let item = frm.doc.item
				item.forEach(child_data => {
					dialogs.fields_dict.alternative_items.df.data.push({
						"docname": child_data.name,
						"item_code": child_data.item_code,
						"item_name":child_data.item_name,
						"qty": child_data.qty, // Remaining Qty  Tranfor IN To Store
						"uom":child_data.uom,
						"amount":child_data.amount,
						"actual_qty":child_data.actual_qty,
						"remaining_qty":child_data.remaining_qty,
						'rate':child_data.rate,
					});
				})
				data = dialogs.fields_dict.alternative_items.df.data;
				dialogs.fields_dict.alternative_items.grid.refresh();
				dialogs.show();
				
			})
		}
	}  
});
